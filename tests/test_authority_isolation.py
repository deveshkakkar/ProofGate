"""Probe validator/controller tests; actual namespace evidence comes from hosted CI."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from proofgate_authority import isolation


class AuthorityIsolationTests(unittest.TestCase):
    def test_process_success_cannot_authorize_identity_credentials_or_admission(self):
        result = isolation.assess([copy.deepcopy(isolation.EXPECTED)])
        self.assertTrue(result['process_checks_passed'])
        for key in ('coding_agent_tools_verified', 'github_principal_verified',
                    'credential_release_authorized', 'policy_admitted', 'merge_eligible'):
            self.assertIs(result[key], False)

    def test_missing_extra_malformed_and_integer_boolean_observations_reject(self):
        extra = copy.deepcopy(isolation.EXPECTED); extra['DO_NOT_EXPORT_SECRET'] = 'sensitive'
        wrong_type = copy.deepcopy(isolation.EXPECTED); wrong_type['owner_fixture_blocked'] = 1
        bad_ns = copy.deepcopy(isolation.EXPECTED); bad_ns['namespace_separation']['pid'] = 1
        missing = copy.deepcopy(isolation.EXPECTED); del missing['source_read_only']
        for value in (None, {}, [], [extra], [wrong_type], [bad_ns], [missing],
                      [copy.deepcopy(isolation.EXPECTED)] * 2):
            with self.subTest(value=value):
                result = isolation.assess(value)
                self.assertFalse(result['process_checks_passed'])
                self.assertTrue(result['unexpected_observations_rejected'])
                self.assertEqual(result['observations'], [])
                self.assertNotIn('DO_NOT_EXPORT_SECRET', json.dumps(result))

    def test_typed_failed_probe_retains_only_safe_boolean_diagnostics(self):
        row = copy.deepcopy(isolation.EXPECTED); row['owner_fixture_blocked'] = False
        result = isolation.assess([row])
        self.assertFalse(result['process_checks_passed'])
        self.assertFalse(result['unexpected_observations_rejected'])
        self.assertFalse(result['observations'][0]['owner_fixture_blocked'])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux controller metadata')
    def test_controller_uses_fixed_source_private_fixture_and_restores_environment(self):
        observed_calls = []
        def invoke(artifact, entry, rows, output):
            self.assertEqual(entry, '/app/worker_probe.py')
            fixture = Path(rows[0]['owner_fixture'])
            self.assertTrue(fixture.is_file())
            self.assertEqual(fixture.stat().st_mode & 0o777, 0o600)
            self.assertFalse(fixture.is_relative_to(artifact))
            self.assertEqual(set(rows[0]['host_namespaces']), {'pid', 'mnt', 'net'})
            self.assertIn('PROOFGATE_OWNER_CONTEXT_CANARY', os.environ)
            result = [copy.deepcopy(isolation.EXPECTED)]
            (output / 'stdout').write_text(json.dumps(result)); observed_calls.append(entry)
            return result
        original_hash = isolation.runtime.file_hash
        def offline_hash(path):
            return 'f' * 64 if str(path).startswith('/usr/bin/') else original_hash(path)
        with patch.dict(os.environ, {'PROOFGATE_OWNER_CONTEXT_CANARY': 'previous harmless marker'}), \
             patch.object(isolation.runtime, 'preflight'), patch.object(isolation.runtime, 'invoke', side_effect=invoke), \
             patch.object(isolation.runtime, 'file_hash', side_effect=offline_hash):
            result = isolation.run_probe()
            self.assertEqual(os.environ['PROOFGATE_OWNER_CONTEXT_CANARY'], 'previous harmless marker')
        self.assertTrue(result['process_checks_passed'])
        self.assertTrue(result['owner_fixture_readable_on_host'])
        self.assertEqual(observed_calls, ['/app/worker_probe.py'])

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux controller metadata')
    def test_snapshot_mutation_cannot_return_process_pass(self):
        def mutate(artifact, entry, rows, output):
            (artifact / 'worker_probe.py').write_text('# altered\n')
            return [copy.deepcopy(isolation.EXPECTED)]
        with patch.object(isolation.runtime, 'preflight'), \
             patch.object(isolation.runtime, 'invoke', side_effect=mutate):
            with self.assertRaisesRegex(RuntimeError, 'snapshot changed'):
                isolation.run_probe()
