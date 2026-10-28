#!/usr/bin/env python3
"""Reconstruct exact official Linux x86_64 toolchains without changing system tools.
Run from a packaged baseline/ directory; sibling toolchains/ is download storage.
"""
import hashlib,json,pathlib,platform,shutil,subprocess,tempfile,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent
TOOLS=[
 {'name':'Bend','file':'bend-2.0.39-linux-x64.tar.gz','dir':'bend','url':'https://github.com/bendlang/bend/releases/download/v2.0.39/bend-2.0.39-linux-x64.tar.gz','sha256':'6cf462fd8f70b094a4950ebb709a9c4ffd8f1d1189d9cedf1fd63cd5d041c7ab'},
 {'name':'Lean','file':'lean-4.34.0-linux.tar.zst','dir':'lean-4.34.0-linux','url':'https://github.com/leanprover/lean4/releases/download/v4.34.0/lean-4.34.0-linux.tar.zst','sha256':'caaa98356098c85dc0fcbbd28e1ec66f39eb6551829972b752ff20e1286b646b'},
 {'name':'Node','file':'node-v24.22.1-linux-x64.tar.xz','dir':'node-v24.22.1-linux-x64','url':'https://nodejs.org/dist/v24.22.1/node-v24.22.1-linux-x64.tar.xz','sha256':'6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6'}]

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):raise SystemExit('This pinned experiment requires Linux x86_64; no unsupported platform substitution.')
 for command in ['bwrap','tar','zstd','python3']:
  if not shutil.which(command):raise SystemExit('Missing prerequisite: '+command)
 target=ROOT/'toolchains';target.mkdir(exist_ok=True)
 for t in TOOLS:
  if (target/t['dir']).exists():continue
  archive=target/t['file']
  if not archive.exists():
   with urllib.request.urlopen(t['url'],timeout=120) as src,open(archive,'wb') as dst:shutil.copyfileobj(src,dst)
  if sha(archive)!=t['sha256']:raise SystemExit('Archive hash mismatch: '+t['name'])
  with tempfile.TemporaryDirectory(dir=target,prefix='extract-') as tmp:
   subprocess.run(['tar','-xf',str(archive),'-C',tmp],check=True)
   tree=pathlib.Path(tmp)/t['dir']
   if not tree.is_dir():raise SystemExit('Missing archive root: '+t['name'])
   tree.rename(target/t['dir'])
 import gate
 baseline=pathlib.Path(__file__).resolve().parent
 print(json.dumps({'toolchain_sha256':gate.assert_runtime(baseline,gate.read_json(baseline/'policy.json'))}))
if __name__=='__main__':main()
