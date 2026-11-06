# Architecture and verification boundaries

ProofGate separates the code being evaluated from the authority that decides whether it may be deployed. Its demonstration is deliberately small: reserve credits from an initial balance of 100, persist each decision, and make retries safe.

## Three responsibilities

| Component | Responsibility |
| --- | --- |
| Candidate | Proposes the admission implementation, its proofs, and the TypeScript HTTP/SQLite service. |
| Frozen baseline | Supplies the reviewed mathematical model, required laws, entry point, checks, build recipe, and runtime lock. |
| Supervisor and gate | Applies allowed proposals, evaluates a clean snapshot, records evidence, and deploys accepted artifacts. |

In the recorded Codex experiment, the agent used a read-only session with no command tools and returned structured file proposals. A separate supervisor applied only allowed candidate paths. The supervisor, rather than the candidate, held evaluation and deployment authority. See the [experiment report](../REPORT.md#independent-gate-and-authority).

## The proof boundary

The server calls `Core.admission` from the generated `admission.mjs` module. Its reservation decision is therefore the compiled Bend implementation, rather than a separate handwritten TypeScript version of the algorithm.

The protected [model](../baseline/formal/Model.bend) and [laws](../baseline/formal/LAWS.bend) require:

1. A successful grant equals the requested amount.
2. The next balance plus the grant equals the previous balance.
3. Nonpositive or unaffordable requests are rejected with zero grant and unchanged balance.
4. Every positive, affordable request succeeds.

These are universal properties of the mathematical admission function. The fourth property prevents an implementation from satisfying the safety properties simply by rejecting every request. The [candidate proofs](../candidate/formal/PROOF.bend) are checked by the pinned Bend toolchain, which uses Lean for its verification kernel runtime.

The mathematical model uses natural-number balances and grants and a signed representation for requested amounts. The executable uses JavaScript numbers, so the HTTP boundary limits amounts to integers in `[-(2^48 - 1), 2^48 - 1]`; the persisted balance remains in `0..100`. The compiled-core bridge tests exercise this representation boundary, but do not prove the compiler correct.

## Four required checks

The [gate policy](../baseline/policy.json) requires all four checks:

| Check | What it establishes |
| --- | --- |
| Formal | The admission implementation satisfies the protected laws. |
| Build | The same admission implementation compiles to the executable module used by the service. |
| Bridge | The compiled module behaves as expected across 11,716 selected inputs, including boundary cases. |
| Application | Independent HTTP tests exercise validation, grants, retries, conflicts, concurrent requests, persistence, and process restart. |

The double-charge experiment illustrates why both proofs and application checks matter. The faulty service charged a retried request again without violating the pure admission function's laws. The HTTP/SQLite tests caught that application-level error. The agent's repair then passed the unchanged gate. This was an intentionally injected regression, not a claim of discovering a production incident.

Missing checks, malformed results, missing tools, timeouts, or changes to the frozen baseline prevent acceptance. The controlled timeout case simulates a hung checker; it is not a report that Bend itself hung.

## Accepted bytes and deployment

The gate records source and artifact hashes, checks that the artifact remains unchanged after testing, and copies accepted bytes into a new deployment directory. It does not rebuild at deployment time. An additional smoke test checks the copied service; its SQLite state is stored separately from the artifact.

These hashes establish correspondence within a trusted evaluation process. They are not signed third-party attestations or a zero-knowledge protocol. The verifier, its records, the supervisor, and the host remain trusted.

[`BASELINE.sha256`](../BASELINE.sha256) identifies the reviewed manifest in [`baseline/frozen.json`](../baseline/frozen.json). Files inside that baseline are preserved byte for byte. In particular, its README contains historical staging wording; the root report, acceptance record, and checked manifest describe the completed freeze. Changing a protected file requires a new reviewed baseline, not an edit to the historical record.

## What the prototype does not prove

The admission proofs do not cover the HTTP parser, numeric adapter, SQLite implementation, compiler, operating system, or deployment infrastructure. Runtime checks and finite experiments cover selected behavior at these boundaries.

The service uses one Node process and one SQLite connection. The additional [crash](../CRASH_REPLAY.md), [concurrent-history](../REALTIME_HISTORY.md), [lost-response](../PENDING_HISTORY.md), and [partial-body](../PARTIAL_BODY.md) experiments extend the tested scenarios. They do not establish correctness for arbitrary histories, power failures, or distributed deployments.

Bubblewrap limits the candidate process's filesystem and process visibility during evaluation. The pinned experiment shares host networking, and does not certify isolation against arbitrary hostile code or a compromised host. Use a dedicated Linux environment for reproduction and keep the demo local.

## Evidence versus a fresh run

[`REPORT.md`](../REPORT.md), [`ACCEPTANCE.md`](../ACCEPTANCE.md), and the checked-in evidence describe recorded experiments. `python3 reproduce.py` reruns the main gate and its negative controls with the current pinned inputs; it does not repeat the historical model calls. The four follow-up experiments have separate reproduction instructions in their linked documents.

The archived `supervisor/run-codex.*` launchers refer to the original experimental environment and are not portable setup commands. Public reproduction starts with `reproduce.py`.
