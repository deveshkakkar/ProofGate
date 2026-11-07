"""Synthetic consistency demonstration; no proof, checker or deployment is run."""
import json
from .kernel import digest, contract_digest, identity, verify


def main():
    contract = {'schema': 1, 'checks': ['rule', 'boundary'],
                'assumptions': ['Trusted external evaluator supplies observations.']}
    inputs = {group: {'example': digest(group)} for group in
              ('source', 'artifact', 'verifier', 'environment')}
    rows = [{'id': check, 'status': 'passed', 'identity': identity(contract, inputs)}
            for check in contract['checks']]
    expected = contract_digest(contract)
    original = verify(contract, expected, inputs, rows)
    inputs['artifact']['example'] = digest('changed executable')
    changed = verify(contract, expected, inputs, rows)
    print(json.dumps({'scope': 'synthetic identity validation only',
                      'original': original, 'changed_artifact': changed}, indent=2))
    return 0 if original['consistent'] and not changed['consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
