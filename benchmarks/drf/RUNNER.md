# Inspected-code shadow runner

The portable consistency kernel and scorer remain separate from this Linux adapter. It evaluates one candidate module against a pinned DRF historical reference and exact held-out test file. It creates a private snapshot from `git archive`, overlays only the candidate module, runs protected test inputs in a network-disabled namespace and retains observations and identities. The reference working tree is not executed or modified. Existing output directories are refused.

Example using a prepared checkout and isolated dependency directory:

```sh
python3 -B -m benchmarks.drf.replay \
  --case model_permissions \
  --reference /path/to/drf-git-checkout \
  --candidate /path/to/inspected/permissions.py \
  --heldout /path/to/pinned/test_permissions.py \
  --dependencies /path/to/isolated/dependencies \
  --output /path/to/new-report-directory \
  --compatibility
```

Reference commits and held-out file digests come from results.json. The Git checkout must contain the selected base object; local edits are ignored. The candidate must be a regular file no larger than256 KiB. The held-out file must match its pinned digest. Exit 0 means all selected checks match; exit 1 means a confirmed check mismatch; exit 2 means incomplete/setup failure. `run-state.json` starts incomplete, and only completed evaluation creates report.json and marks completion. Never treat an incomplete directory as acceptance.

Namespaces hide host home, credentials and networking. Read-only mounts protect inputs from the candidate process; systemd scopes bound aggregate memory 512 MiB, processes 32, CPU 1 and runtime 45 s per suite plus a 1 s termination grace, with control-group killing. `/tmp` is 64 MiB and each output file is capped at 2 MiB after privilege drop. The controller rejects root execution. Source, artifact, evaluator, held-out tests and declared environment are bound through the framework kernel. Dependencies and evaluated snapshots are rechecked afterward. Host standard libraries remain trusted and incompletely fingerprinted. Same-user concurrent interference is outside scope.

This is for inspected code. Python candidate imports share a process with pytest and can tamper with checks if deliberately malicious. Namespace isolation and identities do not solve that semantic problem. No production acceptance, hostile-runner resistance or formal proof is claimed.

## Fixed historical controls

`python3 -B -m benchmarks.drf.ci` prepares original/upstream files for only the three fixed public cases. Its options are shown by `--help`. It uses public Git fetches, no new credentials and no model calls. Dependencies must already exist under the supplied path; hash-pinned wheel requirements for each environment are included. Installing into a new private target directory avoids system package changes.

The controller exits 0 when the *expected per-suite historical result* is reproduced. That is different from the candidate passing. In particular, original defective code is expected to be rejected, and upstream8009 is expected to fail the separately enabled anonymous-read compatibility check. Inspect control.json and report.json for both the expected and observed verdicts.

## Manual GitHub transport

`Historical shadow controls` is dispatch-only. It checks out the selected evaluator workflow revision, uses a read-only repository token and never passes host credentials or environment into candidate execution. A GitHub-hosted backend creates a transient system resource scope, then drops to the original runner UID/GID before Python or candidate execution. Namespace prerequisite failure stops the job; the workflow changes no host security policy to bypass it. Artifacts include logs, reports and the upstream license; provider transcripts and auth are never collected.

Local user-scope execution has live evidence. GitHub-hosted privilege dropping currently has mocked command-construction coverage only; the hosted workflow has not been dispatched. The existing registered offline workflow also has an optional manual-only bridge, allowing feature-branch transport testing before merge. Normal push/PR jobs do not invoke the shadow job. Default-branch activation still requires a separately authorized merge.

`main` had no classic branch protection or active repository/branch rules at inspection. Therefore this manual transport is a diagnostic experiment, not independently enforced acceptance authority. That later step needs an explicitly approved contract/evaluator protection and admission policy. Changing repository protection or authentication and merging/deploying are separate approval boundaries under the home-server AGENTS policy.
