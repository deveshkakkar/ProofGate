import importlib.util
from pathlib import Path
import signal
import unittest

spec = importlib.util.spec_from_file_location('crash_replay', Path(__file__).with_name('crash-replay.py'))
crash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crash)


class ValidationTests(unittest.TestCase):
    def test_marker_requires_exact_evidence(self):
        good = {'phase': 'before', 'commit': 2, 'pid': 123}
        crash.validate_marker(good, 'before', 123, -signal.SIGKILL, False)
        bad = [None, {}, {**good, 'phase': 'after'}, {**good, 'commit': 1},
               {**good, 'commit': True}, {**good, 'pid': 124}, {**good, 'extra': 1}]
        for marker in bad:
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                crash.validate_marker(marker, 'before', 123, -signal.SIGKILL, False)
        for code, response in [(0, False), (1, False), (None, False), (-signal.SIGKILL, True)]:
            with self.subTest(code=code, response=response), self.assertRaises(ValueError):
                crash.validate_marker(good, 'before', 123, code, response)

    def test_http_requires_exact_status_and_body(self):
        reply = {'transport': 'response', 'status': 200, 'body': 'historical'}
        crash.validate_http(reply, 200, 'historical')
        for changed in [{**reply, 'status': 409}, {**reply, 'body': 'current'},
                        {**reply, 'transport': 'timeout'}]:
            with self.assertRaises(ValueError):
                crash.validate_http(changed, 200, 'historical')
        crash.validate_http({'transport': 'response', 'status': 409,
                             'body': '{"error":"conflict"}'}, 409, '{"error":"conflict"}')

    def test_sql_requires_exact_rows_and_balance(self):
        row = {'request_id': 'a', 'amount': 30, 'response': 'old'}
        crash.validate_sql({'balance': 70, 'rows': [row]}, 70, [row])
        for state in [None, {}, {'balance': 100, 'rows': [row]},
                      {'balance': 70, 'rows': []},
                      {'balance': 70, 'rows': [{**row, 'response': 'new'}]}]:
            with self.assertRaises(ValueError):
                crash.validate_sql(state, 70, [row])

    def test_startup_timeout_reaps_child_before_returning_ownership(self):
        from unittest.mock import Mock, patch
        proc, thread = Mock(), Mock()
        with patch.object(crash.subprocess, 'Popen', return_value=proc), \
             patch.object(crash.threading, 'Thread', return_value=thread), \
             patch.object(crash.time, 'monotonic', side_effect=[0, 6]), \
             patch.object(crash, 'stop') as reap:
            with self.assertRaises(TimeoutError):
                crash.launch(Path('/node/node'), Path('/artifact'), Path('/db'),
                             12345, Path('/log'))
            reap.assert_called_once_with(proc, thread)

    def test_protected_pin_mismatch(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for name in crash.PINS:
                (root / name).write_bytes(b'wrong')
            node = root / 'node'
            node.write_bytes(b'wrong')
            with self.assertRaises(ValueError):
                crash.verify_pins(root, node)


if __name__ == '__main__':
    unittest.main()
