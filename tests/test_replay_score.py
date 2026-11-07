import json
from pathlib import Path
import unittest
from benchmarks.drf.score import classify, summarize

PASS = {'exit_code': 0, 'tests': 14, 'failures': 0, 'errors': 0, 'skipped': 0}
FAIL = dict(PASS, exit_code=1, failures=2)


def arm(observation):
    return {'heldout': observation, 'contract': dict(observation, tests=1, failures=min(observation['failures'], 1))}


class ReplayScoringTests(unittest.TestCase):
    def test_complete_observations(self):
        self.assertEqual(classify(PASS), 'passed')
        self.assertEqual(classify(FAIL), 'failed')

    def test_setup_skips_empty_timeouts_and_contradictions_are_inconclusive(self):
        observations = [None, {}, dict(PASS, tests=0), dict(PASS, skipped=1),
                        dict(PASS, errors=1), dict(PASS, exit_code=None),
                        dict(PASS, exit_code=-9), dict(FAIL, exit_code=0),
                        dict(FAIL, failures=20), dict(PASS, tests=True)]
        for observation in observations:
            with self.subTest(observation=observation):
                self.assertEqual(classify(observation), 'inconclusive')

    def test_all_outcome_classes_and_no_dropped_cases(self):
        pairs = [('win', arm(FAIL), arm(PASS)), ('loss', arm(PASS), arm(FAIL)),
                 ('both_pass', arm(PASS), arm(PASS)), ('both_fail', arm(FAIL), arm(FAIL)),
                 ('missing', arm(PASS), {})]
        report = {'schema': 1, 'cases': [{'id': name, 'expected_tests': {'heldout': 14, 'contract': 1}, 'controls': {'original': arm(FAIL), 'upstream': arm(PASS)}, 'arms': {'baseline': left, 'contract': right}}
                                       for name, left, right in pairs]}
        result = summarize(report)
        for key in ('treatment_wins', 'treatment_losses', 'ties_passed', 'ties_failed', 'inconclusive_pairs'):
            self.assertEqual(result[key], 1)
        self.assertEqual(len(result['cases']), 5)

    def test_old_test_compatibility_is_informational(self):
        report = {'schema': 1, 'cases': [{'id': 'changed_semantics', 'expected_tests': {'heldout': 14, 'contract': 1}, 'controls': {'original': arm(FAIL), 'upstream': arm(PASS)}, 'arms': {
            'baseline': dict(arm(PASS), old=FAIL), 'contract': dict(arm(PASS), old=FAIL)}}]}
        self.assertEqual(summarize(report)['ties_passed'], 1)

    def test_missing_or_disagreeing_controls_are_inconclusive(self):
        for controls in ({}, {'original': arm(PASS), 'upstream': arm(PASS)},
                         {'original': arm(FAIL), 'upstream': arm(FAIL)}):
            report = {'schema': 1, 'cases': [{'id': 'control', 'expected_tests': {'heldout': 14, 'contract': 1}, 'controls': controls,
                       'arms': {'baseline': arm(FAIL), 'contract': arm(PASS)}}]}
            result = summarize(report)
            self.assertEqual(result['inconclusive_pairs'], 1)
            self.assertEqual(result['treatment_wins'], 0)

    def test_partial_treatment_suite_cannot_count_as_win(self):
        treatment = arm(PASS)
        treatment['heldout'] = dict(PASS, tests=1)
        report = {'schema': 1, 'cases': [{'id': 'partial',
                  'expected_tests': {'heldout': 14, 'contract': 1},
                  'controls': {'original': arm(FAIL), 'upstream': arm(PASS)},
                  'arms': {'baseline': arm(FAIL), 'contract': treatment}}]}
        result = summarize(report)
        self.assertEqual(result['inconclusive_pairs'], 1)
        self.assertEqual(result['treatment_wins'], 0)

    def test_published_pilot_keeps_three_cases_and_null_result(self):
        path = Path(__file__).resolve().parents[1] / 'benchmarks/drf/results.json'
        result = summarize(json.loads(path.read_text()))
        self.assertEqual(len(result['cases']), 3)
        self.assertEqual(result['ties_passed'], 3)
        self.assertEqual(result['treatment_wins'], 0)
        self.assertEqual(result['inconclusive_pairs'], 0)

    def test_invalid_or_duplicate_cases_are_not_silently_counted(self):
        for report in ({'schema': True, 'cases': []}, {'schema': 1, 'cases': []},
                       {'schema': 1, 'cases': [{'id': 'a'}, {'id': 'a'}]},
                       {'schema': 1, 'cases': [None]}):
            with self.assertRaises(ValueError):
                summarize(report)
