#!/usr/bin/env python3
"""Fresh Linux integration and adversarial controls. No provider calls or mocks."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time
import threading
import gate as g

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4');a=p.parse_args()
    root=a.output.resolve();root.mkdir(exist_ok=False,parents=True);cache=a.cache.resolve()
    results=[]
    def passed(name,layer,detail):
        results.append({'control':name,'result':'passed','layer':layer,'detail':detail})
        print(json.dumps(results[-1]),flush=True)
        (root/'controls.json').write_text(json.dumps(results,indent=2)+'\n')
    def expect(name,layer,fn,reason=None):
        try: fn()
        except g.Rejected as exc:
            assert exc.layer==layer,(name,layer,str(exc))
            if reason: assert reason in str(exc),(name,str(exc))
            if layer=='formal-failed' and name!='crash-with-spoofed-diagnostics':
                logs=(root/name/'run/proof.log').read_text()
                required={'overgrant':'unsolved goals','always-reject':'unsolved goals',
                  'sorry':"Illegal axiom detected: 'sorryAx'",'custom-axiom':"Illegal axiom detected: 'ProofGate.forbidden'",
                  'native-evaluation':'Illegal axiom detected:',
                  'altered-statement':'Challenge and solution theorem statement do not match',
                  'referenced-definition-bypass':"Const does not match between challenge and target 'ProofGate.admission'",
                  'spoofed-proof-success':"Illegal axiom detected: 'sorryAx'"}[name]
                assert required in logs,(name,required,logs[-3000:])
                passed(name,'proof-obligation' if name in ['overgrant','always-reject'] else 'statement-or-axiom',
                       {'gate_status':'formal-failed','known_fixture_diagnostic':required})
            else: passed(name,layer,str(exc))
            return
        raise AssertionError(name+' unexpectedly accepted')
    valid=root/'valid'
    receipt,tools,node=g.evaluate(g.ROOT/'candidate',valid,cache)
    path=g.finish(receipt,tools,node,g.ROOT/'candidate',valid)
    expected=g.sha(path)
    passed('valid','formal/build/bridge/application',{'receipt_sha256':expected,'snapshot_sha256':receipt['snapshot_sha256']})
    # Admission check consumes exact verifier-owned receipt digest; no rebuild.
    g.copy_checked(path,expected,g.ROOT/'candidate',valid/'artifact',cache,root/'accepted-copy')
    passed('accepted-copy','identity','copied tested bytes without rebuild; no service deployed')
    def variant(name,edit):
        candidate=root/name/'candidate';candidate.parent.mkdir();shutil.copytree(g.ROOT/'candidate',candidate)
        edit(candidate)
        return lambda:g.evaluate(candidate,root/name/'run',cache)
    def change(c,file,old,new):
        f=c/file;text=f.read_text();assert old in text;f.write_text(text.replace(old,new))
    expect('overgrant','formal-failed',variant('overgrant',lambda c:change(c,'formal/Admission.lean','⟨true, n, b - n⟩','⟨true, n + 1, b - n⟩')))
    expect('always-reject','formal-failed',variant('always-reject',lambda c:change(c,'formal/Admission.lean','⟨true, n, b - n⟩','⟨false, 0, b⟩')))
    # Existing candidate code compiles, but cannot change the trusted challenge.
    challenge=(g.BASE/'Challenge.lean').read_text()
    def proof(c,text): (c/'formal/Proof.lean').write_text(text)
    expect('sorry','formal-failed',variant('sorry',lambda c:proof(c,challenge)))
    expect('custom-axiom','formal-failed',variant('custom-axiom',lambda c:proof(c,
       challenge.replace('namespace ProofGate','namespace ProofGate\naxiom forbidden : False').replace('sorry','exact forbidden.elim'))))
    expect('altered-statement','formal-failed',variant('altered-statement',lambda c:proof(c,
       'import Admission\nnamespace ProofGate\n'+''.join('theorem '+n+' : True := by trivial\n' for n in
        ['exact_grant','conservation','failure_preservation','total_success'])+'end ProofGate\n')))
    expect('spoofed-proof-success','formal-failed',variant('spoofed-proof-success',lambda c:proof(c,
       challenge+'\n#eval IO.println "Your solution is okay!"\n')))
    native=(g.ROOT/'candidate/formal/Proof.lean').read_text().replace(':= by',':= by\n  have nativeTruth : True := by native_decide')
    expect('native-evaluation','formal-failed',variant('native-evaluation',lambda c:proof(c,native)))
    # Same names and plausible proofs, but a model that makes positivity impossible.
    fake_model=(g.BASE/'Model.lean').read_text().replace('| .nonneg n => 0 < n','| .nonneg _ => False')
    fake_impl='namespace ProofGate\ndef admission (b : Nat) (_ : Amount) : Response := ⟨false, 0, b⟩\nend ProofGate\n'
    fake_proofs=(g.ROOT/'candidate/formal/Proof.lean').read_text().replace('import Admission','')
    fake_proofs=fake_proofs[:fake_proofs.index('theorem exact_grant')]+"""
theorem exact_grant (b : Nat) (a : Amount) :
    (admission b a).success = true → a = .nonneg (admission b a).granted := by simp [admission]
theorem conservation (b : Nat) (a : Amount) :
    (admission b a).balance + (admission b a).granted = b := by simp [admission]
theorem failure_preservation (b : Nat) (a : Amount) :
    (¬ positive a ∨ ¬ affordable a b) → admission b a = ⟨false, 0, b⟩ := by simp [admission]
theorem total_success (b : Nat) (a : Amount) :
    positive a → affordable a b → (admission b a).success = true := by cases a <;> simp [positive]
end ProofGate
"""
    expect('referenced-definition-bypass','formal-failed',variant('referenced-definition-bypass',lambda c:proof(c,fake_model+fake_impl+fake_proofs)))
    crashing=(g.ROOT/'candidate/formal/Proof.lean').read_text()+'\n#eval IO.println "tactic axiom match"\n#eval (IO.Process.exit 17 : IO Unit)\n'
    expect('crash-with-spoofed-diagnostics','formal-failed',variant('crash-with-spoofed-diagnostics',lambda c:proof(c,crashing)))
    crash_log=(root/'crash-with-spoofed-diagnostics/run/proof.log').read_text()
    assert 'tactic axiom match' in crash_log and 'code 17' in crash_log,crash_log
    expect('missing-proof','source-policy',variant('missing-proof',lambda c:(c/'formal/Proof.lean').rename(c/'formal/Other.lean')))
    expect('altered-model','source-policy',variant('altered-model',lambda c:(c/'formal/Model.lean').write_text('def fake := True\n')))
    expect('runtime-substitution','runtime-policy',variant('runtime-substitution',lambda c:change(c,'formal/Admission.lean','def admission','@[implemented_by fake]\ndef admission')))
    expect('extern-substitution','runtime-policy',variant('extern-substitution',lambda c:change(c,'formal/Admission.lean','def admission','@[extern "fake"]\ndef admission')))
    expect('driver-spoof','driver-policy',variant('driver-spoof',lambda c:change(c,'app/server.ts','Core.admission(prior, signed)',"({ $: 'Response', success: true, granted: input.amount, balance: prior - input.amount })")))
    # Retain the actual retry/double-charge regression in the HTTP driver as well
    # as rejecting all unreviewed service changes at the immutable-driver layer.
    double=root/'double-charge';shutil.copytree(valid/'artifact',double)
    f=double/'server.ts';text=f.read_text();text=text.replace('const body = existing.response;',
      "const body = existing.response; updateState.run(Math.max(0, balance() - Math.max(0, input.amount))); ")
    f.write_text(text)
    doubleout=root/'double-charge-tests';doubleout.mkdir()
    expect('double-charge-http','process',lambda:g.application_checks(double,tools,node,doubleout))
    assert 'AssertionError' in (doubleout/'application.log').read_text()
    tampered=root/'substituted';shutil.copytree(valid/'artifact',tampered)
    (tampered/'core').write_bytes(b'not the accepted executable')
    expect('artifact-substitution','identity',lambda:g.verify_identity(path,expected,g.ROOT/'candidate',tampered,cache),'accepted artifact substituted')
    expect('forged-receipt','identity',lambda:g.verify_identity(path,'0'*64,g.ROOT/'candidate',valid/'artifact',cache),'independently supplied digest')
    stale=root/'stale';shutil.copytree(g.ROOT/'candidate',stale)
    f=stale/'formal/Proof.lean';f.write_text(f.read_text()+'\n-- later edit\n')
    expect('stale-source','identity',lambda:g.verify_identity(path,expected,stale,valid/'artifact',cache))
    missing_log=root/'evidence-missing';shutil.copytree(valid,missing_log)
    (missing_log/'bridge.log').rename(missing_log/'renamed-bridge.log')
    try:
        g.verify_identity(missing_log/'receipt.json',expected,g.ROOT/'candidate',valid/'artifact',cache)
    except (g.Rejected,OSError) as exc: passed('missing-evidence','identity',str(exc))
    else: raise AssertionError('missing evidence accepted')
    # A live edit after snapshot selection must not borrow the running verdict.
    race_candidate=root/'concurrent-edit-candidate';shutil.copytree(g.ROOT/'candidate',race_candidate)
    raced=root/'concurrent-edit-run'
    proof_file=race_candidate/'formal/Proof.lean'
    proof_file.write_text(proof_file.read_text()+'\n#eval IO.sleep 1500\n')
    def edit_live():
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            if (raced/'proof.log').exists() and 'Building Proof' in (raced/'proof.log').read_text(errors='replace'):
                f=race_candidate/'formal/Admission.lean';f.write_text(f.read_text()+'\n-- live edit\n');return
            time.sleep(.05)
        raise RuntimeError('did not observe proof build')
    editor=threading.Thread(target=edit_live);editor.start()
    expect('concurrent-edit','identity',lambda:g.evaluate(race_candidate,raced,cache),'inputs changed during checking')
    editor.join(timeout=3);assert not editor.is_alive()
    expect('missing-tool','infrastructure',lambda:g.check_tools(root/'missing-cache'))
    expect('missing-executable','infrastructure',lambda:g.run(['/missing/proofgate-checker'],root,root/'missing-executable.log'))
    empty=root/'infra';empty.mkdir()
    expect('real-timeout','infrastructure',lambda:g.run(g.scope()+g.sandbox(tools,node,empty,[])+['/bin/sleep','10'],root,root/'timeout.log',timeout=.2))
    # Genuine nonzero isolation setup; not counted as a rejected proof.
    expect('isolation-mount-failure','process',lambda:g.run(g.sandbox(tools,node,empty,[])+['--ro-bind','/missing-proofgate-mount','/missing','/bin/true'],root,root/'isolation-failure.log'))
    assert 'bwrap:' in (root/'isolation-failure.log').read_text()
    passed('all-controls','summary',{'count':len(results),'policy_admitted':False,'photon_demonstration':False})
    (root/'handoff.json').write_text(json.dumps({'receipt':str(path),'receipt_sha256':expected,'controls':results},indent=2)+'\n')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'FAILED: {exc}',file=sys.stderr);raise
