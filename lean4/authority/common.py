"""Fixed reservation authority contract. No kernel.verify authority shortcut."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
POLICY = Path(__file__).with_name('policy-v1.json')
REPO = 'deveshkakkar/ProofGate'
WORKFLOW = '.github/workflows/lean-authority.yml'
PREDICATE = 'https://slsa.dev/provenance/v1'
ENVIRONMENT = 'proofgate-lean-policy-v1'
VARIABLE = 'PROOFGATE_LEAN_ADOPTION'


class Rejected(RuntimeError):
    pass


def need(value, reason):
    if not value:
        raise Rejected(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    def pairs(items):
        result = {}
        for k, v in items:
            need(k not in result, 'duplicate-json-key')
            result[k] = v
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: need(False, 'nonfinite-json'))


def policy():
    return decode(POLICY.read_bytes())


def adoption(value):
    need(isinstance(value, dict) and set(value) == {'schema','adopted','owner_id','policy_sha256',
         'producer_sha','producer_ref','epoch','human_adoption_ref'}, 'adoption-shape')
    need(type(value['schema']) is int and value['schema'] == 1 and value['adopted'] is True and value['owner_id'] == 41484281,
         'explicit-human-adoption-required')
    need(value['policy_sha256'] == sha(POLICY.read_bytes()), 'adopted-policy-mismatch')
    need(isinstance(value['producer_sha'], str) and re.fullmatch('[0-9a-f]{40}',value['producer_sha']), 'producer-pin')
    need(isinstance(value['producer_ref'], str) and re.fullmatch(r'refs/tags/proofgate-lean-[A-Za-z0-9._-]+',value['producer_ref']), 'producer-ref')
    need(isinstance(value['epoch'], str) and re.fullmatch('[A-Za-z0-9._-]{1,80}',value['epoch']), 'policy-epoch')
    need(isinstance(value['human_adoption_ref'], str) and re.fullmatch(r'https://github.com/deveshkakkar/ProofGate/issues/46#issuecomment-[0-9]+',value['human_adoption_ref']), 'human-adoption-reference')
    return value


def pinned_gh(path):
    lock = policy()['gh']
    p = Path(path)
    need(p.is_file() and not p.is_symlink() and sha(p.read_bytes()) == lock['binary_sha256'], 'gh-verifier-pin')
    return p.resolve()


class GitHub:
    def __init__(self, gh):
        self.gh = pinned_gh(gh)

    def command(self, args, *, timeout=90):
        proc = subprocess.run([str(self.gh), *args], capture_output=True, timeout=timeout)
        need(proc.returncode == 0, 'github-or-authentication-unavailable')
        need(len(proc.stdout) <= 24*1024*1024, 'github-output-bound')
        return decode(proc.stdout)

    def get(self, endpoint):
        return self.command(['api','--hostname','github.com','--method','GET','-H','Accept: application/vnd.github+json',endpoint])

    def authenticate(self, archive, attestation, adopted):
        # Only the pinned real CLI can produce this report in the public command.
        # No --auth-report, custom root, identity override or unsigned fallback.
        return self.command(['attestation','verify',str(archive),'--hostname','github.com','--bundle',str(attestation),
            '--repo',REPO,'--signer-workflow',REPO+'/'+WORKFLOW,
            '--signer-digest',adopted['producer_sha'],'--source-digest',adopted['producer_sha'],
            '--source-ref',adopted['producer_ref'],'--cert-identity',
            'https://github.com/'+REPO+'/'+WORKFLOW+'@'+adopted['producer_ref'],
            '--cert-oidc-issuer','https://token.actions.githubusercontent.com',
            '--deny-self-hosted-runners','--predicate-type',PREDICATE,'--format','json'])


def current_adoption(api, adopted, *, active_variable=True):
    adoption(adopted)
    if active_variable:
        v = api.get(f'repos/{REPO}/environments/{ENVIRONMENT}/variables/{VARIABLE}')
        need(v['name'] == VARIABLE and decode(v['value']) == adopted, 'policy-revoked-or-changed')
    ident = adopted['human_adoption_ref'].rsplit('-',1)[1]
    comment = api.get(f'repos/{REPO}/issues/comments/{ident}')
    need(comment['html_url'] == adopted['human_adoption_ref'] and
         comment['user']['id'] == 41484281 and comment['user']['type'] == 'User', 'human-policy-owner')
    expected = {'type':'proofgate.lean.adoption.v1','adopted':True,
                **{k:adopted[k] for k in ['policy_sha256','producer_sha','producer_ref','epoch']}}
    need(decode(comment['body']) == expected, 'human-policy-not-adopted')


def source_identity(api, number):
    need(type(number) is int and number > 0, 'pr-number')
    p = policy()
    repo = api.get(f'repos/{REPO}')
    need(repo['id'] == p['repository_id'] and repo['full_name'] == REPO and
         repo['owner']['id'] == p['policy_owner']['id'], 'source-repository')
    pr = api.get(f'repos/{REPO}/pulls/{number}')
    need(pr['number'] == number and pr['state'] == 'open' and pr['merged'] is False,
         'source-pr-not-open')
    need(pr['base']['repo']['id'] == p['repository_id'] and pr['base']['ref'] == p['base_ref'], 'source-base')
    need(pr['head']['repo'] is not None, 'source-head-repository')
    head, base = pr['head']['sha'], pr['base']['sha']
    need(all(isinstance(s,str) and re.fullmatch('[0-9a-f]{40}',s) for s in [head,base]), 'source-sha')
    branch = api.get(f'repos/{REPO}/branches/{p["base_ref"]}')
    need(branch['commit']['sha'] == base, 'stale-base')
    # Never join a frozen head with the mutable PR-files endpoint: A/B/A can
    # make that endpoint describe another head. Compare immutable Git objects.
    comparison = api.get(f'repos/{REPO}/compare/{base}...{head}')
    need(comparison['base_commit']['sha'] == base and comparison['commits'] and
         comparison['commits'][-1]['sha'] == head, 'immutable-comparison-identity')
    changed = comparison['files']
    permitted = {p['repository_prefix']+x for x in p['candidate_paths']}
    need(isinstance(changed,list) and 0 < len(changed) <= 3 and
         len({x['filename'] for x in changed}) == len(changed) and
         all(x['filename'] in permitted and x['status'] == 'modified' for x in changed), 'candidate-changed-protected-input')
    commit = api.get(f'repos/{REPO}/git/commits/{head}')
    need(commit['sha'] == head, 'source-commit')
    tree = api.get(f'repos/{REPO}/git/trees/{commit["tree"]["sha"]}?recursive=1')
    need(tree['sha'] == commit['tree']['sha'] and tree.get('truncated') is False, 'source-tree-truncated')
    entries = {x['path']:x for x in tree['tree']}
    need(len(entries) == len(tree['tree']), 'source-tree-ambiguous')
    blobs = {}
    for local in p['candidate_paths']:
        e = entries.get(p['repository_prefix']+local)
        need(e is not None and e['type'] == 'blob' and e['mode'] == '100644' and
             type(e['size']) is int and 0 < e['size'] <= 256000, 'candidate-file-policy')
        blobs[local] = e['sha']
    return {'repository':REPO,'repository_id':p['repository_id'],'pr':number,
            'head':head,'head_repository_id':pr['head']['repo']['id'],'base':base,
            'base_ref':p['base_ref'],'merge_base':comparison['merge_base_commit']['sha'],
            'tree':tree['sha'],'blobs':blobs}


def candidate_bytes(api, identity):
    result = {}
    for name, ident in identity['blobs'].items():
        obj = api.get(f'repos/{REPO}/git/blobs/{ident}')
        need(obj['sha'] == ident and obj['encoding'] == 'base64', 'source-blob')
        raw = base64.b64decode(''.join(obj['content'].split()), validate=True)
        need(0 < len(raw) <= 256000 and len(raw) == obj['size'] and
             hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == ident, 'source-blob-integrity')
        result[name] = raw
    return result


def verify_certificate(report, adopted, bundle_sha, execution):
    need(isinstance(report,list) and len(report) == 1, 'producer-authentication-ambiguous')
    verified = report[0]['verificationResult']
    cert = verified['signature']['certificate']
    uri = f'https://github.com/{REPO}/actions/runs/{execution["run_id"]}/attempts/{execution["attempt"]}'
    expected = {'issuer':'https://token.actions.githubusercontent.com',
        'buildSignerURI':'https://github.com/'+REPO+'/'+WORKFLOW+'@'+adopted['producer_ref'],
        'buildSignerDigest':adopted['producer_sha'],'sourceRepositoryURI':'https://github.com/'+REPO,
        'sourceRepositoryDigest':adopted['producer_sha'],'sourceRepositoryRef':adopted['producer_ref'],
        'sourceRepositoryIdentifier':str(policy()['repository_id']),
        'sourceRepositoryOwnerIdentifier':'41484281','runnerEnvironment':'github-hosted',
        'buildTrigger':'workflow_dispatch','runInvocationURI':uri}
    need(all(cert.get(k) == v for k,v in expected.items()), 'producer-certificate-binding')
    statement = verified['statement']
    need(statement['_type'] == 'https://in-toto.io/Statement/v1' and statement['predicateType'] == PREDICATE and
         statement['subject'] == [{'name':'reservation-bundle.zip','digest':{'sha256':bundle_sha}}], 'signed-subject-binding')
    need(statement['predicate']['runDetails']['metadata']['invocationId'] == uri, 'signed-run-binding')
    return uri


def successful_run(api, execution, adopted):
    ident, attempt = execution['run_id'], execution['attempt']
    need(isinstance(ident,str) and ident.isdigit() and type(attempt) is int and attempt > 0, 'run-identity')
    current = api.get(f'repos/{REPO}/actions/runs/{ident}')
    exact = api.get(f'repos/{REPO}/actions/runs/{ident}/attempts/{attempt}')
    for run in [current,exact]:
        need(run['id'] == int(ident) and run['run_attempt'] == attempt and run['status'] == 'completed' and
             run['conclusion'] == 'success' and run['event'] == 'workflow_dispatch' and
             run['head_sha'] == adopted['producer_sha'] and run['path'] == WORKFLOW and
             run['repository']['id'] == policy()['repository_id'], 'producer-run-not-current-success')
    when = datetime.fromisoformat(exact['created_at'].replace('Z','+00:00'))
    need(0 <= (datetime.now(timezone.utc)-when).total_seconds() <= policy()['maximum_age_seconds'], 'expired-result')
