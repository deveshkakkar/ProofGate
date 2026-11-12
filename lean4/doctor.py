#!/usr/bin/env python3
"""Read-only host/toolchain preflight, plus temporary actual isolation probes."""
import argparse
import json
from pathlib import Path
import platform
import tempfile
import gate as g
p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4');a=p.parse_args()
try:
    if (platform.system(),platform.machine())!=('Linux','x86_64'):raise g.Rejected('infrastructure','Linux x86_64 required')
    tools,node=g.check_tools(a.cache.resolve())
    with tempfile.TemporaryDirectory(prefix='proofgate-lean-doctor-') as tmp:
        root=Path(tmp);project=root/'project';project.mkdir()
        g.run(g.scope()+g.sandbox(tools,node,project,[])+['/bin/true'],root,root/'runtime.log',timeout=15)
        g.run(g.scope()+[str(g.BASE/'checker-bwrap.py'),'--ro-bind','/','/',
               '--unshare-all','--die-with-parent','--proc','/proc','--dev','/dev',
               '--tmpfs','/tmp','--tmpfs','/home','--tmpfs','/root','--','/bin/true'],root,root/'proof.log',timeout=15)
    print(json.dumps({'prerequisites':'passed','formal_verification':False,'policy_admitted':False}))
except (g.Rejected,OSError,ValueError) as exc:
    raise SystemExit(f'Preflight failed: {exc}')
