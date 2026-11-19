# Protected reservation artifact admission v1

Implementation dependency of [#28](https://github.com/deveshkakkar/ProofGate/issues/28)
and [P0 #46](https://github.com/deveshkakkar/ProofGate/issues/46). **Not activated.**
Live `policy_admitted=false`; both issues remain open. Main stays at
`3ed4e8d868808bde351e750020dc9644a3fe44b0`; publication PR #48 remains unmerged.

## Concrete boundary

The policy owner is human `deveshkakkar` (GitHub ID41484281), acting through
repository/environment authority outside the candidate principal. Ownership is
an external prerequisite, not inferred from matching hashes, filesystem modes,
a merge, or this engineering session's owner-account access. There is no recorded
separate human adoption of the Lean policy/baseline/evaluator yet.

`lean4/authority/policy-v1.json` pins the unchanged reservation evaluator,
baseline manifest, toolchains, repository IDs, three permitted candidate paths,
workflow, verifier binary and artifact inventory. It preserves all four original
laws and the mathematical/application input domain. No legacy Bend input,
Lean baseline, evaluator, bridge or historical receipt is modified.

The owner-controlled adoption root binds that policy's **file SHA256**, an exact
producer commit and tag, an epoch, and an explicit owner-authored adoption comment.
The pinned workflow rejects dispatch at another ref/commit. Only a PR number is
accepted; source identity and bytes are fetched independently through GitHub GETs.
PRs changing anything outside the three existing candidate files are rejected.
There is no candidate repository checkout, candidate workflow, candidate-selected
policy, command, build script, output directory, signing identity or verifier.

`.github/workflows/lean-authority.yml` has two separate GitHub-hosted jobs:

1. **verify:** read-only token, no OIDC or signing permission. Run the fixed
   evaluator with its existing user/mount/PID/network isolation and resource
   limits. Candidate proof code sees only its sandbox, toolchains and pinned
   baseline; producer credentials, host home, result writer and adopted policy
   are outside its mounts/environment. The independent checker and clean native
   build remain unchanged. Run all bridge and application checks, independently
   verify the receipt, and copy the exact accepted executable. A trusted writer
   creates an inert ZIP binding receipt, six logs, three sources and five artifacts
   to PR repository/head/base/tree/blobs, policy/adoption and run/attempt identity.
2. **attest:** fresh runner, exact artifact **ID** and SHA256 from the verify job's
   protected outputs. Recheck policy, source and handoff before signing. Execute
   no candidate source, artifact or receipt command. Only this job gets GitHub OIDC
   and attestation-write permission. The pinned official action signs the ZIP's
   exact digest with standard GitHub/Sigstore SLSA provenance. Signing authority
   never enters the candidate execution environment.

`admit.py` is an operator-side consumer, not an MCP tool, daemon, deployer or
merge bot. It accepts an independently supplied owner-private adoption root and
expected PR number. It captures archive/signature bytes once, verifies a private
frozen copy using the hash-pinned real `gh attestation verify`, and only then
parses the bounded strict ZIP. No unsigned/auth-report/custom-root bypass exists.
It checks verified certificate repository/owner IDs, workflow/tag/commit, hosted
runner, invocation, signed subject and predicate; checks latest successful run
attempt and one-hour age; checks receipt/source/artifact/log bindings against
pinned policy; and fetches current head/base/adoption again before atomically
publishing an exclusive accepted directory. It copies bytes without rebuilding
or executing them. Missing network, authority, adoption, evidence or identity
fails closed. The consumer cannot accept a locally self-consistent forged row
without producer authentication.

## Authority and remaining assumptions

Trust includes the adopted producer code and actions, GitHub-hosted runner/kernel
isolation, GitHub API/OIDC and Sigstore verification roots, the pinned verification
CLI and its host, Lean/kernel/nanoda/compiler/runtime, pinned Node/SQLite bridge
and host libraries recorded by the evaluator. Hosted OS/packages are not claimed
bit-reproducible; their actual identities are bound in the signed receipt. A
compiler or runner compromise is outside the proof theorem. Owner-account,
environment or signer compromise remains an authority compromise.

The operator must run admission outside candidate write/control access, with an
owner-controlled executable/adoption root/output parent. File permissions alone
do not establish separation if a candidate already has the same owner authority.
The root must correspond to a protected environment variable and an exact JSON
owner adoption comment; deletion/change/revocation rejects subsequent admissions.
This design does not issue App tokens or use the owner VM.

`observations_consistent` means fixed evaluator checks passed.
`producer_authenticated` means the signature plus exact producer/run binding was
verified. `policy_admitted` in an accepted artifact decision additionally requires
external human adoption and live freshness. **No such live decision exists yet.**
The original Lean receipt always retains `policy_admitted=false` and is never
rewritten. `merge_eligible` is always false: there is no authoritative check or
merge operation in this path. A later server-enforced required-check identity and
head/base/policy-epoch merge boundary remain separate acceptance work. A
client-side check cannot prevent a remote policy/base change after its final GET;
its decision concerns the exact recorded snapshot, never future merge eligibility.

## Smallest owner activation decision (after review)

No activation is performed by this PR. GitHub must have the workflow registered
on the default branch before dispatch can be used. The current main pin prohibits
that merge during this work; releasing that pin and merging reviewed code remain
owner decisions, with the original mission kept paused. The evaluator itself stays
byte-pinned to3ed4e8d even when a future approved producer is registered. The consolidated next decision is to adopt
this exact policy + unchanged Lean baseline/evaluator + reviewed final producer
commit, create/retain its immutable `proofgate-lean-v1` tag, protect environment
`proofgate-lean-policy-v1` against candidate administration (owner approval only),
and place the same adoption JSON in its `PROOFGATE_LEAN_ADOPTION` variable and in
an operator-controlled file outside candidate access. Protect the producer tag
and approved workflow revision; do not grant the candidate workflow/protection,
variable, environment or attestation administration. Existing owner review and
merge gates remain. Do not infer these protections from workflow YAML alone.

The adoption file has exactly these fields (placeholders deliberately invalid):

```json
{"schema":1,"adopted":true,"owner_id":41484281,"policy_sha256":"POLICY_FILE_SHA256","producer_sha":"REVIEWED_FINAL_COMMIT","producer_ref":"refs/tags/proofgate-lean-v1","epoch":"reservation-v1","human_adoption_ref":"https://github.com/deveshkakkar/ProofGate/issues/46#issuecomment-OWNER_COMMENT_ID"}
```

The referenced comment must have exactly this JSON body, authored by the owner:

```json
{"type":"proofgate.lean.adoption.v1","adopted":true,"policy_sha256":"POLICY_FILE_SHA256","producer_sha":"REVIEWED_FINAL_COMMIT","producer_ref":"refs/tags/proofgate-lean-v1","epoch":"reservation-v1"}
```

A separately authorized platform acceptance would dispatch **only** this workflow
at the adopted tag for a disposable reservation-only PR, retain the run artifact
and signature, and invoke the consumer. No live issuer, coding mission, default
cutover, merge or deployment is needed or authorized here. The candidate PR must
change at least one allowed file; no meaningless result/publication PR is needed
for the historical candidate already equal to main.

After adoption and a separately authorized protected run, operator commands are:

```sh
python3 -B lean4/authority/bootstrap_gh.py --output /OWNER_CONTROLLED/authority-gh
python3 -B lean4/authority/admit.py --gh /OWNER_CONTROLLED/authority-gh \
  --adoption /OWNER_CONTROLLED/adoption.json --pr PR_NUMBER \
  --archive /OWNER_CONTROLLED/reservation-bundle.zip \
  --attestation /OWNER_CONTROLLED/sigstore-bundle.json \
  --destination /OWNER_CONTROLLED/new-exclusive-accepted-directory
```

Use the reviewed producer checkout and read-only API access sufficient to inspect
the environment variable, owner comment, PR and workflow run. The adoption path
must have no symlink/group/world-writable components; file mode0600 and own UID.
No credentials are placed in Git, command arguments, candidate mounts or bundles.
Do not execute the admitted executable as an implicit deployment action.

## Validation and evidence classes

See [VALIDATION.md](VALIDATION.md). The ordinary PR test workflow has read-only
permissions, no OIDC/signing and cannot produce authenticated admission.
Protected platform acceptance remains pending until separately activated/tested.
The existing authority/canary Axx controls remain independently scoped: local
fixtures do not discharge missing platform permission denials, A13 dismissal
controls, A14 owner-local recovery or atomic merge freshness.

The original Photon repair/verification, separate independent static review and
November18 guarded authentication smoke are distinct historical evidence. The
later owner report says maintenance and read-only verification completed. This
PR does not replay them, authenticate their old receipts, settle the paused
uncertain mission or count a smoke as release admission. Their raw private
reports and runtime records remain outside public Git; issues28/46 record their
provenance separately.

References: [GitHub attestation verification](https://cli.github.com/manual/gh_attestation_verify),
[protected signing jobs](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/increase-security-rating).
The cryptographic test inputs are public MIT-licensed CLI fixtures from
[cli/cli v2.105.0](https://github.com/cli/cli/tree/v2.105.0/pkg/cmd/attestation/test/data).
They are downloaded by exact SHA256 and are not ProofGate signatures.
