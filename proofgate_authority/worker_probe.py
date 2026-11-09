"""Fixed credential-free probe executed only inside the bounded Linux worker."""
import json
import os
from pathlib import Path
import sys

ENV_NAMES = ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_ENTERPRISE_TOKEN', 'GITHUB_ENTERPRISE_TOKEN',
             'SSH_AUTH_SOCK', 'GIT_ASKPASS', 'SSH_ASKPASS', 'PROOFGATE_OWNER_CONTEXT_CANARY')


def main():
    rows = json.load(sys.stdin)
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError('invalid probe input')
    row = rows[0]
    if set(row) != {'owner_fixture', 'host_namespaces'}:
        raise ValueError('invalid probe fields')
    host = row['host_namespaces']
    if not isinstance(host, dict) or set(host) != {'pid', 'mnt', 'net'}:
        raise ValueError('invalid namespace input')
    isolated = {name: os.stat('/proc/self/ns/' + name).st_ino != host[name] for name in host}
    # Do not touch the outside fixture if launched without namespace separation.
    if not all(isolated.values()):
        raise RuntimeError('probe requires isolated namespaces')
    fixture_readable = False
    try:
        with Path(row['owner_fixture']).open('rb'):
            fixture_readable = True
    except OSError:
        pass
    source_writable = False
    try:
        with Path('/app/write-probe').open('xb'):
            source_writable = True
    except OSError:
        pass
    result = {'namespace_separation': isolated,
              'owner_fixture_blocked': not fixture_readable,
              'owner_environment_absent': all(name not in os.environ for name in ENV_NAMES),
              'source_read_only': not source_writable,
              'host_home_absent': not Path('/home').exists(),
              'host_run_absent': not Path('/run').exists()}
    print(json.dumps([result], sort_keys=True))


if __name__ == '__main__':
    main()
