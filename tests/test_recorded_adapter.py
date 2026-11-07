"""Regression for coherent archived updates escaping receipt identity."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from framework import inspect_recorded
import scripts.check_release as release


class RecordedAdapterTests(unittest.TestCase):
    def test_consistent_log_update_changes_bound_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('baseline', 'candidate', 'runs', 'review', 'scripts', 'framework'):
                shutil.copytree(inspect_recorded.ROOT / name, root / name)
            shutil.copyfile(inspect_recorded.ROOT / 'BASELINE.sha256', root / 'BASELINE.sha256')
            def inspect():
                output = io.StringIO()
                with patch.object(inspect_recorded, 'ROOT', root), patch.object(release, 'ROOT', root), contextlib.redirect_stdout(output):
                    self.assertEqual(inspect_recorded.main(), 0)
                return json.loads(output.getvalue())['receipt']
            before = inspect()
            run = root / 'runs/supervisor-resume/accepted-run'
            log = run / 'logs/formal.stderr'
            log.write_bytes(log.read_bytes() + b'archived diagnostic update\n')
            result = json.loads((run / 'result.json').read_text())
            result['checks'][0]['stderr_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
            (run / 'result.json').write_text(json.dumps(result))
            checkpoint = root / 'runs/supervisor-resume/checkpoint.json'
            record = json.loads(checkpoint.read_text())
            record['accepted_result_sha256'] = hashlib.sha256((run / 'result.json').read_bytes()).hexdigest()
            checkpoint.write_text(json.dumps(record))
            after = inspect()
            self.assertTrue(before['consistent'] and after['consistent'])
            self.assertNotEqual(before['identity'], after['identity'])
