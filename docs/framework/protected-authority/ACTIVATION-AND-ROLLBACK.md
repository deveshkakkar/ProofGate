# Final approval scope, activation sequence and rollback

**Nothing here is authorized to execute yet.** Architecture is approved; credential creation, App registration/installation, account/owner access changes, ruleset activation and auto-merge are not. These procedures define what the next human approval would cover. Default on uncertainty: stop new coder activity and preserve human administration, not weaken review or inject an owner token into the agent.

## Exact proposed artifacts

- [proofgate-coder.proposed.json](proofgate-coder.proposed.json): private App owned by `deveshkakkar`; installation authentication, exact permission allowlist and selected operational repository ID 1437623154. All IDs for a newly registered App/installation remain unknown until owner registration/readback.
- [CODEOWNERS.proposed](CODEOWNERS.proposed): `* @deveshkakkar`, installed at `.github/CODEOWNERS` only after approval. No exclusion or bot owner.
- [main-ruleset.proposed.json](main-ruleset.proposed.json): active branch rule targeting only `refs/heads/main`, zero bypass actors; PR plus one human CODEOWNER approval, dismissal of stale approvals, last-push approval, resolved threads, owner-only review dismissal, no deletion/force pushes; latest-base `offline` check from observed GitHub Actions App 15368. This existing App/check is not the future verifier authority.
- [repository-settings.proposed.json](repository-settings.proposed.json): auto-merge remains false; preserve Actions default read permissions and Actions PR-review approval false. No other repo preference change is proposed.

## Owner decisions before any activation

Record explicit approval of the exact packet revision/diff and whether an existing reviewed App qualifies or a new private `proofgate-coder` should be registered. Owner must select the canary repository/name/ID and authorize any creation/install/token/cleanup actions there; none are assumed from this document. The current public slug lookup does not reserve a name. If the name is unavailable, stop for a reviewed alternative rather than installing an unrelated App.

Choose the actual isolated worker and owner-controlled credential issuer, including independent operator identity and the paths/tools excluded from the worker. A restricted App alongside this session's readable owner `gh` config/connector is unacceptable. The owner keeps current administrative access; no credentials or access are silently deleted, rotated or reduced by this plan.

Approval for canary registration/testing does not automatically approve adding ProofGate to an installation, activating main protection, a future verifier App or automatic merging. Those production steps require final review of actual identity/isolation/test/recovery evidence and the exact read-back configuration.

## Sequence after the corresponding approval

1. **Snapshot/readback.** Owner captures effective repo rulesets (including parents), classic protection, all active CODEOWNERS locations, repository auto-merge, Actions defaults, App grants/selected repositories and owner admin access at that time. Save sanitized digests/IDs and privately retain any sensitive admin recovery metadata. The November 9 snapshot is not a license to overwrite later changes. Stop on drift until reviewed.
2. **Register or qualify identity.** Owner verifies App owner/ID/private visibility and exact permissions; keeps any generated private key in the owner-controlled issuer, outside coding tools/files/processes. No user-token OAuth flow. Install only on the explicitly approved canary initially; mint only appropriately scoped temporary credentials after isolation gates are met. Do not use an all-repositories installation or an existing owner-user connection as the coder identity.
3. **Bootstrap canary governance.** Before releasing a coding credential into canary, owner establishes the exact approved CODEOWNERS and ruleset through a one-time owner-controlled bootstrap. This is explicit root-policy setup, not evidence of independent approval. Never leave an unprotected credential-enabled gap. A human cannot approve their own bootstrap PR; either owner directly installs the explicitly reviewed bootstrap before protection exists, or an independently authored bootstrap PR is manually reviewed/merged under separately agreed safeguards. Record which path was approved and used.
4. **Verify.** Read back effective configuration, CODEOWNERS parsing/owner access and expected check source. Execute the bounded [canary tests](NEGATIVE-SECURITY-TESTS.md). Confirm owner can recover without worker access to owner credentials. Any unexpected authorization stops release; do not fix it by broadening permissions, changing approvers or adding bypasses.
5. **Production approval checkpoint.** Present App/installation IDs, verified isolation boundary, actual test matrix (including failures/NOT_RUN), recovery evidence, current production snapshot, exact artifact digests and proposed installation scope change for explicit human approval. Do not apply canary rules or credentials to ProofGate merely because tests pass.
6. **Only after production authorization:** owner-controlled installation/governance application, readback and bounded live validation. Initial workflow is App-authored candidate PR → fresh human review on exact head → human manual merge. No agent merge or automatic-merge enablement. Source/policy/workflow/security changes all require human approval initially.

Issue28 remains open after stage 1; no `policy_admitted` or `merge_eligible` result may be inferred from manual-review protection. Independently authenticated verification and merge-time freshness are separate later work with their own proof and approval. Narrowing human ownership or enabling automatic routine merging is a future reviewed change, never an implicit consequence of this rollout.

## Rollback procedure (human-controlled; not executed)

R0. **Contain new authority first.** Stop the new worker and stop new token issuance. Owner decides whether to revoke only the newly issued coder tokens/suspend or remove the new canary/operational installation grant. Do not affect unrelated Apps, owner sessions, keys or services. Merely waiting for expiry is not immediate containment. No credential enters the coding environment during recovery.

R1. **Record state and preserve evidence.** Capture relevant App/rule/installation IDs, branch SHA, approval/check metadata and unexpected authorization, with secrets excluded. Preserve the last-known-good snapshot and all failed test outcomes. Do not delete artifacts or force-reset source history to hide the failure.

R2. **Prefer retaining protection.** If the worker/issuer fails but human review/admin still works, leave human main protection in place and pause coding. Reverting to unprotected main is not the default recovery.

R3. **If governance itself locks out intended work**, the human administrator uses their independent recovery route to modify only this rollout's identified ruleset/changes to the exact approved prior state after comparing current drift. Revert CODEOWNERS through a human-authorized path. If prior rules were absent, restoring absence weakens protection and needs explicit owner approval after coder access is contained. Never delete every ruleset, add a general bypass, or overwrite concurrent governance changes.

R4. **Verify recovery.** Owner checks admin access, effective rules, source SHA, App selected repositories and disabled auto-merge. Prove the stopped/removed coder grant cannot write. Restore normal work only after the owner reviews recovery evidence. Current owner credentials/access remain unchanged; rollback does not reattach them to the worker.

R5. **Cleanup is separately scoped.** Closing/deleting harmless canary PRs/refs, deleting an App/key or removing test repositories are destructive/revocation actions requiring the owner's scoped permission. Their existence is not permission to clean them up automatically. If owner recovery fails, stop and escalate to the owner; the coding agent never self-grants an emergency credential or bypass.
