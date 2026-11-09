# Audit execution: what now works and what remains open

PRs [38](https://github.com/deveshkakkar/ProofGate/pull/38) and [39](https://github.com/deveshkakkar/ProofGate/pull/39) are merged after passing checks, fresh independent review and completed no-findings Codex reviews on their exact heads. This is technical onboarding/integration progress, not developer adoption evidence or production admission.

## Actual hosted CLI observations

| Run | Executed boundary | Result |
| --- | --- | --- |
| [42536381195](https://github.com/deveshkakkar/ProofGate/actions/runs/42536381195) | Existing entitlement CLI with real Linux namespaces and systemd user scope | Empty doctor passes; baseline has 0/72 rule and 0/80 application mismatches; immutable-report retry exits 2; tenant spoof preserves rule and causes 6/80 application mismatches, exit 1 |
| [42537171457](https://github.com/deveshkakkar/ProofGate/actions/runs/42537171457) | Isolated evaluator launcher from an external python-stdnum checkout, pinned JSON fixtures and selected source | Baseline matches 7/7; immutable report is preserved, exit 2; deliberate checksum predicate mutation causes 2/7 mismatches, exit 1 |
| [42537171450](https://github.com/deveshkakkar/ProofGate/actions/runs/42537171450) | Existing entitlement CLI regression after the shared CLI extension | Hosted job passes; reported separately from the first entitlement artifact and external example |

The external example uses python-stdnum 006192e59be8ed6e08fd680256868a6c31eb2ba9. Five expectations interpret its published Luhn examples through the JSON shim; two invalid-input fixtures are explicitly agent-authored. The mutation incorrectly accepts `7894` and `not-a-number`. This is a deliberate negative control, not a newly found upstream bug. Equivalent CI with the same seven fixtures can detect it too. We did not measure comparative integration cost or detection advantage.

[AUDIT-EXECUTION-RESULTS.json](AUDIT-EXECUTION-RESULTS.json) records the first two runs' reviewed heads, distinct hosted PR merge revisions, artifact/report digests, exact source manifests, check counts and command exits. Both downloaded archive digests, all consumed verifier/contract hashes and recomputed consistency receipts were checked against reviewed code. The four exact raw JSON reports are now committed under [audit-reports](audit-reports/README.md), with bytes matching the original summary digests. Private raw copies are also retained; hosted ZIP artifacts/logs have seven-day retention and are separate from the committed reports. The committed raw reports make their observations/digests publicly inspectable after artifact expiry. Neither raw-file self-consistency nor this owner-reviewed summary authenticates the original producer or substitutes for hosted provenance.

No setup repair or automated PR-feedback repair was required for either hosted integration. Each live phase is complete; unused retry allowances are discarded. No candidate/upstream source or model run was performed on this home server. The host was not reconfigured. All 121 offline framework tests and release 46/six checks passed. Missing-dependency, timeout, unavailable-sandbox, invalid-output and concurrent-edit paths are unit tests with mocks. The isolated-launcher help path is an actual trusted-evaluator subprocess, without candidate execution. These categories must not be conflated with live negative sandbox trials or hostile-source security validation.

## Audit disposition

| Issue | Implemented/observed | Remaining acceptance gap |
| --- | --- | --- |
| #25 external integration | Selected-file JSON contract and external checkout work without evaluator edits | Selected Python batch boundaries without managed dependency packaging; host packages may be importable; customer-owned service integration and protected policy ownership unvalidated |
| #26 real CLI CI | Actual entitlement and external CLI smoke, source binding and immutable reports | Live infrastructure-failure matrix and broader clean-host/backend coverage |
| #27 portability/preflight | Candidate-free bounded `doctor`; setup failure before report reservation | No native macOS/Windows or supported container/VM backend |
| #28 authority | Explicit unauthenticated/unadmitted/unauthorized states for external results | No protected admission integration, attestation or repository protection change |
| #29 snapshot applicability | Visible identity, original-selected-file end comparison and exit 2 on observed change | No worktree lock; no merge-time exact-PR-head admission enforcement |
| #30 usefulness | No new claim; existing null comparisons retained | Actual developers, total specification/maintenance cost, comparison and repeat use |
| #31 setup/retry | Predictable preflight failure leaves the output path unused; later failed records remain immutable with retry guidance | Live setup failure/fix/retry matrix remains untested |
| #32 diagnosis | Stable redacted runtime codes, stage and completed checks | No reliable import/resource-exhaustion subdiagnosis from an arbitrary nonzero child exit |
| #33 summaries | Mismatch totals, up to three examples, fixture/source identities and scope | Examples are ordered, not minimized or grouped by semantic failure class |
| #34 distribution | Isolated checkout launcher and smallest external compatible example | No installable distribution or general reusable external admission action |
| #35 environment | Cleared environment declared and bound | No configurable environment matrix; production-only behavior remains outside coverage |
| #36 navigation | First-screen research/check-your-code/trust/evidence paths | Navigation changes have no measured newcomer comprehension benefit |

These entries are deliberately not automatic issue closures. A green fixture demonstration does not satisfy the broader acceptance criteria in the audit tracker.

## Next validation boundary

Use [the external integration instructions](EXTERNAL-JSON.md) for a developer-owned, compatible rule and [the existing real-developer trial protocol](DEVELOPER-TRIAL.md) to record total specification/adaptation, diagnosis/review effort, mistakes, refusals and second use against equivalent protected CI. The earlier equal-fact review packet remains suitable only for its own comprehension questions; it is not a substitute for an owned integration trial. There are no participants or responses yet. No outreach was sent.

The next missing input is an owned rule and an actual developer/reviewer response or an explicitly authorized contact. Technical replays cannot supply voluntary repeat use. Protected admission additionally requires an owner-selected policy authority and concrete repository/merge boundary; this prototype grants none. Continue independent safe fixes when justified, but do not fill these gaps by inventing customer requirements, weakening CI or extending autonomous repair loops.


## November 9 post-merge corrections

The original external run used a candidate-controlled schema 1 driver. Its results establish fixture agreement only; they do not prove that the intended Luhn function was called. Schema 2 now requires an independently reviewed driver digest, but does not upgrade old reports or prove arbitrary adversarial source correct. Normal worker Python site initialization remains enabled, so the earlier standard-library-only dependency wording was too strong; host packages may be importable and their inventory is not fully bound. The four original raw reports are public at their unchanged hashes. Current CI runs/logs remain separate evidence and are not silently substituted into that historical summary.
