"""Sanitized installed-environment identifiers; no configuration or URL export."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def tree_id(root):
    digest = hashlib.sha256();count = 0
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in ('.git', '__pycache__', 'node_modules') for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('unsupported identity tree symlink')
        if path.is_file():
            count += 1
            if count > 200000:
                raise ValueError('identity file bound')
            value = hashlib.sha256(path.read_bytes()).hexdigest()
            digest.update(json.dumps([relative.as_posix(), value], separators=(',', ':')).encode() + b'\n')
    return {'sha256': digest.hexdigest(), 'files': count}


def main():
    packages = sorted([{'name': dist.metadata['Name'], 'version': dist.version}
                       for dist in importlib.metadata.distributions()], key=lambda d: (d['name'], d['version']))
    binaries = {}
    for name, flag in [('bench', '--version'), ('node', '--version'), ('mariadbd', '--version'), ('redis-server', '--version')]:
        path = Path(shutil.which(name)).resolve()
        result = subprocess.run([str(path), flag], capture_output=True, text=True, timeout=15, check=True)
        binaries[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'version': result.stdout.strip()[:1024]}
    result = {'schema': 1, 'python': platform.python_version(),
              'python_sha256': hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
              'packages': packages, 'binaries': binaries}
    # sys.prefix reliably identifies the venv; stdlib may live outside it.
    candidates = list((Path(sys.prefix) / 'lib').glob('python*/site-packages'))
    if len(candidates) != 1:
        raise ValueError('ambiguous virtual environment package tree')
    result['site_packages'] = tree_id(candidates[0])
    Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
