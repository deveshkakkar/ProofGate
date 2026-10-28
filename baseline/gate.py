#!/usr/bin/env python3
"""Independent evaluator. Configuration is accepted only from a reviewed frozen baseline.
The candidate cannot supply commands or acceptance reports. This process lives outside
its execution namespace. See README for trust assumptions and limitations.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, signal, subprocess, sys, time, uuid

SCHEMA = 1
REQUIRED_CHECKS = ('formal', 'build', 'bridge', 'application')
ROOT = pathlib.Path(__file__).resolve().parent

def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
def digest(data): return hashlib.sha256(data).hexdigest()
def digest_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def read_json(path): return json.loads(pathlib.Path(path).read_text())
def write_json(path, value): pathlib.Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
def relative(path):
    p=pathlib.PurePosixPath(path)
    if not path or p.is_absolute() or '..' in p.parts or '.' in p.parts: raise ValueError('unsafe relative path')
    return p

def files_manifest(root, exclude=()):
    root=pathlib.Path(root); result={}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if rel in exclude or any(part=='.git' for part in p.relative_to(root).parts): continue
        if p.is_symlink(): raise ValueError(f'symlink prohibited: {rel}')
        if p.is_file(): result[rel]=digest_file(p)
        elif not p.is_dir(): raise ValueError(f'nonregular path prohibited: {rel}')
    return result

def runtime_manifest(root):
    root=pathlib.Path(root).resolve();result={}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():
            resolved=p.resolve()
            if resolved!=root and root not in resolved.parents: raise ValueError('runtime symlink escapes tree')
            result[rel]={'symlink':os.readlink(p)}
        elif p.is_file():result[rel]={'sha256':digest_file(p)}
    return result

def assert_runtime(baseline,policy):
    lock=read_json(baseline/'toolchain-lock.json')
    if len(lock)!=len(policy['runtime_mounts']): raise ValueError('toolchain lock incomplete')
    for item,expected in zip(policy['runtime_mounts'],lock):
        if expected['host_relative']!=item['host_relative'] or expected['guest']!=item['guest']: raise ValueError('runtime mount changed')
        if runtime_manifest(baseline.parent/relative(item['host_relative']))!=expected['files']: raise ValueError('toolchain changed: '+item['guest'])
    return digest(canonical(lock))

def assert_baseline(baseline, expected):
    manifest=read_json(baseline/'frozen.json')
    if manifest.get('schema')!=SCHEMA or manifest.get('review',{}).get('approved') is not True:
        raise ValueError('baseline lacks approved independent review')
    if digest(canonical(manifest))!=expected: raise ValueError('baseline identity mismatch')
    actual=files_manifest(baseline, ('frozen.json',))
    if actual != manifest.get('files'): raise ValueError('baseline content altered, removed, or added')
    return manifest

def check_policy(policy):
    if policy.get('schema')!=SCHEMA: raise ValueError('unsupported policy schema')
    checks=policy.get('checks')
    if not isinstance(checks,list) or tuple(c.get('id') for c in checks)!=REQUIRED_CHECKS:
        raise ValueError('required checks missing, reordered, duplicated, or disabled')
    if any(c.get('enabled',True) is not True for c in checks): raise ValueError('disabled required check')
    for c in checks:
        if not isinstance(c.get('argv'),list) or not c['argv'] or not all(isinstance(a,str) for a in c['argv']):
            raise ValueError('malformed command')
        if not 0 < c.get('timeout_seconds',0) <= 1800: raise ValueError('invalid check timeout')
        if c.get('parser') not in ('marker','json-tests'): raise ValueError('unsupported verification parser')
    if not policy.get('source_files') or not policy.get('artifact_files'): raise ValueError('empty source/artifact specification')
    for f in policy['source_files'] + policy['artifact_files']: relative(f)
    for target,source in policy.get('protected_overlays',{}).items(): relative(target);relative(source)
    if set(policy['source_files']) & set(policy.get('protected_overlays',{})): raise ValueError('candidate owns protected overlay')
    if not policy.get('required_laws') or len(policy['required_laws'])!=4: raise ValueError('four obligations required')

def validate_formal(source, policy):
    allowed=set(policy['allowed_formal_imports'])
    for name in ['formal/Admission.bend','formal/PROOF.bend']:
        text=(source/name).read_text()
        # Deliberately narrow source language for this POC. This is not a general
        # Bend security parser, and does not replace the checker/kernel.
        if re.search(r'@|\bIO\b|\bforeign\b',text): raise ValueError('unsupported unsafe/effectful formal source')
        for line in text.splitlines():
            stripped=line.split('#',1)[0].strip()
            if stripped.startswith('import '):
                token=stripped.split()[1]
                if token not in allowed: raise ValueError('unapproved semantic import: '+token)
    laws=(source/'formal/LAWS.bend').read_text()
    names=re.findall(r'^law\s+([A-Za-z_][A-Za-z0-9_]*)\s*:',laws,re.M)
    if names!=policy['required_laws']: raise ValueError('required law inventory mismatch')


def parse_check(check, raw):
    text=raw.decode('utf-8',errors='strict')
    if check['parser']=='marker':
        marker=check.get('required_marker')
        if not marker or text.splitlines().count(marker)!=1: raise ValueError('missing or duplicate verification marker')
        return {'marker':marker}
    lines=[x for x in text.splitlines() if x.strip()]
    if not lines: raise ValueError('empty test report')
    report=json.loads(lines[-1])
    if not isinstance(report,dict) or report.get('schema')!=1: raise ValueError('malformed test report schema')
    expected=check.get('required_tests')
    rows=report.get('tests')
    if not expected or not isinstance(rows,list) or [x.get('id') for x in rows]!=expected:
        raise ValueError('missing/extra/duplicate/reordered tests')
    if any(set(x)!= {'id','status'} or x['status']!='passed' for x in rows): raise ValueError('failed or skipped test')
    return report


def sandbox_prefix(source, baseline, output, policy, writable=True):
    # Root is an empty bwrap tmpfs. Only runtime libraries and reviewed toolchains
    # are visible. No home, parent PID namespace, auth, repo sibling, or receipts.
    args=['/usr/bin/bwrap','--unshare-user','--unshare-pid','--new-session','--die-with-parent','--cap-drop','ALL',
          '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/etc','--dir','/opt','--dir','/work']
    for path in ('/usr','/bin','/lib','/lib64'):
        if pathlib.Path(path).exists(): args+=['--ro-bind',path,path]
    for path in ('/etc/ld.so.cache','/etc/localtime'):
        if pathlib.Path(path).exists(): args+=['--ro-bind',path,path]
    for item in policy['runtime_mounts']:
        args+=['--ro-bind',str(baseline.parent/relative(item['host_relative'])),item['guest']]
    args+=['--ro-bind',str(source),'/src','--ro-bind',str(baseline),'/baseline',
           ('--bind' if writable else '--ro-bind'),str(output),'/out','--chdir','/src','--clearenv',
           '--setenv','HOME','/tmp','--setenv','PATH',policy['path'],
           '--setenv','BEND_NO_TELEMETRY','1','--setenv','LANG','C.UTF-8',
           '--setenv','TZ','UTC','--setenv','SOURCE_DATE_EPOCH','0']
    return args


def run_check(check, prefix, evidence, fault, host_argv=None):
    cid=check['id']; argv=host_argv or prefix+check['argv']; started=time.time()
    result={'id':cid,'status':'failed','argv':check['argv'],'started_unix':started,'timeout_seconds':check['timeout_seconds']}
    try:
        # Fault injection is evaluator-controlled and can never return acceptance.
        if fault=='unavailable' and cid=='formal': argv=prefix+['/intentionally-missing-proofgate-checker']
        if fault=='timeout' and cid=='formal':
            argv=prefix+['/bin/sleep','5']; timeout=0.1
        else: timeout=check['timeout_seconds']
        result['executed_argv']=argv
        with open(evidence/f'{cid}.stdout','wb') as out, open(evidence/f'{cid}.stderr','wb') as err:
            proc=subprocess.Popen(argv,stdout=out,stderr=err,start_new_session=True)
            try: result['exit_code']=proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait();result['exit_code']=None
                raise TimeoutError('checker timed out')
        if result['exit_code']!=0: raise RuntimeError(f'checker exited {result["exit_code"]}')
        result['parsed']=parse_check(check,(evidence/f'{cid}.stdout').read_bytes())
        result['status']='passed'
    except Exception as exc: result['error']=f'{type(exc).__name__}: {exc}'
    result['elapsed_seconds']=round(time.time()-started,6)
    for stream in ('stdout','stderr'):
        p=evidence/f'{cid}.{stream}'
        if p.exists(): result[stream+'_sha256']=digest_file(p)
    return result


def evaluate(candidate, baseline, expected, destination, fault=None):
    if destination==candidate or candidate in destination.parents or destination==baseline or baseline in destination.parents: raise ValueError('run output must be outside candidate and baseline')
    if baseline==candidate or candidate in baseline.parents: raise ValueError('baseline cannot be candidate-owned')
    destination.mkdir(parents=True,exist_ok=False)
    evidence=destination/'logs';evidence.mkdir();source=destination/'source';source.mkdir();output=destination/'artifact';output.mkdir()
    record={'schema':SCHEMA,'run_id':destination.name,'accepted':False,'fault_injection':fault,'checks':[], 'started_unix':time.time()}
    try:
        manifest=assert_baseline(baseline,expected);policy=read_json(baseline/'policy.json');check_policy(policy)
        record['baseline_sha256']=expected;record['review']=manifest['review'];record['toolchain_sha256']=assert_runtime(baseline,policy)
        for name in policy['source_files']:
            src=candidate/relative(name)
            if src.is_symlink() or not src.is_file() or candidate.resolve() not in src.resolve().parents: raise ValueError('missing/unsafe candidate source: '+name)
            dst=source/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        for target,name in policy.get('protected_overlays',{}).items():
            src=baseline/relative(name);dst=source/target;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        validate_formal(source,policy)
        source_manifest=files_manifest(source);record['source_files']=source_manifest;record['source_sha256']=digest(canonical(source_manifest))
        record['candidate_dirty']=bool(subprocess.run(['git','-C',str(candidate),'status','--porcelain'],capture_output=True,text=True).stdout.strip())
        record['candidate_commit']=subprocess.run(['git','-C',str(candidate),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip() or None
        built_manifest=None
        for check in policy['checks']:
            host_argv=None
            if check['id']=='application':
                test_prefix=sandbox_prefix(source,baseline,output,policy,writable=False)
                host_argv=['/usr/bin/python3',str(baseline/'http_tests.py'),'--prefix-json',json.dumps(test_prefix),'--node',policy['node_guest'],'--entry','/out/server.ts']
            row=run_check(check,sandbox_prefix(source,baseline,output,policy,writable=check['id']=='build'),evidence,fault,host_argv);record['checks'].append(row)
            if row['status']!='passed': break
            if check['id']=='build':
                built_manifest=files_manifest(output)
                if set(built_manifest)!=set(policy['artifact_files']): raise ValueError('missing or extra built artifact files')
                record['built_files']=built_manifest
            elif check['id'] in ('bridge','application') and files_manifest(output)!=built_manifest: raise ValueError('built artifact changed during testing')
        if tuple(x['id'] for x in record['checks'])!=REQUIRED_CHECKS or any(x['status']!='passed' for x in record['checks']):
            raise ValueError('not every required check passed')
        if fault: raise ValueError('intentional fault run cannot accept')
        assert_baseline(baseline,expected)
        if assert_runtime(baseline,policy)!=record['toolchain_sha256']: raise ValueError('toolchain changed during evaluation')
        if files_manifest(source)!=source_manifest: raise ValueError('evaluated source changed')
        artifact_manifest=files_manifest(output)
        if set(artifact_manifest)!=set(policy['artifact_files']): raise ValueError('missing or extra artifact files')
        record['artifact_files']=artifact_manifest;record['artifact_sha256']=digest(canonical(artifact_manifest));record['accepted']=True
    except Exception as exc: record['error']=f'{type(exc).__name__}: {exc}'
    record['elapsed_seconds']=round(time.time()-record['started_unix'],6)
    write_json(destination/'result.json',record)
    return record


def deploy(run, baseline, expected, destination):
    assert_baseline(baseline,expected);record=read_json(run/'result.json');policy=read_json(baseline/'policy.json');check_policy(policy)
    if record.get('accepted') is not True or record.get('fault_injection') or record.get('baseline_sha256')!=expected: raise ValueError('no accepted record')
    if tuple(x['id'] for x in record.get('checks',[]))!=REQUIRED_CHECKS or any(x.get('status')!='passed' for x in record['checks']): raise ValueError('incomplete accepted record')
    if assert_runtime(baseline,policy)!=record.get('toolchain_sha256'): raise ValueError('runtime changed after evaluation')
    actual=files_manifest(run/'artifact')
    if actual!=record.get('artifact_files') or digest(canonical(actual))!=record.get('artifact_sha256'): raise ValueError('artifact changed after acceptance')
    if files_manifest(run/'source')!=record.get('source_files'): raise ValueError('source changed after acceptance')
    destination.mkdir(parents=True,exist_ok=False)
    shutil.copytree(run/'artifact',destination/'artifact')
    if files_manifest(destination/'artifact')!=actual: raise ValueError('deployed artifact differs')
    receipt={'schema':1,'source_sha256':record['source_sha256'],'artifact_sha256':record['artifact_sha256'],
             'artifact_files':actual,'baseline_sha256':expected,'evaluation_run':str(run.resolve()),'rebuilt':False,'deployed_unix':time.time()}
    write_json(destination/'deployment.json',receipt);return receipt


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    for name in ('evaluate','deploy'):
        s=sub.add_parser(name);s.add_argument('--baseline',type=pathlib.Path,required=True);s.add_argument('--baseline-sha256',required=True);s.add_argument('--destination',type=pathlib.Path,required=True)
        if name=='evaluate':s.add_argument('--candidate',type=pathlib.Path,required=True);s.add_argument('--fault',choices=['unavailable','timeout'])
        else:s.add_argument('--run',type=pathlib.Path,required=True)
    a=p.parse_args()
    if a.command=='evaluate':r=evaluate(a.candidate.resolve(),a.baseline.resolve(),a.baseline_sha256,a.destination.resolve(),a.fault)
    else:r=deploy(a.run.resolve(),a.baseline.resolve(),a.baseline_sha256,a.destination.resolve())
    print(json.dumps(r,sort_keys=True));return 0 if (r.get('accepted') or a.command=='deploy') else 1
if __name__=='__main__': sys.exit(main())
