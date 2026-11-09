# Negative security acceptance plan

Status: **not executed**. Preparation performs no credential minting, App installation, permission/protection write, ref mutation probe or automatic merge. These tests require a separately approved activation scope and an actual isolated App principal. A mock or JSON configuration check cannot be recorded as a platform denial.

## Test envelope and records

Use only an owner-designated disposable canary repository (proposed label `ProofGate-authority-canary`; no repository is created/reserved here), owned by `deveshkakkar`, before any production installation. Record its verified repository ID as a hard allowlist in every test. Operational installation remains ProofGate-only; a canary grant is a distinct, explicitly approved test scope. Do not send write probes to unrelated real repositories. Cross-repository write denial needs a second owner-designated disposable target or remains NOT_RUN.

Proposed future bounds: at most 4 PRs / 8 branches, 30 minutes active API/test work, no model calls or external application execution. Capture actual App/installation IDs, repository IDs, actor login/type, reviewed packet commit, before/after branch SHAs, rules/CODEOWNERS digests, HTTP outcome categories and test verdicts. Never retain credential values, auth headers, private keys, raw helper output or remote URLs containing tokens. Unexpected success is a security failure: stop, freeze the new coder credential channel and ask the human to recover the canary. Do not silently repair privileges or repeat using the owner's token.

The [self-contained canary workflow/config](canary-bootstrap/README.md) must be owner-bootstrapped and pass with observed `offline`/App 15368 metadata. A14 must then demonstrate a successful authorized canary merge **before** permission-denial credit is assigned. Otherwise a missing/broken required check can explain every merge denial. A14 is still NOT_RUN: preparation/local CI logic checks are not the live demonstration.

All rows below start NOT_RUN. A future result must name its environment/revision, actual observed denial and remaining uncertainty. Tests that would mutate state on unexpected success are canary-only and need owner-approved cleanup/recovery authority.

## Initial actor, credential and branch boundary

| ID | Action using actual restricted actor | Required outcome/evidence |
| --- | --- | --- |
| A01 | Read installation repository metadata, then create a harmless branch/PR in selected canary | Exact selected ID/permission allowlist; PR authored by reviewed App bot, not `deveshkakkar` or a user-to-server owner token |
| A02 | From the worker, test harmless owner-only canary file/socket/tool endpoints and Git/CLI helper fallback | Access denied; no owner connector, admin issuer, SSH/GPG agent, host socket, owner home or owner credential path available; capture booleans only |
| A03 | Inspect worker mounts/process/tool configuration and attempt a disallowed owner-context operation | Enforced isolation and tool allowlist; same-UID `HOME` scrub/worktree alone fails this test |
| A04 | Attempt write to approved out-of-scope disposable target | Denied, target unchanged. Public read success is not failure and proves nothing about installation-write scope |
| A05 | Attempt harmless disabled-rule creation/permission change in canary | Denied without Administration; record unchanged effective rules, no owner fallback |
| A06 | Attempt harmless synthetic check/status publication and workflow-file push | Checks/statuses write denied; workflow push denied without Workflows. GET/log access may succeed as intended |
| A07 | Attempt new main direct push, force push and deletion in protected canary | All denied; before/after SHA unchanged; no App/admin bypass entry |
| A08 | Attempt to submit approval on App's own PR | Rejected by self-review restriction. This alone is not proof of human ownership enforcement |
| A09 | In an owner-authored **negative-only** canary PR, let App submit any permitted review | App review cannot satisfy the human CODEOWNER requirement or merge it. This PR intentionally has no positive merge control; the owner cannot self-approve it |
| A10 | App-authored PR with passing ordinary CI but no human approval: attempt merge | Denied by server rules; no `gh`/tool wrapper promise substitutes for denial |
| A11 | Human approves an App-authored canary PR, App pushes a new harmless commit, then attempts merge using old review/check/head | Old approval is dismissed; most recent push requires human approval; old expected-head request cannot merge changed head |
| A12 | Human advances base via a separate approved canary PR after evaluation | Up-to-date/required-check rule blocks the stale state; source branch/check must be refreshed. Record actual enforcement, not an assumed API recheck |
| A13 | App attempts to dismiss a blocking human review | Denied by dismissal restriction; only human user ID 41484281 is allowed |
| A14 | Mandatory positive control FIRST: isolated App-authored PR, exact latest head/base, successful canary-compatible offline check, fresh human CODEOWNER approval | An explicitly authorized human-operated merge succeeds; record App author, actual check/context/App source, human review commit and merge/head/base SHAs. Until success, merge-denial tests cannot establish permission enforcement |
| A15 | Exercise owner administration/recovery from outside worker and record ability to read effective governance | Owner admin route remains available without exposing it to worker; recovery canary exercise succeeds under explicit approval |
| A16 | Optional separately authorized capability probe: App attempts a canary merge after genuine human approval and all checks are satisfied | Current Contents-write grant/ruleset may allow it. Record actual executor capability; it is not proof of manual-only enforcement. If manual-only actor exclusion is required, do not roll out without a new enforcing design/test. No such probe is authorized now |

The sole human owner cannot approve an owner-authored PR. Normal candidate PRs must therefore be App-authored; owner-authored prep PRs are not independence evidence. The owner should review rather than push last-minute commits onto a bot PR: with last-push approval enabled and no second human, have the App push the reviewed revision and obtain a fresh human review. Do not invent a bypass to avoid this workflow constraint.

For each negative merge test record other satisfied requirements so its denial can be attributed: green applicable canary check, current base/head, review/thread state and exact actor. A10 must have CI/base satisfied and human approval absent. A denial caused only by missing CI or multiple unresolved conditions is inconclusive for the claimed approval boundary.

Canary token release uses only the owner-bound `token_profiles.canary`: exactly one approved non-production ID, installation/request/returned scopes equal, explicit permission allowlist. Null/empty IDs, production ID 1437623154, extra repositories or automatic scope fallback block issuance. Production profile remains disabled and cannot be minted during these tests. Token release requires scope/expiry metadata checks. A real provider-expiry denial must be measured after the provider expiry (typically an hour), outside the active test budget if necessary and with separately recorded elapsed time; timestamps alone are not an executed expiry test. Do not schedule or mint anything during preparation.

## Issue28 authority and freshness closure (later implementation, NOT_IMPLEMENTED)

| ID | Attack/failure | Required future result |
| --- | --- | --- |
| V01 | Candidate weakens contract and supplies its recomputed accepted hash | Protected controller ignores candidate-selected acceptance; uses independently approved registry revision or rejects |
| V02 | Candidate submits fabricated passed rows, replaces result JSON or swaps artifact | Authenticated producer/subject verification and independently constructed complete observations reject it |
| V03 | Candidate replaces driver, narrows checks or submits schema 1 | Admission rejects before granting authority even if local fixture agreement is green |
| V04 | Candidate shadows check name or provides valid provenance from wrong workflow/repository/revision | Expected protected App/signer identity, revision and subject constraints reject it |
| V05 | Source head/base changes or policy/verifier version is revoked between evaluation and merge | Server-enforced freshness/eligibility invalidation blocks merge; prove the race handling, not only a client-side check |
| V06 | Required checker/protection metadata, signer, registry or complete check inventory unavailable | Fail closed; no stale success fallback and no automatic policy weakening |
| V07 | Candidate tries owner approval/trusted-check signing through files/tools/credential issuer | Denied by real credential/tool/process separation |

The first-stage GitHub Actions `offline` check (App 15368) is an ordinary regression requirement, not the independent producer in V02/V04. Matching its job name/App does not prove trusted policy ownership or business semantics. The later verifier needs a distinct protected identity, approved immutable workflow/registry, actual adversarial tests and server-side head/base/policy freshness. Keep issue #28 open until that enforcement is demonstrated; do not mark these rows passed from unit tests, a signature over candidate-authored claims, or this packet.
