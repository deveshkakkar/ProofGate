import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from benchmarks.erpnext.obligations import EXPECTED_COVERAGE_SHA256, review
from framework.kernel import digest

HERE = Path(__file__).resolve().parents[1] / 'benchmarks/erpnext'


class ObligationReviewTests(unittest.TestCase):
    def setUp(self):
        self.wrapper = json.loads((HERE / 'lifecycle-results.json').read_text())
        self.producer = json.loads((HERE / 'lifecycle-producer.json').read_text())
        self.manifest = json.loads((HERE / 'structured-candidates.json').read_text())
        self.coverage = json.loads((HERE / 'obligations.json').read_text())

    def call(self, report=None, coverage=None, pin=None):
        report = self.wrapper['report'] if report is None else report
        return review(report, digest(report), self.producer, self.manifest,
                      self.coverage if coverage is None else coverage, EXPECTED_COVERAGE_SHA256 if pin is None else pin)

    def test_actual_complete_archive_has_failed_negative_control_and_passing_authors(self):
        result = self.call()
        self.assertTrue(result['available'], result)
        self.assertEqual(len(result['rows']), 5)
        denied = next(r for r in result['rows'] if r['id'] == 'select-without-read')
        self.assertEqual(denied['verdicts'], {'base': 'failed', 'head': 'passed', 'baseline': 'passed', 'feedback': 'passed'})
        for row in result['rows']:
            self.assertIn(row['test_id'], self.wrapper['report']['observations']['baseline']['runs'][0]['test_ids'])
            self.assertEqual(row['verdicts']['baseline'], 'passed')
            self.assertEqual(row['verdicts']['feedback'], 'passed')
        for key in ('producer_authenticated', 'fresh_source_execution', 'policy_admitted', 'release_authority'):
            self.assertFalse(result[key])

    def test_actual_incomplete_archive_has_no_positive_coverage(self):
        old = json.loads((HERE / 'structured-results.json').read_text())
        result = review(old['report'], old['record_sha256'],
                        json.loads((HERE / 'structured-producer.json').read_text()), self.manifest,
                        self.coverage, EXPECTED_COVERAGE_SHA256)
        self.assertFalse(result['available'])
        self.assertEqual(result['rows'], [])

    def test_synthetic_candidate_error_is_unknown_for_all_its_groups(self):
        report = copy.deepcopy(self.wrapper['report'])
        row = report['observations']['baseline']['runs'][0]
        row['error_ids'] = row['test_ids'][:1]
        result = self.call(report=report)
        self.assertTrue(result['available'], result)
        self.assertTrue(all(r['verdicts']['baseline'] == 'unknown' for r in result['rows']))
        self.assertTrue(all(r['verdicts']['feedback'] == 'passed' for r in result['rows']))

    def test_wrong_record_or_coverage_pin_rejects_without_rows(self):
        result = review(self.wrapper['report'], '0' * 64, self.producer, self.manifest,
                        self.coverage, EXPECTED_COVERAGE_SHA256)
        self.assertFalse(result['available']);self.assertEqual(result['rows'], [])
        changed = copy.deepcopy(self.coverage);changed['groups'][0]['title'] += ' changed'
        result = self.call(coverage=changed)
        self.assertFalse(result['available']);self.assertEqual(result['rows'], [])

    def test_recomputed_pin_does_not_approve_wrong_source_inventory_shape_or_labels(self):
        for mutation in ('source', 'missing', 'extra', 'duplicate-id', 'duplicate-test', 'unknown-test',
                         'extra-field', 'bool-schema', 'bad-group', 'newline', 'bad-limits'):
            coverage = copy.deepcopy(self.coverage)
            if mutation == 'source': coverage['test_source_sha256'] = '0' * 64
            if mutation == 'missing': coverage['groups'].pop()
            if mutation == 'extra': coverage['groups'].append(copy.deepcopy(coverage['groups'][0]))
            if mutation == 'duplicate-id': coverage['groups'][1]['id'] = coverage['groups'][0]['id']
            if mutation == 'duplicate-test': coverage['groups'][1]['test'] = coverage['groups'][0]['test']
            if mutation == 'unknown-test': coverage['groups'][0]['test'] = 'test_unknown'
            if mutation == 'extra-field': coverage['path'] = '../other'
            if mutation == 'bool-schema': coverage['schema'] = True
            if mutation == 'bad-group': coverage['groups'][0] = None
            if mutation == 'newline': coverage['groups'][0]['title'] += '\nFake pass'
            if mutation == 'bad-limits': coverage['limits'] = [True]
            result = self.call(coverage=coverage, pin=digest(coverage))
            self.assertFalse(result['available'], mutation);self.assertEqual(result['rows'], [])

    def test_actual_cli_opt_in_and_mismatched_coverage_pin(self):
        argv = [sys.executable, '-B', '-m', 'benchmarks.erpnext.structured_review',
                '--attempt', 'lifecycle', '--obligations', '--json']
        good = subprocess.run(argv, cwd=HERE.parents[1], text=True, capture_output=True, timeout=10)
        self.assertEqual(good.returncode, 0, good.stderr)
        payload = json.loads(good.stdout)
        self.assertTrue(payload['obligations']['available'])
        self.assertEqual(payload['outcome'], 'passing-tie')
        bad = subprocess.run(argv + ['--expected-obligations-sha256', '0' * 64],
                             cwd=HERE.parents[1], text=True, capture_output=True, timeout=10)
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout)['obligations']['available'])
        self.assertEqual(json.loads(bad.stdout)['obligations']['rows'], [])

    def test_synthetic_coverage_read_failures_preserve_actual_archived_score(self):
        import contextlib
        import io
        from unittest.mock import patch
        from benchmarks.erpnext import structured_review as cli
        original = cli.read_json
        for error in (FileNotFoundError(), ValueError('malformed JSON')):
            def read(path):
                if path.name == 'obligations.json': raise error
                return original(path)
            out = io.StringIO()
            with patch.object(cli, 'read_json', side_effect=read), patch.object(sys, 'argv',
                    ['review', '--attempt', 'lifecycle', '--obligations', '--json']), contextlib.redirect_stdout(out):
                status = cli.main()
            self.assertEqual(status, 1)
            result = json.loads(out.getvalue())
            self.assertTrue(result['valid_controls'])
            self.assertEqual(result['outcome'], 'passing-tie')
            self.assertFalse(result['obligations']['available'])
            self.assertEqual(result['obligations']['rows'], [])
            self.assertIn(type(error).__name__, result['obligations']['reason'])
