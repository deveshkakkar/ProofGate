#!/usr/bin/env python3
"""Real pinned CLI signature checks of upstream CLI fixtures. NOT our producer."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from common import canonical, need, pinned_gh, sha

FIXTURES = {
 'github_provenance_demo-0.0.12-py3-none-any.whl':'ae57936def59bc4c75edd3a837d89bcefc6d3a5e31d55a6fa7a71624f92c3c3b',
 'github_provenance_demo-0.0.12-py3-none-any-bundle.jsonl':'4f8c096e38a0eee242574ab100d16701928605409225e59784a3636f742bb27e'}
# MIT licensed github.com/cli/cli v2.105.0 test fixtures; see README attribution.
BASE = 'https://raw.githubusercontent.com/cli/cli/v2.105.0/pkg/cmd/attestation/test/data/'


def check(gh, output, fixtures):
    gh = pinned_gh(gh); fixtures.mkdir(parents=True,exist_ok=True)
    for name, expected in FIXTURES.items():
        path = fixtures/name
        if not path.exists():
            with urllib.request.urlopen(BASE+name,timeout=30) as r: raw = r.read(100000)
            need(sha(raw) == expected,'upstream-fixture-pin'); path.write_bytes(raw)
        need(sha(path.read_bytes()) == expected,'upstream-fixture-pin')
    artifact = fixtures/next(iter(FIXTURES)); bundle = fixtures/list(FIXTURES)[1]
    args = ['attestation','verify',str(artifact),'--bundle',str(bundle),'--repo','actions/attest-demo',
      '--signer-workflow','actions/attest-demo/.github/workflows/build-python.yml',
      '--signer-digest','a6c23b9806c593664f68637c8f9d45dfcf98b2db',
      '--source-digest','a6c23b9806c593664f68637c8f9d45dfcf98b2db',
      '--deny-self-hosted-runners','--format','json']
    rows = []
    def run(name, argv, passes, reason=None):
        r = subprocess.run([str(gh),*argv],capture_output=True,timeout=90)
        need(r.returncode == (0 if passes else 1),'real-crypto-control-'+name)
        if reason:
            need(reason in r.stderr.decode().lower(),'wrong-crypto-rejection-reason-'+name+' '+r.stderr.decode())
        rows.append({'id':name,'expected_success':passes,'exit':r.returncode,
                     'stdout_sha256':sha(r.stdout),'stderr_sha256':sha(r.stderr)})
    run('upstream-authenticated-positive',args,True)
    wrong = args.copy(); wrong[wrong.index('--signer-workflow')+1] = 'deveshkakkar/ProofGate/.github/workflows/lean-authority.yml'
    run('wrong-producer',wrong,False,'verifying with issuer')
    run('positive-after-wrong-producer',args,True)
    with tempfile.TemporaryDirectory() as tmp:
        replaced = Path(tmp)/artifact.name; replaced.write_bytes(artifact.read_bytes()+b'replaced')
        changed = args.copy(); changed[2] = str(replaced)
        run('replaced-artifact',changed,False,'verifying with issuer')
        run('positive-after-replaced-artifact',args,True)
        from bundle import pack
        from test_authority import FixtureAPI, fixture_files
        forged = Path(tmp)/'reservation-bundle.zip'
        pack(fixture_files(FixtureAPI()),forged)
        changed[2] = str(forged)
        run('self-consistent-forgery-no-signed-subject',changed,False,'verifying with issuer')
        run('positive-after-forgery',args,True)
        missing = Path(tmp)/'invalid-attestation.json'; missing.write_bytes(b'{}')
        changed = args.copy(); changed[changed.index('--bundle')+1] = str(missing)
        run('invalid-producer-authentication',changed,False,'error:')
        run('positive-after-invalid-authentication',args,True)
    report = {'schema':1,'kind':'real-cryptography; upstream-fixture-only; no-ProofGate-platform-run',
              'verifier_sha256':sha(gh.read_bytes()),'fixtures':FIXTURES,'controls':rows,
              'policy_admitted':False,
              'limitation':'CLI emits aggregate verification errors; inner crypto reason not independently exposed. Each negative is followed by the genuine positive.'}
    with output.open('xb') as out: out.write(canonical(report))
    print(canonical(report).decode())


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--gh',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--fixtures',type=Path,required=True)
    a = p.parse_args(); check(a.gh,a.output,a.fixtures)
