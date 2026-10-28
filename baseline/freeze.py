#!/usr/bin/env python3
"""Supervisor operation after independent review; never available to candidate tools."""
import argparse,pathlib,shutil,json
import gate

def main():
    p=argparse.ArgumentParser();p.add_argument('--review',required=True,type=pathlib.Path);p.add_argument('--destination',required=True,type=pathlib.Path);a=p.parse_args()
    src=pathlib.Path(__file__).resolve().parent;review=gate.read_json(a.review)
    files=gate.files_manifest(src)
    if any('__pycache__' in pathlib.PurePosixPath(n).parts for n in files):raise ValueError('remove pycache before review/freeze')
    if review.get('approved') is not True or not review.get('reviewer') or review.get('reviewed_files')!=files:raise ValueError('independent review absent or does not cover exact staging files')
    gate.check_policy(gate.read_json(src/'policy.json'));gate.assert_runtime(src,gate.read_json(src/'policy.json'))
    shutil.copytree(src,a.destination)
    manifest={'schema':1,'review':review,'files':files}
    gate.write_json(a.destination/'frozen.json',manifest)
    print(json.dumps({'baseline':str(a.destination.resolve()),'baseline_sha256':gate.digest(gate.canonical(manifest))},sort_keys=True))
if __name__=='__main__':main()
