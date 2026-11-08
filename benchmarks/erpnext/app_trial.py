"""Fixed inspected-code ERPNext trial controller; GitHub-hosted runners only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(case, observation, variant):
    """Require exact inventory and expected failure identities, not a generic exit."""
    try:
        if variant not in ('base', 'head') or type(observation) is not dict or type(observation.get('schema')) is not int or observation.get('schema') != 1:
            return False
        transport = observation['transport_exit']
        if type(transport) is not int or transport not in ((0,) if variant == 'head' else (0, 1)):
            return False
        runs = observation['runs']
        if type(runs) is not list or len(runs) != 1:
            return False
        row = runs[0]
        prefix = case['test_module'] + '.' + case['test_class'] + '.'
        expected = {prefix + name for name in case['test_names']}
        ids = row['test_ids']
        if (type(ids) is not list or any(type(i) is not str for i in ids) or len(ids) != len(expected) or
                set(ids) != expected or type(row['tests']) is not int or row['tests'] != len(expected)):
            return False
        if any(row[key] != [] for key in ('error_ids', 'skipped_ids', 'expected_failure_ids', 'unexpected_success_ids')):
            return False
        failures = row['failure_ids']
        wanted = {prefix + name for name in case['original_failure_names']} if variant == 'base' else set()
        return (type(failures) is list and all(type(i) is str for i in failures) and
                len(failures) == len(set(failures)) and set(failures) == wanted)
    except (KeyError, TypeError, ValueError):
        return False


def extract(archive, destination):
    """Bounded GitHub archive extraction; no links or path escapes supported."""
    destination.mkdir()
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if len(members) > 100000 or sum(m.size for m in members) > 512 * 1024 * 1024:
            raise ValueError('source archive exceeds bound')
        for member in members:
            name = Path(member.name)
            if name.is_absolute() or '..' in name.parts or not (member.isdir() or member.isfile()):
                raise ValueError('unsupported source archive path/type')
            target = destination.joinpath(*name.parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, target.open('xb') as output:
                    shutil.copyfileobj(data, output)


def download(url, path, limit):
    with urllib.request.urlopen(url, timeout=60) as response, path.open('xb') as output:
        count = 0
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if count > limit:
                raise ValueError('download exceeds bound')
            output.write(chunk)
    return sha(path)


def local_snapshot(directory):
    # Bench consumes local Git URLs. These synthetic commits describe archived
    # bytes, not original history; real source revisions and archive hashes are
    # recorded separately. No credential helper, hooks, or remote is configured.
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(directory), 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0'}
    for argv in (['git', 'init', '-q', '-b', 'develop'], ['git', 'add', '-f', '.'],
                 ['git', '-c', 'user.name=Snapshot', '-c', 'user.email=snapshot@example.invalid',
                  '-c', 'core.hooksPath=/dev/null', 'commit', '-q', '-m', 'Pinned archived source snapshot']):
        subprocess.run(argv, cwd=directory, env=env, check=True, timeout=45, stdout=subprocess.DEVNULL)


def execute(work):
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted' or os.getuid() == 0:
        raise ValueError('requires disposable GitHub-hosted runner and unprivileged controller')
    work.mkdir(parents=False, exist_ok=False)
    output = work / 'results';output.mkdir()
    inputs = work / 'inputs';inputs.mkdir()
    case = json.loads((HERE / 'app_case.json').read_text())
    report = {'schema': 1, 'scope': 'inspected-code full-app historical controls only',
              'completed': False, 'case': case, 'sources': {}, 'stage': 'preflight',
              'verifier': {name: sha(HERE / name) for name in
                           ('app_case.json', 'app_trial.py', 'app_bootstrap.py', 'app_collect.py', 'app_inventory.py')}}
    name = 'proofgate-erp-' + uuid.uuid4().hex
    started = time.monotonic()

    def save():
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'stage': report['stage'], 'completed': report['completed']}), flush=True)

    def command(label, argv, timeout=600):
        with (output / (label + '.log')).open('xb') as handle:
            proc = subprocess.run(argv, stdout=handle, stderr=subprocess.STDOUT, timeout=timeout)
        if proc.returncode:
            raise RuntimeError(label + ' exit=' + str(proc.returncode))

    created = False
    try:
        save()
        if shutil.disk_usage(work).free < 12 * 1024 ** 3:
            raise ValueError('requires12GiB disk headroom before image acquisition')
        for app in ('frappe', 'payments', 'erpnext'):
            revision = case['erpnext_base'] if app == 'erpnext' else case[app]
            if not re.fullmatch('[0-9a-f]{40}', revision):
                raise ValueError('invalid pinned revision')
            archive = work / (app + '.tar.gz')
            report['sources'][app] = {'revision': revision, 'archive_sha256': download(
                'https://codeload.github.com/frappe/' + app + '/tar.gz/' + revision, archive, 64 * 1024 ** 2)}
            extract(archive, inputs / app)
            local_snapshot(inputs / app)
        base = inputs / 'erpnext' / case['module']
        shutil.copyfile(base, inputs / 'base-report.py')
        report['sources']['base-module'] = {'sha256': sha(base)}
        for filename, source_path in (('head-report.py', case['module']), ('heldout.py', case['tests'])):
            report['sources'][filename] = {'sha256': download('https://raw.githubusercontent.com/frappe/erpnext/' +
                case['erpnext_head'] + '/' + source_path, inputs / filename, 256 * 1024)}
        report['stage'] = 'image-acquisition';save()
        command('image-pull', ['docker', 'pull', case['image']], timeout=300)
        argv = ['docker', 'create', '--name', name, '--user', '1001:1001', '--read-only',
                '--memory', '5g', '--memory-swap', '5g', '--cpus', '2', '--pids-limit', '256',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--network', 'bridge',
                '--tmpfs', '/home/ci:rw,exec,nosuid,size=4294967296,uid=1001,gid=1001,mode=0700',
                '--tmpfs', '/tmp:rw,nosuid,size=134217728,uid=1001,gid=1001,mode=1777',
                '--mount', 'type=bind,src=' + str(inputs.resolve()) + ',dst=/inputs,readonly',
                '--mount', 'type=bind,src=' + str(HERE) + ',dst=/driver,readonly',
                '--env', 'HOME=/home/ci', '--env', 'PYTHONDONTWRITEBYTECODE=1',
                '--env', 'PIP_CONFIG_FILE=/dev/null', '--env', 'PIP_INDEX_URL=https://pypi.org/simple',
                '--env', 'UV_INDEX_URL=https://pypi.org/simple', '--env', 'GIT_CONFIG_GLOBAL=/dev/null',
                '--env', 'GIT_TERMINAL_PROMPT=0', '--env', 'GITHUB_TOKEN=', '--env', 'GH_TOKEN=',
                '--env', 'CI_GITHUB_TOKEN=', '--workdir', '/home/ci', '--entrypoint', 'sleep', case['image'], '1800']
        command('container-create', argv, timeout=30);created = True
        command('container-start', ['docker', 'start', name], timeout=30)
        report['stage'] = 'dependency-bootstrap';save()
        command('dependency-bootstrap', ['docker', 'exec', name, 'python', '/driver/app_bootstrap.py', 'setup'], timeout=900)
        inventory = subprocess.check_output(['docker', 'exec', name, 'cat', '/home/ci/trial/environment.json'], timeout=30)
        if len(inventory) > 2 * 1024 * 1024:
            raise ValueError('environment inventory bound')
        report['environment'] = json.loads(inventory)
        (output / 'environment.json').write_bytes(inventory)
        command('disconnect-network', ['docker', 'network', 'disconnect', 'bridge', name], timeout=30)
        info = json.loads(subprocess.check_output(['docker', 'inspect', name], timeout=30))[0]
        if info['NetworkSettings']['Networks']:
            raise ValueError('test container still has network attachment')
        report['isolation'] = {'network_attachments': info['NetworkSettings']['Networks'],
                               'memory': info['HostConfig']['Memory'], 'memory_swap': info['HostConfig']['MemorySwap'],
                               'pids': info['HostConfig']['PidsLimit'], 'readonly_root': info['HostConfig']['ReadonlyRootfs'],
                               'cap_drop': info['HostConfig']['CapDrop'], 'security': info['HostConfig']['SecurityOpt'],
                               'user': info['Config']['User'], 'image_id': info['Image']}
        report['stage'] = 'application-controls';save()
        command('application-controls', ['docker', 'exec', name, 'python', '/driver/app_bootstrap.py', 'test'], timeout=900)
        report['observations'] = {}
        for variant in ('base', 'head'):
            raw = subprocess.check_output(['docker', 'exec', name, 'cat', '/home/ci/trial/' + variant + '-result.json'], timeout=30)
            if len(raw) > 1024 * 1024:
                raise ValueError('observation bound')
            value = json.loads(raw)
            report['observations'][variant] = value
        report['controls_match'] = all(
            classify(case, value, variant) and value.get('source_before') == value.get('source_after') and
            value.get('source_before') == {
                'module_sha256': report['sources']['base-module' if variant == 'base' else 'head-report.py']['sha256'],
                'heldout_sha256': report['sources']['heldout.py']['sha256']}
            for variant, value in report['observations'].items())
        report['completed'] = True
    except (OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
    finally:
        if created:
            # Export only our fixed sanitized log/result directory, never site
            # configurations, databases, environment dumps or a container root.
            export = "import json,pathlib,re; p=pathlib.Path('/home/ci/trial'); ok=json.loads((p/'logs-sanitized.json').read_text()).get('sanitized') is True; print(json.dumps({f.name:'\\n'.join('<redacted sensitive line>' if re.search('password|secret|token|encryption_key|authorization',l,re.I) else l for l in f.read_text(errors='replace')[-2097152:].splitlines()) for f in p.glob('*.log') if ok and f.is_file() and not f.is_symlink()}))"
            try:
                logs = subprocess.check_output(['docker', 'exec', name, 'python', '-c', export], timeout=30)
                if len(logs) <= 20 * 1024 * 1024:
                    (output / 'sanitized-container-logs.json').write_bytes(logs)
            except subprocess.SubprocessError:
                pass
            subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        report['seconds'] = round(time.monotonic() - started, 3);save()
    return 0 if report.get('completed') and report.get('controls_match') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    raise SystemExit(execute(parser.parse_args().work))
