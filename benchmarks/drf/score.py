"""Portable offline scoring; does not execute candidate code or trust merge status."""
import argparse
import json
from pathlib import Path


def classify(observation, expected_tests=None):
    """Only complete, internally consistent test observations can pass or fail."""
    if not isinstance(observation, dict):
        return 'inconclusive'
    fields = ('exit_code', 'tests', 'failures', 'errors', 'skipped')
    if any(type(observation.get(key)) is not int for key in fields):
        return 'inconclusive'
    code, tests, failures, errors, skipped = (observation[key] for key in fields)
    if min(tests, failures, errors, skipped) < 0 or tests == 0:
        return 'inconclusive'
    if expected_tests is not None and (type(expected_tests) is not int or tests != expected_tests):
        return 'inconclusive'
    if failures + errors + skipped > tests or errors or skipped:
        return 'inconclusive'
    if code == 0 and failures == 0:
        return 'passed'
    if code == 1 and failures > 0:
        return 'failed'
    return 'inconclusive'


def outcome(arm, inventory):
    if (not isinstance(inventory, dict) or set(inventory) != {'heldout', 'contract'} or
            any(type(count) is not int or count <= 0 for count in inventory.values())):
        return 'inconclusive'
    if not isinstance(arm, dict):
        return 'inconclusive'
    statuses = [classify(arm.get(check), inventory[check]) for check in ('heldout', 'contract')]
    if 'inconclusive' in statuses:
        return 'inconclusive'
    return 'passed' if all(status == 'passed' for status in statuses) else 'failed'


def summarize(report):
    if not isinstance(report, dict) or type(report.get('schema')) is not int or report['schema'] != 1:
        raise ValueError('unsupported report schema')
    cases = report.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('nonempty cases required')
    ids = [case.get('id') if isinstance(case, dict) else None for case in cases]
    if any(not isinstance(name, str) or not name for name in ids) or len(set(ids)) != len(ids):
        raise ValueError('invalid or duplicate case IDs')
    result = {'cases': [], 'treatment_wins': 0, 'treatment_losses': 0,
              'ties_passed': 0, 'ties_failed': 0, 'inconclusive_pairs': 0}
    for case in cases:
        arms = case.get('arms', {})
        if not isinstance(arms, dict):
            raise ValueError('arms must be an object')
        inventory = case.get('expected_tests')
        baseline, contract = outcome(arms.get('baseline'), inventory), outcome(arms.get('contract'), inventory)
        controls = case.get('controls', {})
        controls_valid = (isinstance(controls, dict) and
                          outcome(controls.get('original'), inventory) == 'failed' and
                          outcome(controls.get('upstream'), inventory) == 'passed')
        if not controls_valid or 'inconclusive' in (baseline, contract):
            category = 'inconclusive_pairs'
        elif baseline == contract:
            category = 'ties_' + baseline
        elif contract == 'passed':
            category = 'treatment_wins'
        else:
            category = 'treatment_losses'
        result[category] += 1
        result['cases'].append({'id': case['id'], 'baseline': baseline,
                                'contract': contract, 'controls_valid': controls_valid, 'category': category})
    result['scope'] = 'descriptive paired outcomes only; no statistical or novelty claim'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    try:
        with args.report.open('rb') as handle:
            raw = handle.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError('report exceeds 4 MiB')
        print(json.dumps(summarize(json.loads(raw)), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, 'Cannot score report: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
