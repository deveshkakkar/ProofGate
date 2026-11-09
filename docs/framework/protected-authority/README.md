# Protected policy authority — proposal, not active enforcement

**November 9 update:** architecture is approved; activation is not. The current [approval packet](APPROVAL-PACKET.md) contains the authentication inventory, exact App/config proposals, evidence gaps, negative tests and rollback. No credentials/permissions/protections/auto-merge are activated, and this packet is not automatically merged. The design below remains the staged implementation contract.

Issue [28](https://github.com/deveshkakkar/ProofGate/issues/28) remains open. A contract and its hash supplied by the same caller cannot establish independent policy approval. The current kernel, CLI, schema 2 driver pins and clean CI runs supply no authenticated admission authority. A schema 1 warning is useful diagnostic wording, not an acceptable admission fallback.

## Confirmed current state

Read-only checks on November 9, 2026 found main at 2a6c541 with `protected:false`, a classic-protection response 404 `Branch not protected`, and an empty repository ruleset collection including parent rules. The connector's separate classic-protection request returned 403 because its integration lacks that permission; the local GitHub client supplied the positive unprotected observation. [observed-state.json](observed-state.json) retains sanitized facts. These are point-in-time observations, not a continuous monitor.

The coding session currently operates through the owner's GitHub context. While an agent can act as the policy owner, it is not an independent principal. Requiring it to promise that it will not approve a policy is not an enforced boundary. Separating identities also requires keeping owner credentials and approval tools out of the coding agent's execution environment; a differently named bot alongside accessible owner credentials is insufficient.

## Recommended first activation: human-owned policy and protected main

Human policy owner: `@deveshkakkar`, acting through credentials unavailable to the agent. Candidate author: a distinct restricted GitHub App/account. The agent may propose branches/PRs, but cannot administer rules, impersonate the owner, bypass main protection, or publish the future trusted verifier's check. Contents-write permission alone does not prohibit the merge API: server-side protections must remain enforced for that actor. It may merge only when those independent server requirements have been satisfied.

The inactive [CODEOWNERS proposal](CODEOWNERS.proposed) initially assigns every changed path to the human policy owner, including transitive evaluator/runtime dependencies and newly added helpers. The refined inactive ruleset also restricts review dismissal to that human and requires the observed ordinary `offline` check against the latest base. Narrowing that scope is a later reviewed change; it is not inferred from a list of current top-level policy files. The inactive [main ruleset proposal](main-ruleset.proposed.json) requires a PR and one approval, code-owner approval, dismissal of stale approvals, approval of the most recent push, resolved review threads, and no force pushes/deletion. There are no bypass actors. CODEOWNERS is not protection by itself; it must be installed and enforced together with the ruleset. The administrator remains the ultimate trusted owner able to change governance.

Activation preconditions:

1. The owner chooses/provisions the distinct agent identity and confines it to an environment without owner credentials, approval tools, rule administration or a trusted-check signing key. Do not print, copy, rotate or delete current credentials as part of this proposal.
2. Verify that a PR authored by that identity can be approved by the human owner. Current owner-authored PRs cannot serve as a demonstration of independent owner approval. Do not lock the sole approver out or bypass the requirement to make this test pass.
3. Capture current rules/CODEOWNERS as rollback inputs. Install the approved CODEOWNERS and exact reviewed ruleset through an owner-controlled administration step. These files under docs are not automatically applied. No application action or branch-protection write occurs in this PR.
4. Read back the effective rules and test denied direct pushes, unapproved policy PRs, stale approvals, agent approval attempts, and force pushes using harmless proposed commits in a designated test repository first. Test the owner's recovery path before applying to main. Missing permissions/state produce an unverified result, not assumed protection.

When activated and verified, this step enforces human approval before every main PR merge. It does not enforce that a human executes the merge: the Contents-write App may call the merge API after requirements pass. A human-operated merge remains a procedure unless a separately approved enforcing boundary is added. It does **not** authenticate arbitrary JSON evidence or complete issue #28. It also changes the current automatic-merge arrangement: a clean Codex review alone would no longer satisfy human policy approval. That operational change and credential/role changes require the owner's explicit approval.

## Next implementation: protected evaluator and authenticated merge check

The following is the intended implementation contract; it is not a deployed workflow or a claim that the current sandbox is hostile-source safe.

| Material/decision | Authority | Candidate may control |
| --- | --- | --- |
| Accepted rule/contract, minimum schema, driver pin and evaluator revision | Human-reviewed policy registry on protected main (or a separately administered policy repository) | Propose a policy PR; cannot approve/adopt it |
| Policy selection for a source PR | Trusted workflow/controller loads the approved registry at an explicit protected revision | No contract path or accepted digest supplied by the source PR is authoritative |
| Source snapshot | Controller obtains repository, PR number, head SHA and base SHA from GitHub and binds selected file bytes | Proposed implementation bytes, never a different passing revision substituted for the live head |
| Driver and verifier | Registry-pinned reviewed implementation, immutable to the worker | Cannot replace the driver, check inventory, result parser or accepted pin |
| Finite observations | Secret-free isolated worker; trusted controller evaluates complete typed outputs outside candidate control | Source may emit outputs, but not a preaccepted receipt or signing/check credential |
| Result provenance | Separate trusted signing job/service, no candidate code or untrusted artifact execution; authenticated signer constrained to approved workflow/revision | No arbitrary `passed` JSON accepted as authoritative; no signing credential in the worker |
| Merge eligibility | Independently protected GitHub App/check identity and repository enforcement | Cannot satisfy a required check by copying its name into a different workflow |

Policy and implementation changes are separate approvals. A source PR that changes a contract and recomputes its hash continues to be tested against the already approved registry. A changed policy must first pass its separate human-controlled review/adoption path, then source verification reruns under the approved version. Schema 1 is unconditionally rejected by this future admission path even when its local fixture checks pass; schema 2 alone is still insufficient without protected ownership/provenance.

Use an established attestation format/provenance verifier rather than inventing a signature scheme. Verification must constrain the signer workflow/repository **and approved immutable revision**, artifact subject/digest and relevant run identity; finding a valid attestation from any workflow in the repository is insufficient. The statement must bind exact source repo/PR/head/base, approved registry/contract/driver/verifier revisions and the complete result. Candidate-authored predicate fields are not made truthful by signing them. A trusted signer must only attest a result independently constructed by the approved controller.

Before merge, enforce freshness against the live PR head and the active policy/verifier version. Head changes, policy revocation and base changes invalidate the applicable result. Use GitHub's expected-head merge guard together with server-side up-to-date/required-check enforcement (or a supported merge queue); a client-side recheck followed by an unchecked merge leaves a race. Independent policy-version changes also need coordinated revocation of old eligibility, for example a required-check epoch rotated under owner control. A specific server-side design and race tests must pass before automatic admission is enabled; the current proposal does not solve a distributed policy-update/merge race by assertion.

Do not use a same-named GitHub Actions job as the sole trusted producer. The trusted check's expected App identity and credentials must be independently protected; an agent allowed to use that App's credentials could still forge it. Initially retain the human approval requirement while exercising this path in shadow mode. No signing permissions, App installation, required-check identifier or production trust root is selected/created here.

## Required negative acceptance evidence

- Candidate weakens contract and supplies its own new hash: approved policy remains unchanged; admission rejects or evaluates against the original approved requirements.
- Candidate supplies fabricated passed rows, swaps an artifact, alters the driver, shadows the check name or supplies an attestation from another workflow/revision: no eligible authoritative check.
- Schema 1 fixture agreement: no admission, regardless of local warning or exit 0.
- Source changes after evaluation, base advances, approvals become stale or policy/verifier is revoked: old eligibility cannot merge the new/now-disallowed state.
- Missing/expired signing material, incomplete/failed/skipped checks, unavailable protection metadata or inaccessible registry: fail closed and expose why.
- Agent attempts owner approval, rule bypass/direct push, credential access or trusted-check submission: denied by platform/isolation enforcement, not only a unit-test mock.

Separate pure parsing tests, hosted verifier observations, live GitHub enforcement tests and administrative recovery evidence. Do not label unit tests or a self-authored JSON registry as proof of independent authority. Keep `observations_consistent`, `producer_authenticated`, `policy_admitted` and `merge_eligible` distinct; the existing diagnostic paths must never grant the latter states.

## Recovery and approval boundary

The human administrator retains a separately stored recovery route and a snapshot of prior effective configuration. Before activation, agree how to restore prior rules if the owner cannot approve a test PR; any removal/relaxation is an explicit owner action, not an agent bypass or automatic fallback. No credentials are copied into Git, and no recovery secrets belong in these files. A test activation that cannot be independently verified is rolled back by the owner rather than silently treated as secure.

The independent-principal/human-approval architecture is now approved. The owner still must review the concrete App/identity/environment/configuration packet and explicitly authorize activation actions; none are approved merely by architecture. Dependent credential/protection activation remains paused. All diagnostic results stay unauthenticated/unadmitted and issue #28 remains open.

## Primary references checked November 9, 2026

- [GitHub ruleset capabilities and expected status-check source](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets): server enforcement, review requirements and trusted check identity. Documentation does not prove this repository is configured.
- [GitHub reusable-workflow attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating): signer workflow selection and required signing permissions. No claim of SLSA compliance is made here.
- [GitHub CLI attestation verification](https://cli.github.com/manual/gh_attestation_verify): constrain signer identity and treat untrusted predicate content carefully. A valid signature alone does not approve business requirements.
