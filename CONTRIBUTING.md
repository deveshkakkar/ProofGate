# Contributing to ProofGate

ProofGate is a research prototype with a frozen experiment and recorded evidence.
Start with the [README](README.md), [architecture](docs/architecture.md), and
[demo guide](docs/demo.md) to understand which guarantees are proved and which
behaviors are tested.

## Quick local check

From the repository root, run:

```sh
python3 -B scripts/check_release.py
```

This uses Python 3.10+ and its standard library on a POSIX host with
`/bin/true`, `/bin/false`, and `/bin/sleep`. CI runs on Ubuntu. There are no pip
dependencies, downloads, API calls, or toolchain installations in this check.
Temporary regression fixtures are removed when their tests finish.

The command verifies the frozen baseline and policy, toolchain-lock metadata,
accepted source and artifact bytes, recorded log hashes, deployment receipts,
the resume checkpoint, both eight-case recorded matrices, and the recorded
25-row acceptance review. It also runs the existing gate, crash-replay,
real-time history, pending-response, and partial-body regression suites, plus
the archived applier's six rejection cases in an isolated temporary directory.

Exit `0` means these offline checks passed; failure returns a nonzero status
with a diagnostic. Recorded outcomes are historical evidence. This command
does not execute Bend, Lean, Node, the compiled bridge, or the HTTP service,
and does not establish a new formal proof. Hash consistency also does not
independently authenticate the origin of a repository snapshot.

## Full reproduction

On a supported Linux x86_64 host, inspect the host requirements first:

```sh
python3 -B scripts/check_host.py
python3 -B reproduce.py
```

See the [demo guide](docs/demo.md) for prerequisites, disk requirements, expected
results, and local service usage. Full reproduction downloads pinned toolchain
archives when needed, checks their hashes and the runtime lock, runs the four
required gate stages, exercises the negative matrix, and verifies the exact
accepted artifact in a loopback deployment smoke test. It creates a new run
directory. It does not replay the recorded model sessions or require paid
inference. The offline CI job deliberately does not perform this download or
full reproduction.

## Preserve the evidence boundary

Keep the existing `baseline/`, `BASELINE.sha256`, `candidate/`, recorded `runs/`,
`evidence/`, and review records intact when improving documentation or tooling.
The release check expects the packaged candidate to match the recorded accepted
source. A change to the implementation should be a new experiment with its own
source, verification run, and reviewable evidence; it should not overwrite the
historical experiment or update hashes merely to make a check pass.

The gate's trusted files and acceptance policy are frozen. Changes to laws,
required checks, or toolchains need a new reviewed baseline and identity. Do
not weaken sandbox settings or skip required checks to accommodate a host.
Report the failed prerequisite and use a supported host instead.

Archived Codex launchers and the original applier test retain paths from the
recorded workspace. The supported public entry points are the release check,
host check, and reproduction commands above. Do not run archived authoring
scripts as part of a routine contribution.

## Proposing a change

Explain the concrete problem, the resulting behavior, and how it was checked.
For correctness claims, link the relevant proof obligation, test, or recorded
result and state its limits. Add focused regression coverage when changing a
checker or another acceptance boundary; documentation edits generally need
only the quick release check and a review of their links and claims.

Report sensitive issues using [SECURITY.md](SECURITY.md). Review
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before adding dependencies or
redistributing third-party material. A project-wide license has not yet been
selected; public visibility by itself does not grant an open-source license.
