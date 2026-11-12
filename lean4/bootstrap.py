#!/usr/bin/env python3
"""Explicit user-local bootstrap. Download only the reviewed archives; no apt/sudo."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import urllib.request
from gate import BASE, Rejected, check_tools, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4');a=p.parse_args()
    if (platform.system(),platform.machine()) != ('Linux','x86_64'): raise Rejected('infrastructure','requires Linux x86_64')
    a.cache.mkdir(parents=True,exist_ok=True)
    for entry in json.loads((BASE/'toolchain.json').read_text()).values():
        if (a.cache/entry['directory']).exists(): continue
        archive=a.cache/entry['archive']
        if not archive.exists():
            with urllib.request.urlopen(entry['url'],timeout=60) as source,archive.open('xb') as dest:
                while block:=source.read(1024*1024): dest.write(block)
        if sha(archive)!=entry['archive_sha256']: raise Rejected('infrastructure','archive digest mismatch')
        with tempfile.TemporaryDirectory(dir=a.cache,prefix='extract-') as temporary:
            subprocess.run(['tar','-xf',str(archive),'-C',temporary],check=True,timeout=180)
            (Path(temporary)/entry['directory']).rename(a.cache/entry['directory'])
    check_tools(a.cache)
    print('Pinned Lean and Node trees verified.')
if __name__=='__main__':
    try: main()
    except (Rejected,OSError,ValueError,subprocess.SubprocessError) as exc:
        print(exc,file=sys.stderr);sys.exit(1)
