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

## Second slice — local experimental evidence

The core was reused unchanged for two integrations: `python3 -B -m framework.inspect_recorded` runs the existing reservation offline integrity checker, and `python3 -B examples/entitlement/experiment.py` runs a fresh finite-domain entitlement matrix. The reservation adapter reports only archived consistency; it does not relabel past proof checks as current observations.

Entitlement: 72 rule cases and 80 application cases per variant. Original passes both; always-deny and always-grant fail both; application tenant spoof passes the pure rule but fails boundary checks. Four small evaluator-authored variants only. No universal proof, deployed service, credential freshness or adversarial runner acceptance. Fresh review found missing replay coverage and incomplete aggregate limits; freshness is explicitly deferred, and transient systemd scopes plus bounded tmpfs were added. Adversarial exhaustion tests are still required before expanding supported inputs.

Private development evidence: `/home/devesh/.local/share/proofgate-framework/20261107/` contains reservation-inspection.json and entitlement-matrix.json. Reports include input identities and observed checks. The entitlement matrix ran locally in under one second after adding aggregate limits. These measurements are not competitive benchmarks. No paid provider calls or dependencies were added.

Next architectural dependency: select independent acceptance authority before building a general runner. Protected CI contracts, a separately administered local evaluator, and a developer consistency tool have different threat models and privileges. The prototype deliberately does not choose a production trust boundary or grant itself authority. A question has been sent to the owner; dependent runner work waits for that decision. Continue only independent documentation/tests while it is pending.
