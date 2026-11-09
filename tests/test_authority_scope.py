"""Canary issuer scope guards, with synthetic metadata and no live credentials."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from proofgate_authority.scope import CanaryBinding, PERMISSIONS, ScopeError, token_request, validate_grant

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def fixtures():
    binding = CanaryBinding('deveshkakkar/authority-canary', 987654321, 1234567, 7654321)
    installation = {'id': binding.installation_id, 'app_id': binding.app_id,
                    'app_slug': 'proofgate-coder', 'account': {'id': 41484281, 'login': 'deveshkakkar', 'type': 'User'},
                    'suspended_at': None, 'repository_selection': 'selected', 'permissions': dict(PERMISSIONS)}
    repositories = {'total_count': 1, 'repositories': [{'id': binding.repository_id, 'full_name': binding.repository}]}
    grant = {'expires_at': '2026-11-09T13:00:00Z', 'permissions': dict(PERMISSIONS),
             'repositories': copy.deepcopy(repositories['repositories']), 'repository_selection': 'selected'}
    return binding, installation, repositories, grant


class CanaryScopeTests(unittest.TestCase):
    def test_exact_request_and_redacted_grant_cannot_grant_authority(self):
        binding, installation, repos, grant = fixtures()
        request = token_request(binding, installation, repos)
        self.assertEqual(request, {'repository_ids': [987654321], 'permissions': dict(PERMISSIONS)})
        request['permissions']['administration'] = 'write'
        self.assertNotIn('administration', token_request(binding, installation, repos)['permissions'])
        result = validate_grant(binding, installation, repos, grant, NOW)
        self.assertTrue(result['scope_valid'])
        for key in ('producer_authenticated', 'policy_admitted', 'merge_eligible'):
            self.assertIs(result[key], False)
        self.assertNotIn('token', result)

    def test_binding_has_no_unbound_bool_or_production_fallback(self):
        values = fixtures()[0].__dict__.copy()
        for key, bad_values in {
            'repository_id': (None, True, 0, -1, 1437623154, '987654321'),
            'app_id': (None, True, 0), 'installation_id': (None, False, 0),
            'repository': ('deveshkakkar/ProofGate', 'deveshkakkar/PROOFGATE', 'other/canary',
                           'deveshkakkar/ProofGate.git', 'deveshkakkar/..', '/canary')}.items():
            for bad in bad_values:
                with self.subTest(key=key, bad=bad), self.assertRaises(ScopeError):
                    CanaryBinding.from_dict({**values, key: bad})
        with self.assertRaises(ScopeError): CanaryBinding.from_dict({**values, 'accepted': True})

    def test_installation_identity_scope_and_permissions(self):
        for field, value in (('id', True), ('id', 1), ('app_id', 1), ('app_slug', 'other-app'),
                             ('suspended_at', 'suspended'), ('repository_selection', 'all'),
                             ('permissions', {**dict(PERMISSIONS), 'administration': 'write'}),
                             ('permissions', {**dict(PERMISSIONS), 'checks': 'write'}),
                             ('permissions', {}), ('account', {'id': 41484281, 'login': 'other', 'type': 'User'})):
            binding, installation, repos, _ = fixtures(); installation[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ScopeError):
                token_request(binding, installation, repos)
        binding, installation, repos, _ = fixtures(); del installation['suspended_at']
        with self.assertRaises(ScopeError): token_request(binding, installation, repos)

    def test_extra_production_empty_paginated_or_alias_repository_rejects(self):
        for bad in ({'total_count': 0, 'repositories': []}, {'total_count': True, 'repositories': []},
                    {'total_count': 2, 'repositories': []},
                    {'total_count': 1, 'repositories': [{'id': 1437623154, 'full_name': 'deveshkakkar/ProofGate'}]},
                    {'total_count': 1, 'repositories': [{'id': 987654321, 'full_name': 'deveshkakkar/other'}]}):
            binding, installation, _, _ = fixtures()
            with self.subTest(bad=bad), self.assertRaises(ScopeError): token_request(binding, installation, bad)
        binding, installation, repos, _ = fixtures()
        repos['repositories'].append({'id': 1437623154, 'full_name': 'deveshkakkar/ProofGate'})
        with self.assertRaises(ScopeError): token_request(binding, installation, repos)

    def test_grant_scope_escalation_and_secret_metadata_reject_without_echo(self):
        for field, bad in (('permissions', {**dict(PERMISSIONS), 'workflows': 'write'}),
                           ('repository_selection', 'all'), ('repositories', []),
                           ('repositories', [{'id': 1437623154, 'full_name': 'deveshkakkar/ProofGate'}]),
                           ('token', 'DO_NOT_ECHO_THIS_SECRET')):
            binding, installation, repos, grant = fixtures(); grant[field] = bad
            with self.subTest(field=field), self.assertRaises(ScopeError) as error:
                validate_grant(binding, installation, repos, grant, NOW)
            self.assertNotIn('DO_NOT_ECHO_THIS_SECRET', str(error.exception))

    def test_grant_expiry_and_clock_fail_closed(self):
        for expiry in ('2026-11-09T12:00:00Z', '2026-11-09T11:59:59Z', '2026-11-09T13:00:01Z',
                       '2026-99-09T12:30:00Z', '2026-11-09', None, True):
            binding, installation, repos, grant = fixtures(); grant['expires_at'] = expiry
            with self.subTest(expiry=expiry), self.assertRaises(ScopeError):
                validate_grant(binding, installation, repos, grant, NOW)
        binding, installation, repos, grant = fixtures()
        with self.assertRaises(ScopeError): validate_grant(binding, installation, repos, grant, NOW.replace(tzinfo=None))

    def test_cli_builds_only_data_and_never_reads_owner_auth(self):
        binding, installation, repos, _ = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, value in [('binding', binding.__dict__), ('installation', installation), ('repositories', repos)]:
                (root / (name + '.json')).write_text(json.dumps(value))
            args = [sys.executable, '-I', '-B', str(ROOT / 'scripts/check_canary_scope.py')]
            for name in ('binding', 'installation', 'repositories'): args += ['--' + name, str(root / (name + '.json'))]
            result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=5,
                                    env={'GH_TOKEN': 'DO_NOT_ECHO_OWNER_CANARY', 'HOME': temp})
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(result.stdout)
            self.assertFalse(record['request_executed']); self.assertFalse(record['policy_admitted'])
            self.assertNotIn('DO_NOT_ECHO_OWNER_CANARY', result.stdout + result.stderr)
            (root / 'binding.json').write_text('{"repository":"DO_NOT_ECHO_SECRET","repository":"duplicate"}')
            bad = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=5)
            self.assertEqual(bad.returncode, 2)
            self.assertNotIn('DO_NOT_ECHO_SECRET', bad.stdout + bad.stderr)
