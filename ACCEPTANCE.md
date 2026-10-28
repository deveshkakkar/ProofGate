# Acceptance matrix

Baseline: `0a634e64bf3ee9c885671f1c6b78f7d53820eddc47ae6ab8def376c26f36fa5e`.
Final evaluated implementation commit: `6a5c0551dc712487feb8c9df6bc7d2506c2cf0ac`.
Final evaluated source: `359a633ce08ad3a39584f01a71ae73ffceb22baf68efde1742a17d7fe11f44d8`.
Final accepted/deployed artifact: `22f322d60be8e88d98c8e2813e6280c9fa2de9966a776164e58b7fb8761615d3`.

**COMPLETE: all 25 independently reviewed acceptance rows PASS.** PASS means actual evidence, not a model assertion. Private publication and final completion review were verified. Independent original checklist is in `review/requirements-review.md` in the delivery bundle.

| ID | Status | Evidence |
|---|---|---|
| P01 | PASS | Preflight logs/toolchain pins, actual Codex `proofgate-delegation-ok` smoke, `evidence/preflight-codex-patchonly.jsonl`, boundary logs |
| P02 | PASS | Start/deadlines/session IDs/attempts in implementation checkpoint; actual durable `runs/supervisor-resume/checkpoint.json` |
| F01 | PASS | Meaningful Bend induction, compiled ES-module real TS call, false invariant rejection: `bend-smoke-verdict.log`, `bend-typescript-call.log`, `bend-broken-verdict.log` |
| F02 | PASS | All four universal obligations: final accepted-run formal stdout `ALL PROOFS CHECK`, exit0 |
| F03 | PASS | Built `admission.mjs` hash, actual service Core.admission call; 11,716 independent compiled bridge cases |
| A01 | PASS | Final application `fresh-grant` group: real fresh SQLite100, grant30, remaining70 |
| A02 | PASS | `boundary`: exact balance succeeds; next positive request rejects |
| A03 | PASS | `invalid`: signed/wire bounds, zero/negative/oversized, malformed types/JSON/UTF8, body limit, invalid-envelope ID reuse, negative zero |
| A04 | PASS | `repeat-conflict`: accepted/rejected historical response replay, conflicting IDs, no extra charge |
| A05 | PASS | `concurrent-distinct`:30 concurrent7-credit requests,14 successes, final2 |
| A06 | PASS | `concurrent-same`: repeated same ID charges once; mixed-amount race yields original and conflicts |
| A07 | PASS | `restart`: actual process stop/restart same SQLite; accepted/rejected replay, balance and conflict persist |
| G01 | PASS | Independent approval and frozen manifest; read-only candidate/no-command interface, protected write and applier-path tests |
| G02 | PASS | Fixed4 checks; independent unit tests, strict result parser, failclosed fault records |
| G03 | PASS | Source snapshot and artifact manifests in final accepted-run/result.json; no rebuild deployment receipt and post-smoke equality |
| M01 | PASS | `runs/initial-matrix/valid/result.json` and final repaired accepted-run/result.json acceptedtrue |
| M02 | PASS | `initial-matrix/overallocation`: actual formal rejection in exact grant; no deployment |
| M03 | PASS | `initial-matrix/always-reject`: actual formal rejection in total_success; not syntax failure |
| M04 | PASS | `runs/main-duplicate-charge`: formal/build/bridge pass, application fails expected balance65; acceptedfalse |
| M05 | PASS | `initial-matrix/removed-law` and `disabled-check`: original frozen identity rejects corrupt copies; actual baseline unchanged; forbidden write tests also deny |
| M06 | PASS | `initial-matrix/unavailable`: actual missing executable OS failure; `timeout`: separately labeled controlled sleep timeout fixture, both reject |
| R01 | PASS | Actual same Codex session repair output/diff/receipt; app-only applied; final same-baseline all4 checks pass |
| D01 | PASS | Final deployment/deployment.json rebuiltfalse; smoke.json passed, unchanged artifact, persistent separate DB, loopback only |
| S01 | PASS | Supervisor session83501 exit130, initialPID12; new session5259/PID6 reload, no evaluation replay, actual deployment; events/checkpoint/tool-result evidence |
| O01 | PASS | Default reproduction including bootstrap passed; docs/raw logs/hashes/resources complete. Private commit cd86020bf255428369791097865595ce54b9d300 verified remotely across all 456 paths; independent closure review confirms all 25 PASS. Supplemental relocated three-archive reconstruction also passed (Lean/Node cached, Bend fresh download). |

Application evidence: `runs/supervisor-resume/accepted-run/logs/application.stdout`; bridge evidence: sibling `bridge.stdout`; exact invocations, exit codes, hashes and elapsed times: `accepted-run/result.json`.

Clarifications: graceful real process restart was tested, not every possible abrupt crash boundary. The timeout is a controlled injected sleep, not an observed Bend hang. The unavailable checker case is an actual failed executable invocation. This is a local supervisor-process restart, not a claimed model-context interruption. All seven application groups and 11,716 bridge inputs are finite tests, distinct from the universal formal obligations.

Initial verified private publication: [cd86020bf255428369791097865595ce54b9d300](https://github.com/deveshkakkar/ProofGate/commit/cd86020bf255428369791097865595ce54b9d300), verified at 2026-10-28 21:55:43 UTC. See `review/closure-review.md` and `evidence/publication-verification.json`. A later docs-only closure commit leaves the evaluated source/baseline/artifact identities above unchanged.
