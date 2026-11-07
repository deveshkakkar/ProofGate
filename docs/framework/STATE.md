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


## Developer usability slice

Owner selected portable evaluator plus protected CI adapter, with developers using coding agents on business applications as the first audience. This supersedes the earlier pending architecture/audience question. PRs #6 and #7 merged into main fc77ce0. Protected CI authority configuration remains future implementation, not an established guarantee.

New developer command accepts a two-file local entitlement candidate, prints a first failing input and saves a new JSON report. Live checks: original exit 0; tenant-spoof application exit 1 with pure-rule PASS and cross-tenant counterexample. Evidence is retained under `/home/devesh/.local/share/proofgate-framework/developer-trial-3b4bmk6z/`. Unit tests use one mocked evaluator error to verify incomplete-report behavior; live candidate executions are separate evidence. No external participants have tried it. The trial protocol in DEVELOPER-TRIAL.md defines proposed usability and repeat-use thresholds plus backtracking triggers. External usefulness remains unvalidated.


## Paired historical replay slice

Owner requested autonomous progress until a real blocker; routine test/PR milestones are not stopping points. PR8 merged externally; working main base is 65817fd. The first private DRF replay was followed by six isolated author sessions for three researched historical PRs (7522, 8009, 9934), with equal prose requirements. Only treatment received executable contract feedback. All six completed under 180 seconds with no tool calls. Evaluations used real upstream modules, selected upstream test classes and finite contracts in network-disabled namespaces. Full upstream suites were not run.

Result: three passing ties, zero treatment wins/losses. This does not justify building another repair orchestrator. Post-hoc checking reproduced the anonymous-read regression in upstream8009 that led to revert9332; both fresh model arms preserved compatibility. This is reproduction of a known defect, not novel discovery or a treatment win. Public sanitized results and scoring code are under benchmarks/drf/. Private original inputs/logs are under ~/.local/share/proofgate-framework/drf-paired-00ypk2ju/. Scorer review found a partial-suite loophole, fixed by requiring exact expected counts across both arms and controls.

Next useful direction: package read-only shadow evaluation and compatibility checks with retained evidence, then a protected CI transport. No model-spending or implementation-advantage claim is inferred from a small null-result pilot. No new PR merge, deployment, repository protection or auth change is authorized by this state record.
