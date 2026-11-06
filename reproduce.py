#!/usr/bin/env python3
"""Reproduce frozen gate, negative experiments and exact-artifact private smoke.
The recorded Codex author/repair sessions are evidence, not replayed model calls.
"""
import argparse,datetime,json,os,pathlib,shutil,subprocess,sys
sys.dont_write_bytecode=True
from scripts.check_host import HostCheckError,check_host
ROOT=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=pathlib.Path);p.add_argument('--skip-bootstrap',action='store_true');a=p.parse_args()
try:check_host(bootstrap=not a.skip_bootstrap)
except HostCheckError as exc:p.exit(1,'Host preflight failed: '+str(exc)+'\n')
BASE=ROOT/'baseline';EXPECTED=(ROOT/'BASELINE.sha256').read_text().strip();OUT=(a.output or ROOT/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('reproduce-%Y%m%dT%H%M%S')).resolve();OUT.mkdir(parents=True,exist_ok=False)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');matrix=[]
def command(argv,label,want=0):
 with (OUT/(label+'.log')).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env)
 if (r.returncode==0)!=(want==0):raise RuntimeError(label+' unexpected exit '+str(r.returncode)+'; see '+str(OUT))
 return r.returncode
def evaluate(label,candidate,fault=None,baseline=BASE):
 dest=OUT/label;argv=[sys.executable,str(BASE/'gate.py'),'evaluate','--baseline',str(baseline),'--baseline-sha256',EXPECTED,'--candidate',str(candidate),'--destination',str(dest)]
 if fault:argv+=['--fault',fault]
 code=command(argv,label,want=0 if label=='valid' else 1);record=json.loads((dest/'result.json').read_text());matrix.append({'case':label,'exit_code':code,'accepted':record['accepted'],'checks':record['checks']});return dest
if not a.skip_bootstrap:command([sys.executable,str(BASE/'bootstrap.py')],'bootstrap')
valid=evaluate('valid',ROOT/'candidate')
command([sys.executable,str(ROOT/'supervisor/prepare-mutations.py'),'--candidate',str(ROOT/'candidate'),'--destination',str(OUT/'mutants')],'prepare-mutants')
for name in ('overallocation','always-reject','duplicate-charge'):evaluate(name,OUT/'mutants'/name)
for fault in ('unavailable','timeout'):evaluate(fault,ROOT/'candidate',fault=fault)
# Copies are deliberately corrupt; the real reviewed baseline remains unchanged.
for label in ('removed-law','disabled-check'):
 bad=OUT/(label+'-baseline');shutil.copytree(BASE,bad)
 if label=='removed-law':(bad/'formal/LAWS.bend').write_text('import Base\n')
 else:
  q=bad/'policy.json';j=json.loads(q.read_text());j['checks'][0]['enabled']=False;q.write_text(json.dumps(j))
 evaluate(label,ROOT/'candidate',baseline=bad)
command([sys.executable,str(BASE/'gate.py'),'deploy','--baseline',str(BASE),'--baseline-sha256',EXPECTED,'--run',str(valid),'--destination',str(OUT/'deployment')],'deploy')
command([sys.executable,str(ROOT/'supervisor/deployment-smoke.py'),'--baseline',str(BASE),'--deployment',str(OUT/'deployment')],'deployment-smoke')
(OUT/'matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
print(json.dumps({'passed':True,'results':str(OUT),'accepted_artifact':json.loads((valid/'result.json').read_text())['artifact_sha256'],'private_demo':'loopback only; smoke process stopped; see README local launch','codex_repair':'recorded session evidence, not replayed by this script'},indent=2))
