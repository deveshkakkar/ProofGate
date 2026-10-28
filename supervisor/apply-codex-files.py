#!/usr/bin/env python3
"""Trusted, non-executing candidate-only file interface. Never accepts shell output."""
import argparse, json, os, pathlib, tempfile, hashlib, datetime
ROOT=pathlib.Path('/workspace/scratch/95589aefb3bf/proofgate').resolve()
CANDIDATE=ROOT/'candidate'
INITIAL={'formal/Model.bend','formal/LAWS.bend','formal/Admission.bend','formal/PROOF.bend','formal/INTERFACE.md','app/server.ts','README.md','package.json','IMPLEMENTATION-CHECKPOINT.json'}
REPAIR={'formal/Admission.bend','formal/PROOF.bend','app/server.ts'}
def validate(payload, allowed):
 if not isinstance(payload,dict) or set(payload)!= {'summary','files','checksToRun','limitations'}: raise ValueError('invalid top-level schema')
 if not isinstance(payload['summary'],str): raise ValueError('summary must be string')
 for k in ('checksToRun','limitations'):
  if not isinstance(payload[k],list) or not all(isinstance(v,str) for v in payload[k]): raise ValueError('invalid metadata')
 if not isinstance(payload['files'],list) or not 1<=len(payload['files'])<=20: raise ValueError('invalid files array')
 seen=set(); result=[]
 for f in payload['files']:
  if not isinstance(f,dict) or set(f)!= {'path','content'}: raise ValueError('invalid file schema')
  p,c=f['path'],f['content']
  if not isinstance(p,str) or not isinstance(c,str) or len(c.encode())>1000000: raise ValueError('invalid file fields')
  if p not in allowed or p in seen or '\\' in p or '\x00' in p: raise ValueError('path not allowlisted or duplicate')
  rel=pathlib.PurePosixPath(p)
  if rel.is_absolute() or any(x in ('..','.','') for x in rel.parts) or str(rel)!=p: raise ValueError('noncanonical path')
  target=CANDIDATE/p
  for node in (target,*target.parents):
   if node==CANDIDATE.parent: break
   if node.is_symlink(): raise ValueError('symlink path prohibited')
  if not target.resolve().is_relative_to(CANDIDATE): raise ValueError('escaped candidate')
  if target.exists() and not target.is_file(): raise ValueError('destination not regular file')
  seen.add(p);result.append((p,c,target))
 return result

def apply(payload,mode):
 files=validate(payload, INITIAL if mode=='initial' else REPAIR)
 records=[]
 for name,content,target in files:
  before=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
  target.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(prefix='.codex-',dir=target.parent)
  try:
   with os.fdopen(fd,'w') as w: w.write(content);w.flush();os.fsync(w.fileno())
   os.replace(tmp,target)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
  records.append({'path':name,'beforeSha256':before,'afterSha256':hashlib.sha256(target.read_bytes()).hexdigest()})
 return {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':mode,'files':records,'metadataCommandsExecuted':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('response');p.add_argument('--mode',choices=['initial','repair'],required=True);p.add_argument('--record',required=True);a=p.parse_args()
 response=json.loads(pathlib.Path(a.response).read_text())
 record=apply(response,a.mode);pathlib.Path(a.record).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
