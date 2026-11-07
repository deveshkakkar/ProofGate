import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from framework.change import check, spec_id
from framework.kernel import digest


class ChangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        bench = cls.root / 'benchmarks/drf'
        cls.spec = json.loads((bench / 'query-proposed-change.json').read_text())
        cls.traces = json.loads((bench / 'query-traces.json').read_text())
        cls.pin = json.loads((bench / 'query-results.json').read_text())['specification_sha256']

    def test_real_unchanged_source_preserves_but_does_not_implement_query(self):
        report = check(self.spec, self.pin, self.traces['base'], self.traces['base'])
        self.assertTrue(report['valid'])
        self.assertTrue(report['preservation']['preserved'])
        self.assertFalse(report['satisfied'])
        self.assertEqual(report['intended_change']['checked_inputs'], 64)
        self.assertEqual(report['intended_change']['violation_count'], 48)

    def test_real_head_satisfies_declared_finite_proposal_without_authority(self):
        report = check(self.spec, self.pin, self.traces['base'], self.traces['head'])
        self.assertTrue(report['satisfied'])
        self.assertEqual(report['preservation']['checked_inputs'], 448)
        self.assertTrue(report['specified_change_checked'])
        for field in ('policy_admitted', 'source_execution_verified', 'producer_authenticated',
                      'reference_correctness_established'):
            self.assertFalse(report[field])

    def test_requested_feature_does_not_hide_old_method_regression(self):
        candidate = copy.deepcopy(self.traces['head'])
        row = next(row for row in candidate if row['input']['method'] == 'POST' and
                   row['input']['authenticated'])
        row['output'] = {'kind': 'return', 'value': not row['output']['value']}
        report = check(self.spec, self.pin, self.traces['base'], candidate)
        self.assertFalse(report['satisfied'])
        self.assertFalse(report['preservation']['preserved'])
        self.assertTrue(report['intended_change']['satisfied'])

    def test_incomplete_duplicate_or_outside_expected_region_rejected(self):
        for change in ('missing', 'duplicate', 'outside'):
            spec = copy.deepcopy(self.spec)
            if change == 'missing':
                spec['expected_change'].pop()
            elif change == 'duplicate':
                spec['expected_change'][-1] = spec['expected_change'][0]
            else:
                spec['expected_change'][0]['input']['method'] = 'POST'
            with self.assertRaises(ValueError):
                spec_id(spec)

    def test_reference_or_spec_cannot_change_after_pin(self):
        reference = copy.deepcopy(self.traces['base']);reference[0]['output'] = None
        self.assertFalse(check(self.spec, self.pin, reference, self.traces['head'])['valid'])
        spec = copy.deepcopy(self.spec)
        spec['expected_change'][0]['output'] = None
        self.assertFalse(check(spec, self.pin, self.traces['base'], self.traces['head'])['valid'])
        spec = copy.deepcopy(self.spec);spec['reference_trace_sha256'] = digest(reference)
        self.assertFalse(check(spec, self.pin, reference, self.traces['head'])['valid'])

    def test_candidate_coverage_and_type_are_checked(self):
        for candidate in (self.traces['head'][:-1], self.traces['head'] + self.traces['head'][:1]):
            report = check(self.spec, self.pin, self.traces['base'], candidate)
            self.assertFalse(report['valid']);self.assertFalse(report['satisfied'])
        candidate = copy.deepcopy(self.traces['head'])
        row = next(row for row in candidate if row['input']['method'] == 'QUERY')
        row['output']['value'] = int(row['output']['value'])
        report = check(self.spec, self.pin, self.traces['base'], candidate)
        self.assertTrue(report['valid']);self.assertFalse(report['satisfied'])

    def test_no_changed_region_is_not_a_change_proposal(self):
        spec = copy.deepcopy(self.spec);spec['preservation']['allowed_change'] = None
        with self.assertRaises(ValueError):
            spec_id(spec)

    def test_cli_exit_codes_for_real_sources_and_incomplete_observations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = {}
            for name, value in [('specification', self.spec), ('reference', self.traces['base'])]:
                paths[name] = root / (name + '.json');paths[name].write_text(json.dumps(value))
            candidate = root / 'candidate.json'
            command = [sys.executable, '-B', '-m', 'framework.change',
                       '--specification', str(paths['specification']), '--reference', str(paths['reference']),
                       '--candidate', str(candidate), '--expected-specification-sha256', self.pin]
            for trace, expected in [(self.traces['head'], 0), (self.traces['base'], 1),
                                    (self.traces['head'][:-1], 2)]:
                candidate.write_text(json.dumps(trace))
                result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(json.loads(result.stdout)['satisfied'], expected == 0)
