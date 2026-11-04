#!/usr/bin/env python3
"""Bounded lost-response histories across a real ProofGate process crash."""
import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from supervisor.pending_checker import check_pending


spec = importlib.util.spec_from_file_location('crash_replay', Path(__file__).with_name('crash-replay.py'))
crash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crash)


def completed(port, label, kind, request_id=None, amount=None):
    start = time.monotonic_ns()
    reply = crash.http_request(port, 'GET' if kind == 'status' else 'POST',
                               '/status' if kind == 'status' else '/reserve',
                               None if kind == 'status' else {'requestId': request_id, 'amount': amount})
    end = time.monotonic_ns()
    if reply['transport'] != 'response' or reply['status'] not in (200, 409):
        raise AssertionError(f'{label}: missing completed HTTP response')
    op = {'id': label, 'kind': kind, 'start_ns': start, 'end_ns': end,
          'status': reply['status'], 'body': json.loads(reply['body'])}
    if kind == 'reserve':
        op.update(request_id=request_id, amount=amount)
    return op


def run_case(phase, node, artifact, hook, output):
    folder = output / phase
    folder.mkdir()
    db = folder / 'state.sqlite'
    marker = folder / 'marker.json'
    request_id = f'uncertain-{phase}'
    proc = thread = None
    history = []
    try:
        port = crash.free_port()
        proc, thread = crash.launch(node, artifact, db, port, folder / 'crash.log',
                                    hook, phase, marker)
        start = time.monotonic_ns()
        lost = crash.http_request(port, 'POST', '/reserve',
                                  {'requestId': request_id, 'amount': 30})
        if lost['transport'] != 'connection_lost':
            raise AssertionError('crashed request did not lose its response')
        returncode = proc.wait(timeout=3)
        stopped = time.monotonic_ns()
        crash.validate_marker(json.loads(marker.read_text()), phase, proc.pid,
                              returncode, lost['response_received'])
        if returncode != -signal.SIGKILL:
            raise AssertionError('crash was not SIGKILL')
        history.append({'id': 'uncertain', 'kind': 'pending_reserve',
                        'request_id': request_id, 'amount': 30,
                        'start_ns': start, 'stop_ns': stopped})
        crash.stop(proc, thread)
        proc = thread = None
        inspected, image = crash.inspect_crash_copy(db, folder / 'inspection-copy')
        expected_balance = 100 if phase == 'before' else 70
        historical, _ = crash.expected(request_id, 30, 100)
        original_row = {'request_id': request_id, 'amount': 30, 'response': historical}
        crash.validate_sql(inspected, expected_balance,
                           [] if phase == 'before' else [original_row])
        if crash.crash_image(db) != image['before']:
            raise AssertionError('original crash image changed before restart')
        port = crash.free_port()
        proc, thread = crash.launch(node, artifact, db, port, folder / 'replay.log')
        history.append(completed(port, 'post-crash-status', 'status'))
        history.append(completed(port, 'replay', 'reserve', request_id, 30))
        history.append(completed(port, 'later-grant', 'reserve', f'later-{phase}', 5))
        history.append(completed(port, 'historical-replay', 'reserve', request_id, 30))
        history.append(completed(port, 'final-status', 'status'))
        verdict = check_pending(history)
        if not verdict['linearizable'] or verdict['pending_applied'] != (phase == 'after'):
            raise AssertionError('pending effect classification disagrees with observed history')
        wrong = check_pending(history, force_effect=(phase != 'after'))
        if wrong['linearizable']:
            raise AssertionError('wrong pending-effect control was accepted')
        crash.stop(proc, thread)
        proc = thread = None
        final = crash.sql_state(db)
        later_id = f'later-{phase}'
        later_response, _ = crash.expected(later_id, 5, 70)
        later_row = {'request_id': later_id, 'amount': 5, 'response': later_response}
        crash.validate_sql(final, 65,
                           sorted([original_row, later_row], key=lambda row: row['request_id']))
        return {'phase': phase, 'history': history, 'verdict': verdict,
                'wrong_effect_rejected': True, 'crash_image': image,
                'stopped_sql': inspected, 'final_sql': final}
    finally:
        crash.stop(proc, thread)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=Path, required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.node, args.artifact, args.output = (args.node.resolve(), args.artifact.resolve(),
                                            args.output.resolve())
    if args.output.exists():
        parser.error('output must not exist')
    if args.artifact in args.output.parents or args.output in args.artifact.parents:
        parser.error('artifact and output must be separate')
    pins = crash.verify_pins(args.artifact, args.node)
    source = {name: crash.digest(Path(__file__).with_name(name)) for name in
              ('pending-history.py', 'pending_checker.py', 'test_pending_checker.py',
               'realtime_checker.py', 'crash-replay.py')}
    args.output.mkdir(parents=True)
    report = {'passed': False, 'pins': pins, 'source_sha256': source,
              'cases': [], 'started_at': crash.utc()}
    try:
        hook = args.output / 'commit-hook.mjs'
        hook.write_text(crash.HOOK)
        for phase in ('before', 'after'):
            report['cases'].append(run_case(phase, args.node, args.artifact, hook, args.output))
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
