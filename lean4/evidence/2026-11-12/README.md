# Fresh local Lean engineering evidence — 2026-11-12

These are real local executions on Ubuntu 24.04.5 x86_64, not mocks or
authenticated admission. The valid receipt describes the precommit development
snapshot at base 5bbc9a1 with candidate files dirty; its source/evaluator/build
identities remain recorded exactly. It must not be used to admit a later PR head.
A new final-head receipt is produced separately by the current gate/hosted CI.

`controls.json` contains 26 completed controls plus its summary. `valid/` retains
the actual dual-kernel proof, build, batched and unchanged legacy bridge, HTTP
and preflight logs, with their exact original receipt. Core binary bytes remain
at `/tmp/proofgate-lean-matrix-4/valid/artifact/core`; source-controlled evidence
binds their SHA256 without committing the compiled runtime.

The matrix diagnostic-exit fixture initially failed elaboration, so that one
row is superseded by `negative-logs/corrected-diagnostic-exit.log`: it proves the
corrected fixture actually emitted the misleading words and exited with code
17. The gate preserved unknown failure and issued no accepted receipt. The final
harness asserts both conditions. The remaining fixture logs document expected
proof, axiom and statement/definition mismatch errors. Generic infrastructure
failures are never treated as proof rejection evidence.

`core-failure.json` records a real EACCES failure, HTTP 500, transaction rollback,
subsequent exactly-once retry, persistence and restart check against a disposable
copy of the accepted core/service. No production state was involved.

Fresh-context review fixed diagnostic classification and resource wording; its
follow-up found no further consequential issue. The final implementation also
copies the toolchain's license files into its artifact. Neither this evidence
nor the later engineering CI activates release authority or completes the
Photon-origin restricted-agent demonstration.
