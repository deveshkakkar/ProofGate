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


## Portable shadow runner and hosted validation

A reusable Linux read-only runner now snapshots the pinned Git reference, substitutes one inspected module, checks exact held-out test identity, executes finite/compatibility checks with resource bounds, and binds source/artifact/verifier/workflow/dependency identities through the portable kernel. Incomplete/empty/skipped/error suites never pass. Historical-control success requires the exact expected per-suite pattern; a generic rejection is insufficient. Fresh review found and fixed that control-pattern loophole.

Hosted validation used the existing dispatcher on the review branch, so a merge was not required for testing. Three initial failures were retained (missing package, then namespace denial twice). The privilege-drop hypothesis was insufficient. Research and rootless inspection identified Ubuntu's shipped bwrap-userns-restrict profile; its hash is pinned, site overrides refused, global restrictions retained, setup guarded to disposable GitHub-hosted runners only. Two subsequent hosted runs succeeded:42341886078 accepted the valid ORfix;42341942377 rejected the known anonymous-read regression with heldout/contract passing and compatibility failing. Neither kernel/AppArmor global restriction was disabled. No package/profile was installed or loaded on the home server.

Full evidence is private under ~/.local/share/proofgate-framework/hosted-shadow-RUNID/; public sanitized lifecycle is benchmarks/drf/hosted-results.json. Exact local verifier evidence includes shadow-final-tj_1jr_7 and shadow-privcheck-bcm5z6s0; earlier full Git-prep evidence in shadow-ci-local-eaeg7v6p predates final verifier hashing. Fresh verifier/workflow hashes and current hosted records distinguish revisions.32 tests and original release checks pass. Hosted transport remains inspected-code diagnostics: in-process Python tests can be tampered with by hostile modules; no release authority is asserted.

Next independent verification: whole permissions-module tests on original and both proposed repairs, to check unrelated APIs omitted from the frozen class-level paired score. Do not silently amend the original three-case score with these post-hoc observations. Default-branch activation and new PR merges remain separate owner approval gates.

## Completed supplementary compatibility experiments

Owner authorized PR9/10 merges; main0d54be2 contains both. No later merge is authorized. Whole corresponding test files now pass without skips for both agent arms and upstream:43 OR,47 model permissions,65 renderer (155 total per repaired variant). Original controls fail2/1/1 respectively. Initial optional-dependency skips are retained in fullmodule-results.json; adding pinned django-guardian2.4.0 resolved the permissions skips. This is supplementary evidence, not the full DRF suite or a changed paired score.

Two fresh documentation-only contract authors both invented an anonymous-write restriction incompatible with the reference and all repairs; each generated eight failures (32/48 total tests), with no errors/skips. Neither specified the unresolved read behavior. doc-contract-results.json retains every result and proposed property. Django supports authorization backends granting anonymous permissions. Automatic admission is rejected; these proposals do not establish a defect or a correct requirement.

A caller-pinned finite change-frame comparator now checks complete observations outside an explicit proposed scope. Retrospective real-module probes enumerate448 inputs:384 protected and64 authenticated GET/HEAD inputs exempted from preservation. Reference and both agent repairs have zero outside-scope differences; historical upstream has12 anonymous-read differences. This reproduces known compatibility failure, not blind discovery or general superiority. Proposed scope is not approved business policy; the changed region still needs its own correctness obligations. Comparator runs outside source worker; producer authentication, reference correctness and hostile-source assurance are not established. Public traces support offline comparison; private snapshots/runtime manifests are retained in drf-preservation-380jvcxl.

Next decision boundary: authoritative acceptance needs an owner-approved change frame and intended new behavior. Independent research and prospective case selection can continue; no further repair orchestration is supported by the three passing ties. A future live shadow case must predeclare obligations before authoring, retain all outcomes and await upstream outcome without contacting maintainers.

## Intended-change composition and live open-PR observations

Owner authorized PR11 merge; merged bd2e2db and local main fast-forwarded. Separate worktree change-obligations-20261107 builds a pure finite proposal check that pins reference trace plus complete expected outputs inside an allowed change region. Existing preservation logic checks everything outside it. This prevents unchanged source passing a request simply because it preserves legacy behavior. The command reads traces only; it does not execute or authenticate source.

The retained live DRF10091 trial (base4acc640/head0951830, still open at metadata check) supplies two actual512-observation traces. Seven old methods preserve all448 observations. Unchanged base matches16/64 declared QUERY expectations and fails48; proposed head matches64/64. Expected outputs follow the contributor's stated empty permission map/class authentication intent, not an inferred RFC authorization mandate or approved application policy. Private sources/runtime records: ~/.local/share/proofgate-framework/drf-query-shadow-i7y_y2gl/. Public query-* evidence distinguishes actual observations from synthetic fault controls. No extra model calls or source runs were needed for composition; prior independent review validated private traces and identities.

Existing runtime limitation persists: these module probes use earlier Django4.1 wheels, although current DRF declares Django>=5.2. Their results establish mocked permission-method observations only. Supported-runtime/database/HTTP boundary validation is a separate next slice, with separate bounds and preserved failures. Neither finite matching nor a PR merge grants policy-admission or deployment authority. Automated repairs remain bounded to one pass per new PR; no later PR merge is authorized by this record.
