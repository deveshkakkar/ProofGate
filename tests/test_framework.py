import copy
import unittest
from framework.kernel import contract_digest, identity, verify


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.contract = {'schema': 1, 'checks': ['rule', 'boundary'],
                         'assumptions': ['external evaluator controls evidence']}
        self.inputs = {k: {'file': str(i) * 64} for i, k in enumerate(
            ('source', 'artifact', 'verifier', 'environment'))}
        self.expected = contract_digest(self.contract)
        self.evidence = [{'id': k, 'status': 'passed', 'identity': identity(self.contract, self.inputs)}
                         for k in self.contract['checks']]

    def verify(self):
        return verify(self.contract, self.expected, self.inputs, self.evidence)['consistent']

    def test_complete(self):
        self.assertTrue(self.verify())

    def test_every_input_invalidates(self):
        for key in self.inputs:
            with self.subTest(key=key):
                inputs = copy.deepcopy(self.inputs)
                inputs[key]['file'] = 'f' * 64
                self.assertFalse(verify(self.contract, self.expected, inputs, self.evidence)['consistent'])

    def test_contract_mutation(self):
        self.contract['assumptions'].append('new assumption')
        self.assertFalse(self.verify())

    def test_evidence_completeness(self):
        for rows in ([], self.evidence[:1], self.evidence * 2,
                     self.evidence[::-1], [self.evidence[0]] * 2):
            self.assertFalse(verify(self.contract, self.expected, self.inputs, rows)['consistent'])

    def test_nonpass(self):
        for status in ('failed', 'skipped', 'timeout', 'unavailable', True, None):
            self.evidence[0]['status'] = status
            self.assertFalse(self.verify())

    def test_bad_manifest(self):
        for path in ('/absolute', '../escape', 'a/../b', 'a//b', 'a\\b', 'a/./b', 'bad\nname'):
            self.inputs['source'] = {path: 'a' * 64}
            self.assertFalse(self.verify())
        for files in ({}, {'ok': 'xyz'}, {'ok': True}):
            self.inputs['source'] = files
            self.assertFalse(self.verify())

    def test_unknown_fields(self):
        self.evidence[0]['command'] = 'true'
        self.assertFalse(self.verify())

    def test_independent_contract_and_file_inventory(self):
        contract = {'schema': 1, 'checks': ['eligibility', 'tenant', 'http'],
                    'assumptions': ['finite entitlement domain']}
        inputs = {group: {'decision.py': 'a' * 64, 'adapter.py': 'b' * 64}
                  for group in ('source', 'artifact', 'verifier', 'environment')}
        expected = contract_digest(contract)
        rows = [{'id': check, 'status': 'passed', 'identity': identity(contract, inputs)}
                for check in contract['checks']]
        self.assertTrue(verify(contract, expected, inputs, rows)['consistent'])
        for operation in ('add', 'remove', 'rename'):
            with self.subTest(operation=operation):
                changed = copy.deepcopy(inputs)
                files = changed['source']
                if operation == 'add':
                    files['extra.py'] = 'c' * 64
                elif operation == 'remove':
                    del files['adapter.py']
                else:
                    files['renamed.py'] = files.pop('adapter.py')
                self.assertFalse(verify(contract, expected, changed, rows)['consistent'])

    def test_missing_contract_fields(self):
        del self.contract['assumptions']
        self.assertFalse(self.verify())

    def test_identity_order_independent(self):
        self.assertEqual(identity(self.contract, self.inputs),
                         identity(self.contract, dict(reversed(list(self.inputs.items())))))


if __name__ == '__main__':
    unittest.main()
