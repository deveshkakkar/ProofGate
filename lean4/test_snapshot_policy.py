#!/usr/bin/env python3
"""Deterministic policy/snapshot boundary tests; no Lean/build/process execution.

Real files, copies and SHA256 are used. Toolchain checking is substituted to
schedule B→A; subprocess execution is substituted with a stop at first preflight.
The exact reviewed evaluate() fixture is compared with the current evaluator.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch
import gate as g

REVIEWED = '40af8d46f89b0fb1e219157974f4b6fbb142b660'
FIXTURE = g.ROOT/'tests/fixtures/evaluate-40af8d4.py.txt'
FIXTURE_SHA256 = 'ad2f1652874c3b41949c3be7b9cb678373a54a8ba45a03c0359dd5996d885176'

class PreflightReached(Exception):
    """Stop before launching any subprocess; never a proof/build verdict."""

class SnapshotPolicyTests(unittest.TestCase):
    reports = []

    def exercise(self, policy, *, old=False, approved=False, inconsistent=False):
        module = g
        if old:
            source = FIXTURE.read_bytes()
            self.assertEqual(hashlib.sha256(source).hexdigest(), FIXTURE_SHA256)
            module = types.ModuleType('reviewed_gate')
            module.__dict__.update(vars(g))
            exec(compile(source, str(FIXTURE), 'exec'), module.__dict__)
        real_snapshot = module.snapshot
        with tempfile.TemporaryDirectory(prefix='proofgate-policy-aba-') as temporary:
            root = Path(temporary)
            candidate = root/'candidate'
            shutil.copytree(g.ROOT/'candidate', candidate)
            target = candidate/('formal/Admission.lean' if policy=='runtime' else 'app/server.ts')
            benign = target.read_bytes()
            if policy=='runtime':
                unapproved = benign.replace(b'def admission', b'@[implemented_by fake]\ndef admission')
            else:
                unapproved = benign.replace(b'Core.admission(prior, signed)',
                    b"({ $: 'Response', success: true, granted: input.amount, balance: prior - input.amount })")
            self.assertNotEqual(benign, unapproved)
            initial_bytes = benign if approved else unapproved
            target.write_bytes(initial_bytes)
            events = []
            first = True

            def replace(data):
                staged = target.with_name(target.name+'.swap')
                staged.write_bytes(data)
                os.replace(staged, target)

            def scheduled_snapshot(path):
                nonlocal first
                value = real_snapshot(path)
                if path==candidate and first:
                    first = False
                    events.append('hash-initial-'+('B' if approved else 'A'))
                    replace(benign)
                    events.append('live-B')
                elif path==root/'run/source':
                    events.append('verify-frozen')
                return value

            def scheduled_tools(_):
                # Old evaluator has already checked B. Repaired evaluator has
                # not checked source policies yet. Restore A before either copy.
                replace(benign if (approved or inconsistent) else unapproved)
                events.append('live-B' if (approved or inconsistent) else 'live-A')
                return root/'unused-lean', root/'unused-node'

            def stop(*args, **kwargs):
                self.assertEqual(Path(args[2]).name, 'preflight.log')
                events.append('preflight-stop-no-execution')
                raise PreflightReached()

            output = root/'run'
            with patch.object(module, 'snapshot', side_effect=scheduled_snapshot), \
                 patch.object(module, 'check_tools', side_effect=scheduled_tools), \
                 patch.object(module, 'run', side_effect=stop) as execution, \
                 patch.object(module, 'prepare') as prepare:
                if inconsistent:
                    with self.assertRaises(g.Rejected) as caught:
                        module.evaluate(candidate, output, root/'unused-cache')
                    self.assertEqual(caught.exception.layer, 'identity')
                    execution.assert_not_called()
                    outcome = 'identity'
                elif old or approved:
                    with self.assertRaises(PreflightReached):
                        module.evaluate(candidate, output, root/'unused-cache')
                    execution.assert_called_once()
                    outcome = 'preflight-stop-no-execution'
                else:
                    with self.assertRaises(g.Rejected) as caught:
                        module.evaluate(candidate, output, root/'unused-cache')
                    self.assertEqual(caught.exception.layer, policy+'-policy' if policy=='runtime' else 'driver-policy')
                    execution.assert_not_called()
                    outcome = caught.exception.layer
                prepare.assert_not_called()
            expected_frozen = benign if (approved or inconsistent) else unapproved
            self.assertEqual((output/'source'/target.relative_to(candidate)).read_bytes(), expected_frozen)
            if not inconsistent:
                self.assertEqual(real_snapshot(candidate), real_snapshot(output/'source'))
            self.assertFalse((output/'receipt.json').exists())
            self.assertFalse((output/'checkpoint.json').exists())
            self.reports.append({
                'evaluator': 'reviewed-'+REVIEWED if old else 'repaired',
                'policy': policy, 'schedule': events, 'outcome': outcome,
                'approved_control': approved, 'inconsistent_copy_control': inconsistent,
                'unapproved_snapshot_reached_preflight': old and not approved,
                'candidate_processes_started': 0,
                'A_sha256': hashlib.sha256(unapproved).hexdigest(),
                'B_sha256': hashlib.sha256(benign).hexdigest(),
                'frozen_source': real_snapshot(output/'source')})

    def test_reviewed_runtime_A_B_A_reaches_preflight(self):
        self.exercise('runtime', old=True)

    def test_reviewed_driver_A_B_A_reaches_preflight(self):
        self.exercise('driver', old=True)

    def test_repaired_runtime_A_B_A_rejected_before_execution(self):
        self.exercise('runtime')

    def test_repaired_driver_A_B_A_rejected_before_execution(self):
        self.exercise('driver')

    def test_approved_snapshot_reaches_preflight(self):
        self.exercise('runtime', approved=True)

    def test_changed_copy_rejected_before_execution(self):
        self.exercise('runtime', inconsistent=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args=parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SnapshotPolicyTests))
    report={'schema':1, 'scope':'focused policy/snapshot boundary; controlled scheduling; substituted toolchain/preflight; no Lean/build execution',
            'reviewed_commit':REVIEWED, 'reviewed_evaluate_sha256':FIXTURE_SHA256,
            'repaired_evaluator_sha256':g.sha(Path(g.__file__)), 'passed':result.wasSuccessful(),
            'tests_run':result.testsRun, 'cases':SnapshotPolicyTests.reports}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
