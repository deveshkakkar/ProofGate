#!/usr/bin/env python3
"""Real hosted CLI baseline/mutation smoke; no models, upstream apps or admission."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from framework.kernel import digest, identity


def main():
    if os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('This source-executing smoke is for disposable GitHub-hosted runners only.')
    output = Path(sys.argv[1]); output.mkdir(parents=True, exist_ok=False)
    records = []
    def command(label, args, expected):
        result = subprocess.run(['/usr/bin/python3', '-B', '-m', 'framework', *args],
                                cwd=ROOT, capture_output=True, text=True, timeout=40)
        # Fixed inspected candidates only; bounded outer job, no inherited environment in worker.
        (output / (label + '.stdout')).write_text(result.stdout)
        (output / (label + '.stderr')).write_text(result.stderr)
        records.append({'name': label, 'exit': result.returncode, 'expected_exit': expected})
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        if result.returncode != expected:
            raise RuntimeError(label + ': unexpected exit; inspect retained diagnostics')
        return result
    command('doctor', ['doctor'], 0)
    candidate = output / 'candidate'; candidate.mkdir()
    for name in ('app.py', 'rule.py'):
        shutil.copyfile(ROOT / 'examples/entitlement' / name, candidate / name)
    report_path = output / 'baseline.json'
    common = ['check-entitlement', '--candidate', str(candidate)]
    baseline = command('baseline', common + ['--output', str(report_path)], 0)
    report = json.loads(report_path.read_text())
    assert report['receipt']['consistent'] and report['candidate_matches_snapshot']
    assert report['receipt']['identity'] == identity(report['contract'], report['inputs'])
    assert digest(report['inputs']['source']) in baseline.stdout
    for name in ('app.py', 'rule.py'):
        assert report['inputs']['source'][name] == hashlib.sha256((candidate / name).read_bytes()).hexdigest()
    frozen = report_path.read_bytes()
    command('no-overwrite', common + ['--output', str(report_path)], 2)
    assert report_path.read_bytes() == frozen
    app = candidate / 'app.py'
    old = "return {'allowed': allow(**row)}"
    assert app.read_text().count(old) == 1
    app.write_text(app.read_text().replace(old,
        "row = dict(row, resource_tenant=row['subject_tenant'])\n    return {'allowed': allow(**row)}"))
    changed_path = output / 'spoof.json'
    failed = command('tenant-spoof', common + ['--output', str(changed_path)], 1)
    changed = json.loads(changed_path.read_text())
    assert changed['candidate_matches_snapshot'] and not changed['receipt']['consistent']
    assert [c['passed'] for c in changed['checks']] == [True, False]
    assert '6/80 mismatches' in failed.stdout and 'Expected: {"allowed": false}' in failed.stdout
    assert 'no policy admission' in failed.stdout
    (output / 'smoke-result.json').write_text(json.dumps({
        'completed': True, 'revision': os.environ.get('GITHUB_SHA'),
        'scope': 'actual CLI, fixed inspected entitlement baseline and tenant-spoof; not hostile-source or admission assurance',
        'commands': records}, indent=2) + '\n')
    print('PASS: actual CLI baseline, mutation, source binding and immutable report checks')


if __name__ == '__main__':
    main()
