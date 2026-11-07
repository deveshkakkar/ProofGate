"""Finite change-scope preservation over trusted, externally collected traces.

This compares observations; it does not execute code, authenticate producers,
certify the reference or verify behavior inside the allowed change region.
"""
import argparse
import itertools
import json
from pathlib import Path
import re

from .kernel import digest

LIMIT = 4096


def canonical(value):
    def validate(item, depth=0):
        require(depth <= 16, 'JSON nesting exceeds bound')
        if type(item) is dict:
            require(all(type(key) is str for key in item), 'JSON object keys must be strings')
            for child in item.values():
                validate(child, depth + 1)
        elif type(item) is list:
            for child in item:
                validate(child, depth + 1)
        else:
            require(type(item) in (str, int, float, bool, type(None)), 'JSON values required')
    validate(value)
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(policy):
    require(type(policy) is dict and set(policy) == {'schema', 'input_domain', 'allowed_change', 'assumptions'}, 'invalid policy fields')
    require(type(policy['schema']) is int and policy['schema'] == 1, 'unsupported policy schema')
    assumptions = policy['assumptions']
    require(type(assumptions) is list and assumptions and all(type(a) is str and a.strip() for a in assumptions), 'explicit assumptions required')
    domain = policy['input_domain']
    require(type(domain) is dict and 0 < len(domain) <= 16, 'invalid domain')
    count = 1
    for key, values in domain.items():
        require(type(key) is str and re.fullmatch('[a-z][a-z0-9_]{0,63}', key), 'invalid dimension')
        require(type(values) is list and 0 < len(values) <= 64, 'invalid dimension values')
        require(all(type(v) in (str, int, bool, type(None)) for v in values), 'domain values must be JSON scalars without floats')
        encoded = [canonical(v) for v in values]
        require(all(len(value) <= 128 for value in encoded), 'domain value exceeds128 characters')
        require(len(set(encoded)) == len(values), 'duplicate dimension values')
        count *= len(values)
        require(count <= LIMIT, 'domain exceeds4096 inputs')
    scope = policy['allowed_change']
    require(scope is None or type(scope) is dict and scope, 'empty scope would exempt everything')
    if scope is not None:
        require(set(scope) <= set(domain), 'unknown scope dimension')
        for key, values in scope.items():
            require(type(values) is list and values, 'invalid scope values')
            encoded = [canonical(v) for v in values]
            require(len(encoded) == len(set(encoded)) and set(encoded) <= {canonical(v) for v in domain[key]}, 'scope outside domain')
    names = sorted(domain)
    inputs = [dict(zip(names, values)) for values in itertools.product(*(domain[name] for name in names))]
    excluded = {canonical(row) for row in inputs if scope is not None and
                all(canonical(row[key]) in {canonical(value) for value in values} for key, values in scope.items())}
    require(len(excluded) < len(inputs), 'scope exempts the entire domain')
    return inputs, excluded


def policy_id(policy):
    prepare(policy)
    return digest(policy)


def index_trace(rows, inputs):
    require(type(rows) is list and len(rows) == len(inputs), 'trace must cover the exact domain')
    expected = {canonical(row) for row in inputs}
    result = {}
    for row in rows:
        require(type(row) is dict and set(row) == {'input', 'output'}, 'invalid observation fields')
        require(type(row['input']) is dict, 'invalid observed input')
        key = canonical(row['input'])
        require(key in expected and key not in result, 'unknown or duplicate observed input')
        output = canonical(row['output'])
        require(len(output) <= 16384, 'observed output exceeds bound')
        result[key] = row['output']
    require(set(result) == expected, 'missing observed input')
    return result


def compare(policy, expected_policy, reference, candidate):
    result = {'assurance': 'finite preservation only', 'new_semantics_checked': False,
              'producer_authenticated': False, 'reference_correctness_established': False}
    try:
        inputs, excluded = prepare(policy)
        require(type(expected_policy) is str and re.fullmatch('[0-9a-f]{64}', expected_policy), 'invalid policy pin')
        require(digest(policy) == expected_policy, 'policy identity mismatch')
        old, new = index_trace(reference, inputs), index_trace(candidate, inputs)
        violations = []
        for row in inputs:
            key = canonical(row)
            if key not in excluded and canonical(old[key]) != canonical(new[key]):
                violations.append({'input': row, 'reference': old[key], 'candidate': new[key]})
        result.update(valid=True, preserved=not violations, policy_sha256=expected_policy,
                      domain_inputs=len(inputs), checked_inputs=len(inputs) - len(excluded),
                      unverified_change_inputs=len(excluded), violation_count=len(violations),
                      counterexamples=violations[:20], reference_trace_sha256=digest(reference),
                      candidate_trace_sha256=digest(candidate))
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        result.update(valid=False, preserved=False, error=str(exc))
    return result


def read_json(path):
    with path.open('rb') as source:
        raw = source.read(4 * 1024 * 1024 + 1)
    require(len(raw) <= 4 * 1024 * 1024, 'JSON input exceeds4MiB')
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('policy', 'reference', 'candidate'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-policy-sha256', required=True)
    args = parser.parse_args()
    try:
        result = compare(read_json(args.policy), args.expected_policy_sha256,
                         read_json(args.reference), read_json(args.candidate))
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, 'Cannot read preservation inputs: ' + type(exc).__name__ + '\n')
    print(json.dumps(result, indent=2))
    return 2 if not result['valid'] else 0 if result['preserved'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
