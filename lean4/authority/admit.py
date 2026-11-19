#!/usr/bin/env python3
"""Authenticate a frozen bundle and copy its exact artifact. Never merge or run it."""
import argparse
import ctypes
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from common import (GitHub, Rejected, adoption, canonical, current_adoption, decode,
                    need, sha, source_identity, successful_run, verify_certificate)
from bundle import MAX, unpack, validate


def private_root(path):
    path = Path(path)
    need(path.is_absolute(), 'adoption-path-absolute')
    for part in [path,*path.parents]:
        info = part.lstat()
        need(not stat.S_ISLNK(info.st_mode) and info.st_uid in [0,os.getuid()] and
             not info.st_mode & 0o022, 'adoption-path-owner-permissions')
    need(path.is_file() and path.stat().st_uid == os.getuid() and
         path.stat().st_mode & 0o077 == 0, 'adoption-file-private')
    return adoption(decode(path.read_bytes()))


def bounded(path, maximum):
    with Path(path).open('rb') as f:
        raw = f.read(maximum+1)
    need(len(raw) <= maximum, 'input-bound')
    return raw


def admit(api, adopted, number, archive, attestation, destination):
    # Capture input bytes once. Authentication and parsing use that same private
    # frozen copy; caller-side substitutions cannot change the accepted bytes.
    raw = bounded(archive, MAX); signature = bounded(attestation, 4*1024*1024)
    current_adoption(api, adopted)
    with tempfile.TemporaryDirectory(prefix='proofgate-auth-') as tmp:
        frozen = Path(tmp)/'reservation-bundle.zip'; frozen.write_bytes(raw)
        sig = Path(tmp)/'attestation.json'; sig.write_bytes(signature)
        report = api.authenticate(frozen, sig, adopted)  # fail before parsing untrusted ZIP
    files = unpack(raw); result, receipt = validate(files, adopted)
    need(result['source']['pr'] == number, 'requested-pr-mismatch')
    invocation = verify_certificate(report, adopted, sha(raw), result['execution'])
    successful_run(api, result['execution'], adopted)
    current_adoption(api, adopted)
    need(source_identity(api, number) == result['source'], 'stale-head-base-or-source')
    destination = Path(destination)
    # Caller must select an owner-controlled destination outside candidate access.
    # No replace, rebuild, service start, GitHub status or merge operation exists.
    parent = destination.parent.resolve(strict=True)
    need(destination.is_absolute() and parent == destination.parent and
         parent.stat().st_uid == os.getuid() and not parent.stat().st_mode & 0o022,
         'accepted-output-parent')
    decision = {'schema':1,'observations_consistent':True,'producer_authenticated':True,
                'policy_admitted':True,'merge_eligible':False,'bundle_sha256':sha(raw),
                'receipt_sha256':sha(files['receipt.json']),'source':result['source'],
                'adoption':adopted,'execution':result['execution'],'invocation':invocation,
                'artifact':receipt['artifact']}
    staging = Path(tempfile.mkdtemp(prefix='.proofgate-admit-',dir=parent))
    try:
        for name, entry in receipt['artifact'].items():
            target = staging/name
            with target.open('xb') as out:
                out.write(files['artifact/'+name])
            target.chmod(0o755 if entry['executable'] else 0o644)
            need(sha(target.read_bytes()) == entry['sha256'], 'accepted-copy-mismatch')
        (staging/'admission.json').write_bytes(canonical(decision))
        successful_run(api, result['execution'], adopted)
        current_adoption(api, adopted)
        need(source_identity(api, number) == result['source'], 'freshness-changed-before-copy')
        # Exclusive destination creation prevents overwrite even under concurrency.
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
        rename.restype = ctypes.c_int
        need(rename(-100, os.fsencode(staging), -100, os.fsencode(destination), 1) == 0,
             'accepted-destination-exists-or-atomic-rename-unavailable')
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return decision


def main():
    p = argparse.ArgumentParser(); p.add_argument('--gh',type=Path,required=True)
    p.add_argument('--adoption',type=Path,required=True); p.add_argument('--pr',type=int,required=True)
    p.add_argument('--archive',type=Path,required=True); p.add_argument('--attestation',type=Path,required=True)
    p.add_argument('--destination',type=Path,required=True); a = p.parse_args()
    try:
        result = admit(GitHub(a.gh), private_root(a.adoption), a.pr, a.archive, a.attestation, a.destination)
        print(canonical(result).decode())
    except (Rejected,OSError,ValueError,KeyError,TypeError) as exc:
        print('admission-rejected: '+type(exc).__name__,file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
