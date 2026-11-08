"""Finite JSON batch adapter; caller-pinned fixtures, no admission authority."""
import hashlib
import json
from pathlib import Path
import re
import tempfile

from framework.errors import EvaluationError
from framework.kernel import contract_digest, digest, identity, verify
from examples.entitlement import experiment as runtime

MAX_SPEC = 256 * 1024
MAX_FILE = 256 * 1024
MAX_SOURCE = 1024 * 1024


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        _require(key not in obj, 'Duplicate JSON object key in contract.')
        obj[key] = value
    return obj


def _path(name):
    _require(isinstance(name, str) and len(name) <= 128 and
             re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', name) and
             all(p not in ('.', '..') for p in name.split('/')) and name.endswith('.py'),
             'Contract source paths must be safe relative Python file names.')


def prepare(candidate, contract_path, expected_sha):
    _require(isinstance(expected_sha, str) and re.fullmatch('[0-9a-f]{64}', expected_sha),
             'Supply an independently reviewed --expected-contract SHA256.')
    _require(not contract_path.is_symlink() and contract_path.is_file(), 'Contract must be a regular file.')
    with contract_path.open('rb') as stream:
        raw = stream.read(MAX_SPEC + 1)
    _require(len(raw) <= MAX_SPEC, 'Contract exceeds 256 KiB.')
    _require(hashlib.sha256(raw).hexdigest() == expected_sha, 'Contract SHA256 does not match the reviewed pin.')
    try:
        spec = json.loads(raw, object_pairs_hook=_unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON value.')))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('Contract must be bounded strict JSON without duplicate keys or non-finite values.') from exc
    _require(isinstance(spec, dict) and set(spec) == {'schema', 'runtime', 'files', 'entrypoint', 'assumptions', 'checks'},
             'Invalid contract fields.')
    _require(type(spec['schema']) is int and spec['schema'] == 1 and spec['runtime'] == 'python-json-batch-v1',
             'Unsupported contract schema/runtime.')
    files = spec['files']
    _require(isinstance(files, list) and 1 <= len(files) <= 32 and all(isinstance(p, str) for p in files),
             'Contract needs 1–32 selected files.')
    _require(len(files) == len(set(files)), 'Duplicate selected source file.')
    for name in files:
        _path(name)
    _require(spec['entrypoint'] in files, 'Entrypoint must be a selected source file.')
    checks = spec['checks']
    _require(isinstance(checks, list) and 1 <= len(checks) <= 4, 'Contract needs 1–4 finite checks.')
    for check in checks:
        _require(isinstance(check, dict) and set(check) == {'id', 'inputs', 'expected'}, 'Invalid check fields.')
        _require(isinstance(check['inputs'], list) and isinstance(check['expected'], list) and
                 1 <= len(check['inputs']) <= 256 and len(check['inputs']) == len(check['expected']),
                 'Each check needs 1–256 inputs and one expected JSON result per input.')
    contract = {'schema': 1, 'checks': [check['id'] for check in checks],
                'assumptions': spec['assumptions']}
    contract_digest(contract)  # Validate IDs, duplicates and explicit nonempty scope.
    # Re-encode to reject overflowing finite-number literals (e.g. 1e999).
    try:
        json.dumps(spec, allow_nan=False)
    except (ValueError, RecursionError) as exc:
        raise ValueError('Contract contains an unsupported JSON number or nesting depth.') from exc
    _require(not candidate.is_symlink() and candidate.is_dir(), 'Candidate must be a regular directory.')
    selected = {}
    for name in files:
        path = candidate
        for component in name.split('/'):
            path = path / component
            _require(not path.is_symlink(), 'Selected source must not traverse symlinks.')
        _require(path.is_file(), 'A selected source file is missing or not regular.')
        with path.open('rb') as stream:
            data = stream.read(MAX_FILE + 1)
        _require(len(data) <= MAX_FILE, 'Selected source exceeds 256 KiB per file.')
        selected[name] = data
    _require(sum(map(len, selected.values())) <= MAX_SOURCE, 'Selected source exceeds 1 MiB total.')
    return {'spec': spec, 'contract': contract, 'contract_sha256': expected_sha,
            'candidate': candidate, 'selected': selected}


def source_matches(candidate, selected):
    try:
        for name, data in selected.items():
            path = candidate
            if path.is_symlink():
                return False
            for component in name.split('/'):
                path = path / component
                if path.is_symlink():
                    return False
            if not path.is_file():
                return False
            with path.open('rb') as stream:
                if stream.read(MAX_FILE + 1) != data:
                    return False
        return True
    except OSError:
        return False


def run(prepared):
    spec, contract = prepared['spec'], prepared['contract']
    with tempfile.TemporaryDirectory(prefix='proofgate-json-') as temporary:
        base = Path(temporary); artifact = base / 'source'; artifact.mkdir()
        for name, data in prepared['selected'].items():
            path = artifact / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        hashes = {name: hashlib.sha256(data).hexdigest() for name, data in prepared['selected'].items()}
        inputs = {'source': hashes, 'artifact': dict(hashes),
                  'verifier': {'fixture-contract.json': prepared['contract_sha256'],
                               'framework/json_contract.py': runtime.file_hash(Path(__file__)),
                               'scripts/proofgate.py': runtime.file_hash(runtime.ROOT / 'scripts/proofgate.py')},
                  'environment': {'python': runtime.file_hash(Path('/usr/bin/python3').resolve()),
                                  'bwrap': runtime.file_hash(Path('/usr/bin/bwrap')),
                                  'systemd-run': runtime.file_hash(Path('/usr/bin/systemd-run')),
                                  'scope': digest({'python': runtime.sys.version,
                                      'environment': 'cleared; PATH=/usr/bin:/bin',
                                      'stdlib': 'host-trusted; not fully fingerprinted'})}}
        for name in ('kernel.py', '__main__.py', 'errors.py'):
            inputs['verifier']['framework/' + name] = runtime.file_hash(runtime.ROOT / 'framework' / name)
        for name in ('experiment.py', 'probe.py'):
            inputs['verifier']['examples/entitlement/' + name] = runtime.file_hash(runtime.HERE / name)
        bound = identity(contract, inputs)
        observations = []; checks = []
        for index, check in enumerate(spec['checks']):
            output = base / ('check-' + str(index)); output.mkdir()
            try:
                observed = runtime.invoke(artifact, '/app/' + spec['entrypoint'], check['inputs'], output)
            except EvaluationError as exc:
                exc.stage = check['id']; exc.completed_checks = [c['id'] for c in checks]; raise
            try:
                encoded = json.dumps(observed, sort_keys=True, allow_nan=False)
            except (ValueError, RecursionError) as exc:
                raise EvaluationError('invalid_result', check['id'], 'The check returned unsupported JSON values.',
                                      [c['id'] for c in checks]) from exc
            passed = encoded == json.dumps(check['expected'], sort_keys=True)
            observations.append({'id': check['id'], 'status': 'passed' if passed else 'failed', 'identity': bound})
            checks.append({'id': check['id'], 'passed': passed, 'cases': len(check['inputs']),
                           'inputs': check['inputs'], 'expected': check['expected'], 'observed': observed,
                           'stdout_sha256': runtime.file_hash(output / 'stdout')})
        for name, h in hashes.items():
            if runtime.file_hash(artifact / name) != h:
                raise EvaluationError('snapshot_changed', 'postcheck', 'The evaluated snapshot changed; no acceptance result.',
                                      [c['id'] for c in checks])
        return {'adapter': 'python-json-batch-v1', 'contract': contract,
                'fixture_contract_sha256': prepared['contract_sha256'], 'inputs': inputs,
                'checks': checks, 'observations': observations,
                'receipt': verify(contract, contract_digest(contract), inputs, observations),
                'candidate_matches_snapshot': source_matches(prepared['candidate'], prepared['selected']),
                'producer_authenticated': False, 'policy_admitted': False, 'release_authorized': False}
