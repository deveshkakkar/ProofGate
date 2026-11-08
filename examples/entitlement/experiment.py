#!/usr/bin/env python3
"""Fresh finite-domain checks. Uses temporary read-only bwrap snapshots; no deployment."""
import hashlib
import itertools
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from framework.kernel import digest, contract_digest, identity, verify
from framework.errors import EvaluationError
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
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))


def preflight():
    if platform.system() != 'Linux':
        raise EvaluationError('unsupported_platform', 'preflight',
                              'Use a Linux host with bubblewrap and a systemd user manager.')
    for binary in ('/usr/bin/python3', '/usr/bin/bwrap', '/usr/bin/systemd-run'):
        if not Path(binary).is_file() or not os.access(binary, os.X_OK):
            raise EvaluationError('missing_dependency', 'preflight',
                                  'Required executable unavailable: ' + binary)
    # Exercise namespaces and the same bounded scope with a fixed empty probe,
    # never candidate code. File checks alone cannot establish runtime usability.
    with tempfile.TemporaryDirectory(prefix='proofgate-doctor-') as temporary:
        base = Path(temporary)
        artifact = base / 'empty'; artifact.mkdir()
        output = base / 'probe'; output.mkdir()
        try:
            invoke(artifact, 'empty_probe', [], output, expect_json=False)
        except EvaluationError as exc:
            raise EvaluationError('sandbox_unavailable', 'preflight',
                'The bounded sandbox probe failed. Check the systemd user manager, '
                'unprivileged namespaces and cgroup support; do not disable isolation.') from exc
    return {'ready': True, 'scope': 'Linux namespaces and bounded systemd user scope; empty probe only'}


def invoke(artifact, entry, rows, output, expect_json=True):
    argv = ['/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
            '--new-session', '--die-with-parent', '--cap-drop', 'ALL', '--proc', '/proc',
            '--dev', '/dev', '--size', '16777216', '--tmpfs', '/tmp']
    for directory in ('/usr', '/bin', '/lib', '/lib64'):
        if Path(directory).exists():
            argv += ['--ro-bind', directory, directory]
    argv += ['--ro-bind', str(artifact), '/app', '--ro-bind', str(HERE / 'probe.py'),
             '/probe.py', '--chdir', '/app', '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
             '/usr/bin/python3', '-B']
    argv += [entry] if expect_json else ['-c', 'pass']
    argv = ['/usr/bin/systemd-run', '--user', '--scope', '--quiet',
            '--property=MemoryMax=268435456', '--property=TasksMax=16',
            '--property=CPUQuota=100%', '--property=RuntimeMaxSec=5s'] + argv
    try:
        with (output / 'stdout').open('wb') as out, (output / 'stderr').open('wb') as err:
            proc = subprocess.run(argv, input=json.dumps(rows).encode(), stdout=out, stderr=err,
                                  timeout=10, preexec_fn=limits)
    except subprocess.TimeoutExpired as exc:
        raise EvaluationError('timeout', entry, 'The bounded check timed out.') from exc
    except OSError as exc:
        raise EvaluationError('runner_unavailable', entry, 'The sandbox process could not start.') from exc
    if proc.returncode:
        raise EvaluationError('check_process_failed', entry,
                              'The sandboxed check exited unsuccessfully; no passing result.')
    if not expect_json:
        return None
    try:
        return json.loads((output / 'stdout').read_text())
    except (ValueError, UnicodeError) as exc:
        raise EvaluationError('invalid_result', entry,
                              'The check did not return valid JSON; no passing result.') from exc


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
        for name in ('kernel.py', '__main__.py', 'errors.py'):
            inputs['verifier']['framework/' + name] = file_hash(ROOT / 'framework' / name)
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
            try:
                observed = invoke(artifact, entry, rows, output)
            except EvaluationError as exc:
                exc.stage = check
                exc.completed_checks = [r['id'] for r in results]
                raise
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
                'receipt': verify(CONTRACT, contract_digest(CONTRACT), inputs, observations),
                'candidate_matches_snapshot': all(
                    (candidate / name).is_file() and not (candidate / name).is_symlink() and
                    file_hash(candidate / name) == inputs['source'][name]
                    for name in ('app.py', 'rule.py'))}


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
