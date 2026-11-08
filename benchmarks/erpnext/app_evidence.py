"""Read-only consistency adapter for archived fixed ERPNext control observations.

This does not execute source or authenticate the producer. A passing historical
control includes expected original failures and grants no release authority.
"""
import argparse
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
        case = json.loads((HERE / 'app_case.json').read_text())
        if report['case'] != case or type(report['verifier']) is not dict or set(report['verifier']) != set(FILES):
            raise ValueError('unsupported case or verifier inventory')
        if any(sha(HERE / name) != report['verifier'][name] for name in FILES):
            raise ValueError('recorded producer verifier differs from current fixed evaluator')
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
                      evidence=evidence, receipt=receipt, record_sha256=expected_record)
    except (KeyError, TypeError, ValueError, OSError, RecursionError) as exc:
        result.update(consistent=False, reason=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--expected-record-sha256', required=True)
    args = parser.parse_args()
    from framework.preservation import read_json
    try:
        report = read_json(args.report)
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, 'Cannot read archive: ' + type(exc).__name__ + '\n')
    result = inspect(report, args.expected_record_sha256)
    print(json.dumps(result, indent=2))
    return 0 if result['consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
