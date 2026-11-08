"""Read-only consistency adapter for archived fixed ERPNext control observations.

This does not execute source or authenticate the producer. A passing historical
control includes expected original failures and grants no release authority.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

from framework.kernel import contract_digest, digest, identity, verify, sha as valid_sha
from .app_trial import HERE, classify, sha

CONTRACT = {'schema': 1, 'checks': ['original-regressions-reproduced', 'upstream-fixed-tests'],
            'assumptions': ['Archived inspected-code observations only; no fresh source execution.',
                            'Record pin must come from a trusted review path; no producer authentication.',
                            'Fixed five-test case, declared runtime; no whole-app or frontend guarantee.',
                            'Recorded hashes bind claims, not proof that a producer ran those bytes.',
                            'Host libraries incompletely fingerprinted; no admission or release authority.']}
FILES = ('app_case.json', 'app_trial.py', 'app_bootstrap.py', 'app_collect.py', 'app_inventory.py')


def producer_profile(report):
    """Select a reviewed historical producer, never infer one from the record."""
    registry = json.loads((HERE / 'producer-profiles.json').read_text())
    if (type(registry) is not dict or set(registry) != {'schema', 'profiles'} or
            type(registry['schema']) is not int or registry['schema'] != 1 or
            type(registry['profiles']) is not list or not registry['profiles']):
        raise ValueError('invalid producer profile registry')
    source = (HERE / 'app_trial.py').read_text()
    predicates = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == 'classify']
    if len(predicates) != 1:
        raise ValueError('ambiguous control predicate')
    predicate = hashlib.sha256(ast.get_source_segment(source, predicates[0]).encode()).hexdigest()
    matches = []
    ids = set()
    for profile in registry['profiles']:
        if (type(profile) is not dict or set(profile) !=
                {'id', 'producer_revision', 'case', 'verifier', 'control_predicate_source_sha256'} or
                type(profile['id']) is not str or not profile['id'] or profile['id'] in ids or
                type(profile['producer_revision']) is not str or len(profile['producer_revision']) != 40 or
                any(c not in '0123456789abcdef' for c in profile['producer_revision']) or
                type(profile['case']) is not dict or type(profile['verifier']) is not dict or
                set(profile['verifier']) != set(FILES)):
            raise ValueError('invalid producer profile')
        ids.add(profile['id'])
        for value in [*profile['verifier'].values(), profile['control_predicate_source_sha256']]:
            valid_sha(value)
        if profile['case'] == report['case'] and profile['verifier'] == report['verifier']:
            matches.append(profile)
    if len(matches) != 1 or matches[0]['control_predicate_source_sha256'] != predicate:
        raise ValueError('unknown/ambiguous producer profile or changed control predicate')
    return matches[0]


def inspect(report, expected_record):
    result = {'mode': 'archived-consistency-only', 'producer_authenticated': False,
              'fresh_source_execution': False, 'policy_admitted': False, 'release_authority': False}
    try:
        valid_sha(expected_record)
        if type(report) is not dict:
            raise ValueError('record must be a JSON object')
        if digest(report) != expected_record:
            raise ValueError('record identity mismatch')
        if (type(report.get('schema')) is not int or report['schema'] != 1 or
                report.get('completed') is not True or report.get('controls_match') is not True or report.get('error')):
            raise ValueError('incomplete or failed source run')
        profile = producer_profile(report)
        case = profile['case']
        observations = report['observations']
        if type(observations) is not dict or set(observations) != {'base', 'head'}:
            raise ValueError('incomplete control observations')
        sources = report['sources']
        for name in ('frappe', 'payments', 'erpnext'):
            if sources[name]['revision'] != case['erpnext_base' if name == 'erpnext' else name]:
                raise ValueError('source revision mismatch')
        isolation = report['isolation']
        expected_isolation = {'network_attachments': {}, 'memory': 5368709120, 'memory_swap': 5368709120,
                              'pids': 256, 'readonly_root': True, 'cap_drop': ['ALL'],
                              'security': ['no-new-privileges'], 'user': '1001:1001',
                              'image_id': 'sha256:4643e61ff9ef910bac8e011107d87c0fd0ab14ebacf1d296b0c0a0cd96fefff4'}
        if isolation != expected_isolation or isolation['readonly_root'] is not True:
            raise ValueError('fixed isolation profile mismatch')
        environment = report['environment']
        if (type(environment) is not dict or set(environment) !=
                {'schema', 'python', 'python_sha256', 'packages', 'binaries', 'site_packages'} or
                type(environment['schema']) is not int or environment['schema'] != 1 or
                type(environment['python']) is not str or not environment['python'].strip() or
                type(environment['packages']) is not list or not environment['packages'] or
                type(environment['binaries']) is not dict or
                set(environment['binaries']) != {'bench', 'node', 'mariadbd', 'redis-server'}):
            raise ValueError('invalid installed environment inventory')
        valid_sha(environment['python_sha256'])
        for package in environment['packages']:
            if (type(package) is not dict or set(package) != {'name', 'version'} or
                    any(type(package[key]) is not str or not package[key].strip() for key in ('name', 'version'))):
                raise ValueError('invalid package inventory entry')
        for binary in environment['binaries'].values():
            if (type(binary) is not dict or set(binary) != {'sha256', 'version'} or
                    type(binary['version']) is not str or not binary['version'].strip()):
                raise ValueError('invalid binary inventory entry')
            valid_sha(binary['sha256'])
        tree = environment['site_packages']
        if (type(tree) is not dict or set(tree) != {'sha256', 'files'} or
                type(tree['files']) is not int or not 0 < tree['files'] <= 200000):
            raise ValueError('invalid package file inventory')
        valid_sha(tree['sha256'])
        for variant, row in observations.items():
            expected_source = {'module_sha256': sources['base-module' if variant == 'base' else 'head-report.py']['sha256'],
                               'heldout_sha256': sources['heldout.py']['sha256']}
            if not classify(case, row, variant) or row['source_before'] != expected_source or row['source_after'] != expected_source:
                raise ValueError('control inventory/outcome or source identity mismatch: ' + variant)
        inputs = {
            'source': {name: sources[key]['sha256'] for name, key in
                       [('original-report.py', 'base-module'), ('upstream-report.py', 'head-report.py')]},
            'artifact': {**{name + '.archive': sources[name]['archive_sha256'] for name in ('frappe', 'payments', 'erpnext')},
                         'heldout.py': sources['heldout.py']['sha256'], 'record': expected_record, 'case': digest(case)},
            'verifier': {**{'producer/' + name: value for name, value in report['verifier'].items()},
                         'archive-validator.py': sha(Path(__file__)),
                         'producer-profile': digest(profile),
                         'current-control-predicate': profile['control_predicate_source_sha256'],
                         'kernel.py': sha(HERE.parents[1] / 'framework/kernel.py')},
            'environment': {'recorded-packages-binaries': digest(report['environment']),
                            'recorded-isolation': digest(report['isolation']),
                            'archive-validator-python': sha(Path(sys.executable).resolve()),
                            'recorded-python': environment['python_sha256'],
                            **{'recorded-' + name: value['sha256'] for name, value in environment['binaries'].items()}}}
        bound = identity(CONTRACT, inputs)
        evidence = [{'id': name, 'status': 'passed', 'identity': bound} for name in CONTRACT['checks']]
        receipt = verify(CONTRACT, contract_digest(CONTRACT), inputs, evidence)
        result.update(consistent=receipt['consistent'], contract=CONTRACT, inputs=inputs,
                      evidence=evidence, receipt=receipt, record_sha256=expected_record,
                      producer_profile=profile['id'])
    except (KeyError, TypeError, ValueError, OSError, RecursionError, SyntaxError) as exc:
        result.update(consistent=False, reason=str(exc))
    return result


def summary(report, result):
    """Present validated controls without treating expected failures as passes."""
    if not result['consistent']:
        return 'Archived controls: inconsistent\nReason: ' + json.dumps(result.get('reason', 'unknown'), ensure_ascii=True)
    lines = ['Archived controls: consistent', 'Producer profile: ' + result['producer_profile']]
    for variant, label, revision in (('base', 'Baseline', report['case']['erpnext_base']),
                                      ('head', 'Final report control', report['case']['erpnext_head'])):
        row = report['observations'][variant]['runs'][0]
        failures = len(row['failure_ids'])
        lines.append(f'{label} {revision}: {row["tests"] - failures}/{row["tests"]} tests passed; {failures} failed')
    lines.append('Expected baseline failures reproduced: ' + ', '.join(report['case']['original_failure_names']))
    lines.extend(['Record SHA256: ' + result['record_sha256'],
                  'Archived observations only: no fresh execution, producer authentication or release authority.'])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--expected-record-sha256', required=True)
    parser.add_argument('--format', choices=('json', 'summary'), default='json')
    args = parser.parse_args()
    from framework.preservation import read_json
    try:
        report = read_json(args.report)
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, 'Cannot read archive: ' + type(exc).__name__ + '\n')
    result = inspect(report, args.expected_record_sha256)
    print(summary(report, result) if args.format == 'summary' else json.dumps(result, indent=2))
    return 0 if result['consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
