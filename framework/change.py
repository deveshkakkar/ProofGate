"""Check complete finite intended-change observations and legacy preservation.

Inputs are evaluator-owned traces. A matching proposal has no policy-admission,
source-binding, producer-authentication or deployment authority.
"""
import argparse
import json
from pathlib import Path
import re

from .kernel import digest
from .preservation import canonical, compare, index_trace, prepare, read_json, require


def prepare_spec(spec):
    require(type(spec) is dict and set(spec) == {
        'schema', 'preservation', 'reference_trace_sha256', 'expected_change', 'provenance'},
        'invalid change specification fields')
    require(type(spec['schema']) is int and spec['schema'] == 1, 'unsupported change schema')
    require(type(spec['reference_trace_sha256']) is str and
            re.fullmatch('[0-9a-f]{64}', spec['reference_trace_sha256']), 'invalid reference trace pin')
    provenance = spec['provenance']
    require(type(provenance) is list and provenance and
            all(type(value) is str and value.strip() for value in provenance), 'explicit provenance required')
    inputs, excluded = prepare(spec['preservation'])
    require(excluded, 'intended change region required; use preservation for unchanged behavior')
    changed_inputs = [row for row in inputs if canonical(row) in excluded]
    expected = index_trace(spec['expected_change'], changed_inputs)
    return inputs, changed_inputs, expected


def spec_id(spec):
    prepare_spec(spec)
    canonical(spec)
    return digest(spec)


def check(spec, expected_spec, reference, candidate):
    result = {'assurance': 'finite observations only', 'policy_admitted': False,
              'source_execution_verified': False, 'producer_authenticated': False,
              'reference_correctness_established': False, 'specified_change_checked': False}
    try:
        inputs, changed_inputs, expected = prepare_spec(spec)
        require(type(expected_spec) is str and re.fullmatch('[0-9a-f]{64}', expected_spec),
                'invalid change specification pin')
        require(spec_id(spec) == expected_spec, 'change specification identity mismatch')
        index_trace(reference, inputs)
        require(digest(reference) == spec['reference_trace_sha256'], 'reference trace identity mismatch')
        observed = index_trace(candidate, inputs)
        preservation = compare(spec['preservation'], digest(spec['preservation']), reference, candidate)
        require(preservation['valid'], 'invalid preservation observations')
        violations = []
        for row in changed_inputs:
            key = canonical(row)
            if canonical(expected[key]) != canonical(observed[key]):
                violations.append({'input': row, 'expected': expected[key], 'candidate': observed[key]})
        result.update(valid=True, satisfied=preservation['preserved'] and not violations,
                      specification_sha256=expected_spec, reference_trace_sha256=digest(reference),
                      candidate_trace_sha256=digest(candidate), preservation=preservation,
                      specified_change_checked=True,
                      intended_change={'satisfied': not violations, 'checked_inputs': len(changed_inputs),
                                       'violation_count': len(violations), 'counterexamples': violations[:20]})
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        result.update(valid=False, satisfied=False, error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('specification', 'reference', 'candidate'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-specification-sha256', required=True)
    args = parser.parse_args()
    try:
        report = check(read_json(args.specification), args.expected_specification_sha256,
                       read_json(args.reference), read_json(args.candidate))
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, 'Cannot read change inputs: ' + type(exc).__name__ + '\n')
    print(json.dumps(report, indent=2))
    return 2 if not report['valid'] else 0 if report['satisfied'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
