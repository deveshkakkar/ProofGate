#!/usr/bin/env python3
"""Validate redacted canary metadata offline; never use gh, keys or token APIs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proofgate_authority.scope import CanaryBinding, ScopeError, token_request, validate_grant


def read(path):
    with path.open('rb') as stream:
        raw = stream.read(128*1024+1)
    if len(raw) > 128*1024:
        raise ScopeError('metadata_size_limit')
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ScopeError('duplicate_metadata_key')
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('binding', 'installation', 'repositories'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--grant-metadata', type=Path)
    args = parser.parse_args()
    try:
        binding = CanaryBinding.from_dict(read(args.binding))
        installation = read(args.installation); repositories = read(args.repositories)
        if args.grant_metadata:
            result = validate_grant(binding, installation, repositories,
                                    read(args.grant_metadata), datetime.now(timezone.utc))
        else:
            result = {'request': token_request(binding, installation, repositories),
                      'request_executed': False, 'policy_admitted': False, 'merge_eligible': False}
        print(json.dumps(result, sort_keys=True))
        return 0
    except ScopeError as exc:
        print(json.dumps({'completed': False, 'code': str(exc), 'policy_admitted': False}), file=sys.stderr)
    except (OSError, ValueError, RecursionError, TypeError):
        print(json.dumps({'completed': False, 'code': 'metadata_unavailable_or_invalid',
                          'policy_admitted': False}), file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
