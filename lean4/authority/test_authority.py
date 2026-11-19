#!/usr/bin/env python3
"""Contract fixtures: substituted API and signature report, NEVER platform evidence."""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from common import *
from bundle import LOGS, protected, pack, unpack, validate
from admit import admit
from producer import finalize


def adopted():
    return {'schema':1,'adopted':True,'owner_id':41484281,
            'policy_sha256':sha(POLICY.read_bytes()),'producer_sha':'a'*40,
            'producer_ref':'refs/tags/proofgate-lean-fixture','epoch':'fixture-v1',
            'human_adoption_ref':'https://github.com/deveshkakkar/ProofGate/issues/46#issuecomment-1'}


def gitblob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


class FixtureAPI:
    """Explicitly substituted platform and crypto, not an authentication proof."""
    def __init__(self):
        self.adopted = adopted(); self.bad_auth = False; self.auth_calls = 0
        self.head = 'b'*40; self.base = 'c'*40; self.tree = 'd'*40
        self.sources = {n:(ROOT/'candidate'/n).read_bytes() for n in policy()['candidate_paths']}
        self.changed = [{'filename':'lean4/candidate/formal/Admission.lean','status':'modified'}]
        self.run_status = 'success'; self.live_attempt = 1

    def get(self, endpoint):
        tail = endpoint.removeprefix('repos/'+REPO)
        if tail == '':
            return {'id':1437623154,'full_name':REPO,'owner':{'id':41484281}}
        if tail.startswith('/environments/'):
            return {'name':VARIABLE,'value':canonical(self.adopted).decode()}
        if tail.startswith('/issues/comments/'):
            return {'html_url':self.adopted['human_adoption_ref'],'user':{'id':41484281,'type':'User'},
                    'body':canonical({'type':'proofgate.lean.adoption.v1','adopted':True,**{k:self.adopted[k]
                     for k in ['policy_sha256','producer_sha','producer_ref','epoch']}}).decode()}
        if tail == '/pulls/7':
            return {'number':7,'state':'open','merged':False,'changed_files':len(self.changed),
                    'head':{'sha':self.head,'repo':{'id':1437623154}},
                    'base':{'sha':self.base,'ref':'main','repo':{'id':1437623154}}}
        if tail == '/branches/main': return {'commit':{'sha':self.base}}
        if tail.startswith('/compare/'):
            return {'base_commit':{'sha':self.base},'merge_base_commit':{'sha':self.base},
                    'commits':[{'sha':self.head}],'files':self.changed}
        if tail.startswith('/git/commits/'):
            return {'sha':self.head,'tree':{'sha':self.tree}}
        if tail.startswith('/git/trees/'):
            return {'sha':self.tree,'truncated':False,'tree':[
                {'path':'lean4/candidate/'+n,'sha':gitblob(v),'type':'blob','mode':'100644','size':len(v)}
                for n,v in self.sources.items()]}
        if tail.startswith('/git/blobs/'):
            for raw in self.sources.values():
                if gitblob(raw) == tail.rsplit('/',1)[1]:
                    return {'sha':gitblob(raw),'encoding':'base64','content':base64.b64encode(raw).decode(),'size':len(raw)}
        if tail.startswith('/actions/runs/'):
            return {'id':123,'run_attempt':self.live_attempt,'status':'completed','conclusion':self.run_status,
                    'event':'workflow_dispatch','head_sha':self.adopted['producer_sha'],
                    'path':WORKFLOW,'repository':{'id':1437623154},
                    'created_at':datetime.now(timezone.utc).isoformat()}
        raise AssertionError(endpoint)

    def authenticate(self, archive, signature, root):
        self.auth_calls += 1
        need(not self.bad_auth, 'fixture-authentication-denied')
        return certificate(root, sha(archive.read_bytes()))


def certificate(root, archive_sha):
    uri = 'https://github.com/'+REPO+'/actions/runs/123/attempts/1'
    cert = {'issuer':'https://token.actions.githubusercontent.com',
       'buildSignerURI':'https://github.com/'+REPO+'/'+WORKFLOW+'@'+root['producer_ref'],
       'buildSignerDigest':root['producer_sha'],'sourceRepositoryURI':'https://github.com/'+REPO,
       'sourceRepositoryDigest':root['producer_sha'],'sourceRepositoryRef':root['producer_ref'],
       'sourceRepositoryIdentifier':'1437623154','sourceRepositoryOwnerIdentifier':'41484281',
       'runnerEnvironment':'github-hosted','buildTrigger':'workflow_dispatch','runInvocationURI':uri}
    return [{'verificationResult':{'signature':{'certificate':cert},'statement':{
       '_type':'https://in-toto.io/Statement/v1','subject':[{'name':'reservation-bundle.zip','digest':{'sha256':archive_sha}}],
       'predicateType':PREDICATE,'predicate':{'runDetails':{'metadata':{'invocationId':uri}}}}}}]


def fixture_files(api):
    """Internally consistent forged passing evidence, intentionally NOT real Lean."""
    sources = {n:sha(v) for n,v in api.sources.items()}
    payload = {'source/'+n:v for n,v in api.sources.items()}
    payload.update({'logs/'+n:b'fixture log' for n in LOGS})
    payload.update({'artifact/'+n:b'fixture artifact' for n in policy()['artifact_paths']})
    receipt = {'schema':1,'backend':'lean4-v1','observations_consistent':True,'policy_admitted':False,
       'source':sources,'snapshot_sha256':digest(sources),'protected':protected(),
       'evaluator':policy()['evaluator_files']['gate.py'],'toolchains':policy()['toolchains'],
       'artifact':{n:{'sha256':sha(payload['artifact/'+n]),'executable':n == 'core'} for n in policy()['artifact_paths']},
       'logs':{n:sha(payload['logs/'+n]) for n in LOGS}}
    receipt['identity_sha256'] = digest(receipt)
    payload['receipt.json'] = canonical(receipt)
    manifest = {'schema':1,'policy_sha256':sha(POLICY.read_bytes()),'adoption':api.adopted,
                'source':source_identity(api,7),'execution':{'run_id':'123','attempt':1},
                'files':{k:sha(v) for k,v in payload.items()}}
    payload['result.json'] = canonical(manifest)
    return payload


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name); self.api = FixtureAPI()
        self.files = fixture_files(self.api); self.archive = self.path/'reservation-bundle.zip'
        self.sig = self.path/'signature'; self.sig.write_bytes(b'fixture-only')
        self.save()

    def save(self):
        self.archive.unlink(missing_ok=True); pack(self.files,self.archive)

    def run_admit(self):
        return admit(self.api,adopted(),7,self.archive,self.sig,self.path/'accepted')

    def test_fixture_positive_exact_copy_not_platform_authority(self):
        result = self.run_admit()
        self.assertTrue(result['producer_authenticated']); self.assertFalse(result['merge_eligible'])
        self.assertEqual((self.path/'accepted/core').read_bytes(),self.files['artifact/core'])
        with self.assertRaises(Rejected): self.run_admit()

    def test_forged_consistent_rows_require_external_authentication(self):
        validate(self.files,adopted())  # forged rows really ARE self-consistent
        self.api.bad_auth = True
        with self.assertRaisesRegex(Rejected,'authentication-denied'): self.run_admit()
        self.assertFalse((self.path/'accepted').exists())

    def test_missing_authentication_fails_before_parsing(self):
        self.archive.write_bytes(b'not even a zip'); self.api.bad_auth = True
        with self.assertRaisesRegex(Rejected,'authentication-denied'): self.run_admit()
        self.assertEqual(self.api.auth_calls,1)
        self.sig.unlink()
        with self.assertRaises(OSError): self.run_admit()

    def test_policy_or_evaluator_changes_not_candidate_inputs(self):
        for path in ['lean4/gate.py','lean4/baseline/v1/Statements.lean',
                     'lean4/authority/policy-v1.json','.github/workflows/lean-authority.yml']:
            with self.subTest(path=path):
                self.api.changed = [{'filename':path,'status':'modified'}]
                with self.assertRaisesRegex(Rejected,'protected-input'): source_identity(self.api,7)

    def test_replaced_artifact_or_output(self):
        for name in ['artifact/core','receipt.json','logs/proof.log','source/formal/Proof.lean']:
            with self.subTest(name=name):
                files = copy.deepcopy(self.files); files[name] += b'changed'
                with self.assertRaisesRegex(Rejected,'bundle-file-binding'): validate(files,adopted())
        with self.assertRaisesRegex(Rejected,'handoff-substituted'):
            finalize(self.api,adopted(),7,self.archive,'0'*64,{'run_id':'123','attempt':1})

    def test_stale_head_base_policy_or_replayed_attempt(self):
        for field in ['head','base','policy','attempt']:
            with self.subTest(field=field):
                self.api = FixtureAPI()
                if field in ['head','base']: setattr(self.api,field,'e'*40)
                elif field == 'policy': self.api.adopted['epoch'] = 'revoked'
                else: self.api.live_attempt = 2
                with self.assertRaises(Rejected): self.run_admit()
                self.assertFalse((self.path/'accepted').exists())

    def test_immutable_path_policy_rejects_A_B_A_mutable_pr_files_race(self):
        # Old join would accept B's permitted list between two observations of A.
        approved_B = self.api.changed
        unapproved_A = [{'filename':'lean4/gate.py','status':'modified'}]
        original = self.api.get
        def racing(endpoint):
            if '/pulls/7/files' in endpoint: return approved_B
            if '/compare/' in endpoint:
                result = original(endpoint); result['files'] = unapproved_A; return result
            return original(endpoint)
        self.api.get = racing
        self.assertTrue(all(x['filename'].startswith('lean4/candidate/')
                            for x in racing('repos/'+REPO+'/pulls/7/files?per_page=100')))
        with self.assertRaisesRegex(Rejected,'protected-input'): source_identity(self.api,7)

    def test_wrong_pr(self):
        with self.assertRaisesRegex(Rejected,'requested-pr'):
            admit(self.api,adopted(),8,self.archive,self.sig,self.path/'accepted')

    def test_wrong_certificate_workflow_source_run_subject_or_runner(self):
        report = certificate(adopted(),sha(self.archive.read_bytes()))
        for key in ['buildSignerURI','buildSignerDigest','sourceRepositoryIdentifier','runInvocationURI','runnerEnvironment']:
            altered = copy.deepcopy(report); altered[0]['verificationResult']['signature']['certificate'][key] = 'wrong'
            with self.subTest(key=key), self.assertRaisesRegex(Rejected,'certificate-binding'):
                verify_certificate(altered,adopted(),sha(self.archive.read_bytes()),{'run_id':'123','attempt':1})
        with self.assertRaisesRegex(Rejected,'subject-binding'):
            verify_certificate(report,adopted(),'0'*64,{'run_id':'123','attempt':1})

    def test_adoption_is_explicit_not_merge_or_bool_schema(self):
        for key,value in [('adopted',False),('schema',True),('policy_sha256','0'*64)]:
            root = adopted(); root[key] = value
            with self.subTest(key=key),self.assertRaises(Rejected): adoption(root)

    def test_zip_inventory_modes_and_duplicate_paths(self):
        raw = io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z: z.writestr('../core',b'bad')
        with self.assertRaisesRegex(Rejected,'inventory'): unpack(raw.getvalue())

    def test_source_change_at_last_freshness_check_no_copy(self):
        original = self.api.get; calls = 0
        def changed(endpoint):
            nonlocal calls
            if endpoint.endswith('/pulls/7'):
                calls += 1
                if calls == 2: self.api.head = 'e'*40
            return original(endpoint)
        self.api.get = changed
        with self.assertRaisesRegex(Rejected,'freshness-changed-before-copy'): self.run_admit()
        self.assertFalse((self.path/'accepted').exists())
        self.assertFalse(list(self.path.glob('.proofgate-admit-*')))

    def test_pinned_download_handoff_path(self):
        # v5 download-artifact's merge-multiple:true resolves to input path,
        # including when selecting the exact artifact ID rather than its name.
        workflow = (ROOT.parent/'.github/workflows/lean-authority.yml').read_text()
        self.assertIn('634f93cb2916e3fdff6788551b99b062d0335ce0',workflow)
        self.assertIn('merge-multiple: true',workflow)
        self.assertNotIn('/handoff/verified-reservation/',workflow)
        self.assertIn('--archive "$RUNNER_TEMP/handoff/reservation-bundle.zip"',workflow)
        self.assertIn('subject-path: ${{ runner.temp }}/handoff/reservation-bundle.zip',workflow)

    def test_signer_handoff_same_run_no_candidate_execution(self):
        result = finalize(self.api,adopted(),7,self.archive,sha(self.archive.read_bytes()),{'run_id':'123','attempt':1})
        self.assertTrue(result['ready_for_attestation'])
        with self.assertRaisesRegex(Rejected,'handoff-execution'):
            finalize(self.api,adopted(),7,self.archive,sha(self.archive.read_bytes()),{'run_id':'124','attempt':1})


if __name__ == '__main__':
    unittest.main()
