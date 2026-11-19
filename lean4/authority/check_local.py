#!/usr/bin/env python3
"""Real fixed Lean execution; platform selection/adoption are explicit fixtures."""
import argparse
from pathlib import Path
from common import canonical
from producer import produce, finalize
from test_authority import FixtureAPI

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cache',type=Path,default=Path.home()/'.cache/proofgate-lean4')
    a = p.parse_args(); api = FixtureAPI()
    result = produce(api,api.adopted,7,a.output.resolve(),a.cache.resolve(),{'run_id':'123','attempt':1})
    finalize(api,api.adopted,7,a.output/'reservation-bundle.zip',result['bundle_sha256'],{'run_id':'123','attempt':1})
    evidence = {'kind':'real-local-Lean; substituted-GitHub-and-adoption; no-attestation',**result}
    (a.output/'local-control.json').write_bytes(canonical(evidence))
    print(canonical(evidence).decode())
