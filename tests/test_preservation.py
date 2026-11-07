import copy
import json
from pathlib import Path
import unittest
from framework.preservation import compare, policy_id, prepare


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.policy = {'schema': 1, 'input_domain': {'authenticated': [False, True], 'method': ['GET', 'POST']},
                       'allowed_change': {'authenticated': [True], 'method': ['GET']},
                       'assumptions': ['Finite declared inputs; reference may contain defects.']}
        self.reference = [{'input': row, 'output': False} for row in prepare(self.policy)[0]]
        self.expected = policy_id(self.policy)

    def test_allowed_change_is_not_claimed_verified(self):
        candidate = copy.deepcopy(self.reference)
        for row in candidate:
            if row['input'] == {'authenticated': True, 'method': 'GET'}:
                row['output'] = True
        result = compare(self.policy, self.expected, self.reference, candidate)
        self.assertTrue(result['preserved'])
        self.assertEqual(result['checked_inputs'], 3)
        self.assertEqual(result['unverified_change_inputs'], 1)
        self.assertFalse(result['new_semantics_checked'])

    def test_outside_change_has_counterexample(self):
        candidate = copy.deepcopy(self.reference);candidate[0]['output'] = True
        result = compare(self.policy, self.expected, self.reference, candidate)
        self.assertFalse(result['preserved'])
        self.assertEqual(result['violation_count'], 1)
        self.assertEqual(result['counterexamples'][0]['input'], candidate[0]['input'])

    def test_missing_extra_duplicate_and_wrong_dimension_are_rejected(self):
        cases = [self.reference[:-1], self.reference * 2, [self.reference[0]] * 4,
                 [{'input': {'other': 1}, 'output': False}] * 4]
        for candidate in cases:
            self.assertFalse(compare(self.policy, self.expected, self.reference, candidate)['valid'])

    def test_policy_cannot_expand_after_pin(self):
        self.policy['allowed_change'] = {'authenticated': [False, True], 'method': ['GET']}
        self.assertFalse(compare(self.policy, self.expected, self.reference, self.reference)['valid'])

    def test_bool_and_int_are_not_equal(self):
        candidate = copy.deepcopy(self.reference);candidate[0]['output'] = 0
        self.assertFalse(compare(self.policy, self.expected, self.reference, candidate)['preserved'])
        self.policy['allowed_change']['authenticated'] = [1]
        with self.assertRaises(ValueError):
            policy_id(self.policy)

    def test_full_and_empty_exemptions_and_unknown_scope_rejected(self):
        for scope in ({}, {'authenticated': [False, True]}, {'unknown': [False]}):
            self.policy['allowed_change'] = scope
            with self.assertRaises(ValueError):
                policy_id(self.policy)

    def test_no_change_scope_compares_everything(self):
        self.policy['allowed_change'] = None
        result = compare(self.policy, policy_id(self.policy), self.reference, list(reversed(self.reference)))
        self.assertTrue(result['preserved']);self.assertEqual(result['checked_inputs'], 4)

    def test_domain_limit_and_duplicates(self):
        for domain in ({'a': list(range(64)), 'b': list(range(64)), 'c': [0, 1]}, {'a': [True, True]}):
            self.policy['input_domain'] = domain
            with self.assertRaises(ValueError):
                policy_id(self.policy)

    def test_nan_output_rejected(self):
        candidate = copy.deepcopy(self.reference);candidate[0]['output'] = float('nan')
        self.assertFalse(compare(self.policy, self.expected, self.reference, candidate)['valid'])

    def test_non_json_output_keys_and_large_domain_values_rejected(self):
        candidate = copy.deepcopy(self.reference);candidate[0]['output'] = {1: False}
        self.assertFalse(compare(self.policy, self.expected, self.reference, candidate)['valid'])
        self.policy['input_domain'] = {'a': ['x' * 129]}
        with self.assertRaises(ValueError):
            policy_id(self.policy)

    def test_recorded_real_module_regression(self):
        root = Path(__file__).resolve().parents[1] / 'benchmarks/drf'
        policy = json.loads((root / 'proposed-read-change.json').read_text())
        traces = json.loads((root / 'preservation-traces.json').read_text())
        pin = json.loads((root / 'preservation-results.json').read_text())['policy_sha256']
        for name, expected in [('original', 0), ('baseline', 0), ('contract', 0), ('upstream', 12)]:
            result = compare(policy, pin, traces['original'], traces[name])
            self.assertTrue(result['valid'])
            self.assertEqual(result['violation_count'], expected)
            self.assertEqual(result['checked_inputs'], 384)
            self.assertEqual(result['unverified_change_inputs'], 64)
