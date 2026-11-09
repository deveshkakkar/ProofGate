"""Actual bounded process probe, not full coding-agent isolation/admission proof."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from examples.entitlement import experiment as runtime

EXPECTED = {'namespace_separation': {'pid': True, 'mnt': True, 'net': True},
            'owner_fixture_blocked': True, 'owner_environment_absent': True,
            'source_read_only': True, 'host_home_absent': True, 'host_run_absent': True}


def assess(observations):
    # Only fixed, typed diagnostic fields may leave the worker. Unexpected
    # strings/keys are not copied into the report (even on a failed probe).
    shape_ok = (isinstance(observations, list) and len(observations) == 1 and
                isinstance(observations[0], dict) and set(observations[0]) == set(EXPECTED))
    if shape_ok:
        row = observations[0]
        namespaces = row['namespace_separation']
        shape_ok = (isinstance(namespaces, dict) and set(namespaces) == {'pid', 'mnt', 'net'} and
                    all(type(value) is bool for value in namespaces.values()) and
                    all(type(row[name]) is bool for name in EXPECTED if name != 'namespace_separation'))
    passed = bool(shape_ok and observations == [EXPECTED])
    return {'process_checks_passed': passed,
            'observations': observations if shape_ok else [],
            'unexpected_observations_rejected': not shape_ok,
            'coding_agent_tools_verified': False,
            'github_principal_verified': False, 'credential_release_authorized': False,
            'policy_admitted': False, 'merge_eligible': False,
            'scope': 'Fixed process diagnostic only; complete coding agent/tool/credential boundary unverified'}


def run_probe():
    """No user commands, credentials, owner paths or candidate source accepted."""
    runtime.preflight()
    source = Path(__file__).with_name('worker_probe.py')
    with tempfile.TemporaryDirectory(prefix='proofgate-isolation-') as temporary:
        base = Path(temporary)
        owner_fixture = base / 'owner-marker'
        owner_fixture.write_bytes(b'harmless isolation canary; not a credential\n')
        owner_fixture.chmod(0o600)
        # Establish that a denial is meaningful: the host can read this marker.
        if not owner_fixture.read_bytes().startswith(b'harmless isolation canary;'):
            raise RuntimeError('owner fixture preparation failed')
        artifact = base / 'snapshot'; artifact.mkdir()
        probe_bytes = source.read_bytes()
        (artifact / 'worker_probe.py').write_bytes(probe_bytes)
        output = base / 'output'; output.mkdir()
        namespaces = {name: os.stat('/proc/self/ns/' + name).st_ino for name in ('pid', 'mnt', 'net')}
        previous = os.environ.get('PROOFGATE_OWNER_CONTEXT_CANARY')
        os.environ['PROOFGATE_OWNER_CONTEXT_CANARY'] = 'harmless environment canary'
        try:
            observed = runtime.invoke(artifact, '/app/worker_probe.py',
                                      [{'owner_fixture': str(owner_fixture), 'host_namespaces': namespaces}], output)
        finally:
            if previous is None:
                os.environ.pop('PROOFGATE_OWNER_CONTEXT_CANARY', None)
            else:
                os.environ['PROOFGATE_OWNER_CONTEXT_CANARY'] = previous
        if (artifact / 'worker_probe.py').read_bytes() != probe_bytes:
            raise RuntimeError('probe snapshot changed')
        result = assess(observed)
        result['owner_fixture_readable_on_host'] = True
        result['source_sha256'] = hashlib.sha256(probe_bytes).hexdigest()
        result['controller_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result['runtime_sha256'] = runtime.file_hash(runtime.HERE / 'experiment.py')
        if not result['unexpected_observations_rejected']:
            result['raw_output_sha256'] = runtime.file_hash(output / 'stdout')
        result['executables'] = {name: runtime.file_hash(Path('/usr/bin/' + name).resolve())
                                 for name in ('python3', 'bwrap', 'systemd-run')}
        return result
