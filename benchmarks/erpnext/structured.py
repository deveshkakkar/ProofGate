"""Fixed structured-author replay helpers; inspected diagnostics, no authority."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

from framework.kernel import digest, sha as valid_sha
from .module_edits import apply_edits

HERE = Path(__file__).resolve().parent
ARMS = ('baseline', 'feedback')
VARIANTS = ('base', 'head', *ARMS)
FILES = ('app_case.json', 'app_trial.py', 'app_bootstrap.py', 'app_collect.py',
         'app_inventory.py', 'module_edits.py', 'structured.py', 'structured-candidates.json')
BASE_SHA = '394bf2f7608ce57a19d0f976896bd7f09fa1ec948d9e86d88475e9031851b687'
HEAD_SHA = '3e916f2c9c7f6a17fa6f27b30c134ee2d22c7c40258d8a50ec8e92723f714049'
TEST_SHA = '57bc21891324dd9c099af619b5d0132ad6c507d3f4e887e163d168b1c9b7be6b'


def prepare_candidates(source, manifest, destination):
    """Reconstruct both exact eligible edits into fixed readonly worker inputs."""
    if (type(manifest) is not dict or type(manifest.get('schema')) is not int or manifest['schema'] != 1 or
            manifest.get('protocol') != 'structured-exact-text-v2' or manifest.get('source_sha256') != BASE_SHA or
            manifest.get('base_revision') != '04afe19d8ef067eec3852f4ac8007af42718d0b6' or
            type(manifest.get('arms')) is not dict or set(manifest['arms']) != set(ARMS)):
        raise ValueError('unsupported fixed structured candidate manifest')
    candidates = {}
    for arm in ARMS:
        row = manifest['arms'][arm]
        if type(row) is not dict or row.get('eligible') is not True:
            raise ValueError('both fixed candidates must be eligible before execution')
        valid_sha(row['module_sha256'])
        candidate = apply_edits(source, BASE_SHA, row['proposal'])
        ast.parse(candidate)  # Syntax validation, not source execution.
        if hashlib.sha256(candidate.encode()).hexdigest() != row['module_sha256']:
            raise ValueError('reconstructed candidate identity mismatch')
        candidates[arm] = candidate
    # All checks precede writes. Candidate data cannot choose paths/commands.
    for arm, candidate in candidates.items():
        (destination / (arm + '-report.py')).write_text(candidate)
    (destination / 'structured-variants.json').write_text(json.dumps(list(VARIANTS)) + '\n')


def candidate_verdict(case, observation):
    """Require the same complete five-test inventory before interpreting failures."""
    incomplete = {'status': 'inconclusive'}
    try:
        if type(observation) is not dict or type(observation.get('schema')) is not int or observation['schema'] != 1:
            return incomplete
        runs = observation['runs']
        if type(runs) is not list or len(runs) != 1 or type(runs[0]) is not dict: return incomplete
        row = runs[0]
        prefix = case['test_module'] + '.' + case['test_class'] + '.'
        wanted = {prefix + name for name in case['test_names']}
        ids, failures = row['test_ids'], row['failure_ids']
        if (type(ids) is not list or any(type(x) is not str for x in ids) or len(ids) != len(wanted) or set(ids) != wanted or
                type(row['tests']) is not int or row['tests'] != len(wanted) or
                type(failures) is not list or any(type(x) is not str for x in failures) or
                len(failures) != len(set(failures)) or not set(failures) <= wanted or
                any(row[key] != [] for key in ('error_ids', 'skipped_ids', 'expected_failure_ids', 'unexpected_success_ids')) or
                type(observation['transport_exit']) is not int or
                observation['transport_exit'] not in ((0, 1) if failures else (0,))):
            return incomplete
        change = prefix + case['original_failure_names'][0]
        return {'status': 'failed' if failures else 'passed', 'tests': len(wanted),
                'earlier_four_preserved': not (set(failures) - {change}),
                'read_denial_satisfied': change not in failures, 'failure_ids': failures}
    except (KeyError, TypeError, IndexError):
        return incomplete


def score(report, expected_record, producer, manifest):
    """Check an independently pinned archived report and reviewed producer profile.

    Profile registration binds reviewed historical claims; it is not authentication.
    The producer profile is external trusted input, never created from report data here.
    """
    result = {'scope': 'archived-structured-paired-replay', 'outcome': 'inconclusive', 'valid_controls': False,
              'producer_authenticated': False, 'fresh_source_execution': False,
              'policy_admitted': False, 'release_authority': False}
    try:
        from .app_trial import classify
        valid_sha(expected_record)
        if type(report) is not dict or type(manifest) is not dict:
            raise ValueError('report and candidate manifest must be objects')
        if digest(report) != expected_record: raise ValueError('record identity mismatch')
        case = json.loads((HERE / 'intermediate_case.json').read_text())
        if (type(producer) is not dict or set(producer) != {'schema', 'revision', 'case', 'verifier',
                'candidate_manifest_sha256', 'environment_sha256', 'isolation_sha256', 'control_predicate_source_sha256'} or
                type(producer['schema']) is not int or producer['schema'] != 1 or producer['case'] != case or
                type(producer['revision']) is not str or len(producer['revision']) != 40 or
                any(c not in '0123456789abcdef' for c in producer['revision']) or
                type(producer['verifier']) is not dict or set(producer['verifier']) != set(FILES)):
            raise ValueError('invalid reviewed producer profile')
        for value in [*producer['verifier'].values(), *[producer[k] for k in
                ('candidate_manifest_sha256', 'environment_sha256', 'isolation_sha256', 'control_predicate_source_sha256')]]:
            valid_sha(value)
        text = (HERE / 'app_trial.py').read_text()
        predicate = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == 'classify']
        if len(predicate) != 1 or hashlib.sha256(ast.get_source_segment(text, predicate[0]).encode()).hexdigest() != producer['control_predicate_source_sha256']:
            raise ValueError('changed control predicate')
        if (type(report.get('schema')) is not int or report['schema'] != 1 or report.get('completed') is not True or
                report.get('controls_match') is not True or report.get('error') or report.get('profile') != 'structured' or
                report['case'] != case or report['verifier'] != producer['verifier'] or
                digest(manifest) != producer['candidate_manifest_sha256'] or
                report['candidate_manifest_sha256'] != digest(manifest) or
                digest(report['environment']) != producer['environment_sha256'] or
                digest(report['isolation']) != producer['isolation_sha256']):
            raise ValueError('incomplete or mismatched reviewed run')
        # Exact environment/isolation content is independently checked at profile registration.
        sources = report['sources']
        for name in ('frappe', 'payments', 'erpnext'):
            if sources[name]['revision'] != case['erpnext_base' if name == 'erpnext' else name]:
                raise ValueError('source revision mismatch')
            valid_sha(sources[name]['archive_sha256'])
        if (sources['base-module']['sha256'] != BASE_SHA or sources['head-report.py']['sha256'] != HEAD_SHA or
                sources['heldout.py']['sha256'] != TEST_SHA or set(report['observations']) != set(VARIANTS)):
            raise ValueError('fixed source/test/variant inventory mismatch')
        if (type(manifest.get('schema')) is not int or manifest['schema'] != 1 or
                manifest.get('protocol') != 'structured-exact-text-v2' or manifest.get('source_sha256') != BASE_SHA or
                manifest.get('base_revision') != case['erpnext_base'] or set(manifest['arms']) != set(ARMS) or
                any(manifest['arms'][arm]['eligible'] is not True for arm in ARMS)):
            raise ValueError('fixed candidate manifest mismatch')
        for variant in VARIANTS:
            observation = report['observations'][variant]
            module = BASE_SHA if variant == 'base' else HEAD_SHA if variant == 'head' else manifest['arms'][variant]['module_sha256']
            valid_sha(module)
            if variant in ARMS and sources[variant + '-report.py']['sha256'] != module:
                raise ValueError('candidate source input mismatch')
            expected_source = {'module_sha256': module, 'heldout_sha256': TEST_SHA}
            if observation['source_before'] != expected_source or observation['source_after'] != expected_source:
                raise ValueError('source/test identity drift: ' + variant)
            if variant in ('base', 'head') and not classify(case, observation, variant):
                raise ValueError('fixed control inventory/outcome mismatch')
        result['valid_controls'] = True
        arms = {arm: candidate_verdict(case, report['observations'][arm]) for arm in ARMS}
        result['arms'] = arms
        states = [arms[arm]['status'] for arm in ARMS]
        if 'inconclusive' not in states:
            result['outcome'] = ('passing-tie' if states == ['passed', 'passed'] else
                                 'neither-passed' if states == ['failed', 'failed'] else
                                 'feedback-only-passed' if states[1] == 'passed' else 'baseline-only-passed')
        result.update(record_sha256=expected_record, producer_revision=producer['revision'],
                      producer_profile_sha256=digest(producer),
                      archive_validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError, SyntaxError) as exc:
        result.update(valid_controls=False, outcome='inconclusive', reason=str(exc))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--producer', type=Path, required=True)
    parser.add_argument('--expected-record-sha256', required=True)
    args = parser.parse_args()
    from framework.preservation import read_json
    try:
        result = score(read_json(args.report), args.expected_record_sha256,
                       read_json(args.producer), read_json(HERE / 'structured-candidates.json'))
    except (ValueError, OSError, RecursionError) as exc:
        parser.exit(2, 'Cannot read replay inputs: ' + type(exc).__name__ + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['valid_controls'] else 1)
