#!/usr/bin/env python3
"""Download one pinned public verification binary; never installs system-wide."""
import argparse
import io
from pathlib import Path
import tarfile
import urllib.request
from common import need, pinned_gh, policy, sha


def install(destination):
    destination = Path(destination)
    if destination.exists():
        return pinned_gh(destination)
    lock = policy()['gh']
    with urllib.request.urlopen(lock['archive_url'], timeout=90) as response:
        archive = response.read(64*1024*1024+1)
    need(len(archive) <= 64*1024*1024 and sha(archive) == lock['archive_sha256'], 'gh-archive-pin')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        members = [m for m in tar.getmembers() if m.name == lock['member']]
        need(len(members) == 1 and members[0].isfile() and members[0].size <= 64*1024*1024, 'gh-archive-member')
        raw = tar.extractfile(members[0]).read()
    need(sha(raw) == lock['binary_sha256'], 'gh-binary-pin')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as out:
        out.write(raw)
    destination.chmod(0o755)
    return pinned_gh(destination)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    print(install(p.parse_args().output))
