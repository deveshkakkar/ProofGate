# Adapter experiments

Status: specification; neither adapter is implemented in this slice.

## Reservation adapter

Consume an evaluator-owned reservation run and the independently pinned baseline digest. Reuse the frozen gate's baseline validation, policy validation and result parsers without modifying their bytes. Recompute source, artifact and log digests from regular files; compare the policy's exact ordered check inventory and each successful parsed result. Reject fault-injected runs and output outside the policy inventory. Bind the toolchain lock, gate implementation and all policy files. An offline historical mode must say that toolchain availability and fresh execution were not checked. A fresh mode must validate the installed runtime and execute the original gate under its existing sandbox, not turn an archived report into a new proof.

Acceptance controls: accepted archived run succeeds only as historical consistency; duplicate-charge run fails; changing artifact, source, baseline, required check, parser output or log fails. Fresh results require a separate execution record. The adapter grants no deployment authority.

## Second application: finite entitlement policy

Purpose: test reuse on authorization rather than numeric reservation. Technical validation only; this does not select a buyer or market.

Pure executable decision: allow access iff subject is active, subject tenant equals resource tenant, entitlement is present, and the resource is enabled. Inputs use an explicit finite tenant ID domain and booleans; reject unknown fields, unsupported types and out-of-domain tenant IDs before invoking the rule. The decision has no side effects.

Required obligations: inactive subjects are denied; cross-tenant access is denied; missing entitlement or disabled resources are denied; every fully eligible request is allowed. Check the actual executable function over the complete declared finite domain. Describe this as exhaustive finite-domain checking, not an unrestricted mathematical proof. A later Bend/Lean adapter may supply stronger claims only after implementation correspondence is shown.

Boundary checks must call the packaged executable through the application interface and include malformed input, JSON boolean/integer confusion, tenant spoofing and stale entitlement replay. Deliberate mutations must include an always-deny implementation (safety passes, completeness fails), a cross-tenant grant (rule fails), and an adapter that swaps tenant fields (rule passes, application checks fail). Evidence must identify the exact checked executable and packaged application. A receipt-only fixture is insufficient.

Reusable core changes must be counted. Report contract authoring time, adapter code size, runtime and negative control outcomes; compare to competent ordinary CI. Do not infer superiority from a green demo. Defer deployment, persistent sessions, caching, distributed access control and paid provider calls.

## Executor decision pending evidence

Do not accept arbitrary shell commands or dynamic plugins from candidates. Candidate execution needs OS-enforced separation, resource and output bounds, immutable evaluated inputs and an evaluator-owned evidence sink. Reuse the existing sandbox before considering another engine. Environment hashing describes declared inputs; it does not fully capture or authenticate the host.
