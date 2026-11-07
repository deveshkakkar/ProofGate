# Extraction state — 2026-11-07

Base: ProofGate 96c5b52. Working branch: framework-contract-evidence-20261107.
Requirements source: vault master 47695e5, November 6 framework extraction hypothesis.

## Decision memo

- Preserve frozen reservation evaluator and evidence. Rewriting its baseline would destroy the comparison point.
- Start with a pure consistency kernel and no candidate-command execution. Shared lifecycle extraction needs two real adapters before defining its execution API.
- Use whole-input invalidation initially. Selective memoization without independently justified dependencies could reuse stale evidence.
- Return `consistent`, not a deployment authorization: unsigned evaluator observations cannot establish authority.
- Do not claim novelty for content addressing or immutable acceptance authority; Tenet and in-toto are close prior art. Research sources and limits are in SPEC.md.

## Evidence

Synthetic demonstration and focused unit tests only. Run results and PR review are recorded in the PR. Existing frozen offline release checks are the historical regression gate. No fresh formal, live-provider or end-to-end framework execution has occurred.

## Next depth-first branch

Implement a reservation adapter that consumes actual evaluator observations and validates file bytes and parsed output before constructing framework evidence. Do not stamp arbitrary historical reports with a fresh identity. Establish a second application with a materially different executable rule and independent failure controls, then measure which core changes were needed.

## Unresolved design questions

How does a trusted runner bind its own implementation and environment to observations? How are immutable snapshots enforced outside the original bubblewrap runner? Which second rule exposes meaningful application failures with affordable formal specification? These do not block the pure prototype but block claiming a reusable release gate. Do not treat the current API as stable or production authority.
