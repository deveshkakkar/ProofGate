#!/usr/bin/env python3
"""Smoke exact deployed bytes in private loopback process, DB separate and durable."""
import argparse,hashlib,importlib.util,json,os,pathlib,subprocess,time,urllib.request,urllib.error,socket,sys
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--deployment',type=pathlib.Path,required=True);p.add_argument('--baseline',type=pathlib.Path,required=True);a=p.parse_args();d=a.deployment.resolve();b=a.baseline.resolve()
spec=importlib.util.spec_from_file_location('gate',b/'gate.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
receipt=json.loads((d/'deployment.json').read_text());original=gate.files_manifest(d/'artifact')
assert original==receipt['artifact_files']
state=d/'state';state.mkdir(exist_ok=True);log=d/'service.log';events=[];policy=json.loads((b/'policy.json').read_text())
# Root-empty evaluator sandbox; deployed artifact is read-only, only DB state writable.
prefix=gate.sandbox_prefix(d/'artifact',b,d/'artifact',policy,writable=False)
def call(port,path,body=None):
 r=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
 try:x=urllib.request.urlopen(r,timeout=10)
 except urllib.error.HTTPError as e:x=e
 v=(x.status,json.loads(x.read()));events.append({'path':path,'request':body,'status':v[0],'body':v[1]});return v
def start():
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 f=log.open('ab');cmd=prefix+['--bind',str(state),'/data','--setenv','PORT',str(port),'--setenv','DB_PATH','/data/demo.sqlite',policy['node_guest'],'/out/server.ts'];proc=subprocess.Popen(cmd,stdout=f,stderr=f)
 for _ in range(100):
  if proc.poll() is not None:raise RuntimeError(log.read_text())
  try:
   r=urllib.request.urlopen(f'http://127.0.0.1:{port}/status',timeout=1)
   if r.status==200:return proc,f,port
  except OSError:time.sleep(.05)
 raise RuntimeError('readiness timeout')
def stop(proc,f):
 proc.terminate()
 try:proc.wait(timeout=5)
 except subprocess.TimeoutExpired:proc.kill();proc.wait()
 f.close()
proc,f,port=start()
try:
 assert call(port,'/status')==(200,{'balance':100})
 first=call(port,'/reserve',{'requestId':'demo-first','amount':30});assert first[0]==200 and first[1]['balance']==70
 rejected=call(port,'/reserve',{'requestId':'demo-rejected','amount':100});assert rejected[1]['success'] is False
 assert call(port,'/reserve',{'requestId':'demo-first','amount':30})==first
 assert call(port,'/reserve',{'requestId':'demo-first','amount':31})==(409,{'error':'conflict'})
finally:stop(proc,f)
proc,f,port=start()
try:
 assert call(port,'/status')==(200,{'balance':70})
 assert call(port,'/reserve',{'requestId':'demo-first','amount':30})==first
 assert call(port,'/reserve',{'requestId':'demo-rejected','amount':100})==rejected
finally:stop(proc,f)
assert gate.files_manifest(d/'artifact')==original
report={'passed':True,'artifact_sha256':receipt['artifact_sha256'],'source_sha256':receipt['source_sha256'],'rebuilt':False,'artifact_unchanged':True,'process_restart':True,'private_binding':'127.0.0.1','persistent_database':str(state/'demo.sqlite'),'events':events}
(d/'smoke.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
