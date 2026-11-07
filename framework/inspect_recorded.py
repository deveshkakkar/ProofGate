"""Adapt the existing offline reservation integrity checker; never replay proofs."""
import contextlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_release import check_integrity
from framework.kernel import digest, contract_digest, identity, verify


def main():
    # This is trusted evaluator code, not a candidate-provided policy.
    contract = {'schema': 1, 'checks': ['recorded_integrity'],
                'assumptions': ['Archived evidence consistency only; no fresh formal or service execution.',
                                'Repository and host evaluator are trusted; no producer authentication.']}
    from hashlib import sha256
    def files(folder):
        result = {}
        for p in sorted(folder.rglob('*')):
            if p.is_symlink():
                raise ValueError('symlink in recorded inputs')
            if p.is_file():
                result[p.relative_to(folder).as_posix()] = sha256(p.read_bytes()).hexdigest()
            elif not p.is_dir():
                raise ValueError('nonregular recorded input')
        return result
    run = ROOT / 'runs/supervisor-resume/accepted-run'
    def capture():
        inputs = {'source': files(run / 'source'), 'artifact': files(run / 'artifact'),
                  'verifier': {},
                  'environment': {'scope': digest({'python': sys.version,
                      'runtime': 'not installed or verified by this adapter'})}}
        # Conservative whole-tree binding includes every archived observation,
        # deployment, checkpoint, matrix and review consumed by check_integrity.
        # Extra archived files invalidate evidence too; no selective caching yet.
        for directory in ('baseline', 'candidate', 'runs', 'review'):
            inputs['verifier'].update({directory + '/' + name: value
                for name, value in files(ROOT / directory).items()})
        for name in ('BASELINE.sha256', 'scripts/check_release.py',
                     'framework/kernel.py', 'framework/inspect_recorded.py'):
            inputs['verifier'][name] = sha256((ROOT / name).read_bytes()).hexdigest()
        inputs['environment']['python'] = sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()
        return inputs
    inputs = capture()
    # Reuse all original recorded-integrity assertions and output parsers. This
    # observation says only that this offline checker succeeded, not that old
    # formal/application observations were freshly executed.
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        check_integrity()
    if inputs != capture():
        raise ValueError('recorded snapshot changed during inspection')
    evidence = [{'id': 'recorded_integrity', 'status': 'passed', 'identity': identity(contract, inputs)}]
    receipt = verify(contract, contract_digest(contract), inputs, evidence)
    print(json.dumps({'scope': 'archived reservation consistency only', 'contract': contract,
                      'inputs': inputs, 'evidence': evidence, 'checker_output': output.getvalue(),
                      'receipt': receipt}, indent=2))
    return 0 if receipt['consistent'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
