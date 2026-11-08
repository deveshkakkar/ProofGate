"""Developer-facing trial command; execution is delegated to the Linux adapter."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

from framework.kernel import digest, identity
from framework.errors import EvaluationError


def validate_candidate(candidate):
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError('candidate must be a regular directory')
    entries = list(candidate.iterdir())
    if {p.name for p in entries} != {'app.py', 'rule.py'}:
        raise ValueError('candidate directory must contain exactly app.py and rule.py')
    for path in entries:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('candidate files must be regular files, without symlinks')
        if path.stat().st_size > 256 * 1024:
            raise ValueError('candidate file exceeds 256 KiB limit')


def summarize(report):
    lines = ['PASS: checked snapshot matches the finite contract.' if
             report['receipt']['consistent'] else 'FAIL: checked snapshot does not match the finite contract.']
    if 'source' in report.get('inputs', {}):
        lines.append('Source snapshot SHA256: ' + digest(report['inputs']['source']))
        lines.append('Evidence identity: ' + report['receipt'].get('identity',
                     identity(report['contract'], report['inputs'])))
    if 'fixture_contract_sha256' in report:
        lines.append('Reviewed fixture SHA256: ' + report['fixture_contract_sha256'])
        lines.append('Authority: observations only; producer unauthenticated; policy not admitted.')
    if report.get('candidate_matches_snapshot') is False:
        lines.append('CURRENT SOURCE CHANGED: this result describes the copied snapshot only; rerun with a new report path.')
    for check in report['checks']:
        observed = check['observed']
        if not isinstance(observed, list) or len(observed) != len(check['expected']):
            lines.append(f"  {check['id']}: FAIL; expected one response per input ({check['cases']} cases).")
            continue
        differences = [(row, want, actual) for row, want, actual in
                       zip(check['inputs'], check['expected'], observed)
                       if json.dumps(want, sort_keys=True) != json.dumps(actual, sort_keys=True)]
        lines.append(f"  {check['id']}: {'PASS' if check['passed'] else 'FAIL'} "
                     f"({len(differences)}/{check['cases']} mismatches)")
        for row, wanted, actual in differences[:3]:
            lines.extend(['    Input: ' + json.dumps(row, sort_keys=True),
                          '    Expected: ' + json.dumps(wanted, sort_keys=True),
                          '    Observed: ' + json.dumps(actual, sort_keys=True)])
    lines.append('Scope: finite declared inputs; local inspected code; no policy admission or deployment authorization.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Experimental business-rule verification trial')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='probe Linux sandbox prerequisites without candidate execution')
    command = sub.add_parser('check-entitlement', help='check an inspected two-file entitlement application')
    command.add_argument('--candidate', type=Path, required=True)
    command.add_argument('--output', type=Path, required=True, help='new JSON report path; never overwritten')
    external = sub.add_parser('check-json', help='check selected Python files against independently pinned JSON fixtures')
    external.add_argument('--candidate', type=Path, required=True)
    external.add_argument('--contract', type=Path, required=True)
    external.add_argument('--expected-contract', required=True, help='SHA256 obtained from independent contract review')
    external.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        from examples.entitlement.experiment import preflight, run_variant
        if args.command == 'doctor':
            print(json.dumps(preflight(), sort_keys=True))
            return 0
        prepared = None
        if args.command == 'check-json':
            from framework import json_contract
            prepared = json_contract.prepare(args.candidate, args.contract, args.expected_contract)
        else:
            validate_candidate(args.candidate)
        # Avoid even the empty probe when an immutable report already exists.
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError()
        if not args.output.parent.is_dir():
            raise ValueError('Cannot create report. Check that its parent directory exists and is writable.')
        preflight()
        # Reserve before execution: do not spend time running a check when the
        # requested evidence destination cannot be created safely.
        try:
            fd = os.open(args.output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise
        except OSError as exc:
            raise ValueError('Cannot create report. Check that its parent directory exists and is writable.') from exc
        with os.fdopen(fd, 'w') as output:
            try:
                report = (json_contract.run(prepared) if prepared is not None else
                          run_variant('local_candidate', candidate=args.candidate.resolve()))
            except Exception as exc:
                diagnostic = {'schema': 1, 'completed': False,
                              'reason': 'Evaluator could not complete; no acceptance result.',
                              'code': exc.code if isinstance(exc, EvaluationError) else 'evaluator_failed',
                              'stage': exc.stage if isinstance(exc, EvaluationError) else 'evaluation',
                              'completed_checks': exc.completed_checks if isinstance(exc, EvaluationError) else []}
                json.dump(diagnostic, output)
                output.write('\n')
                raise
            json.dump(report, output, sort_keys=True, indent=2)
            output.write('\n')
        print(summarize(report))
        print('Report: ' + str(args.output))
        if report.get('candidate_matches_snapshot') is False:
            return 2
        return 0 if report['receipt']['consistent'] else 1
    except Exception as exc:
        # Raw child stderr may contain candidate-controlled content; keep this
        # terminal message to the exception category and a fixed diagnostic.
        if isinstance(exc, EvaluationError):
            message = exc.code + ' [' + exc.stage + ']: ' + str(exc)
        elif isinstance(exc, FileExistsError):
            message = 'Output already exists; choose a new report path.'
        elif isinstance(exc, ValueError):
            message = str(exc)
        else:
            message = 'evaluator_failed: evaluation did not complete; no acceptance result.'
        print('ERROR: ' + message, file=sys.stderr)
        if args.command != 'doctor' and args.output.exists():
            print('Report preserved: ' + str(args.output) +
                  '. After resolving the failure, choose a new --output path; existing evidence is never overwritten.',
                  file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
