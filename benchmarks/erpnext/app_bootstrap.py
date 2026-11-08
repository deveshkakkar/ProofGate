"""Fixed report trial inside the bounded container; never run on the home server."""
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

HOME = Path('/home/ci')
BENCH = HOME / 'bench'
STATE = HOME / 'trial'
STATE.mkdir(exist_ok=True)
CASE = json.loads(Path('/driver/app_case.json').read_text())
SECRETS = []
PROCESSES = []


def log_tail(path):
    with path.open('rb') as handle:
        start = max(0, path.stat().st_size - 2097152)
        handle.seek(start)
        if start:
            handle.readline()
        return handle.read(2097152).decode(errors='replace')


def run(label, argv, cwd=HOME, timeout=600, input_data=None):
    # Captured logs are bounded by the container filesystem; only explicit,
    # redacted command output is later exported. Command arguments stay private.
    log = STATE / (label + '.log')
    with log.open('wb') as output:
        proc = subprocess.run(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, timeout=timeout, input=input_data)
    text = log_tail(log)
    for value in SECRETS:
        text = text.replace(value, '<redacted>')
    log.write_text(text[-2 * 1024 * 1024:])
    if proc.returncode:
        raise RuntimeError(label + ' exit=' + str(proc.returncode))


def setup():
    # Backend-only trial: do not invoke frontend package lifecycle scripts.
    (HOME / '.yarnrc').write_text('--install.ignore-scripts true\n')
    run('bench-init', ['bench', 'init', '--skip-assets', '--no-backups', '--frappe-path', '/inputs/frappe',
                       '--frappe-branch', 'develop', '--python', sys.executable, str(BENCH)])
    for app in ('payments', 'erpnext'):
        run('install-' + app, ['bench', 'get-app', '--skip-assets', '--branch', 'develop', app,
                              '/inputs/' + app], cwd=BENCH)
    run('dev-requirements', ['bench', 'setup', 'requirements', '--dev'], cwd=BENCH)
    run('environment-inventory', [str(BENCH / 'env/bin/python'), '/driver/app_inventory.py',
                                  str(STATE / 'environment.json')], cwd=BENCH)
    print(json.dumps({'stage': 'dependencies-installed'}))


def launch(name, argv):
    log = (STATE / (name + '.log')).open('wb')
    proc = subprocess.Popen(argv, cwd=HOME, stdout=log, stderr=subprocess.STDOUT)
    PROCESSES.append((proc, log))


def services():
    data = HOME / 'db'
    run('database-init', ['mariadb-install-db', '--datadir=' + str(data),
                          '--auth-root-authentication-method=normal', '--skip-test-db'])
    launch('mariadb', ['mariadbd', '--datadir=' + str(data), '--socket=' + str(HOME / 'mysql.sock'),
                       '--pid-file=' + str(HOME / 'mysql.pid'), '--bind-address=127.0.0.1',
                       '--port=3306', '--innodb-buffer-pool-size=128M',
                       '--character-set-server=utf8mb4', '--collation-server=utf8mb4_unicode_ci'])
    for _ in range(60):
        ping = subprocess.run(['mariadb-admin', '--socket=' + str(HOME / 'mysql.sock'), 'ping'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ping.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('database did not become ready')
    launch('redis', ['redis-server', '--bind', '127.0.0.1', '--port', '13000',
                     '--save', '', '--appendonly', 'no', '--dir', str(HOME)])
    config = BENCH / 'sites/common_site_config.json'
    value = json.loads(config.read_text())
    value.update(redis_cache='redis://127.0.0.1:13000/0', redis_queue='redis://127.0.0.1:13000/1',
                 redis_socketio='redis://127.0.0.1:13000/2', developer_mode=1)
    config.write_text(json.dumps(value))


def test():
    services()
    root_secret = secrets.token_hex(32)
    SECRETS.append(root_secret)
    statement = ("ALTER USER 'root'@'localhost' IDENTIFIED BY '" + root_secret + "';")
    run('database-root-credential', ['mariadb', '--user=root',
                                    '--socket=' + str(HOME / 'mysql.sock')],
        input_data=statement.encode(), timeout=30)
    variants = ('base', 'head')
    descriptor = Path('/inputs/structured-variants.json')
    if descriptor.is_file():
        declared = json.loads(descriptor.read_text())
        if declared != ['base', 'head', 'baseline', 'feedback']:
            raise ValueError('unsupported fixed structured variant inventory')
        variants = ('base', 'head', 'baseline', 'feedback')
    for variant in variants:
        target = BENCH / 'apps/erpnext' / CASE['module']
        target.write_bytes(Path('/inputs/' + variant + '-report.py').read_bytes())
        heldout = BENCH / 'apps/erpnext' / CASE['tests']
        heldout.write_bytes(Path('/inputs/heldout.py').read_bytes())
        before = {'module_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'heldout_sha256': hashlib.sha256(heldout.read_bytes()).hexdigest()}
        site = 'shadow-' + variant + '.localhost'
        secret = secrets.token_urlsafe(32)
        db_secret = secrets.token_urlsafe(32)
        SECRETS.extend([secret, db_secret])
        run('site-' + variant, ['bench', 'new-site', site, '--db-socket', str(HOME / 'mysql.sock'),
                                '--db-root-username', 'root', '--db-root-password', root_secret,
                                '--admin-password', secret, '--db-password', db_secret, '--install-app', 'erpnext'], cwd=BENCH)
        run('enable-tests-' + variant, ['bench', '--site', site, 'set-config', 'allow_tests', 'true'], cwd=BENCH)
        output = STATE / (variant + '-result.json')
        # Nonzero exit is expected for the historical original. The controller
        # consumes exact structured test identities and outcomes separately.
        log = STATE / ('tests-' + variant + '.log')
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        with log.open('wb') as handle:
            proc = subprocess.run([str(BENCH / 'env/bin/python'), '/driver/app_collect.py', str(output),
                                   site, CASE['test_module']], cwd=BENCH / 'sites', env=env,
                                  stdout=handle, stderr=subprocess.STDOUT, timeout=300)
        value = json.loads(output.read_text()) if output.is_file() else {'schema': 1, 'runs': []}
        value['transport_exit'] = proc.returncode
        value['source_before'] = before
        value['source_after'] = {'module_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                                 'heldout_sha256': hashlib.sha256(heldout.read_bytes()).hexdigest()}
        output.write_text(json.dumps(value, indent=2))
    print(json.dumps({'stage': 'tests-finished'}))


if __name__ == '__main__':
    if os.getuid() != 1001 or not (Path('/inputs/frappe').is_dir() and Path('/driver/app_case.json').is_file()):
        raise SystemExit('requires fixed isolated container layout and uid1001')
    marker = STATE / 'logs-sanitized.json'
    marker.write_text(json.dumps({'sanitized': False}))
    code = 0
    try:
        {'setup': setup, 'test': test}[sys.argv[1]]()
    except BaseException as exc:
        # TimeoutExpired includes command arguments, possibly test credentials.
        # Export only the type; sanitized logs carry the diagnostic details.
        print(json.dumps({'stage': 'error', 'error_type': type(exc).__name__}))
        code = 1
    finally:
        for proc, log in PROCESSES:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=5)
            log.close()
        for path in STATE.glob('*.log'):
            if path.is_symlink() or not path.is_file():
                continue
            text = log_tail(path)
            for value in SECRETS:
                text = text.replace(value, '<redacted>')
            text = '\n'.join('<redacted sensitive line>' if re.search(r'password|secret|token|encryption_key|authorization', line, re.I) else line for line in text.splitlines())
            path.write_text(text[-2097152:])
        marker.write_text(json.dumps({'sanitized': True}))
    raise SystemExit(code)
