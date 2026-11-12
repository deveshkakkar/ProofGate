"""Canary token scope validation. No network, token minting or authentication claims.

Bindings and installation/grant metadata must come from an independently trusted
issuer. Passing caller-authored metadata here does not establish its provenance.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from types import MappingProxyType

PRODUCTION_ID = 1437623154
OWNER_ID = 41484281
PERMISSIONS = MappingProxyType({
    'metadata': 'read', 'contents': 'write', 'pull_requests': 'write',
    'issues': 'read', 'actions': 'read', 'checks': 'read', 'statuses': 'read',
})


class ScopeError(ValueError):
    """Fixed error codes only; supplied data must never enter diagnostics."""


def require(condition, code):
    if not condition:
        raise ScopeError(code)


def integer(value):
    return type(value) is int and value > 0


@dataclass(frozen=True)
class CanaryBinding:
    repository: str
    repository_id: int
    app_id: int
    installation_id: int

    def __post_init__(self):
        require(isinstance(self.repository, str) and re.fullmatch(
            r'deveshkakkar/[A-Za-z0-9_.-]+', self.repository) is not None,
            'invalid_canary_repository')
        name = self.repository.split('/')[1]
        require(name not in ('.', '..') and not name.lower().endswith('.git'),
                'invalid_canary_repository')
        require(self.repository.lower() != 'deveshkakkar/proofgate', 'production_forbidden')
        require(integer(self.repository_id), 'unbound_repository_id')
        require(self.repository_id != PRODUCTION_ID, 'production_forbidden')
        require(integer(self.app_id), 'unbound_app_id')
        require(integer(self.installation_id), 'unbound_installation_id')

    @classmethod
    def from_dict(cls, value):
        require(isinstance(value, dict) and set(value) == {
            'repository', 'repository_id', 'app_id', 'installation_id'}, 'invalid_binding_fields')
        return cls(**value)


def _permissions(value):
    require(isinstance(value, dict) and value == PERMISSIONS, 'permission_scope_mismatch')


def _repository(binding, row):
    require(isinstance(row, dict), 'invalid_repository_metadata')
    require(integer(row.get('id')) and row['id'] == binding.repository_id,
            'repository_scope_mismatch')
    require(row.get('full_name') == binding.repository, 'repository_name_mismatch')


def validate_installation(binding, installation, repositories):
    require(type(binding) is CanaryBinding, 'invalid_binding')
    CanaryBinding.__post_init__(binding)
    require(isinstance(installation, dict), 'invalid_installation_metadata')
    require(integer(installation.get('id')) and installation['id'] == binding.installation_id,
            'installation_id_mismatch')
    require(integer(installation.get('app_id')) and installation['app_id'] == binding.app_id,
            'app_id_mismatch')
    require(installation.get('app_slug') == 'proofgate-coder', 'app_slug_mismatch')
    account = installation.get('account')
    require(isinstance(account, dict) and account.get('login') == 'deveshkakkar' and
            type(account.get('id')) is int and account['id'] == OWNER_ID and
            account.get('type') == 'User', 'installation_account_mismatch')
    require('suspended_at' in installation and installation['suspended_at'] is None,
            'installation_suspended_or_unknown')
    require(installation.get('repository_selection') == 'selected', 'all_repository_installation_forbidden')
    _permissions(installation.get('permissions'))
    require(isinstance(repositories, dict) and type(repositories.get('total_count')) is int and
            repositories['total_count'] == 1 and isinstance(repositories.get('repositories'), list) and
            len(repositories['repositories']) == 1, 'installation_not_canary_only')
    _repository(binding, repositories['repositories'][0])


def token_request(binding, installation, repositories):
    """Build data for an issuer; never performs POST or accepts a default scope."""
    validate_installation(binding, installation, repositories)
    return {'repository_ids': [binding.repository_id], 'permissions': dict(PERMISSIONS)}


def validate_grant(binding, installation, repositories, metadata, now):
    """Validate *redacted metadata*, not a bearer token or its authenticity."""
    validate_installation(binding, installation, repositories)
    require(isinstance(metadata, dict) and set(metadata) == {
        'expires_at', 'permissions', 'repositories', 'repository_selection'},
        'invalid_grant_metadata_fields')
    require(metadata['repository_selection'] == 'selected', 'grant_selection_mismatch')
    _permissions(metadata['permissions'])
    require(isinstance(metadata['repositories'], list) and len(metadata['repositories']) == 1,
            'grant_not_canary_only')
    _repository(binding, metadata['repositories'][0])
    require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None,
            'trusted_clock_required')
    expires = metadata['expires_at']
    require(isinstance(expires, str) and re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', expires) is not None, 'invalid_expiry')
    try:
        expiry = datetime.fromisoformat(expires.replace('Z', '+00:00'))
    except ValueError:
        raise ScopeError('invalid_expiry') from None
    remaining = (expiry - now.astimezone(timezone.utc)).total_seconds()
    require(0 < remaining <= 3600, 'expired_or_excessive_lifetime')
    return {'scope_valid': True, 'repository_id': binding.repository_id,
            'app_id': binding.app_id, 'installation_id': binding.installation_id,
            'expires_at': expires, 'authority': 'metadata-validation-only',
            'producer_authenticated': False, 'policy_admitted': False,
            'merge_eligible': False}
