#!/usr/bin/env python3
"""Finite real-time ordering experiment against the pinned, unchanged service."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import time

from realtime_checker import check


spec = importlib.util.spec_from_file_location('crash_replay', Path(__file__).with_name('crash-replay.py'))
crash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crash)


def operation(port, label, kind, request_id=None, amount=None):
    path = '/status' if kind == 'status' else '/reserve'
    payload = None if kind == 'status' else {'requestId': request_id, 'amount': amount}
    start = time.monotonic_ns()
    reply = crash.http_request(port, 'GET' if kind == 'status' else 'POST', path, payload)
    end = time.monotonic_ns()
    if reply['transport'] != 'response' or reply['status'] not in (200, 409):
        raise AssertionError(f'{label}: missing or unexpected HTTP response')
    body = json.loads(reply['body'])
    row = {'id': label, 'kind': kind, 'start_ns': start, 'end_ns': end,
           'status': reply['status'], 'body': body}
    if kind == 'reserve':
        row.update(request_id=request_id, amount=amount)
    return row


def concurrent(port, specs):
    barrier = threading.Barrier(len(specs) + 1)

    def run(spec):
        barrier.wait(timeout=5)
        return operation(port, *spec)

    with ThreadPoolExecutor(max_workers=len(specs)) as pool:
        futures = [pool.submit(run, spec) for spec in specs]
        barrier.wait(timeout=5)
        return [future.result(timeout=8) for future in futures]


def overlaps(a, b):
    return a['start_ns'] < b['end_ns'] and b['start_ns'] < a['end_ns']


def held_reservation(port, sent, release):
    """Keep one client response pending while later operations complete."""
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
    try:
        start = time.monotonic_ns()
        body = json.dumps({'requestId': 'held', 'amount': 10}, separators=(',', ':'))
        connection.request('POST', '/reserve', body=body,
                           headers={'Content-Type': 'application/json'})
        sent.set()
        if not release.wait(timeout=8):
            raise TimeoutError('held client response was not released')
        response = connection.getresponse()
        data = response.read(65537)
        end = time.monotonic_ns()
        if response.status != 200 or len(data) > 65536:
            raise AssertionError('held reservation response invalid or oversized')
        return {'id': 'held', 'kind': 'reserve', 'request_id': 'held', 'amount': 10,
                'start_ns': start, 'end_ns': end, 'status': 200,
                'body': json.loads(data)}
    finally:
        connection.close()


def phased(port):
    sent, release = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(held_reservation, port, sent, release)
        try:
            if not sent.wait(timeout=5):
                raise TimeoutError('held reservation did not send')
            grant = operation(port, 'completed-grant', 'reserve', 'grant', 30)
            if not grant['body']['success']:
                raise AssertionError('phased grant did not succeed')
            read = operation(port, 'read-during-held', 'status')
        finally:
            release.set()
        held = future.result(timeout=5)
    if not (grant['end_ns'] < read['start_ns'] < held['end_ns']):
        raise AssertionError('phased real-time witness absent')
    return [held, grant, read]


def run_round(index, mode, node, artifact, output):
    folder = output / f'{mode}-{index:02d}'
    folder.mkdir()
    port = crash.free_port()
    proc = thread = None
    try:
        proc, thread = crash.launch(node, artifact, folder / 'state.sqlite', port, folder / 'service.log')
        history = []
        if mode == 'phased':
            history.extend(phased(port))
        elif mode == 'replay':
            history.append(operation(port, 'seed', 'reserve', 'seed', 30))
            specs = [('replay', 'reserve', 'seed', 30),
                     ('conflict', 'reserve', 'seed', 31),
                     ('next', 'reserve', 'next', 50),
                     ('read-a', 'status'), ('read-b', 'status')]
        else:
            specs = [('reserve-a', 'reserve', 'a', 30),
                     ('reserve-b', 'reserve', 'b', 50),
                     ('reserve-c', 'reserve', 'c', 40),
                     ('read-a', 'status'), ('read-b', 'status')]
        if mode != 'phased':
            history.extend(concurrent(port, specs))
        history.append(operation(port, 'final-read', 'status'))
        verdict = check(history)
        if not verdict['linearizable']:
            raise AssertionError(f'{mode} round {index}: no valid real-time order')
        final = history[-1]['body']['balance']
        if not 0 <= final < 100:
            raise AssertionError('expected at least one successful reservation')
        target = 'read-during-held' if mode == 'phased' else 'final-read'
        stale_balances = (100, 90) if mode == 'phased' else (100,)
        for stale_balance in stale_balances:
            stale = copy.deepcopy(history)
            next(op for op in stale if op['id'] == target)['body']['balance'] = stale_balance
            if check(stale)['linearizable']:
                raise AssertionError(f'stale {target} read was accepted')
        overlap_count = sum(overlaps(a, b) for a in history for b in history
                            if a['kind'] == 'reserve' and b['kind'] == 'status'
                            and b['id'] != 'final-read')
        grant_read_overlaps = sum(overlaps(a, b) for a in history for b in history
                                  if a['kind'] == 'reserve' and a['status'] == 200
                                  and a['body']['success'] and b['kind'] == 'status'
                                  and b['id'] != 'final-read')
        crash.stop(proc, thread)
        proc = thread = None
        state = crash.sql_state(folder / 'state.sqlite')
        if state['balance'] != final:
            raise AssertionError('HTTP final balance differs from persisted SQL')
        return {'mode': mode, 'round': index, 'history': history, 'order': verdict['order'],
                'overlapping_reserve_reads': overlap_count,
                'stale_read_rejections': list(stale_balances),
                'grant_read_overlaps': grant_read_overlaps,
                'intermediate_read_balances': [op['body']['balance'] for op in history
                                               if op['kind'] == 'status' and op['id'] != 'final-read'],
                'stale_control_target': target,
                'final_balance': final, 'sql_row_count': len(state['rows'])}
    finally:
        crash.stop(proc, thread)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=8)
    args = parser.parse_args()
    args.node = args.node.resolve()
    args.artifact = args.artifact.resolve()
    args.output = args.output.resolve()
    if not 1 <= args.rounds <= 16 or args.output.exists():
        parser.error('rounds must be 1..16 and output must not exist')
    pins = crash.verify_pins(args.artifact, args.node)
    source = {name: crash.digest(Path(__file__).with_name(name)) for name in
              ('realtime-history.py', 'realtime_checker.py', 'test_realtime_checker.py')}
    args.output.mkdir(parents=True)
    report = {'passed': False, 'pins': pins, 'source_sha256': source,
              'rounds': [], 'started_at': crash.utc()}
    try:
        for mode in ('fresh', 'replay', 'phased'):
            for index in range(args.rounds):
                report['rounds'].append(run_round(index, mode, args.node, args.artifact, args.output))
        report['overlap_count'] = sum(row['overlapping_reserve_reads'] for row in report['rounds'])
        report['grant_read_overlap_count'] = sum(row['grant_read_overlaps'] for row in report['rounds'])
        report['phased_witnesses'] = sum(row['stale_control_target'] == 'read-during-held'
                                         for row in report['rounds'])
        if report['overlap_count'] == 0:
            raise AssertionError('no reservation/status intervals overlapped')
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
