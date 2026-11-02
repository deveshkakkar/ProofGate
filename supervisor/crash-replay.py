#!/usr/bin/env python3
"""Bounded, local process-crash and replay check for the pinned ProofGate artifact."""
import argparse
from contextlib import closing
import datetime
import hashlib
import http.client
import json
import os
from pathlib import Path
import signal
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time

PINS = {
    'server.ts': '0a71fd2b140713bd80d253e829694bb0ea5dd53fd9934dee813374ffab93e09d',
    'admission.mjs': 'e842815ab774645585fbd240514dd31fffee919b1c16403fb958bc735ae9d47e',
}
NODE_SHA = 'e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb'
NODE_VERSION = 'v24.22.1'
ARTIFACT_ID = '22f322d60be8e88d98c8e2813e6280c9fa2de9966a776164e58b7fb8761615d3'
CASES = [('before', 30, 100, 0), ('before', 101, 100, 0),
         ('after', 30, 70, 1), ('after', 101, 100, 1)]
HOOK = r'''import { DatabaseSync } from 'node:sqlite';
import { writeFileSync } from 'node:fs';
const original = DatabaseSync.prototype.exec;
let commit = 0;
DatabaseSync.prototype.exec = function (sql) {
  if (typeof sql === 'string' && /^\s*COMMIT\s*;?\s*$/i.test(sql)) {
    commit++;
    if (commit === 2) {
      const marker = { phase: process.env.CRASH_PHASE, commit, pid: process.pid };
      if (marker.phase === 'before') {
        writeFileSync(process.env.CRASH_MARKER, JSON.stringify(marker), { flag: 'wx' });
        process.kill(process.pid, 'SIGKILL');
      }
      const result = original.call(this, sql);
      writeFileSync(process.env.CRASH_MARKER, JSON.stringify(marker), { flag: 'wx' });
      process.kill(process.pid, 'SIGKILL');
      return result;
    }
  }
  return original.call(this, sql);
};
'''


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def verify_pins(artifact, node):
    found = {name: digest(artifact / name) for name in PINS}
    found['node'] = digest(node)
    require(all(found[name] == value for name, value in PINS.items()), 'artifact pin mismatch')
    require(found['node'] == NODE_SHA, 'Node binary pin mismatch')
    version = subprocess.run([str(node), '--version'], capture_output=True,
                             text=True, timeout=3, check=True).stdout.strip()
    require(version == NODE_VERSION, 'Node version mismatch')
    found['node_version'] = version
    return found


def validate_marker(marker, phase, pid, returncode, response_received):
    require(isinstance(marker, dict) and set(marker) == {'phase', 'commit', 'pid'},
            'missing or malformed crash marker')
    require(marker['phase'] == phase and phase in ('before', 'after'), 'wrong crash phase')
    require(type(marker['commit']) is int and marker['commit'] == 2, 'wrong COMMIT ordinal')
    require(type(marker['pid']) is int and marker['pid'] == pid and pid > 0,
            'wrong crash PID')
    require(returncode == -signal.SIGKILL, 'child did not die by SIGKILL')
    require(response_received is False, 'crashed request received an HTTP response')


def validate_sql(state, balance, rows):
    require(isinstance(state, dict) and set(state) == {'balance', 'rows'},
            'malformed SQL state')
    require(type(state['balance']) is int and state['balance'] == balance,
            'unexpected persisted balance')
    require(isinstance(state['rows'], list) and state['rows'] == rows,
            'unexpected persisted reservations')


def validate_http(reply, status, body):
    require(reply.get('transport') == 'response' and reply.get('status') == status
            and reply.get('body') == body, 'unexpected HTTP response')


def expected(request_id, amount, prior):
    success = amount > 0 and amount <= prior
    balance = prior - amount if success else prior
    body = json.dumps({'requestId': request_id, 'amount': amount,
                       'success': success, 'granted': amount if success else 0,
                       'balance': balance,
                       'reason': 'granted' if success else
                       ('invalid_amount' if amount <= 0 else 'insufficient_credits')},
                      separators=(',', ':'))
    return body, balance


def sql_state(db_path):
    with closing(sqlite3.connect(db_path, timeout=1)) as db:
        db.execute('PRAGMA query_only = ON')
        balances = db.execute('SELECT balance FROM state WHERE singleton = 1').fetchall()
        require(len(balances) == 1, 'invalid state row count')
        rows = db.execute('SELECT request_id, amount, response FROM reservations ORDER BY request_id').fetchall()
    return {'balance': balances[0][0],
            'rows': [{'request_id': rid, 'amount': amount, 'response': response}
                     for rid, amount, response in rows]}


def crash_image(db_path):
    """Read raw bytes only: never open the original crash image with SQLite."""
    return {suffix: {'bytes': path.stat().st_size, 'sha256': digest(path)}
            if path.exists() else None
            for suffix in ('', '-wal', '-shm')
            for path in (Path(str(db_path) + suffix),)}


def inspect_crash_copy(db_path, destination):
    # The caller has reaped the crashed process: these files are now quiescent.
    before = crash_image(db_path)
    require(before[''] is not None, 'missing crash database')
    destination.mkdir()
    for suffix, identity in before.items():
        if identity is not None:
            shutil.copyfile(Path(str(db_path) + suffix), destination / (db_path.name + suffix))
    try:
        state = sql_state(destination / db_path.name)
    finally:
        after = crash_image(db_path)
        require(after == before, 'original crash image changed during inspection')
    return state, {'before': before, 'after_inspection': after}


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def http_request(port, method, path, payload=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
    response_received = False
    try:
        body = None if payload is None else json.dumps(payload, separators=(',', ':'))
        connection.request(method, path, body=body,
                           headers={'Content-Type': 'application/json'} if body else {})
        response = connection.getresponse()
        response_received = True
        data = response.read().decode('utf-8')
        return {'transport': 'response', 'response_received': True,
                'status': response.status, 'body': data}
    except (TimeoutError, socket.timeout) as error:
        return {'transport': 'timeout', 'response_received': response_received,
                'error': type(error).__name__}
    except (http.client.RemoteDisconnected, ConnectionResetError, BrokenPipeError,
            ConnectionAbortedError, ConnectionRefusedError) as error:
        return {'transport': 'connection_lost', 'response_received': response_received,
                'error': type(error).__name__}
    except Exception as error:
        return {'transport': 'error', 'response_received': response_received,
                'error': type(error).__name__}
    finally:
        connection.close()


def drain(stream, path):
    remaining = 65536
    with open(path, 'wb') as log:
        while True:
            block = stream.read(4096)
            if not block:
                break
            if remaining:
                piece = block[:remaining]
                log.write(piece)
                remaining -= len(piece)
    stream.close()


def launch(node, artifact, db_path, port, log_path, hook=None, phase=None, marker=None):
    env = {'PATH': '/usr/bin:/bin', 'PORT': str(port), 'DB_PATH': str(db_path)}
    command = [str(node)]
    if hook:
        command += ['--import', str(hook)]
        env.update(CRASH_PHASE=phase, CRASH_MARKER=str(marker))
    command.append(str(artifact / 'server.ts'))
    proc = subprocess.Popen(command, cwd=artifact, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True)
    thread = threading.Thread(target=drain, args=(proc.stdout, log_path), daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    try:
        while time.monotonic() < deadline:
            require(proc.poll() is None, 'server exited during startup')
            probe = http_request(port, 'GET', '/status')
            if probe.get('status') == 200:
                return proc, thread
            time.sleep(0.05)
        raise TimeoutError('server startup exceeded 5 seconds')
    except BaseException:
        # Ownership has not reached run_case yet: reap this child here.
        stop(proc, thread)
        raise


def stop(proc, thread):
    if proc:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=2)
        else:
            proc.wait(timeout=1)
    if thread:
        thread.join(timeout=2)


def run_case(index, spec, node, artifact, output, hook, no_hook=False):
    phase, amount, post_balance, post_count = spec
    folder = output / f'case-{index}-{phase}-{amount}'
    folder.mkdir()
    db_path = folder / 'state.sqlite'
    marker_path = folder / 'crash-marker.json'
    request_id = f'crash-{index}'
    original, first_balance = expected(request_id, amount, 100)
    original_row = {'request_id': request_id, 'amount': amount, 'response': original}
    result = {'phase': phase, 'amount': amount, 'request_id': request_id,
              'started_at': utc(), 'database': str(db_path),
              'crash_command': [str(node), *([] if no_hook else ['--import', str(hook)]), str(artifact / 'server.ts')],
              'replay_command': [str(node), str(artifact / 'server.ts')], 'logs': [str(folder / 'crash.log'), str(folder / 'replay.log')]}
    proc = thread = None
    try:
        verify_pins(artifact, node)
        port = free_port()
        proc, thread = launch(node, artifact, db_path, port, folder / 'crash.log',
                              None if no_hook else hook, phase, marker_path)
        result['crash_pid'] = proc.pid
        reply = http_request(port, 'POST', '/reserve',
                             {'requestId': request_id, 'amount': amount})
        result['crash_http'] = reply
        try:
            result['crash_returncode'] = proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            result['crash_returncode'] = None
        result['marker'] = json.loads(marker_path.read_text()) if marker_path.exists() else None
        require(reply['transport'] == 'connection_lost', 'crashed request did not lose connection')
        validate_marker(result['marker'], phase, proc.pid, result['crash_returncode'],
                        reply['response_received'])
        stop(proc, thread)
        proc = thread = None
        state, image = inspect_crash_copy(db_path, folder / 'inspection-copy')
        result['crash_image'] = image
        result['post_crash_sql'] = state
        validate_sql(state, post_balance, [original_row] if post_count else [])
        verify_pins(artifact, node)
        port = free_port()
        image['before_restart'] = crash_image(db_path)
        require(image['before_restart'] == image['before'],
                'original crash image changed before restart')
        proc, thread = launch(node, artifact, db_path, port, folder / 'replay.log')
        result['replay_pid'] = proc.pid
        for number in (1, 2):
            reply = http_request(port, 'POST', '/reserve',
                                 {'requestId': request_id, 'amount': amount})
            result[f'replay_{number}'] = reply
            validate_http(reply, 200, original)
            state = sql_state(db_path)
            result[f'replay_{number}_sql'] = state
            validate_sql(state, first_balance, [original_row])
        conflict = http_request(port, 'POST', '/reserve',
                                {'requestId': request_id, 'amount': amount + 1})
        result['conflict'] = conflict
        validate_http(conflict, 409, '{"error":"conflict"}')
        validate_sql(sql_state(db_path), first_balance, [original_row])
        later_id = f'later-{index}'
        later, current_balance = expected(later_id, 5, first_balance)
        later_row = {'request_id': later_id, 'amount': 5, 'response': later}
        later_reply = http_request(port, 'POST', '/reserve',
                                   {'requestId': later_id, 'amount': 5})
        result['later_request'] = later_reply
        validate_http(later_reply, 200, later)
        historical = http_request(port, 'POST', '/reserve',
                                  {'requestId': request_id, 'amount': amount})
        result['historical_replay'] = historical
        validate_http(historical, 200, original)
        final_rows = sorted([original_row, later_row], key=lambda row: row['request_id'])
        state = sql_state(db_path)
        result['final_sql'] = state
        validate_sql(state, current_balance, final_rows)
        status = http_request(port, 'GET', '/status')
        result['status'] = status
        validate_http(status, 200, json.dumps({'balance': current_balance}, separators=(',', ':')))
        result['passed'] = True
    except Exception as error:
        result['passed'] = False
        result['failure'] = f'{type(error).__name__}: {error}'
    finally:
        try:
            stop(proc, thread)
        except Exception as error:
            result['passed'] = False
            result['cleanup_failure'] = f'{type(error).__name__}: {error}'
        result['finished_at'] = utc()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--negative-control', choices=['no-hook'])
    args = parser.parse_args()
    node, artifact, output = (path.resolve() for path in
                              (args.node, args.artifact, args.output))
    require(not output.exists(), 'output directory must be new')
    require(artifact not in output.parents and output not in artifact.parents,
            'output and artifact must be separate')
    output.mkdir(parents=True)
    result = {'passed': False, 'instrumented_runtime': args.negative_control is None,
              'no_rebuild': True, 'negative_control': args.negative_control,
              'accepted_artifact_id': ARTIFACT_ID, 'expected_artifact_files': PINS,
              'expected_node_sha256': NODE_SHA, 'expected_node_version': NODE_VERSION,
              'started_at': utc(), 'cases': []}
    try:
        result['pins_before'] = verify_pins(artifact, node)
        hook = output / 'hook.mjs'
        hook.write_text(HOOK)
        specs = CASES[:1] if args.negative_control else CASES
        for index, spec in enumerate(specs, 1):
            result['cases'].append(run_case(index, spec, node, artifact, output, hook,
                                            args.negative_control == 'no-hook'))
        result['pins_after'] = verify_pins(artifact, node)
        result['passed'] = all(case['passed'] for case in result['cases'])
    except Exception as error:
        result['failure'] = f'{type(error).__name__}: {error}'
    result['finished_at'] = utc()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
