#!/usr/bin/env python3
"""Fresh finite-domain checks. Uses temporary read-only bwrap snapshots; no deployment."""
import hashlib
import itertools
import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from framework.kernel import digest, contract_digest, identity, verify
HERE = Path(__file__).resolve().parent
CONTRACT = {'schema': 1, 'checks': ['finite_rule', 'application_boundary'],
            'assumptions': ['Only tenant IDs 0, 1, 2 and boolean flags are modeled.',
                            'Same-user trusted evaluator; hashes do not authenticate observations.',
                            'Finite exhaustive checking is not a proof over arbitrary programs or inputs.']}


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(path):
    return {p.name: file_hash(p) for p in sorted(path.iterdir()) if p.is_file()}


def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))


def invoke(artifact, entry, rows, output):
    argv = ['/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
            '--new-session', '--die-with-parent', '--cap-drop', 'ALL', '--proc', '/proc',
            '--dev', '/dev', '--size', '16777216', '--tmpfs', '/tmp']
    for directory in ('/usr', '/bin', '/lib', '/lib64'):
        if Path(directory).exists():
            argv += ['--ro-bind', directory, directory]
    argv += ['--ro-bind', str(artifact), '/app', '--ro-bind', str(HERE / 'probe.py'),
             '/probe.py', '--chdir', '/app', '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
             '/usr/bin/python3', '-B', entry]
    argv = ['/usr/bin/systemd-run', '--user', '--scope', '--quiet',
            '--property=MemoryMax=268435456', '--property=TasksMax=16',
            '--property=CPUQuota=100%', '--property=RuntimeMaxSec=5s'] + argv
    with (output / 'stdout').open('wb') as out, (output / 'stderr').open('wb') as err:
        proc = subprocess.run(argv, input=json.dumps(rows).encode(), stdout=out, stderr=err,
                              timeout=10, preexec_fn=limits)
    if proc.returncode:
        raise RuntimeError('sandbox/check failed: ' + (output / 'stderr').read_text()[:500])
    return json.loads((output / 'stdout').read_text())


def expected(row):
    # Independent deny-first oracle, intentionally not imported from candidate rule.
    if row['subject_tenant'] != row['resource_tenant']:
        return False
    if False in (row['active'], row['entitled'], row['enabled']):
        return False
    return True


def run_variant(variant, candidate=None):
    candidate = Path(candidate) if candidate is not None else HERE
    with tempfile.TemporaryDirectory(prefix='proofgate-entitlement-') as temporary:
        base = Path(temporary)
        source = base / 'source'; source.mkdir()
        artifact = base / 'artifact'; artifact.mkdir()
        for name in ('rule.py', 'app.py'):
            (source / name).write_bytes((candidate / name).read_bytes())
        if variant == 'always_deny':
            (source / 'rule.py').write_text('def allow(**kwargs): return False\n')
        elif variant == 'cross_tenant':
            (source / 'rule.py').write_text('def allow(**kwargs): return True\n')
        elif variant == 'adapter_spoof':
            p = source / 'app.py'
            p.write_text(p.read_text().replace("return {'allowed': allow(**row)}",
                "row = dict(row, resource_tenant=row['subject_tenant'])\n    return {'allowed': allow(**row)}"))
        for p in source.iterdir():
            (artifact / p.name).write_bytes(p.read_bytes())
        inputs = {'source': manifest(source), 'artifact': manifest(artifact),
                  'verifier': {name: file_hash(HERE / name) for name in ('experiment.py', 'probe.py')},
                  'environment': {'python': file_hash(Path('/usr/bin/python3').resolve()),
                                  'bwrap': file_hash(Path('/usr/bin/bwrap')),
                                  'systemd-run': file_hash(Path('/usr/bin/systemd-run')),
                                  'scope': digest({'python': sys.version, 'stdlib': 'host-trusted; not fully fingerprinted'})}}
        inputs['verifier']['kernel.py'] = file_hash(ROOT / 'framework/kernel.py')
        bound = identity(CONTRACT, inputs)
        cases = [dict(zip(('subject_tenant', 'resource_tenant', 'active', 'entitled', 'enabled'), values))
                 for values in itertools.product(range(3), range(3), (False, True), (False, True), (False, True))]
        malformed = [None, {}, [], dict(cases[-1], active=1), dict(cases[-1], subject_tenant=True),
                     dict(cases[-1], resource_tenant=3), dict(cases[-1], extra=True),
                     dict(cases[-1], entitled='true')]
        observations = []
        results = []
        for check, entry, rows, wanted in (
                ('finite_rule', '/probe.py', cases, [expected(r) for r in cases]),
                ('application_boundary', '/app/app.py', cases + malformed,
                 [{'allowed': expected(r)} for r in cases] + [{'error': 'invalid request'}] * len(malformed))):
            output = base / check; output.mkdir()
            observed = invoke(artifact, entry, rows, output)
            # JSON booleans must remain booleans, rather than accepting integer equality.
            passed = json.dumps(observed, sort_keys=True) == json.dumps(wanted, sort_keys=True)
            observations.append({'id': check, 'status': 'passed' if passed else 'failed', 'identity': bound})
            results.append({'id': check, 'passed': passed, 'cases': len(rows),
                            'stdout_sha256': file_hash(output / 'stdout'),
                            'inputs': rows, 'expected': wanted, 'observed': observed})
        if inputs['source'] != manifest(source) or inputs['artifact'] != manifest(artifact):
            raise RuntimeError('snapshot changed during checking')
        return {'variant': variant, 'contract': CONTRACT, 'inputs': inputs,
                'observations': observations, 'checks': results,
                'receipt': verify(CONTRACT, contract_digest(CONTRACT), inputs, observations)}


def main():
    started = time.monotonic()
    rows = [run_variant(name) for name in ('valid', 'always_deny', 'cross_tenant', 'adapter_spoof')]
    expected_checks = [[True, True], [False, False], [False, False], [True, False]]
    passed = all([c['passed'] for c in row['checks']] == wanted and
                 row['receipt']['consistent'] == (i == 0)
                 for i, (row, wanted) in enumerate(zip(rows, expected_checks)))
    print(json.dumps({'scope': 'fresh finite-domain and application checks; no deployment or universal proof',
                      'passed': passed, 'elapsed_seconds': round(time.monotonic() - started, 3),
                      'matrix': rows}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
