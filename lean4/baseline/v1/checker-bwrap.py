#!/usr/bin/python3
"""Lake sandbox adapter: replace its whole-root read mount with system libraries.
Keep Lake's remaining isolation, read-only inputs and .lake-only write grants.
This executable runs before entering the candidate namespace.
"""
import os
from pathlib import Path
import sys
args=sys.argv[1:]
if args[:3] != ['--ro-bind','/','/']:
    raise SystemExit('unsupported Lake sandbox argument layout')
mounts=[]
for path in ['/usr','/bin','/lib','/lib64','/etc/ld.so.cache','/etc/alternatives']:
    if Path(path).exists(): mounts += ['--ro-bind',path,path]
os.execv('/usr/bin/bwrap',['bwrap']+mounts+args[3:])
