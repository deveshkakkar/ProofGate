# Framework extraction specification

Status: experimental implementation specification, 2026-11-07. This is not an admitted production contract.
Source: vault master 47695e5, “Proof-Carrying Agent Development”, November 6 framework hypothesis.

## Intended behavior

Separate application semantics from evidence acceptance. A small Python standard-library core verifies that every required check passed for the exact contract, source, artifact, verifier implementation and environment supplied by a trusted caller. Bind the complete input set initially: conservative invalidation is preferable to premature dependency caching. Verification must fail on missing, extra, duplicate, skipped, stale or mutated evidence. Return structured reasons for repair. Never execute a command taken from candidate data.

## Authority and trust

The caller supplies the expected contract digest through a trusted channel. A candidate-authored contract plus its digest grants no authority. Checks and their results come from an external trusted evaluator; the core checks identity and completeness, not producer authenticity. The caller must enforce writer separation and immutable snapshots. A same-user Python library does not enforce those boundaries. No signatures or independently authenticated provenance are claimed. Digest consistency is not formal correctness.

A contract contains schema version, a nonempty list of uniquely named checks and explicit assumptions. Inputs contain nonempty maps of logical file names to SHA256 digests for source, artifact, verifier and environment. Each check result contains its ID, passed status and digest of the whole input identity. Contract identity is included in that identity. No check may silently change the accepted assurance scope.

## Allowed writes and excluded scope

Add framework/, tests/, docs/framework/, examples/entitlement/ and a CI invocation. Preserve baseline/, candidate/, historical runs/, evidence/, review/ and BASELINE.sha256 byte for byte. Do not change services, authentication, firewall, backups or deployed agents. No package installs, toolchain downloads, model calls, merges or deployment. Framework prototype is not a replacement gate or production release authority.

## Acceptance evidence

Test acceptance for independent application-shaped input sets; reject changes to every identity dimension, contract mutation, omitted/extra/duplicate checks, non-passing states, unsafe paths and malformed digests. Exercise the CLI against the recorded reservation artifact through an explicit adapter in a later slice; label archived consistency separately from fresh execution. Retain the existing offline release checks.

## Sequence and stopping rules

1. Strict deterministic identity and evidence kernel, mutation tests and documentation.
2. Adapter for archived reservation evidence; preserve specialized parser semantics.
3. A second materially different executable rule and independent boundary checks. Measure core changes and integration effort. A fixture alone is not that demonstration.
4. Evaluate reusable executor extraction only after both adapters identify shared needs.

Per slice: no more than 30 minutes of command execution, 2 GiB new disk or 2 CPU workers. No live-provider spending. Stop a command on those limits and retain evidence. Stop dependent work for missing authority decisions, unavailable external requirements or unsafe changes. Record explored approaches and why they were accepted/rejected; revisit only when inputs change. Finish a reviewed PR before advancing another substantial slice.

## Research and differentiation

Tenet already provides immutable completion authority and candidate-bound evidence: https://github.com/flaviodelgrosso/tenet (reviewed 2026-11-07). in-toto already defines artifact subjects and typed claims: https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md . Do not claim a novel acceptance kernel or invent a substitute signature standard. The testable hypothesis is reduced effort connecting executable business rules, application fault checks and exact artifact release evidence. Product novelty and demand remain unverified.
