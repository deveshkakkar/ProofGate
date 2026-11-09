# Proposed `proofgate-coder` permissions

Status: architectural approval only. [proofgate-coder.proposed.json](proofgate-coder.proposed.json) is a review artifact, not a registration manifest or executed API request. No name is reserved and no App/key/token/installation has been created. An existing private App may still be usable if the owner supplies its registration/permission evidence; the accessible inventory did not confirm one.

## Exact initial grant

Owner/administrator: `@deveshkakkar`. Private App, installable only on its owner's account. No OAuth user authorization, no acting on behalf of the owner, no callback/setup service, no active webhook/subscriptions. Use installation authentication so PR/API actions are attributed to the App bot. Public slug lookup returned 404; registration availability is not established by that lookup.

| Repository permission | Level | Coding purpose |
| --- | --- | --- |
| Metadata | Read (implicit) | Identify the selected repository |
| Contents | Read/write | Read source and push proposed branches |
| Pull requests | Read/write | Open/update PRs and discuss proposed changes |
| Issues | Read | Read requirements; no issue mutation grant |
| Actions | Read | Inspect existing CI run/log/artifact results |
| Checks | Read | Read check conclusions; cannot publish the trusted check |
| Commit statuses (`statuses`) | Read | Read existing status results; cannot publish status |

Every other repository permission is **No access**, including Administration, Workflows, Secrets, Environments, Deployments, Attestations, Checks write, Statuses write and Actions write. No organization, enterprise or user/account permissions. No App manager/admin access for the coding agent. Do not add a permission merely to make a failed test pass.

**Two separate disabled profiles** are defined in `token_profiles` in [the App proposal](proofgate-coder.proposed.json):

- **Canary:** unbound, `repository_ids: []` and owner-approved name/ID null. This is not a mint request. After separate authorization, the issuer must bind exactly one verified canary ID distinct from production1437623154. The installation repositories, explicit request scope and returned token repositories must all equal that canary-only ID. Refuse unbound/empty/omitted scope; never fall back to production or all installation repositories. **No ProofGate token or installation grant is minted/added during canary testing.**
- **Production:** fixed ID1437623154 (`deveshkakkar/ProofGate`) but disabled pending separate production approval after canary/isolation evidence. This profile cannot be selected as a canary default and is never a substitute when a canary ID is unknown.

Both retain the exact permission map above. Do not install on all repositories. Provider tokens expire after about one hour; the future owner-controlled issuer must validate granted scope, permissions and expiry before release. No token is minted during preparation; these profile invariants are not yet a deployed credential issuer.

The App private key stays in an owner-controlled credential issuer outside the coding environment. The coding worker receives at most a short-lived, selected-repository installation token. It receives neither owner tokens nor an App private key capable of minting broader tokens. Do not put tokens in remote URLs, Git configs, PR bodies, logs or Git. Use a private ephemeral credential channel/helper for HTTPS; no `gh auth login` that persists credentials in the worker home, and no fallback to the owner's helper.

## Permission limitations that still need enforcement

Contents write is not a native “PR-only” permission: it can update refs and participate in merging. Pull requests write can submit review operations. Therefore the human CODEOWNER/main ruleset and actor identity tests are mandatory; the permission map alone does not prevent merging without approved rules or establish who approved policy. The intended **human approval before merge** is a server condition after activation/tests. **Human execution of the merge** is only the requested operating procedure: once approval/check requirements are satisfied, the App may invoke the merge API using Contents write. The proposed grant/ruleset does not exclude that executor. The agent must not do so during manual operation, but this instruction is not an independent technical boundary. Repository auto-merge remains disabled; that feature setting does not disable direct API merge calls. If human-only execution is mandatory, rollout must wait for a separately approved enforcing broker/merge-actor boundary and an actual after-approval capability test.

Workflows write is deliberately absent. A GitHub App needs that permission to edit `.github/workflows`; workflow changes can be designed locally as offline patches, but upload/merge is **blocked under the initial two-actor grant**: the App cannot push them and the sole human cannot approve their own authored/latest-pushed PR. A separately approved non-owner author/pusher with workflow permission, or an additional independent human review arrangement, is required before workflow changes can proceed. Neither route is granted here; do not elevate the coder App or loosen review as a workaround. Changes to all currently writable paths still require human ownership review. The App cannot be a future protected verifier/check producer: that requires a different independently protected identity, credential store and review.

Public reads of other repositories may be possible without credentials and are not an installation-scope breach. Test installation scope using declared installation repositories and denial of writes to an owner-approved out-of-scope disposable target, not a public GET. Do not probe writes on unrelated real repositories.

## Source references checked November 9, 2026

- [Choosing App permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app): Contents/Workflows permission distinction and minimum access.
- [Installation token scope](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app): repository/permission restrictions and token lifetime.
- [App versus user token attribution](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps): choose installation identity rather than an owner-user token.
- [Private App visibility](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/making-a-github-app-public-or-private): owner-account installation restriction.

[GitHub merge API permissions](https://docs.github.com/en/rest/pulls/pulls) explicitly allow installation tokens with Contents write; do not represent a manual operator instruction as a platform restriction.
