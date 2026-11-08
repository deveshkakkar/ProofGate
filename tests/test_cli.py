import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from framework.__main__ import main, summarize, validate_candidate


class CLITests(unittest.TestCase):
    def test_input_shape_and_size(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                validate_candidate(root)
            for name in ('app.py', 'rule.py'):
                (root / name).write_text('')
            validate_candidate(root)
            (root / 'rule.py').write_bytes(b'x' * (256 * 1024 + 1))
            with self.assertRaises(ValueError):
                validate_candidate(root)
            (root / 'rule.py').unlink()
            (root / 'rule.py').symlink_to(root / 'app.py')
            with self.assertRaises(ValueError):
                validate_candidate(root)

    def test_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / 'candidate'; candidate.mkdir()
            for name in ('app.py', 'rule.py'):
                (candidate / name).write_text('')
            report = root / 'report.json'; report.write_text('keep')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(report)]), 2)
            self.assertEqual(report.read_text(), 'keep')

    def test_missing_report_parent_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / 'candidate'; candidate.mkdir()
            for name in ('app.py', 'rule.py'):
                (candidate / name).write_text('')
            with contextlib.redirect_stderr(io.StringIO()) as error:
                result = main(['check-entitlement', '--candidate', str(candidate),
                               '--output', str(root / 'missing' / 'report.json')])
            self.assertEqual(result, 2)
            self.assertIn('parent directory', error.getvalue())
            self.assertNotIn('bubblewrap', error.getvalue())

    def test_counterexample_and_boolean_type(self):
        report = {'receipt': {'consistent': False}, 'checks': [
            {'id': 'rule', 'passed': False, 'cases': 1,
             'inputs': [{'active': True}], 'expected': [True], 'observed': [1]}]}
        text = summarize(report)
        self.assertIn('Input:', text)
        self.assertIn('Expected: true', text)
        self.assertIn('Observed: 1', text)

    def test_failure_report_is_not_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root / 'candidate'; candidate.mkdir()
            for name in ('app.py', 'rule.py'):
                (candidate / name).write_text('')
            report = root / 'report.json'
            with patch('examples.entitlement.experiment.preflight'), patch('examples.entitlement.experiment.run_variant', side_effect=RuntimeError('private')), contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(report)]), 2)
            self.assertNotIn('private', error.getvalue())
            self.assertIs(json.loads(report.read_text())['completed'], False)
