# Direct Lean 4 reservation migration

Issue [#46](https://github.com/deveshkakkar/ProofGate/issues/46) is the highest
priority implementation. This versioned development path runs real Lean proofs,
independent checking, a native build, and the reservation service. The later
Photon restricted-agent demonstration and authenticated admission are pending;
this owner-initiated session does not satisfy them. The historical Bend default
reproduction remains preserved pending complete acceptance of the migration.

## Run on the supported development host

Linux x86_64, Python 3.10+, Ubuntu 24.04, bubblewrap with working user namespaces,
a running systemd user manager with cgroup resource controls, tar, xz, zstd and
git are required. The first download is about 600 MiB plus 31 MiB for Node;
allow 5 GiB disk, 4 GiB memory and two CPU cores. No API keys, model provider or
production service is needed. macOS/Windows users need an isolated Linux VM with
these prerequisites; this is not a native cross-platform runner.

```sh
python3 -B lean4/bootstrap.py
python3 -B lean4/doctor.py
python3 -B lean4/gate.py --output /tmp/proofgate-lean-new-run
python3 -B lean4/check.py --output /tmp/proofgate-lean-new-controls
python3 -B lean4/check_core_failure.py --artifact /tmp/proofgate-lean-new-controls/valid/artifact --output /tmp/proofgate-core-failure
```

Use unused output paths. Bootstrap installs only into
`~/.cache/proofgate-lean4`; archive SHA256 and complete extracted-tree identities
are pinned in [toolchain.json](baseline/v1/toolchain.json). Existing tools are
verified, not silently overwritten. Doctor tests the real namespace and resource
manager configuration. Missing tools, unsupported isolation, malformed exports,
checker failures and timeouts fail closed. Host setup is manual; none of these
commands modifies host services, permissions, firewall or credentials.

`check.py` executes the valid path and negative controls with no mocks. Its
`controls.json` records the rejecting layer for each case. `gate.py` produces
`receipt.json` only after proof, build, bridge and application checks all succeed.
`checkpoint.json` is intermediate evidence with `observations_consistent:false`.
Neither receipt authorizes deployment: `policy_admitted` is always false.

## Proof and executable correspondence

The evaluator owns [Model.lean](baseline/v1/Model.lean),
[Challenge.lean](baseline/v1/Challenge.lean), the build and checker configuration,
[Main.lean](baseline/v1/Main.lean), [admission.mjs](baseline/v1/admission.mjs),
the service and the HTTP tests. `baseline-v1.json` lists these exact bytes and
executable modes; `BASELINE.v1.sha256` identifies that manifest. A newly reviewed
baseline needs a new version/identity. The proposed v1 is subject to PR review.

Candidates supply `formal/Admission.lean`, `formal/Proof.lean`, and
`app/server.ts`, with no extra files or symlinks. The server must equal the
protected service byte for byte. Implementations use a deliberately small Lean
term vocabulary inside a fixed declaration envelope: signed cases, natural
arithmetic and conditionals. Unknown identifiers, command syntax, new imports,
attributes, unsafe definitions, FFI and runtime substitutions are rejected.
Proof files may use Lean tactics and metaprograms; they run only in isolation.
This is a bounded reservation workflow, not a general arbitrary-Lean evaluator.

The pure definition retains unbounded `Nat` balances/grants and the original
signed type (`nonneg n`, `neg p` means `-(p+1)`). Required laws quantify over that
whole domain. HTTP parsing and the protected executable protocol retain the
separate amount bounds ±281474976710655 and balance range 0..100.

1. The evaluator takes and hashes a source snapshot. Lake's pinned comparator
   compiles/exports the trusted challenge first and the candidate proof second.
   Both reference the snapshotted admission source. Challenge `sorry` terms are
   intentional placeholders for statements; candidate `sorryAx` is forbidden.
2. Comparator validates serialized exports, compares actual elaborated theorem
   statements and their referenced definitions, checks transitive assumptions
   against exactly `propext`, `Quot.sound`, `Classical.choice`, then invokes both
   the Lean kernel and bundled Rust `nanoda`. No candidate success string is used
   as proof evidence. No definition holes are allowed. A proof of a different
   statement or a weakened model cannot satisfy the comparator.
3. A protected bubblewrap adapter replaces Lake's whole-root read mount with
   system binaries/libraries. It retains Lake's namespace isolation, hidden home
   directories, read-only inputs, private temporary storage and `.lake`-only
   writes. Comparator runs outside the candidate build sandbox. Replay checkers
   receive serialized data in fresh sandboxes with no candidate writable mount.
   Candidate `.olean` files are never imported by the host verifier. Each stage
   runs in a systemd scope: 4 GiB, no swap, 64 tasks, 200% CPU quota, bounded wall
   time. Timeout handling kills the scope and process group.
4. A new clean build directory receives only the restricted admission source and
   protected model/entry point. It never receives candidate proof code or any of
   its `.olean`, generated C, object or executable files. `lake build core`
   compiles `Main → Admission → Model` using the pinned compiler. This prevents
   proof-side compiler hooks/attributes or forged build outputs from substituting
   a different executable. Comparator's challenge comparison establishes which
   admission definition the proof covered; the fresh restricted build compiles
   that same source definition.
5. The protected JavaScript bridge invokes the adjacent `core` executable with
   `execFileSync`, a fixed path, empty custom runtime environment, five-second
   timeout and bounded output. It converts the signed amount, serializes decimal
   input, and validates response shape/numbers. It contains no admission algorithm.
   The service calls this bridge inside its original synchronous SQLite
   transaction. The executable is Lean native code, not Bend-generated JavaScript.
6. A trusted driver checks 11,716 compiled cases, additional malformed conversion
   cases and real single-request calls. The unchanged seven HTTP test groups
   exercise validation, retries/conflicts, concurrency, persistence and restart.
   Double charging is additionally executed as a deliberate service regression;
   ordinary candidate service substitution is rejected earlier by the byte pin.
   A separate genuine executable-permission failure verifies HTTP 500, transaction
   rollback, a successful later retry, and persistence across restart.

## Identity and handoff

The receipt binds source files/snapshot digest, commit and candidate dirty state,
protected model/statements/configuration/driver, effective checker configuration,
complete pinned Lean/Std/checker and Node distributions, evaluator, clean build
inputs/outputs, accepted artifact bytes/modes, host tools/runtime libraries and
hashes of required evidence logs. Artifacts are checked again after tests; live
source and protected inputs must still match the selected snapshot.

`gate.verify_identity(receipt_path, expected_receipt_sha256, candidate, artifact,
cache)` requires the digest from an independently protected verifier handoff.
It rejects changed evidence, current source/commit, checker/bridge dependencies,
and substituted artifact bytes. `gate.copy_checked(...)` verifies then copies
those bytes to a new directory and checks them again; it neither rebuilds nor
starts a service. The matrix exercises this copy. No merge/deploy action is
implemented or authorized by these helpers.

A digest supplied by the candidate is not independent authority. Same-user
repository hashes and engineering CI are not authenticated admission. Issue
[#28](https://github.com/deveshkakkar/ProofGate/issues/28) remains a release blocker.
CI runs without secrets on an ephemeral hosted runner; its verifier changes are
reviewable code, not a newly activated protected admission service.

## Remaining trusted assumptions and limits

The formal claim covers the four mathematical source-level properties only.
Trust remains in Lean's logic, comparator/export parsing and comparison plumbing,
at least one of Lean/nanoda being correct, the sandbox, OS, hardware and protected
evaluator ownership. Compiler, optimizer, C backend/linker and Lean runtime are
not proved by these laws. The complete pinned Lean/Std distribution is trusted
for executable dependencies: its `Nat`/integer arithmetic, strings, parsing, IO,
allocation and standard-library `extern`/`implemented_by` replacements contain
low-level assumptions. The candidate has no corresponding extension authority.
The native executable dynamically uses host glibc/loader libraries, whose hashes
are recorded/rechecked; this is a supported-host build, not a bit-reproducible
cross-distribution binary claim. Node, Python, SQLite, serialization, synchronous
subprocess handling, the protected service and test drivers are also trusted.
Finite bridge/HTTP tests do not prove those components or arbitrary histories.

See [STATUS.md](STATUS.md) for acceptance coverage, exact observed commands,
results and the smallest outstanding steps. Historical `baseline/`, `candidate/`,
`BASELINE.sha256`, archived Bend receipts and reproduction instructions are
unchanged. The new Lean baseline lives separately under `lean4/baseline/v1/`.
