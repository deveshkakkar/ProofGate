# ProofGate technical report

## Result and scope

Implementation, the frozen-gate matrix, actual Codex repair, repaired-candidate acceptance, supervisor interruption/resumption and exact-artifact private deployment smoke all succeeded. Final independent completion review and private-repository publication verification remain pending; see `ACCEPTANCE.md`.

The service is a private loopback TypeScript/SQLite application with 100 initial credits, durable idempotency outcomes (including integer rejections), conflict-before-admission semantics, and one synchronous `BEGIN IMMEDIATE` transaction path. It imports the **generated** Bend module directly. There is no handwritten TypeScript admission algorithm.

## Formal route

Bend 2.0.39 was identified as the official dependent/proof-capable toolchain, not the unrelated HVM language tooling. Before implementation, a meaningful add-zero induction passed `--verdict`, compiled to an ES module and was called from actual TypeScript; a false version was rejected. Lean 4.34.0 supplies the Bend verification kernel runtime; no fallback Lean application was needed.

The model uses `Nonneg{magnitude:n}` for n and `Neg{pred:p}` for -(p+1). Balance and grant are natural numbers. Protected `Model.bend` and `LAWS.bend` define:

1. Successful grant equals the requested amount.
2. Next balance plus grant equals prior balance for every result.
3. Nonpositive or unaffordable amounts return exactly rejection/zero grant/unchanged balance.
4. Every positive affordable amount succeeds (prevents an always-reject loophole).

All four are universal mathematical obligations, not only the demo values. `PROOF.bend` supplies actual checked definitions. Trusted `ENTRY.bend` independently imports the protected laws so removing an implementation proof leaves an unresolved obligation and fails. No candidate-owned predicate redefines affordability or validity.

The compiler represents natural values using JavaScript numbers. The wire guard limits magnitude to 2^48−1; the persisted balance stays in 0..100. Signed conversion and the generated executable are independently tested in **11,716 bridge cases**, including boundary amounts. This does not prove the compiler or give the machine unbounded integers.

## Independent gate and authority

An independent reviewer inspected the semantic model, proof obligations, test behavior, runtime pins and evaluator before freeze. The baseline hash is:

`0a634e64bf3ee9c885671f1c6b78f7d53820eddc47ae6ab8def376c26f36fa5e`

The baseline contains protected model/laws/entry, fixed checks, independent HTTP/bridge drivers, build recipe, bootstrap and complete toolchain lock. It was not changed during mutations or repair. Four checks are required: formal, build, bridge, application. Missing/disabled/duplicate/skipped/malformed/failing/timeout outcomes fail closed. The runner invokes tools and parses their results itself; application output is not an acceptance report.

The actual Codex worker was run with its supported read-only sandbox, no command/connector/browser tools and a read-only candidate mount. It returned JSON file proposals. A separately reviewed supervisor applier validated exact candidate-relative allowlists, traversal, symlinks, duplicate paths and schema; it never executed proposed commands. During repair, only Admission/PROOF/app could be changed. Tests included forbidden baseline writes/chmod/rename and malformed path proposals. Initial setup had a nested filesystem helper failure and a later danger-mode request was denied; that route was stopped, not bypassed. The successful narrow interface retained read-only policy.

Build and application execution use a separate minimal bubblewrap filesystem, private PID namespace, dropped capabilities, read-only source/baseline/artifact mounts and a dedicated writable DB mount. No authentication or deployment credentials are exposed. Network access for host-loopback HTTP tests remains a documented boundary: this is not a general hostile-code or kernel-exploit isolation certification. The separately trusted supervisor and host OS remain part of the trusted computing base.

## Executed experiments

`runs/initial-matrix/matrix.json` records the initial frozen gate cases:

| Case | Expected and observed |
|---|---|
| Valid | Formal/build/11,716 bridge/7 application groups pass; accepted |
| Over-allocation | Formal rejection in exact-grant proof |
| Always reject | Formal rejection specifically in total-success obligation; other vacuous laws adjusted to be valid |
| Duplicate charge | Formal/build/bridge pass; independent replay/balance integration fails |
| Removed law | Corrupted frozen copy rejected by manifest; actual baseline untouched |
| Disabled check | Corrupted frozen copy rejected by manifest; actual baseline untouched |
| Checker unavailable | Actual attempted nonexistent checker invocation fails; no acceptance |
| Timeout fixture | Supervisor-controlled sleep fixture exceeds timeout; killed and rejected; **simulated hung checker**, not a claim that Bend hung |

The missing-proof fixture also produced an actual `1 TODO found` rejection. Independent evaluator unit tests cover malformed reports, incomplete lists and failure behavior. No rejected case received a deployment from its rejected run. An explicit deployment attempt from the rejected duplicate-charge record also failed with exit1 before creating its destination (`evidence/rejected-deploy-attempt.json`).

## Actual Codex implementation and repair

Primary actual CLI session: `01a18450-27eb-7953-adc8-205d7a857993`. The small delegated smoke session was `01a1844f-6857-7190-a598-eb7a18e54241`, returning `proofgate-delegation-ok`.

Initial core/proof/application files were authored by that actual Codex CLI session, not relabeled native edits. Two compiler-directed proof repairs fixed constructor qualification and equality rewrite orientation. After baseline freeze, the supervisor deliberately inserted six lines that charged a cached replay. The actual gate rejected this candidate (local commit `1863a1b`). The same Codex session received the faulty file plus raw gate diagnostics and generated the six-line removal; the separate applier applied it, local repair commit `6a5c0551dc712487feb8c9df6bc7d2506c2cf0ac`. The later local documentation-only commit is `27025372cd1b9593833da6ac5dbb03b38632a056`; evaluated implementation bytes did not change. No baseline/test changes were permitted. The final rerun result is recorded under `runs/supervisor-resume/accepted-run/`.

`evidence/codex-actual-repair.jsonl`, `.receipt.json`, `.files.json`, the actual repair prompt, and `applied-actual-codex-repair.json` preserve the repair. This was an explicitly injected regression, not a naturally discovered production bug. It is distinguishable from a supervisor restoring a saved file: the real resumed Codex output produced the repair and its raw output is retained.

## Identity and deployment

Accepted evaluated source manifest SHA-256:
`359a633ce08ad3a39584f01a71ae73ffceb22baf68efde1742a17d7fe11f44d8`

Accepted artifact manifest SHA-256:
`22f322d60be8e88d98c8e2813e6280c9fa2de9966a776164e58b7fb8761615d3`

Compiled `admission.mjs` SHA-256:
`e842815ab774645585fbd240514dd31fffee919b1c16403fb958bc735ae9d47e`

Service `server.ts` SHA-256:
`0a71fd2b140713bd80d253e829694bb0ea5dd53fd9934dee813374ffab93e09d`

The evaluator snapshots source, proves it, builds once, tests that artifact read-only, and records hashes. Deployment copies those accepted bytes without rebuilding and checks equality; runtime smoke verifies hashes again. SQLite state is separate. The repo publication commit may differ from the local implementation commit because delivery docs/evidence are included; file/source/artifact hashes establish correspondence rather than pretending those commits are identical.

Initial exact-artifact private deployment smoke passed fresh/grant/replay/conflict/rejection and real process restart. Final repaired supervisor deployment receipt and smoke are stored under `runs/supervisor-resume/deployment/`. The demo is local loopback only; launch steps are in README, not a public URL.

## Supervisor interruption

`supervisor/orchestrate.py` is the actual durable local orchestration process. It evaluates the repaired candidate, fsyncs a checkpoint containing accepted source/artifact/result identity, and waits before deployment. As the interruption experiment, the implementation worker terminates that process (worker-scoped tool session, actual exit130) and starts a new process with `--resume`; the resumed process validates the checkpoint, does not rerun successful evaluation, and performs the real exact-artifact deployment. Events, PIDs, exit evidence and checkpoint are retained. This demonstrates **local supervisor process** interruption, not a fabricated chat/model context loss or mere worker restart.

## Budget, usage and interventions

Task start: 2026-10-28 20:47:53 UTC. Final repaired-artifact deployment smoke passed at 21:22:21 UTC (34m28s elapsed); packaging/reproduction/publication checks continued afterward. Overall deadline: 2026-10-29 20:47:53 UTC. Bend trial start: 20:49:19; deadline: 22:19:19. Full four-law proof passed at 21:06:49, inside the 90-minute cap (~17m30s). Main actual repair took 34.83 seconds. Actual per-check timestamps/durations are in result records; initial frozen valid run took 70.38 seconds; repaired final gate took 62.37 seconds (formal 46.64s, build 0.26s, bridge 0.11s, application 1.88s, remainder snapshot/hash overhead).

Latest primary session CLI counters reported input175,599, cached126,336, output16,926, reasoning1,022 tokens. Resumed-session snapshots appear cumulative; they are preserved without falsely summing them as independent billing. Monetary cost is not exposed. Independent supervisor/reviewer usage is not included in these CLI counters. Existing allowances/tools were used; no new paid hosting/service was provisioned.

Human interventions: approval to mount the existing Codex login read-only into a temporary writable runtime (20:53:26), permission for a private repo (20:54:06), and the user's creation of the private ProofGate repository. No login file was copied, no new credential was created, no denied session path was read, and no user computer was used. Machine setup retries/denials and compiler repairs are preserved in raw logs, not hidden as a seamless first pass.

## Limits and next experiment

The pure admission function is formally checked. Parser/representation conversion, SQLite transaction/idempotency durability, HTTP concurrency and process restart are tested, not proved. Compiler/kernel/runtime/host OS, the supervisor and its baseline-review decision are trusted. Numeric wire bounds, single-process service, local-only deployment and Linux-only pinned reproduction are explicit. No claim of production security, distributed linearizability, cloud availability, authenticated multi-user operation or general adversarial-agent resistance is made.

Next useful experiment: inject crashes at transaction boundaries (especially after COMMIT but before HTTP response), then replay request IDs after restart while recording a linearizability history. A separate follow-up could verify or strengthen the adapter/storage specification; neither is silently claimed in this POC.

## Reproduction verification

The default `python3 reproduce.py` path, including warm pinned-bootstrap verification, completed the full valid/negative/fault/tamper matrix and exact-artifact private smoke in the canonical relative layout. `runs/final-reproduction/` and `evidence/final-reproduction-console.log` retain its results; the artifact hash equals the final repaired deployment. Raw CLI capture format notes are in `evidence/README.md`.
