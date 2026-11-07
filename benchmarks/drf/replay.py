"""Read-only historical DRF shadow evaluator for inspected local source."""
import argparse
import hashlib
import json
import os
import resource
import re
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time

from framework.kernel import contract_digest, digest, identity, verify
from .score import classify

HERE = Path(__file__).resolve().parent
NODES = {'or_composition': 'test_or_contract', 'model_permissions': 'test_model_permissions_contract',
         'renderer_boundary': 'test_renderer_boundary_contract'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_regular(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('regular input files required')
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError('input size limit exceeded')
    return data


def manifest(root):
    result = {}; total = 0
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlinks are unsupported')
        if path.is_file():
            total += path.stat().st_size
            if total > 256 * 1024 * 1024 or len(result) >= 10000:
                raise ValueError('input tree exceeds resource bound')
            result[path.relative_to(root).as_posix()] = sha(path)
        elif not path.is_dir():
            raise ValueError('nonregular input tree')
    if not result:
        raise ValueError('empty input tree')
    return result


def extract(archive, destination):
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if len(members) > 10000 or sum(m.size for m in members) > 128 * 1024 * 1024:
            raise ValueError('reference archive exceeds bound')
        for member in members:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or '..' in name.parts or '\\' in member.name or
                    not (member.isdir() or member.isfile())):
                raise ValueError('unsafe reference archive')
            target = destination.joinpath(*name.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, target.open('xb') as output:
                    shutil.copyfileobj(data, output)


def scope_command(argv, backend):
    properties = ['--scope', '--quiet', '--property=MemoryMax=536870912',
                  '--property=TasksMax=32', '--property=CPUQuota=100%', '--property=RuntimeMaxSec=45s',
                  '--property=TimeoutStopSec=1s', '--property=KillMode=control-group', '--property=SendSIGKILL=yes']
    helper = ['/usr/bin/python3', str(HERE / 'resource_exec.py')] + argv
    if os.getuid() == 0:
        raise ValueError('run the controller as an unprivileged user')
    if backend == 'user':
        return ['/usr/bin/systemd-run', '--user'] + properties + helper
    if backend != 'github-hosted' or os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise ValueError('GitHub backend requires a GitHub-hosted Actions runner')
    drop = ['/usr/bin/setpriv', '--reuid=' + str(os.getuid()), '--regid=' + str(os.getgid()),
            '--clear-groups', '--no-new-privs']
    return ['/usr/bin/sudo', '-n', '/usr/bin/systemd-run'] + properties + drop + helper


def run_suite(artifact, dependencies, heldout, output, case, suite, backend):
    stdout = output / (suite + '.stdout'); stderr = output / (suite + '.stderr')
    argv = ['/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net', '--new-session',
            '--die-with-parent', '--cap-drop', 'ALL', '--proc', '/proc', '--dev', '/dev',
            '--size', '67108864', '--tmpfs', '/tmp']
    for path in ('/usr', '/bin', '/lib', '/lib64'):
        if Path(path).exists():
            argv += ['--ro-bind', path, path]
    argv += ['--ro-bind', str(artifact), '/work', '--ro-bind', str(dependencies), '/deps',
             '--dir', '/checks']
    for name in ('run_tests.py', 'contracts.py', 'compatibility.py'):
        target = 'test_contract.py' if name == ('compatibility.py' if suite == 'compatibility' else 'contracts.py') else name
        argv += ['--ro-bind', str(HERE / name), '/checks/' + target]
    argv += ['--ro-bind', str(artifact / 'tests/conftest.py'), '/checks/conftest.py']
    if suite == 'heldout':
        argv += ['--ro-bind', str(heldout), '/work/tests/' + case['test_file']]
    argv += ['--chdir', '/work', '--clearenv', '--setenv', 'PATH', '/usr/bin:/bin',
             '--setenv', 'PYTHONPATH', '/deps:/work', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
             '--setenv', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1', '--setenv', 'PROOFGATE_CASE', case['id'],
             '/usr/bin/python3', '-B', '/checks/run_tests.py', '-p', 'pytest_django.plugin',
             '-p', 'no:cacheprovider', '-o', 'addopts=', '-q']
    if suite == 'heldout':
        argv += ['tests/' + case['test_file'] + '::' + case['test_class']]
    else:
        node = 'test_anonymous_readonly_preserved' if suite == 'compatibility' else NODES[case['id']]
        argv += ['/checks/test_contract.py::' + node]
    started = time.monotonic()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        try:
            proc = subprocess.run(scope_command(argv, backend), stdout=out, stderr=err, timeout=50)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = None
    markers = [line[len('PROOFGATE_RESULT='):] for line in stdout.read_text(errors='replace').splitlines()
               if line.startswith('PROOFGATE_RESULT=')]
    observation = json.loads(markers[-1]) if len(markers) == 1 else {}
    if observation.get('exit_code') != code:
        observation = {}
    expected = case['expected_tests']['heldout'] if suite == 'heldout' else 1
    return {'status': classify(observation, expected), 'observation': observation,
            'exit_code': code, 'seconds': round(time.monotonic() - started, 3),
            'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)}


def evaluate(case, reference, candidate, heldout, dependencies, output, backend='user', compatibility=False):
    allowed_module = ('rest_framework/renderers.py' if case.get('id') == 'renderer_boundary' else 'rest_framework/permissions.py')
    if (case.get('id') not in NODES or case.get('module') != allowed_module or
            not isinstance(case.get('base_sha'), str) or not re.fullmatch('[0-9a-f]{40}', case['base_sha']) or
            not re.fullmatch(r'test_[a-z_]+\.py', case.get('test_file', '')) or
            not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', case.get('test_class', ''))):
        raise ValueError('unsupported reference descriptor')
    if compatibility and case['id'] != 'model_permissions':
        raise ValueError('compatibility check applies to model_permissions only')
    candidate_bytes = read_regular(candidate, 256 * 1024)
    heldout_bytes = read_regular(heldout, 2 * 1024 * 1024)
    if hashlib.sha256(heldout_bytes).hexdigest() != case['heldout_test_sha256']:
        raise ValueError('held-out test identity mismatch')
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    state = output / 'run-state.json'
    state.write_text(json.dumps({'completed': False, 'scope': 'shadow diagnostic only'}) + '\n')
    with tempfile.TemporaryDirectory(prefix='proofgate-shadow-') as temporary:
        work = Path(temporary); artifact = work / 'artifact'; artifact.mkdir()
        archive = work / 'reference.tar'
        def archive_limit():
            resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
        with archive.open('wb') as out:
            proc = subprocess.run(['/usr/bin/git', '--no-replace-objects', '-C', str(reference), '-c', 'core.hooksPath=/dev/null', '-c', 'core.attributesFile=/dev/null',
                                   'archive', '--format=tar', case['base_sha']], stdout=out,
                                  stderr=subprocess.DEVNULL, timeout=20, preexec_fn=archive_limit)
        if proc.returncode or archive.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('cannot read bounded pinned reference commit')
        extract(archive, artifact)
        target = artifact / case['module']
        if sha(target) != case['source_sha256']['original']:
            raise ValueError('reference module identity mismatch')
        target.write_bytes(candidate_bytes)
        pinned = work / 'heldout.py'; pinned.write_bytes(heldout_bytes)
        suites = ['heldout', 'contract'] + (['compatibility'] if compatibility else [])
        contract = {'schema': 1, 'checks': suites,
                    'assumptions': ['Inspected local source; Python tests are not tamper-resistant.',
                                    'Finite domains and selected test classes only.',
                                    'Host and standard libraries trusted; environment only partially fingerprinted.']}
        inputs = {'source': {case['module']: hashlib.sha256(candidate_bytes).hexdigest()},
                  'artifact': manifest(artifact), 'verifier': {},
                  'environment': {'python': sha(Path('/usr/bin/python3').resolve()),
                                  'bwrap': sha(Path('/usr/bin/bwrap')),
                                  'systemd-run': sha(Path('/usr/bin/systemd-run'))}}
        deps_before = manifest(dependencies)
        inputs['environment'].update({'dependencies/' + k: v for k, v in deps_before.items()})
        for name in ('replay.py', 'run_tests.py', 'resource_exec.py', 'contracts.py', 'compatibility.py', 'score.py', 'ci.py'):
            inputs['verifier'][name] = sha(HERE / name)
        inputs['verifier']['kernel.py'] = sha(HERE.parents[1] / 'framework/kernel.py')
        inputs['verifier']['heldout.py'] = hashlib.sha256(heldout_bytes).hexdigest()
        inputs['verifier']['case.json'] = digest(case)
        inputs['environment']['profile'] = digest({'backend': backend, 'network': 'disabled', 'host_libraries': 'trusted; not completely fingerprinted'})
        if backend == 'github-hosted':
            for binary in ('sudo', 'setpriv'):
                inputs['environment'][binary] = sha(Path('/usr/bin') / binary)
        bound = identity(contract, inputs)
        results = {suite: run_suite(artifact, dependencies.resolve(), pinned, output, case, suite, backend)
                   for suite in suites}
        verifier_changed = any(sha(HERE / name) != inputs['verifier'][name]
                               for name in ('replay.py', 'run_tests.py', 'resource_exec.py', 'contracts.py', 'compatibility.py', 'score.py', 'ci.py'))
        verifier_changed = verifier_changed or sha(HERE.parents[1] / 'framework/kernel.py') != inputs['verifier']['kernel.py']
        binaries = ['python', 'bwrap', 'systemd-run'] + (['sudo', 'setpriv'] if backend == 'github-hosted' else [])
        binary_paths = {'python': Path('/usr/bin/python3').resolve()}
        environment_changed = any(sha(binary_paths.get(name, Path('/usr/bin') / name)) != inputs['environment'][name] for name in binaries)
        if verifier_changed or environment_changed or inputs['artifact'] != manifest(artifact) or deps_before != manifest(dependencies):
            raise ValueError('evaluated inputs changed during execution')
        evidence = [{'id': suite, 'status': results[suite]['status'], 'identity': bound} for suite in suites]
        receipt = verify(contract, contract_digest(contract), inputs, evidence)
        report = {'schema': 1, 'case': case['id'], 'scope': 'inspected-code shadow diagnostics only',
                  'contract': contract, 'inputs': inputs, 'evidence': evidence,
                  'checks': results, 'receipt': receipt, 'backend': backend}
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        shutil.copyfile(artifact / 'LICENSE.md', output / 'upstream-LICENSE.md')
        state.write_text(json.dumps({'completed': True, 'consistent': receipt['consistent']}) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=tuple(NODES))
    for name in ('reference', 'candidate', 'heldout', 'dependencies', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--backend', choices=('user', 'github-hosted'), default='user')
    parser.add_argument('--compatibility', action='store_true')
    args = parser.parse_args()
    case = next(case for case in json.loads((HERE / 'results.json').read_text())['cases'] if case['id'] == args.case)
    case = dict(case, test_file='test_renderers.py' if args.case == 'renderer_boundary' else 'test_permissions.py')
    try:
        report = evaluate(case, args.reference, args.candidate, args.heldout, args.dependencies,
                          args.output, args.backend, args.compatibility)
        for name, result in report['checks'].items():
            print(name + ': ' + result['status'])
        print('Report: ' + str(args.output / 'report.json'))
        if any(result['status'] == 'inconclusive' for result in report['checks'].values()):
            return 2
        return 0 if report['receipt']['consistent'] else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, 'Shadow evaluation could not complete: ' + type(exc).__name__ + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
