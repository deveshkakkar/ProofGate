# Independent formal semantics and numeric boundary review

2026-10-28 21:07 UTC. Initial Model/LAWS semantics reviewed before compilation repairs and before freeze.

## Mathematical obligations

Model.Amount distinguishes Nonneg(n) and Neg(p), the latter representing -(p+1). Model.positive checks the mathematical sign and Model.affordable uses Nat.is_le for nonnegative values; negative amounts are affordable relative to a natural balance but invalid because they are not positive. These predicates do not invoke the candidate admission logic.

The four laws express: successful grant equals amount; next balance plus granted equals initial balance for every result; invalid/oversized requests produce exactly failure, zero grant and unchanged balance; every positive affordable request succeeds. The total-success premise prevents always-reject vacuity. Natural result fields enforce nonnegativity in the mathematical model. The conservation and rejection laws do not merely prove a helper detached from admission.

This semantic structure is suitable. Constructor namespace/type-checking repairs are still pending and hashes may change; no proof pass or baseline freeze approval is implied.

## Runtime representation

Inspected installed Bend guide/GUIDE.md lines around 414 and feasibility/smoke.mjs. Non-IO exported definitions cross the JS boundary; constructor values are objects and Nat is a host number. Generated nat_chk throws above 281474976710655 (2^48-1). Generated nat_in admits integers up to 2^53. Therefore a theorem over all mathematical Nat values is not an unbounded machine-integer guarantee.

The chosen API accepts signed integer magnitudes no greater than 2^48-1. All such values are exact JS integers. Negative amount a maps to Neg(abs(a)-1), whose predecessor is also exact. With initialized balance100 and conserved admission transitions, balances and successful grants remain0..100. Candidate take reduces both balance and amount until balance reaches0, so oversized amounts entail no more than100 recursive steps; lift increments only reconstructed balance/grant at most100. This keeps permitted execution away from Nat overflow. The argument assumes the reviewed adapter supplies valid constructors and the DB balance has not been externally corrupted.

Before freeze require an independent compiled-core bridge test over balances0..100, amounts around zero and affordability edges, and signed48 extreme values. Inspect actual emitted exports/constructor field names and the service call site. Run tests against the exact compiled artifact that is then deployed. This is runtime/compiler correspondence testing, not a proof of the Bend compiler or TypeScript adapter.

Noninteger/out-of-domain/malformed wire envelopes are rejected by the API parser; their response/idempotency semantics must be documented separately from valid-domain integer rejection. Formal claims should name this boundary explicitly.
