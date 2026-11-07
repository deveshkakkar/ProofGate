"""Prepare fixed public historical controls and exercise the shadow transport."""
import argparse
import json
from pathlib import Path
import subprocess

from .replay import evaluate
from .score import classify


def git(repository, *args):
    result = subprocess.run(['/usr/bin/git', '-C', str(repository), '-c', 'core.hooksPath=/dev/null',
                             '-c', 'credential.helper=', '-c', 'credential.interactive=false', *args],
                            capture_output=True, timeout=60)
    if result.returncode or len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError('public historical source could not be prepared')
    return result.stdout


def compare_control(case, version, report):
    expected = {suite: classify(case['controls'][version][suite], case['expected_tests'][suite])
                for suite in ('heldout', 'contract')}
    if case['id'] == 'model_permissions':
        expected['compatibility'] = classify(case['posthoc_anonymous_compatibility'][version], 1)
    if any(status == 'inconclusive' for status in expected.values()):
        raise ValueError('reference control expectations are incomplete')
    observed = {suite: row['status'] for suite, row in report['checks'].items()}
    consistent = all(status == 'passed' for status in expected.values())
    return {'schema': 1, 'case': case['id'], 'version': version,
            'expected_statuses': expected, 'observed_statuses': observed,
            'expected_consistent': consistent,
            'observed_consistent': report['receipt']['consistent'],
            'control_matched': observed == expected and report['receipt']['consistent'] is consistent,
            'scope': 'historical control reproduction; not release approval'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=('or_composition', 'model_permissions', 'renderer_boundary'))
    parser.add_argument('--version', required=True, choices=('original', 'upstream'))
    for name in ('dependencies', 'workspace', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--backend', choices=('user', 'github-hosted'), default='user')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    case = next(row for row in json.loads((here / 'results.json').read_text())['cases'] if row['id'] == args.case)
    case = dict(case, test_file='test_renderers.py' if args.case == 'renderer_boundary' else 'test_permissions.py')
    try:
        args.workspace.mkdir(mode=0o700, parents=False, exist_ok=False)
        repository = args.workspace / 'reference'
        subprocess.run(['/usr/bin/git', 'init', '--quiet', '--template=', str(repository)], check=True, timeout=10)
        for revision in (case['base_sha'], case['heldout_sha']):
            git(repository, 'fetch', '--quiet', '--depth=1', 'https://github.com/encode/django-rest-framework.git', revision)
        revision = case['base_sha'] if args.version == 'original' else case['heldout_sha']
        candidate = args.workspace / 'candidate.py'
        candidate.write_bytes(git(repository, 'show', revision + ':' + case['module']))
        heldout = args.workspace / 'heldout.py'
        heldout.write_bytes(git(repository, 'show', case['heldout_sha'] + ':tests/' + case['test_file']))
        report = evaluate(case, repository, candidate, heldout, args.dependencies, args.output,
                          args.backend, compatibility=args.case == 'model_permissions')
        if any(check['status'] == 'inconclusive' for check in report['checks'].values()):
            raise ValueError('shadow control evaluation was inconclusive')
        control = compare_control(case, args.version, report)
        (args.output / 'control.json').write_text(json.dumps(control, indent=2) + '\n')
        print(json.dumps(control))
        return 0 if control['control_matched'] else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'Historical shadow control could not complete: ' + type(exc).__name__ + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
