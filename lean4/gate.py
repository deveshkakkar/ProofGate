#!/usr/bin/env python3
"""Versioned Lean reservation evaluator. Never imports candidate Python or JS."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
import platform

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'baseline/v1'
FILES = ('formal/Admission.lean', 'formal/Proof.lean', 'app/server.ts')
HEADER = 'import Model\nnamespace ProofGate\ndef admission (b : Nat) (a : Amount) : Response :=\n'
FOOTER = '\nend ProofGate\n'
WORDS = set('match a with nonneg n if b then else true false neg _'.split())

class Rejected(RuntimeError):
    def __init__(self, layer, detail):
        self.layer = layer
        super().__init__(f'{layer}: {detail}')

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def tree(path):
    result = {}
    for p in sorted(path.rglob('*')):
        if p.is_symlink():
            result[str(p.relative_to(path))] = {'link': os.readlink(p)}
        elif p.is_file():
            result[str(p.relative_to(path))] = {'sha256': sha(p), 'executable': bool(p.stat().st_mode & 0o111)}
    return result

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def snapshot(candidate):
    actual = set()
    for p in candidate.rglob('*'):
        if p.is_symlink(): raise Rejected('source-policy', 'symlink forbidden')
        if p.is_file(): actual.add(str(p.relative_to(candidate)))
    if actual != set(FILES): raise Rejected('source-policy', f'expected exactly {FILES}; found {sorted(actual)}')
    if any((candidate/f).stat().st_size > 256_000 for f in FILES): raise Rejected('source-policy', 'oversized source')
    return {f: sha(candidate/f) for f in FILES}

def validate_admission(text):
    # Deliberately small executable term language. No attributes, commands, imports,
    # macros, strings, FFI, unsafe code or user-defined runtime replacements.
    if not text.startswith(HEADER) or not text.endswith(FOOTER):
        raise Rejected('runtime-policy', 'admission declaration envelope changed')
    body = text[len(HEADER):-len(FOOTER)]
    if not body.strip() or re.search(r'[^\sA-Za-z0-9_.|<>≤∧⟨⟩,+*()\-=>]', body):
        raise Rejected('runtime-policy', 'unsupported executable syntax')
    words = re.findall(r'[A-Za-z_][A-Za-z_0-9]*', body)
    if set(words) - WORDS: raise Rejected('runtime-policy', 'unsupported executable identifiers')
    if re.search(r'\d{17}', body): raise Rejected('runtime-policy', 'oversized literal')

def run(argv, cwd, log, *, timeout=180, env=None):
    """Bound every process tree; logs are diagnostics, never a success parser."""
    with open(log, 'wb') as output:
        try:
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as exc: raise Rejected('infrastructure', str(exc)) from exc
        try: rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            units=[arg.split('=',1)[1] for arg in argv if arg.startswith('--unit=')]
            for unit in units:
                subprocess.run(['systemctl','--user','kill','--kill-whom=all','--signal=KILL',unit+'.scope'],capture_output=True,timeout=10)
            os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            raise Rejected('infrastructure', f'timeout after {timeout}s; {log}')
    if rc: raise Rejected('process', f'exit {rc}; {log}')

def sandbox(tools, node, project, writable, *, network=False):
    cmd = ['bwrap', '--unshare-all', '--new-session', '--die-with-parent', '--cap-drop', 'ALL',
           '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--dir', '/etc']
    if network: cmd += ['--share-net']  # only loopback HTTP tests; listener binds 127.0.0.1
    for p in ('/usr', '/bin', '/lib', '/lib64', '/etc/ld.so.cache', '/etc/alternatives'):
        if Path(p).exists(): cmd += ['--ro-bind', p, p]
    cmd += ['--ro-bind', str(tools), '/tools', '--ro-bind', str(node), '/node',
            '--ro-bind', str(project), '/project']
    for host, guest in writable: cmd += ['--bind', str(host), guest]
    return cmd + ['--chdir', '/project', '--clearenv', '--setenv', 'PATH', '/tools/bin:/node/bin:/usr/bin:/bin',
                  '--setenv', 'HOME', '/tmp', '--setenv', 'LEAN_ABORT_ON_PANIC', '1', '--setenv', 'COMPARATOR_BWRAP', '/usr/bin/bwrap', '--setenv', 'LEAN_NUM_THREADS', '2']

def scope():
    return ['systemd-run', '--user', '--scope', '--quiet', '--unit=proofgate-lean-'+uuid.uuid4().hex, '-p', 'MemoryMax=4G', '-p', 'MemorySwapMax=0',
            '-p', 'TasksMax=64', '-p', 'CPUQuota=200%']

def prepare(project, candidate, proofs):
    project.mkdir()
    for name in ('Model.lean', 'Main.lean', 'Challenge.lean', 'lakefile.toml', 'lake-manifest.json', 'lean-toolchain', 'comparator.json'):
        shutil.copyfile(BASE/name, project/name)
    shutil.copyfile(candidate/'formal/Admission.lean', project/'Admission.lean')
    if proofs: shutil.copyfile(candidate/'formal/Proof.lean', project/'Proof.lean')
    (project/'.lake').mkdir()

def check_tools(cache):
    lock = json.loads((BASE/'toolchain.json').read_text())
    for name, entry in lock.items():
        directory = cache/entry['directory']
        if not directory.is_dir(): raise Rejected('infrastructure', f'missing {name}: {directory}; run bootstrap.py')
        if digest(tree(directory)) != entry['tree_sha256']: raise Rejected('infrastructure', f'{name} toolchain identity changed')
    return cache/lock['lean']['directory'], cache/lock['node']['directory']

def evaluate(candidate, output, cache):
    if output.exists(): raise Rejected('output-policy', 'output already exists')
    initial = snapshot(candidate)
    if sha(candidate/'app/server.ts') != sha(BASE/'server.ts'):
        raise Rejected('driver-policy','service and call binding must match the protected v1 service')
    validate_admission((candidate/'formal/Admission.lean').read_text())
    protected = tree(BASE)
    evaluator_identity=sha(Path(__file__))
    manifest=ROOT/'baseline-v1.json'
    expected=(ROOT/'BASELINE.v1.sha256').read_text().strip()
    if sha(manifest)!=expected or json.loads(manifest.read_text())!=protected:
        raise Rejected('protected-inputs','Lean baseline identity mismatch')
    tools, node = check_tools(cache)
    output.mkdir(parents=True)
    frozen=output/'source'; shutil.copytree(candidate,frozen)
    if snapshot(frozen)!=initial: raise Rejected('identity','source changed while snapshotting')
    # Probe actual isolation/resource manager before any candidate elaboration.
    probe = output/'probe'; probe.mkdir()
    run(scope()+sandbox(tools,node,probe,[])+['/bin/true'], output, output/'preflight.log', timeout=15)
    project = output/'proof'; prepare(project, frozen, True)
    config = json.loads((project/'comparator.json').read_text())
    config['external_kernels']['nanoda'] = [str(tools/'bin/nanoda_bin')]
    (project/'comparator.json').write_text(json.dumps(config,sort_keys=True)+'\n')
    checker_env = {'PATH':str(tools/'bin')+':/usr/bin:/bin', 'HOME':str(Path.home()),
                   'COMPARATOR_BWRAP':str(BASE/'checker-bwrap.py'), 'LEAN_ABORT_ON_PANIC':'1',
                   'XDG_RUNTIME_DIR':f'/run/user/{os.getuid()}'}
    prefix = scope()
    started = time.monotonic()
    try:
        # Lake sandboxes build/export through the protected minimal-root wrapper.
        # Comparator and replay kernels run outside candidate-writable mounts.
        run(prefix+[str(tools/'bin/lake'),'comparator'], project, output/'proof.log', env=checker_env)
    except Rejected as exc:
        # Candidate output is adversarial. A nonzero comparator result can be a
        # proof rejection, crash, missing tool, or sandbox failure. Do not infer
        # the cause from merged stdout/stderr. Controlled fixtures are adjudicated
        # separately against known inputs; an unknown failure is never a proof result.
        if exc.layer == 'process':
            raise Rejected('formal-failed', 'unverified failure (cause unknown); '+str(exc)) from exc
        raise
    # Build again in a fresh sandbox that never sees candidate proof code or its
    # generated .olean/C files. Only the validated executable term is compiled.
    runtime = output/'runtime'; prepare(runtime, frozen, False)
    run(scope()+sandbox(tools,node,runtime,[(runtime/'.lake','/project/.lake')])+['/tools/bin/lake','build','core'],
        runtime, output/'build.log')
    artifact = output/'artifact'; artifact.mkdir()
    shutil.copyfile(runtime/'.lake/build/bin/core', artifact/'core'); (artifact/'core').chmod(0o755)
    shutil.copyfile(BASE/'admission.mjs', artifact/'admission.mjs')
    shutil.copyfile(frozen/'app/server.ts', artifact/'server.ts')
    for name in ('LICENSE','LICENSES'):
        shutil.copyfile(tools/name,artifact/('LEAN-'+name))
    receipt = {'schema':1, 'backend':'lean4-v1', 'observations_consistent':False, 'policy_admitted':False,
               'source': initial, 'protected':protected, 'toolchains':json.loads((BASE/'toolchain.json').read_text()),
               'evaluator':evaluator_identity, 'artifact':tree(artifact),
               'checker_configuration':json.loads((project/'comparator.json').read_text()),
               'proof_inputs':{p.name:sha(p) for p in project.iterdir() if p.is_file()},
               'build_inputs':{p.name:sha(p) for p in runtime.iterdir() if p.is_file()},
               'build_outputs':tree(runtime/'.lake'),
               'snapshot_sha256':digest(initial), 'revision':revision(candidate),
               'environment':{'system':platform.platform(),'python':sys.version,
                   'os_release':Path('/etc/os-release').read_text(),
                   'host_tools':host_tools()} , 'formal_seconds':time.monotonic()-started}
    if snapshot(candidate)!=initial or tree(BASE)!=protected or sha(Path(__file__))!=evaluator_identity: raise Rejected('identity','inputs changed during checking')
    (output/'checkpoint.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    return receipt,tools,node

def host_tools():
    paths=['/usr/bin/bwrap','/usr/bin/systemd-run','/usr/bin/python3','/usr/bin/git',
           '/usr/lib/x86_64-linux-gnu/libc.so.6','/usr/lib/x86_64-linux-gnu/libm.so.6',
           '/usr/lib/x86_64-linux-gnu/libstdc++.so.6','/usr/lib/x86_64-linux-gnu/libgcc_s.so.1',
           '/lib64/ld-linux-x86-64.so.2',
           '/usr/lib/x86_64-linux-gnu/libpthread.so.0','/usr/lib/x86_64-linux-gnu/libdl.so.2',
           '/usr/lib/x86_64-linux-gnu/librt.so.1']
    return {p:sha(Path(p).resolve()) for p in paths}

def revision(candidate):
    def git(*args):
        r=subprocess.run(['git','-C',str(candidate),*args],capture_output=True,text=True,timeout=10)
        return r.stdout.strip() if r.returncode==0 else None
    return {'commit':git('rev-parse','HEAD'), 'dirty':git('status','--porcelain','--untracked-files=all','--','.')}

def application_checks(artifact, tools, node, output):
    empty=output/'test-root'; empty.mkdir(exist_ok=True)
    prefix=scope()+sandbox(tools,node,empty,[],network=True)
    # All test code and artifacts are read-only; each server gets only its own DB.
    prefix+=['--ro-bind',str(artifact),'/out','--ro-bind',str(BASE),'/baseline']
    run(prefix+['/node/bin/node','/baseline/bridge.mjs'],output,output/'bridge.log',timeout=60)
    run(prefix+['/node/bin/node','/baseline/legacy_bridge.mjs'],output,output/'legacy-bridge.log',timeout=90)
    app_prefix=sandbox(tools,node,empty,[],network=True)+['--ro-bind',str(artifact),'/out']
    run(scope()+[sys.executable,'-B',str(BASE/'http_tests.py'),'--prefix-json',json.dumps(app_prefix),
                 '--node','/node/bin/node','--entry','/out/server.ts'],output,output/'application.log',timeout=120)
    try:
        rows=json.loads((output/'application.log').read_text())
        if rows!={'schema':1,'tests':[{'id':i,'status':'passed'} for i in
          ['fresh-grant','boundary','invalid','repeat-conflict','concurrent-distinct','concurrent-same','restart']]}:
            raise ValueError('unexpected application evidence')
        bridge=json.loads((output/'bridge.log').read_text())
        if bridge['cases']!=11716: raise ValueError('incomplete bridge evidence')
    except (KeyError,ValueError) as exc: raise Rejected('application','malformed or incomplete trusted driver result') from exc
    return {'http':rows,'bridge':bridge}

def verify_identity(receipt_path, expected_receipt_sha256, candidate, artifact, cache):
    # The expected digest must come from the protected verifier's handoff, never
    # from a digest stored alongside an untrusted receipt. This is not authority.
    if not re.fullmatch('[0-9a-f]{64}',expected_receipt_sha256) or sha(receipt_path)!=expected_receipt_sha256:
        raise Rejected('identity','receipt does not match independently supplied digest')
    r=json.loads(receipt_path.read_text())
    for name, expected in r.get('logs',{}).items():
        if name not in ['proof.log','build.log','bridge.log','application.log','preflight.log','legacy-bridge.log'] or not (receipt_path.parent/name).is_file() or sha(receipt_path.parent/name)!=expected:
            raise Rejected('identity','required evidence changed')
    if set(r.get('logs',{})) != {'proof.log','build.log','bridge.log','application.log','preflight.log','legacy-bridge.log'}:
        raise Rejected('identity','required evidence missing')
    if r.get('schema')!=1 or r.get('backend')!='lean4-v1' or r.get('observations_consistent') is not True:
        raise Rejected('identity','missing complete verification evidence')
    if r['source']!=snapshot(candidate) or r['protected']!=tree(BASE) or r['evaluator']!=sha(Path(__file__)):
        raise Rejected('identity','source, specification, checker or evaluator changed')
    if r['revision']!=revision(candidate): raise Rejected('identity','revision/dirty state changed; check fresh snapshot')
    check_tools(cache)
    if r['environment']['host_tools']!=host_tools(): raise Rejected('identity','host tool or runtime library changed')
    if r['artifact']!=tree(artifact): raise Rejected('identity','accepted artifact substituted')
    if r['toolchains']!=json.loads((BASE/'toolchain.json').read_text()): raise Rejected('identity','dependencies changed')
    return r

def copy_checked(receipt_path, expected_digest, candidate, artifact, cache, destination):
    r=verify_identity(receipt_path,expected_digest,candidate,artifact,cache)
    if destination.exists(): raise Rejected('output-policy','copy destination exists')
    shutil.copytree(artifact,destination)
    if tree(destination)!=r['artifact']: raise Rejected('identity','copied artifact mismatch')
    # Copy only, never rebuild or start a service. Merge/deploy authority is separate.
    return r

def finish(result,tools,node,candidate,output):
    artifacts=tree(output/'artifact')
    result['application']=application_checks(output/'artifact',tools,node,output)
    if tree(output/'artifact')!=artifacts: raise Rejected('identity','artifact changed while tested')
    if snapshot(candidate)!=result['source'] or tree(BASE)!=result['protected'] or sha(Path(__file__))!=result['evaluator']:
        raise Rejected('identity','source/protected inputs changed during tests')
    result['observations_consistent']=True
    result['logs']={name:sha(output/name) for name in ['proof.log','build.log','bridge.log','application.log','preflight.log','legacy-bridge.log']}
    result['identity_sha256']=digest({k:v for k,v in result.items() if k not in ['formal_seconds','application']})
    receipt=output/'receipt.json';receipt.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return receipt

def main():
    p=argparse.ArgumentParser(); p.add_argument('--candidate',type=Path,default=ROOT/'candidate'); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4'); a=p.parse_args()
    try:
        result,tools,node=evaluate(a.candidate.resolve(),a.output.resolve(),a.cache.resolve())
        receipt=finish(result,tools,node,a.candidate.resolve(),a.output.resolve())
        print(json.dumps({'observations_consistent':True,'policy_admitted':False,'receipt_sha256':sha(receipt),'snapshot_sha256':result['snapshot_sha256'],'receipt':str(receipt)},sort_keys=True))
    except (Rejected,OSError,ValueError) as exc:
        print(str(exc),file=sys.stderr); return 1
    return 0
if __name__=='__main__': sys.exit(main())
