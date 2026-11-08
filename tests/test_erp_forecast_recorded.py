import copy
import json
from pathlib import Path
import unittest

from benchmarks.erpnext.oracle import future
from framework.change import check


class RecordedForecastTests(unittest.TestCase):
    def test_actual_source_helper_controls_and_independent_oracle(self):
        root = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'
        spec = json.loads((root / 'proposed-change.json').read_text())
        recorded = json.loads((root / 'results.json').read_text())
        traces = json.loads((root / 'traces.json').read_text())
        for expectation in spec['expected_change']:
            self.assertEqual(expectation['output'], future(expectation['input']))
        for name, failures in [('base', 20), ('head', 0)]:
            report = check(spec, recorded['specification_sha256'], traces['base'], traces[name])
            self.assertEqual(report, recorded['observed'][name])
            self.assertTrue(report['preservation']['preserved'])
            self.assertEqual(report['preservation']['checked_inputs'], 54)
            self.assertEqual(report['intended_change']['violation_count'], failures)
        key = {'series': 'steady', 'alpha': '0.5', 'horizon': 4,
               'seed': 'mean_nonzero', 'phase': 'future'}
        self.assertEqual(next(row['output'] for row in traces['head'] if row['input'] == key),
                         [100.0] * 4)

    def test_changed_past_is_rejected_even_if_future_is_flat(self):
        root = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'
        spec = json.loads((root / 'proposed-change.json').read_text())
        recorded = json.loads((root / 'results.json').read_text())
        traces = json.loads((root / 'traces.json').read_text())
        candidate = copy.deepcopy(traces['head'])
        row = next(row for row in candidate if row['input']['phase'] == 'past')
        row['output'][0] += 1
        report = check(spec, recorded['specification_sha256'], traces['base'], candidate)
        self.assertFalse(report['satisfied'])
        self.assertEqual(report['preservation']['violation_count'], 1)
        self.assertTrue(report['intended_change']['satisfied'])
