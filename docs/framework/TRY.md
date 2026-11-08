# Try the developer interface

Experimental audience: developers using coding agents to change business logic. This first adapter supports one tenant entitlement contract and a two-file Python interface. It does not check an arbitrary application or generate its requirements. There is no package installation step.

From a checkout of ProofGate, on Linux with Python 3, bubblewrap and an active systemd user manager:

```sh
python3 -B -m framework doctor
mkdir demo-entitlement
cp examples/entitlement/app.py examples/entitlement/rule.py demo-entitlement/
python3 -B -m framework check-entitlement \
  --candidate demo-entitlement \
  --output entitlement-first.json
```

Expected result: rule PASS (0/72 mismatches), application PASS (0/80 mismatches), exit 0. The summary prints the source-manifest SHA256 and complete evidence identity, with finite scope and no policy/deployment admission. The JSON report is created with owner-only permissions and is never overwritten. Choose a new output name for each run. Exit 1 means an observed mismatch; exit 2 means setup/input/evaluator failure and supplies no passing result. The command runs a bounded empty sandbox probe before reserving the report. Missing prerequisites or a failed probe leave the requested path available for retry. `doctor` runs that probe without loading any candidate. It needs the same systemd user scope and namespaces as the actual checks; it does not install packages or change host configuration.

A later execution error retains an incomplete report with a stable code, failed stage and the checks that completed (completion is not a passing verdict). Errors distinguish unavailable runners, timeouts, nonzero check exits and invalid JSON. Raw candidate stderr is not displayed or exported. A nonzero child exit does not identify its cause reliably: it may be candidate import failure, resource enforcement or another runtime failure; no unsupported diagnosis is invented. After resolving it, keep the failed record and choose a new `--output` path.

Ask your coding agent to modify `demo-entitlement/app.py` so that it overwrites `resource_tenant` with `subject_tenant` before invoking `allow`. Then repeat with `--output entitlement-changed.json`. The pure rule should pass while the application check fails with a concrete cross-tenant input, expected denial and observed grant. The summary counts every mismatch and shows at most three examples per check; the JSON retains all observations. Use those inputs to diagnose and repair the change, then run again under a fresh report name.

The candidate directory must contain exactly regular `app.py` and `rule.py` files, each at most 256 KiB. Start with inspected local source you own. Execution uses the existing Linux adapter with namespaces and resource controls; hostile candidate programs and exhaustion behavior have not been validated. The Python kernel remains independent of this Linux adapter. The environment is partially fingerprinted and observations are unsigned. No deployment approval or credential freshness guarantee is supplied.

The contract is in `examples/entitlement/experiment.py`, controlled with the evaluator. It covers tenant IDs 0–2 and three booleans only. A business contract outside that domain needs another adapter or an explicitly reviewed contract change. Changing the evaluator to make your implementation pass defeats independent checking.

Before expanding the adapter, try the same defect with your existing tests. Record setup and diagnosis effort and whether the added contract helps. See [the developer trial protocol](DEVELOPER-TRIAL.md) for evidence thresholds and backtracking criteria.

## Snapshot applicability

The report describes the two copied source files, identified by their hashes and the printed source-manifest digest. The evaluator checks those immutable copies again after execution and compares the current candidate files with them. If an observed edit makes them differ, the CLI retains the snapshot result, prints `CURRENT SOURCE CHANGED` and exits 2. A passing snapshot receipt does not approve the current working tree or a PR. This end comparison is an observation, not a lock: edits after comparison or an edit-and-restore sequence are not excluded. Merge-time identity enforcement and authenticated admission remain outside this local trial.

## CI and diagnostic evidence

The separate `Entitlement CLI smoke` workflow runs this actual command on a disposable Ubuntu host for the inspected baseline and tenant-spoof mutation. It prepares the packaged AppArmor namespace profile and systemd user manager on that runner, retains complete or incomplete artifacts and checks exits, source identity, mismatch output and no-overwrite behavior. It does not change your host or establish hostile-source security. Unit tests for missing dependencies, unavailable sandboxes, timeout/invalid-output errors and concurrent edits use mocks; those are not live sandbox observations. See [the remediation plan](CLI-AUDIT-PLAN.md) for this phase's bounds and [STATE.md](STATE.md) for actual run outcomes.
