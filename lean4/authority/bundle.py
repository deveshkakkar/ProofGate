"""Bounded inert bundle format, shared by protected producer and consumer."""
import io
from pathlib import Path
import stat
import zipfile
from common import ROOT, canonical, decode, digest, need, policy, sha

LOGS = ['proof.log','build.log','bridge.log','application.log','preflight.log','legacy-bridge.log']
MAX = 64*1024*1024


def protected():
    p = policy()
    for name, expected in p['evaluator_files'].items():
        need(sha((ROOT/name).read_bytes()) == expected, 'protected-evaluator-changed')
    baseline = decode((ROOT/'baseline-v1.json').read_bytes())
    actual = {}
    for path in (ROOT/'baseline/v1').rglob('*'):
        need(not path.is_symlink(), 'protected-baseline-link')
        if path.is_file():
            actual[str(path.relative_to(ROOT/'baseline/v1'))] = {
                'sha256':sha(path.read_bytes()), 'executable':bool(path.stat().st_mode & 0o111)}
    need(actual == baseline, 'protected-baseline-changed')
    need(decode((ROOT/'baseline/v1/toolchain.json').read_bytes()) == p['toolchains'], 'protected-toolchains-changed')
    return baseline


def inventory():
    p = policy()
    return {'result.json','receipt.json', *('logs/'+x for x in LOGS),
            *('source/'+x for x in p['candidate_paths']),
            *('artifact/'+x for x in p['artifact_paths'])}


def pack(files, destination):
    need(set(files) == inventory(), 'bundle-inventory')
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,1,1,0,0,0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | (0o755 if name == 'artifact/core' else 0o644)) << 16
            z.writestr(info, data)
    need(Path(destination).stat().st_size <= MAX, 'bundle-bound')


def unpack(raw):
    need(len(raw) <= MAX, 'bundle-bound')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        need(len(entries) == len(inventory()) and {x.filename for x in entries} == inventory(), 'bundle-inventory')
        need(sum(x.file_size for x in entries) <= MAX, 'bundle-expanded-bound')
        for x in entries:
            mode = x.external_attr >> 16
            need(x.create_system == 3 and mode == stat.S_IFREG | (0o755 if x.filename == 'artifact/core' else 0o644)
                 and not x.flag_bits & 1 and x.compress_type == zipfile.ZIP_STORED, 'bundle-entry-policy')
        return {x.filename:z.read(x) for x in entries}


def validate(files, adopted):
    need(set(files) == inventory(), 'bundle-inventory')
    result = decode(files['result.json']); p = policy()
    need(set(result) == {'schema','policy_sha256','adoption','source','execution','files'}, 'result-shape')
    need(type(result['schema']) is int and result['schema'] == 1 and result['adoption'] == adopted and
         result['policy_sha256'] == sha((ROOT/'authority/policy-v1.json').read_bytes()), 'result-policy')
    need(result['files'] == {k:sha(v) for k,v in files.items() if k != 'result.json'}, 'bundle-file-binding')
    receipt = decode(files['receipt.json'])
    need(receipt['schema'] == 1 and receipt['backend'] == 'lean4-v1' and receipt['observations_consistent'] is True and
         receipt['policy_admitted'] is False, 'verification-incomplete')
    need(receipt['protected'] == protected() and receipt['evaluator'] == p['evaluator_files']['gate.py'] and
         receipt['toolchains'] == p['toolchains'], 'receipt-protected-binding')
    sources = {n:sha(files['source/'+n]) for n in p['candidate_paths']}
    need(receipt['source'] == sources and receipt['snapshot_sha256'] == digest(sources), 'receipt-source-binding')
    import hashlib
    need(set(result['source']['blobs']) == set(sources), 'source-blob-inventory')
    for name, ident in result['source']['blobs'].items():
        raw = files['source/'+name]
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == ident, 'receipt-git-source-binding')
    need(receipt['artifact'] == {n:{'sha256':sha(files['artifact/'+n]), 'executable':n == 'core'}
                                for n in p['artifact_paths']}, 'receipt-artifact-binding')
    need(receipt['logs'] == {n:sha(files['logs/'+n]) for n in LOGS}, 'receipt-log-binding')
    need(receipt['identity_sha256'] == digest({k:v for k,v in receipt.items()
         if k not in ['formal_seconds','application','identity_sha256']}), 'receipt-identity-binding')
    # The signing job never executes the source or artifacts. The producer's fixed
    # evaluator, authenticated separately, supplies proof/application conclusions.
    return result, receipt
