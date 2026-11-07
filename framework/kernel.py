"""Pure acceptance logic. No commands, filesystem access or implicit trust roots."""
import hashlib
import json
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'invalid SHA256')


def contract_digest(contract):
    require(isinstance(contract, dict) and set(contract) == {'schema', 'checks', 'assumptions'},
            'invalid contract fields')
    require(type(contract['schema']) is int and contract['schema'] == 1, 'unsupported schema')
    checks = contract['checks']
    require(isinstance(checks, list) and checks and all(isinstance(c, str) and
            re.fullmatch('[a-z][a-z0-9_-]{0,63}', c) for c in checks), 'invalid checks')
    require(len(set(checks)) == len(checks), 'duplicate checks')
    assumptions = contract['assumptions']
    require(isinstance(assumptions, list) and assumptions and
            all(isinstance(a, str) and a.strip() for a in assumptions), 'missing assumptions')
    return digest(contract)


def identity(contract, inputs):
    contract_sha = contract_digest(contract)
    require(isinstance(inputs, dict) and set(inputs) ==
            {'source', 'artifact', 'verifier', 'environment'}, 'invalid input groups')
    for files in inputs.values():
        require(isinstance(files, dict) and files, 'empty input manifest')
        for name, value in files.items():
            require(isinstance(name, str) and name and not name.startswith('/') and
                    '\\' not in name and all(p not in ('', '.', '..') for p in name.split('/')) and
                    all(ord(c) >= 32 and ord(c) != 127 for c in name), 'unsafe logical path')
            sha(value)
    return digest({'contract': contract_sha, 'inputs': inputs})


def verify(contract, expected_contract, inputs, evidence):
    """Return consistency only; expected_contract and evidence must be evaluator-owned."""
    try:
        sha(expected_contract)
        require(contract_digest(contract) == expected_contract, 'contract identity mismatch')
        bound = identity(contract, inputs)
        require(isinstance(evidence, list), 'invalid evidence')
        require(len(evidence) == len(contract['checks']), 'incomplete or extra evidence')
        for expected, row in zip(contract['checks'], evidence):
            require(isinstance(row, dict) and set(row) == {'id', 'status', 'identity'},
                    'invalid evidence fields')
            require(row['id'] == expected, 'missing, duplicate or reordered check')
            require(row['status'] == 'passed', 'check did not pass: ' + expected)
            require(row['identity'] == bound, 'stale evidence: ' + expected)
        return {'schema': 1, 'consistent': True, 'identity': bound,
                'contract': expected_contract, 'checks': list(contract['checks'])}
    except (ValueError, TypeError, KeyError) as exc:
        return {'schema': 1, 'consistent': False, 'reason': str(exc)}
