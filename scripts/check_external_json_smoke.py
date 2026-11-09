#!/usr/bin/env python3
"""Hosted-only external checkout integration; fixed inspected source and mutation."""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from framework.kernel import identity


def main():
    if os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('Run this source-executing smoke only on disposable GitHub-hosted runners.')
    output = Path(sys.argv[1]); output.mkdir(parents=True, exist_ok=False)
    metadata = json.loads((ROOT/'examples/stdnum-json/source.json').read_text())
    revision = metadata['revision']
    candidate = output.parent / ('stdnum-external-' + revision)
    candidate.mkdir(exist_ok=False)
    url = 'https://codeload.github.com/arthurdejong/python-stdnum/tar.gz/' + revision
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(8*1024*1024+1)
    assert len(data) <= 8*1024*1024, 'Upstream archive exceeds compressed size bound'
    prefix = 'python-stdnum-' + revision
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        assert len(members) <= 10000 and sum(m.size for m in members) <= 32*1024*1024
        for member in members:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == prefix
            assert member.isdir() or member.isfile(), 'Links and special files are excluded'
            destination = candidate.joinpath(*path.parts[1:])
            if member.isdir(): destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as stream:
                    destination.write_bytes(stream.read(member.size+1))
    for name, expected in metadata['selected_source_sha256'].items():
        assert hashlib.sha256((candidate/name).read_bytes()).hexdigest() == expected, name
    shutil.copyfile(ROOT/'examples/stdnum-json/run_json.py', candidate/'run_json.py')
    contract = ROOT/'examples/stdnum-json/contract.json'
    assert hashlib.sha256(contract.read_bytes()).hexdigest() == metadata['contract_sha256']
    records = []
    def command(name, report, expected):
        result = subprocess.run(['/usr/bin/python3', '-I', '-B', str(ROOT/'scripts/proofgate.py'), 'check-json',
            '--candidate', str(candidate), '--contract', str(contract),
            '--expected-contract', metadata['contract_sha256'], '--output', str(report)],
            cwd=candidate, capture_output=True, text=True, timeout=40)
        (output/(name+'.stdout')).write_text(result.stdout)
        (output/(name+'.stderr')).write_text(result.stderr)
        records.append({'name': name, 'exit': result.returncode, 'expected_exit': expected})
        (output/'commands.json').write_text(json.dumps(records, indent=2)+'\n')
        assert result.returncode == expected, name
        return result
    baseline = output/'baseline.json'
    good = command('upstream-baseline', baseline, 0)
    report = json.loads(baseline.read_text())
    assert report['receipt']['consistent'] and report['candidate_matches_snapshot'] and report['entrypoint_pinned']
    assert report['receipt']['identity'] == identity(report['contract'], report['inputs'])
    assert not report['producer_authenticated'] and not report['policy_admitted'] and not report['release_authorized']
    assert report['fixture_contract_sha256'] == metadata['contract_sha256']
    assert report['checks'][0]['observed'] == [False, 6, '9', True, 14, False, False]
    assert '0/7 mismatches' in good.stdout
    original = baseline.read_bytes()
    command('immutable-report', baseline, 2)
    assert baseline.read_bytes() == original
    path = candidate/'stdnum/luhn.py'
    old = 'valid = checksum(number, alphabet) == 0'
    assert path.read_text().count(old) == 1
    path.write_text(path.read_text().replace(old, 'valid = True'))
    mutation = output/'mutation.json'
    failed = command('broken-checksum-control', mutation, 1)
    bad = json.loads(mutation.read_text())
    assert not bad['receipt']['consistent'] and bad['candidate_matches_snapshot']
    assert bad['fixture_contract_sha256'] == metadata['contract_sha256']
    assert bad['inputs']['source']['stdnum/luhn.py'] != report['inputs']['source']['stdnum/luhn.py']
    assert bad['checks'][0]['observed'] == [True, 6, '9', True, 14, False, True]
    assert '2/7 mismatches' in failed.stdout
    # The target remains broken; the candidate also attempts to bypass it.
    # The unchanged reviewed contract must reject the modified driver before execution.
    (candidate/'run_json.py').write_text(
        'import json,sys\njson.load(sys.stdin)\nprint(json.dumps([False,6,"9",True,14,False,False]))\n')
    spoof_path = output/'spoof-attempt.json'
    spoof = command('candidate-driver-spoof', spoof_path, 2)
    assert 'Entrypoint SHA256' in spoof.stderr and not spoof_path.exists()
    (output/'smoke-result.json').write_text(json.dumps({
        'completed': True, 'evaluator_revision': os.environ.get('GITHUB_SHA'),
        'upstream_revision': revision, 'upstream_archive_sha256': hashlib.sha256(data).hexdigest(),
        'fixture_contract_sha256': metadata['contract_sha256'],
        'scope': 'external checkout, five published examples plus two invalid fixtures; no full-package/customer/admission assurance',
        'commands': records}, indent=2)+'\n')
    print('PASS: external checkout, pinned data-only contract, exact source binding and broken-checksum and driver-spoof controls')


if __name__ == '__main__':
    main()
