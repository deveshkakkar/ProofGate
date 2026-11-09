#!/usr/bin/env python3
"""Run only the fixed, credential-free process isolation diagnostic on hosted CI."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework.errors import EvaluationError
from framework.report import ReportDestination
from proofgate_authority.isolation import run_probe


def main():
    if os.environ.get('RUNNER_ENVIRONMENT') != 'github-hosted':
        raise SystemExit('The actual process probe is restricted to disposable hosted CI.')
    if len(sys.argv) != 2:
        raise SystemExit('Supply a new diagnostic report path.')
    destination = ReportDestination(Path(sys.argv[1]))
    destination.publish({'completed': False, 'code': 'probe_in_progress',
                         'credential_release_authorized': False, 'policy_admitted': False}, reserve=True)
    try:
        report = run_probe()
        report['completed'] = True
        report['hosted_revision'] = os.environ.get('GITHUB_SHA')
        destination.publish(report)
        print(json.dumps({k: report[k] for k in ('process_checks_passed', 'coding_agent_tools_verified',
              'github_principal_verified', 'credential_release_authorized', 'policy_admitted')}))
        return 0 if report['process_checks_passed'] else 1
    except (Exception, KeyboardInterrupt) as exc:
        code = exc.code if isinstance(exc, EvaluationError) else 'probe_could_not_complete'
        destination.publish({'completed': False, 'code': code,
                             'credential_release_authorized': False, 'policy_admitted': False})
        print('Probe incomplete; no credential/admission authority.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
