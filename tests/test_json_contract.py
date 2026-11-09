"""Offline parser/source/evidence checks; invokes are mocked, no source execution."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from framework import json_contract as adapter
from framework.__main__ import main, summarize
from framework.errors import EvaluationError


class JSONContractTests(unittest.TestCase):
    def setup_case(self, root):
        candidate = root / 'external'; candidate.mkdir()
        (candidate / 'main.py').write_text('# inspected but never executed in this test\n')
        # An external checkout may contain unrelated files that are not selected.
        (candidate / 'README.md').write_text('unselected')
        spec = {'schema': 1, 'runtime': 'python-json-batch-v1', 'files': ['main.py'],
                'entrypoint': 'main.py', 'assumptions': ['Only these finite examples.'],
                'checks': [{'id': 'source', 'inputs': [1, 2], 'expected': [True, False]}]}
        path = root / 'reviewed.json'
        return candidate, path, spec

    def prepare(self, candidate, path, spec):
        path.write_text(json.dumps(spec))
        return adapter.prepare(candidate, path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_pins_shape_domain_and_path_rejections(self):
        mutations = [lambda s: s.update(schema=True), lambda s: s.update(runtime='shell'),
                     lambda s: s.update(extra='ignored'), lambda s: s.update(files=['../main.py']),
                     lambda s: s.update(files=['main.py', 'main.py']),
                     lambda s: s.update(entrypoint='missing.py'), lambda s: s.update(assumptions=[]),
                     lambda s: s['checks'][0].update(expected=[]),
                     lambda s: s['checks'][0].update(inputs=list(range(257)), expected=[True]*257),
                     lambda s: s['checks'][0].update(id='../unsafe'),
                     lambda s: s['checks'].append(dict(s['checks'][0]))]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, original = self.setup_case(root)
            for mutate in mutations:
                spec = json.loads(json.dumps(original)); mutate(spec)
                with self.subTest(spec=spec), self.assertRaises(ValueError):
                    self.prepare(candidate, path, spec)
            self.prepare(candidate, path, original)
            with self.assertRaises(ValueError):
                adapter.prepare(candidate, path, '0'*64)
            with self.assertRaises(ValueError):
                adapter.prepare(candidate, path, '')

    def test_duplicate_nonfinite_and_oversized_json_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, spec = self.setup_case(root)
            for raw in ('{"schema":1,"schema":1}', '{"x":NaN}', '{"x":1e999}', 'x'*(adapter.MAX_SPEC+1)):
                path.write_text(raw)
                with self.subTest(raw=raw[:32]), self.assertRaises(ValueError):
                    adapter.prepare(candidate, path, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_symlink_missing_and_oversized_sources_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, spec = self.setup_case(root)
            (candidate/'main.py').unlink()
            with self.assertRaises(ValueError): self.prepare(candidate, path, spec)
            (candidate/'main.py').symlink_to(candidate/'README.md')
            with self.assertRaises(ValueError): self.prepare(candidate, path, spec)
            (candidate/'main.py').unlink(); (candidate/'main.py').write_bytes(b'x'*(adapter.MAX_FILE+1))
            with self.assertRaises(ValueError): self.prepare(candidate, path, spec)
            (candidate/'folder').symlink_to(root, target_is_directory=True)
            spec.update(files=['folder/main.py'], entrypoint='folder/main.py')
            with self.assertRaises(ValueError): self.prepare(candidate, path, spec)

    def execute_mocked(self, prepared, observed, edit=None, error=None):
        original_hash = adapter.runtime.file_hash
        def fake_invoke(artifact, entry, rows, output):
            if error: raise error
            (output/'stdout').write_text(json.dumps(observed))
            if edit: edit()
            return observed
        def host_hash(path):
            return 'f'*64 if str(path).startswith('/usr/bin/') else original_hash(path)
        with patch.object(adapter.runtime, 'invoke', side_effect=fake_invoke), \
             patch.object(adapter.runtime, 'file_hash', side_effect=host_hash):
            return adapter.run(prepared)

    def test_bound_receipt_cardinality_type_and_nonfinite_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, spec = self.setup_case(root)
            prepared = self.prepare(candidate, path, spec)
            good = self.execute_mocked(prepared, [True, False])
            self.assertTrue(good['receipt']['consistent'])
            self.assertFalse(good['entrypoint_pinned'])
            self.assertIn('candidate-controlled',summarize(good))
            self.assertEqual(good['inputs']['verifier']['fixture-contract.json'], prepared['contract_sha256'])
            self.assertEqual(set(good['inputs']['source']), {'main.py'})
            self.assertFalse(good['policy_admitted']); self.assertFalse(good['producer_authenticated'])
            for result in ([1, False], [True], {'wrong': True}):
                bad = self.execute_mocked(prepared, result)
                self.assertFalse(bad['receipt']['consistent'])
                self.assertIn('FAIL', summarize(bad))
            with self.assertRaises(EvaluationError):
                self.execute_mocked(prepared, [float('nan'), False])

    def test_current_edit_cannot_relabel_checked_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, spec = self.setup_case(root)
            prepared = self.prepare(candidate, path, spec)
            report = self.execute_mocked(prepared, [True, False],
                edit=lambda: (candidate/'main.py').write_text('# changed\n'))
            self.assertTrue(report['receipt']['consistent'])
            self.assertFalse(report['candidate_matches_snapshot'])
            self.assertIn('CURRENT SOURCE CHANGED', summarize(report))

    def test_reviewed_driver_pin_rejects_candidate_fixture_spoof_before_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); candidate,path,spec=self.setup_case(root)
            spec['schema']=2
            spec['entrypoint_sha256']=hashlib.sha256((candidate/'main.py').read_bytes()).hexdigest()
            prepared=self.prepare(candidate,path,spec)
            report=self.execute_mocked(prepared,[True,False])
            self.assertTrue(report['entrypoint_pinned'])
            self.assertEqual(report['inputs']['verifier']['reviewed-entrypoint/main.py'],spec['entrypoint_sha256'])
            self.assertFalse(report['policy_admitted'])
            (candidate/'main.py').write_text('print("[true,false]")\n')
            pin=hashlib.sha256(path.read_bytes()).hexdigest()
            with patch.object(adapter.runtime,'preflight') as probe, patch.object(adapter,'run') as execute, \
                 contextlib.redirect_stderr(io.StringIO()) as err:
                result=main(['check-json','--candidate',str(candidate),'--contract',str(path),
                             '--expected-contract',pin,'--output',str(root/'spoof.json')])
            self.assertEqual(result,2);probe.assert_not_called();execute.assert_not_called()
            self.assertFalse((root/'spoof.json').exists())
            self.assertIn('Entrypoint SHA256',err.getvalue())
            for value in ('bad',None):
                spec['entrypoint_sha256']=value
                with self.assertRaises(ValueError): self.prepare(candidate,path,spec)
            del spec['entrypoint_sha256']
            with self.assertRaises(ValueError): self.prepare(candidate,path,spec)

    def test_isolated_evaluator_launcher_from_an_external_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'framework').mkdir()
            (root/'framework/__init__.py').write_text('this is invalid Python syntax !!!')
            (root/'sitecustomize.py').write_text('this is invalid Python syntax !!!')
            launcher = Path(__file__).resolve().parents[1]/'scripts/proofgate.py'
            result = subprocess.run([sys.executable, '-I', '-B', str(launcher), '--help'],
                                    cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('check-json', result.stdout)
            self.assertNotIn('SyntaxError', result.stderr)

    def test_wrong_pin_fails_before_preflight_execution_or_report_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate, path, spec = self.setup_case(root)
            self.prepare(candidate, path, spec); output = root/'report.json'
            with patch.object(adapter.runtime, 'preflight') as probe, \
                 patch.object(adapter, 'run') as execute, contextlib.redirect_stderr(io.StringIO()):
                result = main(['check-json', '--candidate', str(candidate), '--contract', str(path),
                               '--expected-contract', '0'*64, '--output', str(output)])
            self.assertEqual(result, 2); probe.assert_not_called(); execute.assert_not_called()
            self.assertFalse(output.exists())
