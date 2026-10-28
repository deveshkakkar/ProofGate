#!/usr/bin/env python3
"""Durable LOCAL PROCESS supervisor demo. Not a model/context restart claim."""
import argparse,hashlib,json,os,pathlib,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--work',type=pathlib.Path,required=True);p.add_argument('--baseline',type=pathlib.Path);p.add_argument('--baseline-sha256');p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--resume',action='store_true');a=p.parse_args();w=a.work.resolve();w.mkdir(parents=True,exist_ok=True);cp=w/'checkpoint.json';events=w/'events.jsonl'
def emit(kind,**kw):
 with events.open('a') as f:f.write(json.dumps(dict(event=kind,pid=os.getpid(),at=time.time(),**kw))+'\n');f.flush();os.fsync(f.fileno())
def save(s):
 q=cp.with_suffix('.tmp');q.write_text(json.dumps(s,indent=2)+'\n')
 with q.open('r+') as f:os.fsync(f.fileno())
 os.replace(q,cp)
def command(argv,log):
 emit('command_started',argv=argv)
 with (w/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
 emit('command_finished',exit_code=r.returncode,log=log)
 if r.returncode:raise RuntimeError('supervised command failed; see '+log)
if not a.resume:
 if cp.exists():raise SystemExit('checkpoint exists; refuse replay; use --resume')
 if not all([a.baseline,a.baseline_sha256,a.candidate]):raise SystemExit('initial arguments missing')
 s=dict(schema=1,phase='evaluating',initial_pid=os.getpid(),baseline=str(a.baseline.resolve()),baseline_sha256=a.baseline_sha256,candidate=str(a.candidate.resolve()),run=str(w/'accepted-run'),deployment=str(w/'deployment'))
 save(s);emit('initial_process')
 command([sys.executable,s['baseline']+'/gate.py','evaluate','--baseline',s['baseline'],'--baseline-sha256',s['baseline_sha256'],'--candidate',s['candidate'],'--destination',s['run']],'evaluate.log')
 r=json.loads((pathlib.Path(s['run'])/'result.json').read_text())
 if r.get('accepted') is not True:raise SystemExit('not accepted')
 s.update(phase='waiting_before_deployment',source_sha256=r['source_sha256'],artifact_sha256=r['artifact_sha256'],accepted_result_sha256=hashlib.sha256((pathlib.Path(s['run'])/'result.json').read_bytes()).hexdigest());save(s);emit('checkpoint_waiting',source_sha256=s['source_sha256'],artifact_sha256=s['artifact_sha256'])
 print(json.dumps(dict(waiting=True,pid=os.getpid(),checkpoint=str(cp))),flush=True)
 while True:time.sleep(60)
else:
 s=json.loads(cp.read_text())
 if s['phase']!='waiting_before_deployment':raise SystemExit('checkpoint not resumable; refuse replay')
 if s['initial_pid']==os.getpid():raise SystemExit('not new process')
 if hashlib.sha256((pathlib.Path(s['run'])/'result.json').read_bytes()).hexdigest()!=s['accepted_result_sha256']:raise SystemExit('accepted record changed')
 emit('resumed_new_process',prior_pid=s['initial_pid'],preserved_source_sha256=s['source_sha256'],preserved_artifact_sha256=s['artifact_sha256'],evaluation_replayed=False)
 command([sys.executable,s['baseline']+'/gate.py','deploy','--baseline',s['baseline'],'--baseline-sha256',s['baseline_sha256'],'--run',s['run'],'--destination',s['deployment']],'deploy.log')
 receipt=json.loads((pathlib.Path(s['deployment'])/'deployment.json').read_text())
 if receipt['artifact_sha256']!=s['artifact_sha256'] or receipt['source_sha256']!=s['source_sha256']:raise SystemExit('identity mismatch')
 s.update(phase='deployed',resume_pid=os.getpid(),evaluation_replayed=False);save(s);emit('deployment_complete',artifact_sha256=s['artifact_sha256']);print(json.dumps(s),flush=True)
