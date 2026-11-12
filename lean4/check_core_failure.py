#!/usr/bin/env python3
"""Real executable failure: HTTP 500 must roll back SQLite and allow a later retry."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import gate as g
p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4');a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False)
tools,node=g.check_tools(a.cache.resolve())
spec=importlib.util.spec_from_file_location('trusted_http',g.BASE/'http_tests.py')
http=importlib.util.module_from_spec(spec);spec.loader.exec_module(http)
with tempfile.TemporaryDirectory(prefix='proofgate-core-failure-') as temporary:
    root=Path(temporary);artifact=root/'artifact';shutil.copytree(a.artifact,artifact)
    empty=root/'empty';empty.mkdir()
    prefix=g.sandbox(tools,node,empty,[],network=True)+['--ro-bind',str(artifact),'/out']
    app=http.App(prefix,'/node/bin/node','/out/server.ts')
    try:
        # The server sees read-only artifacts. Only the trusted test owner changes
        # this disposable copy's execute mode to induce a genuine EACCES failure.
        (artifact/'core').chmod(0o644)
        app.start()
        assert app.reserve('retry-after-core-failure',30)==(500,{'error':'internal_error'})
        assert app.balance()==100
        (artifact/'core').chmod(0o755)
        first=app.reserve('retry-after-core-failure',30)
        http.assert_result(first,True,30,70)
        assert app.reserve('retry-after-core-failure',30)==first
        app.stop();app.start()
        assert app.balance()==70
        assert app.reserve('retry-after-core-failure',30)==first
        result={'case':'core-execution-failure','passed':True,'observed':'EACCES -> HTTP 500, rollback, successful retry, persistence/restart'}
        (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    finally: app.close()
