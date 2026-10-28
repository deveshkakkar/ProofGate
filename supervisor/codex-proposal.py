#!/usr/bin/env python3
"""Capture actual CLI output/status then parse non-executable structured proposal."""
import argparse,datetime,hashlib,json,pathlib,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--session',required=True);p.add_argument('--prompt',type=pathlib.Path,required=True);p.add_argument('--prefix',type=pathlib.Path,required=True);a=p.parse_args();root=pathlib.Path(__file__).resolve().parent.parent
argv=[str(root/'supervisor/run-codex.sh'),'--output-schema',str(root/'evidence/codex-files-schema.json'),'resume',a.session,'-'];t=time.time()
with a.prompt.open('rb') as prompt, a.prefix.with_suffix('.jsonl').open('wb') as log:
 r=subprocess.run(argv,stdin=prompt,stdout=log,stderr=subprocess.STDOUT,timeout=600)
rows=[]
for line in a.prefix.with_suffix('.jsonl').read_text().splitlines():
 try:rows.append(json.loads(line))
 except json.JSONDecodeError:pass
messages=[x['item']['text'] for x in rows if x.get('item',{}).get('type')=='agent_message'];turns=[x for x in rows if x.get('type')=='turn.completed']
record={'session':a.session,'exit_code':r.returncode,'started_unix':t,'elapsed_seconds':time.time()-t,'prompt_sha256':hashlib.sha256(a.prompt.read_bytes()).hexdigest(),'raw_log_sha256':hashlib.sha256(a.prefix.with_suffix('.jsonl').read_bytes()).hexdigest(),'completed_turns':turns,'command_items':[x for x in rows if x.get('item',{}).get('type') in ['command_execution','mcp_tool_call']]}
a.prefix.with_suffix('.receipt.json').write_text(json.dumps(record,indent=2)+'\n')
if r.returncode!=0 or len(messages)!=1 or len(turns)!=1 or record['command_items']:raise SystemExit('CLI failed or unexpected tool/message/completion shape; do not apply')
proposal=json.loads(messages[0]);a.prefix.with_suffix('.files.json').write_text(json.dumps(proposal,indent=2)+'\n');print(json.dumps(record))
