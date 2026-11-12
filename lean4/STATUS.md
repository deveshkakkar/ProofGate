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
- [ ] Fresh CI execution on supported host
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

- Hosted CI: open the normal PR, inspect its fresh Lean job and preserve the run
  link and artifact. A locally passing run does not count as hosted execution.
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
