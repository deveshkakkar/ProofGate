#!/usr/bin/env python3
"""Deterministic mutation fixtures; not implementation repairs or evaluator code."""
import argparse,pathlib,shutil,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--destination',type=pathlib.Path,required=True);a=p.parse_args();a.destination.mkdir(parents=True,exist_ok=False);records=[]
for name in ['overallocation','always-reject','duplicate-charge']:
 d=a.destination/name;shutil.copytree(a.candidate,d,ignore=shutil.ignore_patterns('.git','dist','data'))
 if name=='overallocation':
  p=d/'formal/Admission.bend';s=p.read_text();old='M.Response{True{}, 1n+g, b}';assert s.count(old)==1;s=s.replace(old,'M.Response{True{}, 2n+g, b}');p.write_text(s)
 elif name=='always-reject':
  p=d/'formal/Admission.bend';s=p.read_text();p.write_text(s[:s.index('def admission')]+'''def admission(+b: Nat, a: M.Amount) -> M.Response:
  M.Response{False{}, 0n, b}
''')
  p=d/'formal/PROOF.bend';s=p.read_text();p.write_text(s[:s.index('def L.exact_grant')]+'''def L.exact_grant(b, a):
  Unit{}

def L.conservation(b, a):
  add_zero(b)

def L.failure_preservation(b, a, invalid):
  {==}

'''+s[s.index('def L.total_success'):])
 else:
  p=d/'app/server.ts';s=p.read_text();old='      const body = existing.response;';assert s.count(old)==1;s=s.replace(old,'''      // DELIBERATE EXPERIMENTAL MUTATION: charge an already persisted replay.
      const replaySigned = input.amount < 0
        ? { $: 'Neg', pred: -input.amount - 1 }
        : { $: 'Nonneg', magnitude: input.amount };
      const replayDecision = Core.admission(balance(), replaySigned);
      updateState.run(replayDecision.balance);
'''+old);p.write_text(s)
 records.append({'name':name,'files':{str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in d.rglob('*') if p.is_file()}})
(a.destination/'fixtures.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records))
