# Independent read-only Codex boundary review

2026-10-28 21:00 UTC.

## Verified evidence

- Read supervisor/run-codex.sh, supervisor/sandbox-boundary-test.sh, evidence/bwrap-hardened-boundary.log and evidence/preflight-codex-patchonly.{jsonl,stderr}.
- Actual Codex session 01a1844f-6857-7190-a598-eb7a18e54241 reached turn.completed with the requested `proofgate-delegation-ok` response. Recorded usage: 12,099 input tokens, 10 output tokens. The event stream shows no executed tool call. This proves the small delegated text task, not implementation or repair.
- Final wrapper selects CLI read-only, disables project-document auto-loading and several command/connector/browser routes, and bind-mounts candidate read-only. Existing auth/config are read-only mounts in writable temporary runtime; original home and /run are masked. PID/IPC/UTS namespaces, new-session, die-with-parent and cap-drop ALL are enabled.
- Boundary smoke demonstrated protected supervisor touch/chmod/rename failure with EROFS, hidden original home auth/session paths, a small private process view and zero effective capabilities.

## Qualification

The boundary smoke used a writable candidate bind to demonstrate candidate writes, whereas the successful final CLI wrapper uses a stricter read-only candidate bind. That evidence supports the supervisor protection but is not a byte-identical invocation test. Actual patch-only writes still require a separate trusted applier review.

Retaining the CLI's allowed read-only policy resolves the previous policy denial without changing approval requirements. The ignored inherited config key and deprecated imagegenext flag are warnings; they are not proof of disabled arbitrary tool routes. CLI filesystem enforcement plus outer mounts are the write boundary, not the model's promise or apply_patch_freeform setting.

## Remaining review gates

1. Inspect the actual candidate-only file applier: strict schema, path allowlist, no traversal/absolute paths/symlinks/protected targets, no shell evaluation of generated output, atomic writes where practical.
2. Inspect and freeze actual independent baseline dependencies and manifest.
3. Prove unchanged baseline hashes across actual repair.
4. Separately review evaluator/candidate build execution boundary and exact artifact binding.
5. Correct stale wrapper comments describing the inner sandbox as removed; consider minimal environment allowlist to avoid unnecessary inherited state.

This does not certify network isolation, arbitrary OS exploit resistance, or overall ProofGate acceptance. No additional authenticated launch was performed by the reviewer.

## Candidate file interface review, 21:02 UTC

Inspected supervisor/apply-codex-files.py and supervisor/run-codex.py. The latter now limits inherited environment to a documented transport/profile allowlist and uses the read-only CLI route. evidence/bwrap-patchonly-boundary.log demonstrates direct candidate writes as well as supervisor writes/chmod/rename rejected, with zero effective capabilities.

The applier accepts only structured JSON with exact top-level/file keys, bounded file count/content size, canonical candidate-relative allowlisted paths, and no symlink path components. Initial creation and repair allowlists are separate; repair cannot write Model/LAWS/package metadata. It performs atomic temp-file replacement and does not execute checksToRun or other generated metadata. Independent reviewer ran eight checks in a disposable directory: traversal, absolute/noncanonical path, law modification and symlink rejection, normal allowed write, and preservation of a hardlinked protected file. All passed; logs: proofgate-review/applier-independent-tests.log.

Approved for this scoped serialized supervisor interface. Condition: no concurrent untrusted process may mutate candidate directories during validation/application; path checks are not an adversarial race-proof openat traversal. The supervisor, not generated content, controls apply mode, record path and invocation. Baseline freeze still awaits review of actual formal specs/dependencies, tests, policy and evaluator.
