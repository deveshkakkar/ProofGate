#!/usr/bin/env python3
"""Trusted hosted producer. Never checks out or imports a candidate repository."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gate
from common import (GitHub, ROOT, REPO, Rejected, adoption, canonical, candidate_bytes,
                    current_adoption, decode, need, sha, source_identity)
from bundle import LOGS, pack, protected, unpack, validate


def context(adopted):
    expected = {'GITHUB_REPOSITORY':REPO,'GITHUB_REPOSITORY_ID':'1437623154',
                'GITHUB_EVENT_NAME':'workflow_dispatch','GITHUB_SHA':adopted['producer_sha'],
                'GITHUB_REF':adopted['producer_ref'],'RUNNER_ENVIRONMENT':'github-hosted',
                'GITHUB_ACTIONS':'true','GITHUB_SERVER_URL':'https://github.com'}
    need(all(os.environ.get(k) == v for k,v in expected.items()), 'protected-workflow-context')
    run = os.environ.get('GITHUB_RUN_ID',''); attempt = os.environ.get('GITHUB_RUN_ATTEMPT','')
    need(run.isdigit() and attempt.isdigit() and int(attempt) > 0, 'protected-execution-identity')
    return {'run_id':run,'attempt':int(attempt)}


def fresh(api, adopted, number, identity):
    current_adoption(api, adopted, active_variable=False)
    need(source_identity(api, number) == identity, 'source-head-base-changed')


def produce(api, adopted, number, output, cache, execution):
    protected(); current_adoption(api, adopted, active_variable=False)
    identity = source_identity(api, number)
    files = candidate_bytes(api, identity)
    output.mkdir(mode=0o700)  # exclusive, outside candidate-writable sandboxes
    candidate = output/'candidate'; candidate.mkdir()
    for name, raw in files.items():
        path = candidate/name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw); path.chmod(0o644)
    fresh(api, adopted, number, identity)
    result, tools, node = gate.evaluate(candidate, output/'checked', cache)
    receipt = gate.finish(result, tools, node, candidate, output/'checked')
    receipt_sha = gate.sha(receipt)
    gate.copy_checked(receipt, receipt_sha, candidate, output/'checked/artifact', cache, output/'accepted')
    fresh(api, adopted, number, identity); protected()
    payload = {'source/'+k:v for k,v in files.items()}
    payload['receipt.json'] = receipt.read_bytes()
    payload.update({'logs/'+n:(output/'checked'/n).read_bytes() for n in LOGS})
    payload.update({'artifact/'+n:(output/'accepted'/n).read_bytes() for n in result['artifact']})
    manifest = {'schema':1,'policy_sha256':sha((ROOT/'authority/policy-v1.json').read_bytes()),
                'adoption':adopted,'source':identity,'execution':execution,
                'files':{k:sha(v) for k,v in payload.items()}}
    payload['result.json'] = canonical(manifest)
    validate(payload, adopted)
    archive = output/'reservation-bundle.zip'; pack(payload, archive)
    return {'bundle_sha256':sha(archive.read_bytes()),'receipt_sha256':receipt_sha,
            'observations_consistent':True,'producer_authenticated':False,'policy_admitted':False}


def finalize(api, adopted, number, archive, expected, execution):
    raw = archive.read_bytes()
    need(sha(raw) == expected, 'protected-job-handoff-substituted')
    result, _ = validate(unpack(raw), adopted)
    need(result['execution'] == execution and result['source']['pr'] == number, 'protected-job-handoff-execution')
    fresh(api, adopted, number, result['source'])
    return {'bundle_sha256':expected,'ready_for_attestation':True,'policy_admitted':False}


def main():
    p = argparse.ArgumentParser(); p.add_argument('operation', choices=['verify','finalize'])
    p.add_argument('--gh', type=Path, required=True); p.add_argument('--pr', type=int, required=True)
    p.add_argument('--output', type=Path); p.add_argument('--archive',type=Path); p.add_argument('--expected-sha256')
    p.add_argument('--cache', type=Path, default=Path.home()/'.cache/proofgate-lean4')
    a = p.parse_args()
    try:
        adopted = adoption(decode(os.environ.get('PROOFGATE_LEAN_ADOPTION','null')))
        execution = context(adopted); api = GitHub(a.gh)
        if a.operation == 'verify':
            need(a.output is not None, 'output-required')
            result = produce(api, adopted, a.pr, a.output.resolve(), a.cache.resolve(), execution)
        else:
            need(a.archive is not None and a.expected_sha256 is not None, 'handoff-required')
            result = finalize(api, adopted, a.pr, a.archive, a.expected_sha256, execution)
        print(canonical(result).decode())
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a') as out:
                out.write('bundle_sha256='+result['bundle_sha256']+'\n')
    except (Rejected, gate.Rejected, OSError, ValueError, KeyError, TypeError) as exc:
        # Never echo candidate stdout, source, logs, tokens or raw API responses.
        print('protected-producer-rejected: '+type(exc).__name__, file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
