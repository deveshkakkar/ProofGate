"""Offline error/identity regressions; sandbox execution is covered by hosted smoke."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from framework.__main__ import main, summarize
from framework.errors import EvaluationError
from examples.entitlement import experiment as runner


class AuditCLITests(unittest.TestCase):
    def candidate(self, root):
        candidate = root / 'candidate'; candidate.mkdir()
        for name in ('app.py', 'rule.py'):
            (candidate / name).write_bytes((runner.HERE / name).read_bytes())
        return candidate

    def test_preflight_failure_does_not_reserve_report_or_execute_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = self.candidate(root)
            output = root / 'report.json'
            with patch.object(runner, 'preflight', side_effect=EvaluationError(
                    'sandbox_unavailable', 'preflight', 'Fixed remediation.')), \
                 patch.object(runner, 'run_variant') as execute, \
                 contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(output)]), 2)
            execute.assert_not_called()
            self.assertFalse(output.exists())
            self.assertIn('sandbox_unavailable', stderr.getvalue())
            # Corrected setup can reuse exactly the same output path.
            with patch.object(runner, 'preflight'), \
                 patch.object(runner, 'run_variant', side_effect=EvaluationError(
                     'invalid_result', 'finite_rule', 'Fixed diagnostic.')), \
                 contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(output)]), 2)
            self.assertEqual(json.loads(output.read_text())['code'], 'invalid_result')

    def test_doctor_has_no_candidate_and_reports_readiness(self):
        with patch.object(runner, 'preflight', return_value={'ready': True}), \
             patch.object(runner, 'run_variant') as execute, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['doctor']), 0)
        execute.assert_not_called()
        self.assertTrue(json.loads(out.getvalue())['ready'])

    def test_missing_binary_does_not_launch_probe(self):
        with patch.object(runner.platform, 'system', return_value='Linux'), \
             patch.object(runner.os, 'access', return_value=False), \
             patch.object(runner, 'invoke') as invoke:
            with self.assertRaises(EvaluationError) as error:
                runner.preflight()
        self.assertEqual(error.exception.code, 'missing_dependency')
        invoke.assert_not_called()

    def test_probe_failure_is_redacted(self):
        with patch.object(runner.platform, 'system', return_value='Linux'), \
             patch.object(runner.Path, 'is_file', return_value=True), \
             patch.object(runner.os, 'access', return_value=True), \
             patch.object(runner, 'invoke', side_effect=EvaluationError('timeout', 'probe', 'private')):
            with self.assertRaises(EvaluationError) as error:
                runner.preflight()
        self.assertEqual(error.exception.code, 'sandbox_unavailable')
        self.assertNotIn('private', str(error.exception))

    def test_empty_probe_is_python_code_not_an_executable_as_a_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(runner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
                runner.invoke(root, 'empty_probe', [], root, expect_json=False)
            argv = run.call_args.args[0]
            self.assertEqual(argv[-4:], ['/usr/bin/python3', '-B', '-c', 'pass'])
            self.assertIn('--unshare-net', argv)
            self.assertIn('--scope', argv)

    def test_runner_failure_codes_are_redacted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases = [(subprocess.TimeoutExpired('private', 10), 'timeout'),
                     (OSError('private'), 'runner_unavailable'),
                     (subprocess.CompletedProcess([], 1), 'check_process_failed'),
                     (subprocess.CompletedProcess([], 0), 'invalid_result')]
            for result, code in cases:
                with self.subTest(code=code):
                    kw = {'side_effect': result} if isinstance(result, Exception) else {'return_value': result}
                    with patch.object(runner.subprocess, 'run', **kw):
                        with self.assertRaises(EvaluationError) as error:
                            runner.invoke(root, '/probe.py', [], root)
                    self.assertEqual(error.exception.code, code)
                    self.assertNotIn('private', str(error.exception))

    def test_report_retains_partial_check_stage_and_retry_guidance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = self.candidate(root); output = root / 'report.json'
            with patch.object(runner, 'preflight'), \
                 patch.object(runner, 'run_variant', side_effect=EvaluationError(
                     'timeout', 'application_boundary', 'Bounded check timed out.', ['finite_rule'])), \
                 contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(output)]), 2)
            report = json.loads(output.read_text())
            self.assertFalse(report['completed'])
            self.assertEqual(report['completed_checks'], ['finite_rule'])
            self.assertEqual(report['stage'], 'application_boundary')
            self.assertIn('new --output', err.getvalue())
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_summary_counts_types_and_limits_examples(self):
        report = {'receipt': {'consistent': False}, 'checks': [
            {'id': 'rule', 'passed': False, 'cases': 5,
             'inputs': list(range(5)), 'expected': [True] * 5, 'observed': [1] * 5}]}
        text = summarize(report)
        self.assertIn('5/5 mismatches', text)
        self.assertEqual(text.count('Input:'), 3)
        self.assertIn('no policy admission', text)

    def test_current_candidate_change_is_detected_without_relabeling_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = self.candidate(root)
            def observations(artifact, entry, rows, output):
                (output / 'stdout').write_text('offline mocked observations')
                if entry == '/probe.py':
                    (candidate / 'rule.py').write_text('# concurrent edit\n')
                    return [runner.expected(row) for row in rows]
                return [{'allowed': runner.expected(row)} if isinstance(row, dict) and
                        set(row) == {'subject_tenant', 'resource_tenant', 'active', 'entitled', 'enabled'} and
                        type(row['subject_tenant']) is int and type(row['resource_tenant']) is int and
                        row['resource_tenant'] in range(3) and
                        all(type(row[k]) is bool for k in ('active', 'entitled', 'enabled'))
                        else {'error': 'invalid request'} for row in rows]
            original_hash = runner.file_hash
            def offline_hash(path):
                return 'f' * 64 if str(path).startswith('/usr/bin/') else original_hash(path)
            with patch.object(runner, 'invoke', side_effect=observations), \
                 patch.object(runner, 'file_hash', side_effect=offline_hash):
                report = runner.run_variant('local_candidate', candidate)
            self.assertTrue(report['receipt']['consistent'])
            self.assertFalse(report['candidate_matches_snapshot'])
            self.assertIn('Source snapshot SHA256:', summarize(report))
            with patch.object(runner, 'preflight'), patch.object(runner, 'run_variant', return_value=report), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(['check-entitlement', '--candidate', str(candidate),
                                       '--output', str(root / 'report.json')]), 2)
            self.assertIn('CURRENT SOURCE CHANGED', out.getvalue())
