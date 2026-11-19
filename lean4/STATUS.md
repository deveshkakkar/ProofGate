# Lean migration — issue #46

Development starts from 5bbc9a1 on codex/lean4-migration. This is owner-initiated
Codex engineering, not the pending Photon restricted-agent demonstration.

## Bounded work contract

Intended behavior: retain unbounded natural balances/grants and signed amounts;
prove the four original laws about the executable Lean definition; retain HTTP
bounds ±(2^48-1), SQLite transactions, retries, conflicts and restart behavior.
Allowed writes: new lean4/ baseline, candidate, evaluator, tests and evidence;
current-path documentation and a separate CI workflow. Historical baseline/,
candidate/, BASELINE.sha256, runs/, evidence/ and review records stay unchanged.
No service deployment, owner VM changes, credentials, protection changes, token
issuance, canary recovery or live Photon dispatch. Rollback: abandon this branch;
no existing service or persistent state is modified.

Resources: Linux x86_64, credential-free local toolchain downloads under the user
cache, 200% aggregate CPU quota, 4 GiB per scope, 64 tasks, no swap, bounded subprocess timeouts.
Fresh review corrected the initial two-thread wording: CPU quota bounds bandwidth,
not thread count. Runtime build workers are additionally configured to two; bundled
nanoda uses its upstream four-thread configuration within the same CPU/task quota.
Stop dependent work on unavailable isolation/checker prerequisites, mismatched
protected identities, missing authority, or required architecture outside scope;
continue independent implementation and document exact gaps.

Acceptance evidence: real Lean compile, trusted statement comparison, transitive
axiom policy, external independent checker outside candidate writable sandbox,
compiled-boundary and HTTP tests; each negative control must fail at its expected
layer. Missing tools/crashes/timeouts are infrastructure failures, never proof
rejections. Fresh execution, mocks and archived evidence must remain distinct.

## Issue #46 checklist

- [x] Pure core and all four exact laws; separately versioned baseline
- [x] Pinned toolchain/dependencies/build/checker environment
- [x] Isolated candidate build/export and external kernel replay
- [x] Trusted elaborated statements and referenced definitions matched
- [x] Transitive axiom policy and runtime substitution prevention
- [x] Small protected compiled bridge and unchanged service input bounds
- [x] 11,716 boundary cases, interface timing and HTTP/SQLite regression tests
- [x] Exact fresh identity receipt, stale/substitution rejection, copy without rebuild
- [x] Negative controls and real infrastructure failures
- [x] Fresh CI execution on supported host
- [x] Fresh-context review of requirements/diff/evidence
- [ ] Photon-origin restricted agent demonstration (separate; authority prerequisites)
- [ ] Authenticated admission (#28; separate release blocker)

Default cutover remains pending full evidence. Nothing here authorizes merge or
 deployment. Exact commands, results and remaining work will be appended below.

## Observed development evidence (2026-11-12)

Host: Ubuntu 24.04.5 Linux x86_64, working bubblewrap and systemd user manager.
Lean 4.35.0 (`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`), bundled nanoda,
Node 24.22.1; complete archive/tree hashes are in baseline/v1/toolchain.json.
No live provider calls, production state or authentication changes occurred.

Commands executed from `/home/devesh/ProofGate-lean4-migration`:

```sh
python3 -B lean4/doctor.py
python3 -B lean4/check.py --output /tmp/proofgate-lean-matrix-2
python3 -B lean4/check.py --output /tmp/proofgate-lean-matrix-3
python3 -B lean4/check.py --output /tmp/proofgate-lean-matrix-4
python3 -B scripts/check_release.py
python3 -B -m unittest discover -s tests -v
git diff --check
```

Doctor passed actual namespace/resource probes. Matrix-2 passed all its controls;
matrix-3 added the unchanged original bridge script and passed through native
axiom rejection, then the harness stopped because its definition-mismatch
diagnostic expectation used the wrong wording. Comparator correctly rejected the
changed admission definition. The expectation was corrected to the observed
constant-mismatch diagnostic; matrix-4 is the complete rerun.
The release check passed 46 historical regressions and six archived applier
rejection cases; those are archived consistency checks, not fresh Lean evidence.
All 126 framework tests passed. Historical paths have no diff from 5bbc9a1.

Inside the evaluator, the exact proof command is the pinned `lake comparator`
with the protected configuration and sandbox wrapper; it exports and compares
statements and dependencies, then invokes bundled `nanoda_bin` and
`leanchecker --silent --from-export` in fresh read-only sandboxes. The build
command is `/tools/bin/lake build core` in a separate minimal-root sandbox with
only the restricted admission source and protected inputs. Runtime proof code
and proof-generated binaries are never copied into that clean build.

The initial runnable checkpoint was `/tmp/proofgate-lean-checkpoint-5`:
four laws accepted by Lean and nanoda, native compilation succeeded, 11,716
batched bridge cases and all seven HTTP groups passed. A deliberately
overgranting source in `/tmp/proofgate-lean-overgrant-check` failed on exact-grant
and conservation proof goals, not an infrastructure fault. Intermediate failed
host probes exposed and fixed unsupported nested namespaces; they were never
counted as rejected proofs.

Matrix-3's valid path additionally ran the byte-identical original 11,716-call
bridge and passed. The batched bridge measured 23.72 ms and the seven paired
single-request cross-checks averaged 5.90 ms per pair (two executable launches
per pair). These are local observations, not a latency guarantee. The seven
HTTP groups include retries, conflicts, distinct/same-request concurrency,
SQLite persistence and process restart.

A fresh-context reviewer inspected issue #46, the new diff and real evidence.
Two P2 findings were fixed before PR: generic failures now retain unknown cause
instead of trusting candidate log words, and the resource contract accurately
describes CPU quota versus thread count. The follow-up found no additional
consequential engineering issue; final hosted CI and human PR review remain
separate.

## Remaining acceptance / handoff

- Hosted CI completed: [run 43160320209](https://github.com/deveshkakkar/ProofGate/actions/runs/43160320209)
  passed the complete final harness and genuine core-failure test at `abc6d97`.
  Its [artifact](https://github.com/deveshkakkar/ProofGate/actions/runs/43160320209/artifacts/13916899595)
  contains the compiled bytes, receipt and full diagnostics. The PR workflow now
  explicitly checks out its head SHA; final-revision checks remain visible in
  [PR #47](https://github.com/deveshkakkar/ProofGate/pull/47).
- Human baseline review: review this separately versioned Lean baseline and
  evaluator in the PR. A new manifest identity alone is not external approval.
- Photon-origin restricted agent demonstration: blocked on the existing separate
  authority/runtime prerequisites. After those are resolved, record actual
  agent interventions/repairs/escalations and fresh final identity. Do not count
  this owner-initiated Codex session as that demonstration.
- Authenticated admission/release: #28 remains open. Protect policy/verifier,
  producer and receipt digest out of candidate control, then use the exact-head
  identity check. No new keys, tokens, protection changes, canary recovery,
  merge or deployment were performed by this migration.
- Default cutover: retain historical reproduction until required evidence and
  the above review/demonstration prerequisites exist; then update the default
  path explicitly. Broader packaging, framework expansion and user-value trials
  remain outside this bounded migration.


### Completed local controls

`/tmp/proofgate-lean-matrix-4` completed 26 controls (plus summary), including the
real legacy bridge. Receipt SHA256:
`668aaa6b8b3c63b1a135a441142b6c7e44d00b73963cd97b39b285a15ca32c8b`.
Source snapshot:
`2394f6ead910ea5d48421fc08d4831fd241c25a368d4684fc461359e2449c0a6`.
Native core SHA256:
`47011829f546b3db8e4a2571be436cec5be42edfdda60430bbfb03d6f0fb4a73`.
This was an uncommitted development snapshot; a later commit requires a fresh
receipt. The final runtime also carries the pinned Lean license sidecars.

The controlled diagnostic-exit fixture was tightened after this matrix: its
initial body failed elaboration before exiting. A corrected separate run,
`/tmp/proofgate-lean-diagnostic-exit-run-2`, actually printed the misleading
`tactic axiom match` text and exited Lean with code 17. The gate returned
`formal-failed`, cause unknown, and created no accepted receipt. The final matrix
harness now asserts both the emitted text and real exit code, so a syntax failure
cannot masquerade as this control. This is an abnormal process exit, not a proof
rejection or a claim of observing a segmentation fault.

The additional command
`python3 -B lean4/check_core_failure.py --artifact /tmp/proofgate-lean-matrix-4/valid/artifact --output /tmp/proofgate-lean-core-failure-1`
passed a real executable EACCES -> HTTP 500 -> rollback -> successful retry ->
persisted/restarted response sequence. Its result is retained with the evidence.
The final workflow runs both the complete matrix and this additional failure
check against its freshly compiled artifact.


### Reviewable PR and stable-head handoff

Normal ready-for-review [PR #47](https://github.com/deveshkakkar/ProofGate/pull/47),
branch `codex/lean4-migration`. Implementation commit `14837ca`; evidence commit
`abc6d97`. GitHub's automated review of `abc6d97` completed with no findings;
review submissions and inline review threads were empty when inspected. Human
baseline review/merge/deploy authority is not implied by that result.

A stable-head rerun at `abc6d9705d3661a1f58c0ae11914a42ecf5f2655`, clean candidate,
passed all proof/build/bridge/HTTP stages and exact identity/copy rechecking:

```sh
python3 -B lean4/gate.py --output /tmp/proofgate-lean-final-head-2
```

Receipt `/tmp/proofgate-lean-final-head-2/receipt.json`, SHA256
`25fb4e8847e42e0a344bf0bd89ca4347c0ef571ebc198143afb700707c6dab88`.
`copy_checked` copied its exact artifact to
`/tmp/proofgate-lean-final-head-2-accepted-copy` without rebuild. A prior receipt
at the transient pre-amend evidence commit was correctly rejected by the commit
identity check; it was not used as the final handoff.

The final small CI/documentation update pins PR checkout to the actual head and
coalesces duplicate branch/PR jobs. Its current check results and fresh receipt
belong to the final PR revision, not the older local handoff above. No automatic
repair loop was used; any later findings require owner assessment after the
single repair-pass boundary in the global policy.


## Bounded source-policy snapshot repair

Independent review of `40af8d4` found an early A→B→A race between live-source
policy checks and source copying. This is a new bounded repair task. Intended
behavior: verify the controlled snapshot, then apply both the immutable-service
pin and admission-syntax policy to its exact bytes before any candidate process.
Proof checking and clean runtime compilation must keep using that snapshot;
subsequent live-source and protected-input freshness checks remain required.

Allowed writes: `lean4/gate.py`, focused boundary regressions/old-function fixture,
the Lean CI workflow, this status, and new repair evidence/documentation. Preserve
all original Bend inputs, existing Lean v1 baseline, earlier evidence and receipts.
The previous CPU/memory/task/time limits remain unchanged. No authority, Photon,
merge, deployment, host administration, keys or token changes are in scope.
Rollback: revert the focused repair commit; no running service/state is changed.

Acceptance: deterministic runtime-source and driver A→B→A cases reach controlled
preflight on the exact old evaluate function, then fail at `runtime-policy` and
`driver-policy` on the repaired function before execution. These are focused
boundary tests with substituted toolchain/preflight calls and real file/hash
operations, not Lean/build execution. Separately rerun actual Lean/build/bridge,
HTTP, negative-control, core-failure and offline workflows on the repaired head.
Retain original `40af8d4` receipt as historical evidence, and retain final-head
receipts, logs, controls and executable bytes durably in the project. Stop on
unexpected policy layers or verification failures; preserve existing human review
and deployment/admission gates.

- [x] Validate both policies on verified frozen source; preserve shared proof/build input
- [x] Deterministic old/new A→B→A regressions for both policies
- [x] Fresh-context review of the bounded repair
- [x] Required local real verification on the working repair snapshot
- [x] Original receipt archived; durable final-head retention location established
- Final-head hosted verification, identity inspection and PR/issue handoff: see
  the durable `lean4/evidence/local/final/inspection.json` record and the live
  [PR #47](https://github.com/deveshkakkar/ProofGate/pull/47) /
  [issue #46](https://github.com/deveshkakkar/ProofGate/issues/46) repair checkpoint.
  Those results must identify the final committed head; local development results
  below are not an approval of a later revision.

The earlier successful receipts describe their original commits. They do not
approve this repair or any changed head. Remaining migration acceptance still
includes human baseline/evaluator review, the separate Photon demonstration,
protected admission authority (#28), and explicit default-path cutover.


### Repair validation record

The production diff moves both existing policy checks from the live candidate to
`output/source` immediately after `snapshot(frozen) == initial`. Both `prepare`
calls still consume that same `frozen` directory. Live-source, protected-input,
evaluator and post-test artifact freshness checks remain unchanged. No baseline,
proof statement, dependency, service, bridge or runtime source was changed.

Focused command (real file/hash operations; substituted toolchain/preflight;
no Lean/build execution):

```sh
python3 -B lean4/test_snapshot_policy.py --output /tmp/proofgate-policy-repair-focused.json
```

All six tests passed: the old evaluator reaches intercepted preflight with
unapproved runtime/driver A after A→B→A edits; the repaired evaluator rejects at
`runtime-policy` / `driver-policy` with zero execution/preparation calls. Approved
source still reaches preflight; a changed copy fails identity verification. The
pinned old evaluate fixture was independently verified against `40af8d4`.
[Focused evidence](evidence/source-policy-repair/focused-boundary.json) is distinct
from the actual Lean/build evidence.

Real local workflows executed on the working repair snapshot (evaluator SHA256
`6a7c1d862b7663d89fab24d5004af287bc4dfa9e8807b87e3208460e7b1ed4f5`):

```sh
python3 -B lean4/check.py --output /home/devesh/ProofGate-lean4-migration/lean4/evidence/local/repair-development
python3 -B lean4/check_core_failure.py --artifact lean4/evidence/local/repair-development/valid/artifact --output lean4/evidence/local/repair-development/core-failure
python3 -B scripts/check_release.py
python3 -B -m unittest discover -s tests -v
```

The 26-control real suite passed: dual-kernel proofs, native build, both 11,716
case bridges, seven HTTP groups, mathematical/spec/axiom/driver negatives,
double charging, live edits, artifact substitution and real infrastructure
failures. The genuine executable EACCES/HTTP 500, rollback, retry and restart
control passed separately. Offline results: 46 historical regressions plus six
archived rejection cases, and all 126 framework tests passed.

Fresh-context review found no actionable issue in this bounded fix and
independently reran the six focused tests. The Lean CI workflow now runs and
uploads those focused boundary results in a separate named step before real
Lean verification. Final-revision workflows and inspected evidence are retained
under `lean4/evidence/local/<full-head-sha>/`; `local/final/inspection.json` is the
current local handoff pointer. These generated files are ignored so recording a
receipt cannot alter the Git revision it identifies. They are project data on
the home-server filesystem, rather than transient `/tmp` storage.

The original hosted receipt SHA256
`6e300bd1249bed6211c2388d8ed146a2577f23ddfee1050ed2d1e40f1cb75fa3`
and its six logs are preserved verbatim in
[evidence/source-policy-repair/previous-40af8d4](evidence/source-policy-repair/previous-40af8d4/receipt.json).
It retains its original provenance and the reviewed limitation; it does not
validate the repaired evaluator.


## Merged engineering handoff and next bounded phase

Owner `deveshkakkar` merged PR #47 as `3ed4e8d868808bde351e750020dc9644a3fe44b0`
from repaired head `18199c6`. This records the actual owner merge; no separate
policy-approval record is inferred. Existing post-merge Lean run43174126038 and
offline run43174126041 succeeded and were inspected without starting duplicates.
The merged receipt, evaluator/baseline/source identities, six logs, five artifacts
and five accepted-copy hashes match. Receipt SHA256:
`e33a96fb033156d12b9348028b109cfb2392e2e1557cbee21645f73ebec977e2`.
Raw receipt/logs are preserved under `lean4/evidence/post-merge-3ed4e8d/`; the full
bundle is durable under `lean4/evidence/local/3ed4e8d868808bde351e750020dc9644a3fe44b0/`.
Earlier receipts retain their original identities and limitations.

[Integration acceptance reconciliation](../docs/framework/protected-authority/LEAN-INTEGRATION-ACCEPTANCE.md)
records Axx/Vxx evidence classes, current worker startup and exact remaining gaps.
The next scoped work reuses the existing Photon job store and merged evaluator;
no framework rewrite, new token, canary positive PR, owner-VM connection or live
mission was performed. The fixed proposed mission profile remains inactive.
#28, actual restricted Photon repair and explicit default cutover remain pending.
