"""Developer-facing trial command; execution is delegated to the Linux adapter."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys


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
    lines = ['PASS: finite rule and application checks match the contract.' if
             report['receipt']['consistent'] else 'FAIL: candidate does not match the contract.']
    for check in report['checks']:
        lines.append(f"  {check['id']}: {'PASS' if check['passed'] else 'FAIL'} ({check['cases']} cases)")
        if not check['passed']:
            observed = check['observed']
            if not isinstance(observed, list) or len(observed) != len(check['expected']):
                lines.append('    Expected a result list with one response per input.')
                continue
            for row, wanted, actual in zip(check['inputs'], check['expected'], observed):
                if json.dumps(wanted, sort_keys=True) != json.dumps(actual, sort_keys=True):
                    lines.extend(['    Input: ' + json.dumps(row, sort_keys=True),
                                  '    Expected: ' + json.dumps(wanted, sort_keys=True),
                                  '    Observed: ' + json.dumps(actual, sort_keys=True)])
                    break
    lines.append('Scope: finite declared inputs; local inspected code; no deployment authorization.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Experimental business-rule verification trial')
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('check-entitlement', help='check an inspected two-file entitlement application')
    command.add_argument('--candidate', type=Path, required=True)
    command.add_argument('--output', type=Path, required=True, help='new JSON report path; never overwritten')
    args = parser.parse_args(argv)
    try:
        validate_candidate(args.candidate)
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
                from examples.entitlement.experiment import run_variant
                report = run_variant('local_candidate', candidate=args.candidate.resolve())
            except Exception:
                json.dump({'schema': 1, 'completed': False,
                           'reason': 'Evaluator could not complete; no acceptance result.'}, output)
                output.write('\n')
                raise
            json.dump(report, output, sort_keys=True, indent=2)
            output.write('\n')
        print(summarize(report))
        print('Report: ' + str(args.output))
        return 0 if report['receipt']['consistent'] else 1
    except Exception as exc:
        # Raw child stderr may contain candidate-controlled content; keep this
        # terminal message to the exception category and a fixed diagnostic.
        if isinstance(exc, FileExistsError):
            message = 'Output already exists; choose a new report path.'
        elif isinstance(exc, ValueError):
            message = str(exc)
        else:
            message = 'Check could not complete. Verify Linux, bubblewrap and systemd user-manager prerequisites.'
        print('ERROR: ' + message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
