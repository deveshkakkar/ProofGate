# ProofGate independent requirements and acceptance review

Review origin: independent requirements reviewer, 2026-10-28. Source: the user's adopted 165-line ProofGate prompt, Space file libfile_fc945aef4788819196efb26f19edc9ff. This is a proposed freeze checklist, not a claim that any implementation or check passed.

## Scope and status

The experiment must demonstrate an actual application, formal executable admission core, independent fail-closed evaluator, actual rejected candidate and Codex repair, exact-artifact private deployment, and restart/resumption evidence. Report COMPLETE only after every required row below has execution evidence. A loopback demo with exact local launch instructions is an allowed deliverable; do not describe it as a publicly or remotely reachable deployment.

No implementation code was available at this review's start. Baseline freezing is NOT approved by this document alone. Review the actual spec, imported definitions, tests, toolchain pins, runner and enforcement boundary first, record their hashes, and freeze the reviewed versions.

## Independent mathematical contract

Use a pure function admission(B, a), with B a nonnegative integer balance and a a signed integer amount. Its observable result must include success/rejection, grant g, and next balance B'. Define validity mathematically as a > 0, and affordability as a <= B, independently of the candidate function's branches or candidate-owned helper predicates.

Required obligations, over all admissible B and all signed integer a:

1. Exact grant: success implies g = a (with explicit integer/natural conversion).
2. Conservation: B' + g = B. Prefer this for every result, with a zero grant on rejection.
3. Failure preservation: a <= 0 OR a > B implies rejection AND B' = B AND g = 0.
4. Total success: 0 < a AND a <= B implies success.

Avoid the vacuous laws `success -> ...` alone. The total-success law must reject an always-reject implementation. Failure preservation must cover a negative amount as well as zero and oversized amounts. Specify rejection's zero grant explicitly so an implementation cannot report false while consuming credit. B' and g being natural numbers ensures nonnegativity in this model; if using signed types, prove their nonnegativity too.

The service must execute precisely the candidate function covered by these proofs through the compiled artifact. There must be no handwritten TypeScript admission substitute, lookup table for the demo cases, or unproved production implementation hidden behind a proved reference function.

## API and persistence decisions to fix before freeze

These are reasonable engineering interpretations of the prompt, not extra product features:

- Initialize a new database to 100 exactly once. Opening an existing database must never reset the balance.
- Require a nonempty, bounded string requestId. Invalid envelope or malformed JSON is a bad request before a reservation exists; do not coerce null, strings, booleans, fractions, NaN, infinity or oversized JavaScript integers into valid credits.
- Choose and document a wire number domain. A simple JSON contract accepts only finite safe integers as numeric amounts; negative and zero numeric amounts reach the formal core and reject. The API rejects noninteger/unsafe/non-numeric payloads explicitly. The formal proof over mathematical integers does not by itself prove parser or machine-number conversion correctness.
- For every parsed request with a valid ID and integer amount, persist the original outcome, including insufficient-credit and nonpositive-amount outcomes. Store enough information to replay the original response unchanged; any historical balance in that response is historical, not current status.
- Existing ID lookup precedes admission. Same ID and same canonical amount returns the saved result with no change. Same ID and different canonical amount returns conflict regardless of current balance or whether the new amount would be affordable. Explicitly test a conflict after an originally rejected request.
- A malformed amount has no canonical integer identity under this API; document that its envelope-level rejection does not create or overwrite an idempotency record. If the implementation instead accepts broader JSON amounts, freeze a deterministic identity encoding and test invalid-amount repeats/conflicts too. Do not silently make those two semantics inconsistent.
- Keep ID lookup, decision, reservation-record insert and balance update in the same serialized database transaction. A crash before commit has no accepted effect; a crash after commit but before the response can be resolved by replaying the same ID. Commit must complete before returning success.
- Use one application process and a real local database with one transactional/serialized update path. Concurrency tests establish this tested deployment's behavior, not a distributed or arbitrary multi-process guarantee.
- Database and process boundaries must be real in restart tests. Recreating an in-memory object is not a process-restart test.

## Acceptance matrix

All rows begin NOT RUN. The runner/report must substitute measured statuses, source and artifact hashes, invocation/log paths, exit codes and timing, not narrative assurances.

| ID | Requirement/check | Minimum observable evidence |
|---|---|---|
| P01 | Preflight and delegated round trip | Workspace/integration/runtime/isolation/hosting results; actual small delegated task and returned output; no secrets in logs |
| P02 | Budget and durable supervisor state | Start/deadline, Bend start/deadline, checkpoint schema, session IDs, attempts, next action and deployment state |
| F01 | Bend trial first | Pinned identified Bend toolchain; real meaningful --verdict proof, ES-module compilation, TS invocation, broken invariant rejection; or bounded recorded failure followed by Lean |
| F02 | Formal route executable | Selected pinned formal toolchain; all four intended obligations checked with actual tool invocations; no admitted/unsupported proof claims |
| F03 | Runtime uses proved core | Compiled core hash, adapter invocation evidence and artifact contents; service tested with the same executable; no TS decision duplicate |
| A01 | Fresh state and grant | New DB = 100; reserve 30 succeeds with grant 30 and status balance 70 |
| A02 | Boundary grant | Amount exactly remaining balance succeeds, leaving zero; positive next request rejects |
| A03 | Invalid/oversized | Zero, negative, oversized, fractional, string, null, missing amount, unsafe integer and malformed JSON obey frozen API semantics; no consumption |
| A04 | Repeat and conflict | Repeat accepted and rejected integer requests returns original result; different amount under each used ID conflicts; no balance/record corruption |
| A05 | Concurrent different IDs | More total requested credits than available, concurrent submissions; sum of successful grants plus final balance = 100; no overspend; committed results consistent |
| A06 | Concurrent same ID | Concurrent identical ID/amount charges once; concurrent same ID/different amounts yields at most one original outcome and conflicts for others |
| A07 | Restart durability | Kill/stop actual app, restart with same DB, verify balance and accepted/rejected replay/conflicts retained; fresh DB initializes separately |
| G01 | Independent freeze | Review record plus hashes of laws, semantic imports, tests, manifest/toolchain and gate; candidate repair has enforced lack of write authority |
| G02 | Deterministic complete gate | Fixed required check list and tool invocations; reject missing/duplicate/extra or wrong-result records, skipped checks and malformed output; no candidate-controlled acceptance |
| G03 | Source/artifact binding | Canonical source snapshot hash/commit + proof/test results + core/service artifact digests; candidate edits invalidate record; exact accepted artifact deployed |
| M01 | Valid candidate | All formal and application checks pass with real logs |
| M02 | Over-allocation fault | Explicitly labeled mutation changes executable formal core; formal gate rejects; no deploy receipt for rejected artifact |
| M03 | Always-reject fault | Explicit mutation rejected by independent total-success obligation, not just an unrelated syntax error |
| M04 | Duplicate-charge fault | Service mutation actually double charges and is rejected by independent integration test; no deployment |
| M05 | Removed law/disabled check | Attempt to remove law or skip a required check is denied or rejected by protected manifest/runner policy; demonstrate intended failure rather than trusting candidate's checklist |
| M06 | Unavailable/timeout checker | Deterministic controlled checker fault, bounded timeout, blocked acceptance and no deployment; record distinct unavailable/timeout behavior if both tested |
| R01 | Real Codex repair | Actual Codex session gets rejected candidate/failure evidence, edits allowed candidate surface, and same frozen baseline then accepts repaired result; record diff/attempts/logs |
| D01 | Private deployment | Deploy accepted artifact without rebuilding; runtime artifact hashes match accepted manifest; clean/private test DB; HTTP/CLI smoke checks and private address or launch steps |
| S01 | Supervisor interruption | Checkpoint, end/interruption of supervisor context/process, reload state in resumed session/process, recover same task/artifact identity and continue without replaying uncertain work |
| O01 | Reproduction and final report | Repo/final commit, one documented reproduction command, acceptance matrix, raw evidence, identities, measured usage/time/attempts/interventions, proof/test/assumption limits, next experiment |

## Gate and proof trust review

1. Protected baseline includes definitions the laws import, not only theorem statement files. A candidate-owned helper redefining `valid`, `affordable` or the meaning of equality/success invalidates independence.
2. Compile/check from a clean evaluated snapshot. Pin compiler/runtime/package versions and lockfiles; record actual versions. A successful tool exit alone is insufficient if required declarations were removed, commands never ran, or stdout impersonates another command.
3. The evaluator constructs its own list of checks and spawns the tools itself. Capture start/end, argv, exit, output and timeout; parse reports defensively. Required checks must be exactly present and actually complete. Acceptance is computed by trusted runner code, not a candidate status JSON or shell exit wrapper.
4. For Lean, audit intended theorem declarations and their axioms/dependencies. Reject `sorry`, `admit`, user axioms, unchecked escape routes or candidate replacement of trusted spec imports. A theorem's printed text is not proof evidence. Document the compiler/kernel/runtime trusted base and any allowed foundational axioms. For Bend, prove that the actual invoked verification route supports the obligations rather than treating unavailable `--verdict` as success.
5. Isolation is a claim requiring evidence. Read-only modes on files owned by the same unrestricted worker are not enough because the worker may chmod them. Hash mismatch detection helps fail closed but does not itself satisfy 'outside write authority'. Prefer a separate restricted executor with read-only baseline mounts and candidate-only writable paths, or an enforced tool interface that only returns patches and has no baseline-write operation. Capture an attempted forbidden write and a failed modification check without altering the baseline.
6. Do not expose deployment credentials, signing authority, final acceptance writer or privileged deployment operation to candidate tools. Local private deployment may need no credentials, but access to the acceptance/deployment control still must be separate.
7. Candidate build/test execution can itself be adversarial. Execute it without access to evaluator-owned files, secrets or accepted-release directories. A mutation-only demonstration cannot justify a broad claim of resistance to a fully malicious agent if this execution boundary is unenforced.
8. Immutable snapshot inputs and output digests prevent a TOCTOU gap: build once from evaluated source, hash, test the built service/core, store the accepted package, deploy that package, verify runtime package hash. If any stage rebuilds it, demonstrate reproducible exact equality or re-evaluate the rebuilt bytes.
9. Preserve rejected-candidate evidence before repair. The valid final candidate must pass the same law/test/policy hashes used to reject the faults. Fixing the baseline during repair requires a fresh reviewed baseline and replay of all relevant acceptance cases; report it as an intervention, not the same repair loop.
10. Freeze limits as part of policy: per-check timeout and whole-run limit. Timeout/unavailable/malformed outcomes are explicit failures. Do not let stale previous passing records substitute for checks on the current source/artifact.

## Evidence and completion interpretation

- A real repair is distinguishable from restoring a known-good file: retain Codex session ID, rejected source hash, diagnostic supplied, generated diff and passing rerun. An intentionally injected bug is allowed and must be labeled.
- Supervisor resumption can be deliberately demonstrated with checkpoint/restart, but identify exactly what was interrupted. Worker-process restart alone does not prove supervisor resumption. Never manufacture an interruption event.
- Formal claims cover only the executable pure admission model. Adapter parsing, transaction/idempotency behavior, storage durability and HTTP behavior are tested assumptions unless separately proved. Hash binding demonstrates correspondence only under the trusted build/runner and isolation assumptions.
- Supply all nine requested deliverables even for PARTIAL. Preserve working artifacts and exact blocker/next-action checkpoint; mark any unsupported formal tool route, unavailable Codex repair, unenforced baseline boundary or undeployed artifact incomplete.
