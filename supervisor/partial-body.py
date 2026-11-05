#!/usr/bin/env python3
"""Check that a disconnected, incomplete HTTP body cannot reserve credits."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import time

spec = importlib.util.spec_from_file_location('crash_replay', Path(__file__).with_name('crash-replay.py'))
crash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crash)


def send_partial(port, payload, cut):
    body = json.dumps(payload, separators=(',', ':')).encode()
    fragment = body[:cut]
    if not 0 <= cut < len(body):
        raise ValueError('cut must leave the body incomplete')
    headers = (f'POST /reserve HTTP/1.1\r\nHost: 127.0.0.1\r\n'
               f'Content-Length: {len(body)}\r\nContent-Type: application/json\r\n'
               'Connection: close\r\n\r\n').encode()
    with socket.create_connection(('127.0.0.1', port), timeout=3) as conn:
        conn.settimeout(3)
        conn.sendall(headers + fragment)
        time.sleep(0.05)
        conn.shutdown(socket.SHUT_WR)
        # Observe the peer close after the truncated body. A bounded HTTP 400
        # is acceptable; a successful reservation response is not.
        response = bytearray()
        while True:
            chunk = conn.recv(4097 - len(response))
            if not chunk:
                break
            response.extend(chunk)
            if len(response) > 4096:
                raise AssertionError('truncated-request response exceeded 4 KiB')
        status_line = bytes(response).split(b'\r\n', 1)[0]
        if not status_line.startswith(b'HTTP/1.1 400 '):
            raise AssertionError('truncated request did not receive HTTP 400')
    return {'declared_bytes': len(body), 'sent_bytes': len(fragment),
            'fragment_sha256': hashlib.sha256(fragment).hexdigest(),
            'peer_status': status_line.decode('ascii', 'replace')}


def assert_negative_control():
    """A harness that accepts early admission must fail the SQL validator."""
    for mutant in ({'balance': 70, 'rows': []},
                   {'balance': 100, 'rows': [{'request_id': 'partial',
                                              'amount': 30, 'response': '{}'}]}):
        try:
            crash.validate_sql(mutant, 100, [])
        except ValueError:
            continue
        raise AssertionError('premature-admission negative control passed')


def run_case(name, cut, node, artifact, output):
    folder = output / name
    folder.mkdir()
    db = folder / 'state.sqlite'
    request_id = f'partial-{name}'
    payload = {'requestId': request_id, 'amount': 30}
    proc = thread = None
    try:
        port = crash.free_port()
        proc, thread = crash.launch(node, artifact, db, port, folder / 'first.log')
        if cut is None:
            # Deliberate real-service control: a completed request must not be
            # misclassified as an aborted, admission-free request.
            partial = crash.http_request(port, 'POST', '/reserve', payload)
            expected, _ = crash.expected(request_id, 30, 100)
            crash.validate_http(partial, 200, expected)
        else:
            partial = send_partial(port, payload, cut)
        status = crash.http_request(port, 'GET', '/status')
        if cut is None and status.get('body') == '{"balance":70}':
            raise AssertionError('complete-body control correctly changed state')
        crash.validate_http(status, 200, '{"balance":100}')
        crash.stop(proc, thread)
        proc = thread = None
        stopped, image = crash.inspect_crash_copy(db, folder / 'inspection-copy')
        crash.validate_sql(stopped, 100, [])
        if crash.crash_image(db) != image['before']:
            raise AssertionError('original image changed during inspection')
        port = crash.free_port()
        proc, thread = crash.launch(node, artifact, db, port, folder / 'retry.log')
        first = crash.http_request(port, 'POST', '/reserve', payload)
        expected, _ = crash.expected(request_id, 30, 100)
        crash.validate_http(first, 200, expected)
        replay = crash.http_request(port, 'POST', '/reserve', payload)
        crash.validate_http(replay, 200, expected)
        final_status = crash.http_request(port, 'GET', '/status')
        crash.validate_http(final_status, 200, '{"balance":70}')
        crash.stop(proc, thread)
        proc = thread = None
        final = crash.sql_state(db)
        crash.validate_sql(final, 70, [{'request_id': request_id,
                                        'amount': 30, 'response': expected}])
        return {'case': name, 'partial': partial, 'pre_retry_status': status,
                'pre_retry_sql': stopped, 'crash_image': image,
                'retry': first, 'replay': replay,
                'final_status': final_status, 'final_sql': final}
    finally:
        crash.stop(proc, thread)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--negative-control', choices=('complete-body',))
    args = parser.parse_args()
    args.node, args.artifact, args.output = (args.node.resolve(), args.artifact.resolve(),
                                            args.output.resolve())
    if args.output.exists():
        parser.error('output must not exist')
    if args.artifact in args.output.parents or args.output in args.artifact.parents:
        parser.error('artifact and output must be separate')
    pins = crash.verify_pins(args.artifact, args.node)
    source = {name: crash.digest(Path(__file__).with_name(name)) for name in
              ('partial-body.py', 'test_partial_body.py', 'crash-replay.py')}
    args.output.mkdir(parents=True)
    report = {'passed': False, 'pins': pins, 'source_sha256': source,
              'cases': [], 'started_at': crash.utc()}
    try:
        assert_negative_control()
        cases = (('complete-body', None),) if args.negative_control else (
            ('headers-only', 0), ('body-prefix', 20))
        for name, cut in cases:
            report['cases'].append(run_case(name, cut, args.node, args.artifact,
                                            args.output))
        report['negative_control_rejected'] = True
        report['pins_after'] = crash.verify_pins(args.artifact, args.node)
        if source != {name: crash.digest(Path(__file__).with_name(name)) for name in source}:
            raise AssertionError('experiment source changed during run')
        report['passed'] = True
    except Exception as exc:
        report['failure'] = f'{type(exc).__name__}: {exc}'
    report['finished_at'] = crash.utc()
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
