"""Verify unprivileged host identity, forbid exec gains and bound output."""
import ctypes
import os
from pathlib import Path
import resource
import sys


def ensure_unprivileged():
    uids, gids = os.getresuid(), os.getresgid()
    if len(set(uids)) != 1 or 0 in uids or len(set(gids)) != 1 or 0 in gids:
        raise PermissionError('Real/effective/saved UID and GID must be the unprivileged caller')
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    if any(int(status[field].strip(), 16) != 0 for field in ('CapEff', 'CapPrm', 'CapAmb')):
        raise PermissionError('Host effective, permitted and ambient capabilities must be empty')


def main():
    ensure_unprivileged()
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    prctl.restype = ctypes.c_int
    if prctl(38, 1, 0, 0, 0) != 0:  # Linux PR_SET_NO_NEW_PRIVS
        raise OSError(ctypes.get_errno(), 'Cannot prohibit privilege gains')
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    os.execv(sys.argv[1], sys.argv[1:])


if __name__ == '__main__':
    main()
