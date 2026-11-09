# Final-approval preparation — `proofgate-coder`

**Prepared, not activated.** `@deveshkakkar` has approved the separate-agent architecture and retains human policy/administrative authority. That approval explicitly does not authorize permissions, credentials, installation, protection changes, owner-access changes or automatic merging. This packet and its PR require human review; the coding agent will not merge it automatically.

## Inventory conclusion

No suitable independent coding identity was confirmed. Both active connector and local CLI identify as the human owner; the local CLI can administer ProofGate and Git uses its credential helper. The current same-UID session can read the owner credential config despite mode 0600. This is an observed separation failure, not an independent coding environment.

The accessible connector installation is all-repositories and belongs to that connector App; it is not an account-wide App inventory or a least-privilege `proofgate-coder` identity. The local account-wide installation query returned 403 because that endpoint requires an App-authorized token. Public lookup of `proofgate-coder` returned 404, which does not establish absence of private Apps or guarantee name availability. Therefore propose a **new private App named `proofgate-coder`**, conditional on the owner's registration/installed-App check. No name was registered/reserved and no credential was generated. See [sanitized inventory](authentication-inventory.json) and [credential evidence](CREDENTIAL-SEPARATION.md).

Current main remains unprotected with no effective rulesets. Repository auto-merge is already false, Actions defaults to read and Actions cannot approve PR reviews. Those settings were read, not changed. Issue #28 was found closed and reopened under the owner's explicit instruction to keep it open until enforcement is verified; no issue finding was rewritten.

## Exact proposed configuration

| Artifact | Proposal |
| --- | --- |
| [App configuration](proofgate-coder.proposed.json) / [permission rationale](APP-PERMISSIONS.md) | Private, human-owned App; installation identity; only selected repository; Contents/PR write and necessary read permissions; no workflow/admin/secret/check-signing/status-write/Actions-write or user/org permissions |
| [CODEOWNERS](CODEOWNERS.proposed) | `* @deveshkakkar` — every changed path requires the human owner initially |
| [Main ruleset](main-ruleset.proposed.json) | PR + one fresh human CODEOWNER approval, last-push approval, resolved threads, only human may dismiss reviews, no bypass/force push/deletion; latest-base `offline` check from observed App 15368 |
| [Repository settings](repository-settings.proposed.json) | Preserve auto-merge disabled and Actions read/no-approval defaults; no other settings change |
| [Negative tests](NEGATIVE-SECURITY-TESTS.md) | Actual isolated actor/credential and server-denial tests on an explicitly approved canary; all NOT_RUN |
| [Activation and rollback](ACTIVATION-AND-ROLLBACK.md) | Human-controlled, snapshot-first, canary-first, production approval checkpoint, token containment before any governance rollback |

The initial rule requires human review on **every** main PR, not just policy. A future reduction for routine changes is a separate decision after independently authenticated verification and head/base/policy freshness have passed actual tests. Policy, verifier, workflow and security-boundary changes remain human-owned. The coding App's write permissions are not inherently “no merge”; platform rules and manual operation must be verified. Existing GitHub Actions regression checks are not the independently trusted verifier/check producer.

Workflow writes are intentionally denied to the coder App. Workflow edits may be prepared offline, but their upload/merge is blocked under the initial two-actor grant until a separately approved distinct author/pusher or independent reviewer arrangement exists; there is no implied human-assisted bypass. Owner-authored PRs cannot demonstrate independent owner approval. Future normal PRs need the distinct App author; the human reviews instead of making the last push on the bot PR. This owner-context preparation PR is review material, not a live independence test.

## Evidence and approval gates

**Observed:** owner identity/capabilities, credential-path reachability, narrow environment/SSH absence, unprotected governance, selected current settings/check producer, incomplete installation inventory and issue reopening. No secret values/key contents/token fingerprints were published.

**Not observed:** a suitable restricted App, isolated worker denial of owner access, any minted token's scope/expiry behavior, protected human approval/direct-push denial, independent signing, or merge-time freshness enforcement. Config validation, clean PR review and mock tests cannot fill these gaps. No live negative security tests are run during this preparation.

Before activation the owner must review this exact packet revision, choose/confirm the App and actual canary identity, approve the specific creation/install/credential/isolation test actions and agree recovery access. Canary authorization does not automatically authorize production installation/protection. Production activation needs actual canary/isolation/recovery evidence and a fresh reviewed snapshot. No automatic merging, new verifier App, credential revocation/rotation or owner-access change is implicit.

No credentials, permissions, installation or protections have been activated. Issue #28 stays open until authenticated policy/evidence and actual merge enforcement are verified. Current diagnostics retain false authority states; schema 1 remains diagnostic-only and must be rejected by any future admission path.
