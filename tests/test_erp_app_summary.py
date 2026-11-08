import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ArchivedSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = ROOT / 'benchmarks/erpnext'
        original = json.loads((folder / 'app-results.json').read_text())
        cls.rows = [next(row for row in original['attempts'] if row['run_id'] == 42443539018),
                    json.loads((folder / 'intermediate-results.json').read_text())]

    def invoke(self, row, pin=None, output=None):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / 'report.json'
            report.write_text(json.dumps(row['report']))
            argv = [sys.executable, '-B', '-m', 'benchmarks.erpnext.app_evidence',
                    '--report', str(report), '--expected-record-sha256', pin or row['record_sha256']]
            if output: argv.extend(['--format', output])
            return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=10)

    def test_real_controls_distinguish_baseline_failures_from_final_passes(self):
        for row, baseline_passes in zip(self.rows, (2, 4)):
            result = self.invoke(row, output='summary')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'{baseline_passes}/5 tests passed; {5 - baseline_passes} failed', result.stdout)
            self.assertIn('5/5 tests passed; 0 failed', result.stdout)
            for revision in ('erpnext_base', 'erpnext_head'):
                self.assertIn(row['report']['case'][revision], result.stdout)
            for failure in row['report']['case']['original_failure_names']:
                self.assertIn(failure, result.stdout)
            self.assertIn(row['record_sha256'], result.stdout)
            self.assertIn('no fresh execution, producer authentication or release authority', result.stdout)

    def test_invalid_record_has_no_passing_control_summary_and_nonzero_exit(self):
        result = self.invoke(self.rows[1], pin='0' * 64, output='summary')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Archived controls: inconsistent', result.stdout)
        self.assertNotIn('tests passed', result.stdout)
        self.assertNotIn('failures reproduced', result.stdout)

    def test_default_remains_machine_json_with_authority_flags_false(self):
        result = self.invoke(self.rows[1])
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt['consistent'])
        for name in ('producer_authenticated', 'fresh_source_execution', 'policy_admitted', 'release_authority'):
            self.assertFalse(receipt[name])
