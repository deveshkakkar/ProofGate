"""Real process signals against trusted CLI; candidate evaluation is paused/mocked."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from framework.report import ReportDestination

ROOT = Path(__file__).resolve().parents[1]


class ReportInterruptTests(unittest.TestCase):
    def test_partial_update_and_reservation_never_publish_truncated_json(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'result.json'; writer = ReportDestination(output)
            def interrupted(value, stream, **kwargs):
                stream.write('{partial')
                raise KeyboardInterrupt()
            with patch('framework.report.json.dump', side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt): writer.publish({'completed': False}, reserve=True)
            self.assertFalse(output.exists())
            writer.publish({'completed': False}, reserve=True)
            original = output.read_bytes()
            with patch('framework.report.json.dump', side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt): writer.publish({'completed': True})
            self.assertEqual(output.read_bytes(), original)
            self.assertFalse(json.loads(original)['completed'])
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError): ReportDestination(output).publish({}, reserve=True)
            self.assertEqual(output.read_bytes(), original)

    def test_replaced_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'record.json'; writer = ReportDestination(path)
            writer.publish({'completed': False}, reserve=True)
            other = Path(temp)/'other.json'; other.write_text('unrelated record')
            os.replace(other, path)
            with self.assertRaises(RuntimeError): writer.publish({'completed': True})
            self.assertEqual(path.read_text(), 'unrelated record')

    @unittest.skipUnless(os.name == 'posix', 'POSIX signal regression')
    def test_sigint_and_abrupt_exit_preserve_incomplete_no_overwrite_record(self):
        script = '''
import pathlib, sys, time
sys.path.insert(0,sys.argv[1])
from examples.entitlement import experiment
from framework.__main__ import main
experiment.preflight=lambda: {'ready': True}
def paused(*args, **kwargs):
    pathlib.Path(sys.argv[4]).write_text('ready')
    time.sleep(10)
    raise RuntimeError('paused test evaluator timed out')
experiment.run_variant=paused
raise SystemExit(main(['check-entitlement','--candidate',sys.argv[2],'--output',sys.argv[3]]))
'''
        for abrupt in (False, True):
            with self.subTest(abrupt=abrupt), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); candidate = root/'candidate'; candidate.mkdir()
                for name in ('app.py','rule.py'): (candidate/name).write_text('# not executed\n')
                output=root/'report.json'; ready=root/'ready'
                process=subprocess.Popen([sys.executable,'-I','-B','-c',script,str(ROOT),str(candidate),str(output),str(ready)],
                                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                try:
                    deadline=time.monotonic()+5
                    while not ready.exists() and process.poll() is None and time.monotonic()<deadline:
                        time.sleep(0.01)
                    self.assertTrue(ready.exists(), 'Trusted paused evaluator failed to start')
                    before=json.loads(output.read_text()); self.assertFalse(before['completed'])
                    self.assertEqual(before['code'],'evaluation_in_progress')
                    if abrupt: process.kill()
                    else: process.send_signal(signal.SIGINT)
                    stdout,stderr=process.communicate(timeout=5)
                    self.assertNotIn('PASS:',stdout)
                    if not abrupt:
                        self.assertEqual(process.returncode,2,stderr)
                        self.assertNotIn('Traceback',stderr)
                    record=json.loads(output.read_text())
                    self.assertFalse(record['completed'])
                    self.assertEqual(record['code'],'evaluation_in_progress' if abrupt else 'interrupted')
                    original=output.read_bytes()
                    retry=subprocess.run([sys.executable,'-I','-B',str(ROOT/'scripts/proofgate.py'),
                         'check-entitlement','--candidate',str(candidate),'--output',str(output)],
                         cwd=root,capture_output=True,text=True,timeout=5)
                    self.assertEqual(retry.returncode,2)
                    self.assertIn('already exists',retry.stderr)
                    self.assertEqual(output.read_bytes(),original)
                finally:
                    if process.poll() is None:
                        process.kill();process.communicate(timeout=5)
