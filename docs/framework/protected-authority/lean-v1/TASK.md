# Protected reservation authority implementation

Base3ed4e8d; issue28 is the immediate implementation dependency of P0 issue46.
Implement one owner-activated GitHub-hosted workflow and a strict authenticated
artifact consumer for the fixed reservation evaluator. No issuer/key/token,
protection/environment administration, installation, deployment, live coordinator,
worker/reviewer mission or old-mission replay. Main stays3ed4e8d and PR48 unmerged.

Policy owner: deveshkakkar through authority outside candidate access. No separate
human Lean baseline/evaluator adoption is evidenced by prior merges. The new path
must fail without explicit external adoption of policy, producer and verifier.
Use GitHub/Sigstore attestations, exact workflow/source SHA, isolated secret-free
verification and a separate no-candidate-code signing job. Do not invent crypto.

Allow source only from the three existing reservation candidate paths at the
live PR head/base, independently fetched/hashed. Pin unchanged evaluator/baseline/
toolchains. Sign a complete immutable bundle, then authenticate before parsing/
copying accepted artifacts; recheck live head/base/policy and bind execution/run.
No merge/deploy API. Artifact admission is separate from merge eligibility; later
server-side policy-epoch/head/base enforcement remains explicit rather than a
client-side freshness promise.

Allowed writes: lean4/authority/, new scoped workflows and tests, sanitized docs;
update PR48's publication text separately. Preserve baseline/, candidate/,
BASELINE.sha256, Bend archives, Lean baseline/evaluator and all historical receipts.
Tests: forged consistent rows, protected replacement, output substitution, stale
head/base/policy and missing/invalid/wrong producer; meaningful fixtures + actual
fixed Lean execution; clearly separate cryptographic/platform observations and
pending protected activation. One fresh engineering review and one repair pass.
No live policy_admitted until separately adopted and protected acceptance observed.
