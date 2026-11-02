import importlib.util
from pathlib import Path
import signal
import unittest

spec = importlib.util.spec_from_file_location('crash_replay', Path(__file__).with_name('crash-replay.py'))
crash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crash)


class ValidationTests(unittest.TestCase):
    def make_crash_fixture(self, root):
        import subprocess
        import sys
        db = root / 'state.sqlite'
        subprocess.run([sys.executable, '-c', '''
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1])
db.execute('PRAGMA journal_mode=WAL')
db.execute('CREATE TABLE state (singleton INTEGER PRIMARY KEY, balance INTEGER)')
db.execute('CREATE TABLE reservations (request_id TEXT, amount INTEGER, response TEXT)')
db.execute('INSERT INTO state VALUES (1, 70)')
db.execute("INSERT INTO reservations VALUES ('a', 30, 'historical')")
db.commit()
os._exit(0)
''', str(db)], check=True, timeout=5)
        self.assertTrue(Path(str(db) + '-wal').exists())
        self.assertTrue(Path(str(db) + '-shm').exists())
        return db

    def test_crash_copy_preserves_original_db_wal_and_shm(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as temp:
            root = Path(temp)
            db = self.make_crash_fixture(root)
            # Independent byte oracle, not the helper's own hashing function.
            paths = [Path(str(db) + suffix) for suffix in ('', '-wal', '-shm')]
            before = {p.name: p.read_bytes() for p in paths}
            with patch.object(crash, 'sql_state', wraps=crash.sql_state) as observer:
                state, evidence = crash.inspect_crash_copy(db, root / 'copy')
            observer.assert_called_once_with(root / 'copy' / db.name)
            self.assertEqual(state, {'balance': 70, 'rows': [
                {'request_id': 'a', 'amount': 30, 'response': 'historical'}]})
            self.assertEqual(before, {p.name: p.read_bytes() for p in paths})
            self.assertEqual(evidence['before'], evidence['after_inspection'])

    def test_crash_copy_rejects_original_image_interference(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        original = crash.sql_state
        with TemporaryDirectory() as temp:
            root = Path(temp)
            db = self.make_crash_fixture(root)
            def interfering_observer(copy):
                state = original(copy)
                with Path(str(db) + '-shm').open('ab') as stream:
                    stream.write(b'interference')
                return state
            with patch.object(crash, 'sql_state', side_effect=interfering_observer):
                with self.assertRaisesRegex(ValueError, 'original crash image changed'):
                    crash.inspect_crash_copy(db, root / 'copy')

    def test_sql_connection_closes_on_success_and_failure(self):
        from unittest.mock import Mock, patch
        for failing in (False, True):
            db = Mock()
            db.execute.return_value.fetchall.side_effect = [[(100,)], []]
            if failing:
                db.execute.side_effect = RuntimeError('observer failed')
            with self.subTest(failing=failing), patch.object(crash.sqlite3, 'connect', return_value=db):
                if failing:
                    with self.assertRaises(RuntimeError):
                        crash.sql_state(Path('/unused'))
                else:
                    self.assertEqual(crash.sql_state(Path('/unused')), {'balance': 100, 'rows': []})
            db.close.assert_called_once_with()

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
