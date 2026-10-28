# ProofGate trusted evaluator (staging, NOT FROZEN)

This directory is the evaluator, independent HTTP tests and protected baseline.
Candidate repair may change only formal/Admission.bend, formal/PROOF.bend and
app/server.ts. Model.bend, LAWS.bend and ENTRY.bend are copied from this baseline
into each clean snapshot. ENTRY always imports the intended obligations, even
if candidate proof code omits them. Real tests of removed proofs must confirm
Bend's checker rejects outstanding obligations before acceptance.

`gate.py evaluate --candidate PATH --baseline PATH --baseline-sha256 HASH --destination NEW_RUN`
requires a reviewed frozen.json manifest, checks its externally supplied hash,
and rejects changed/missing/extra baseline files. It performs all formal, build, compiled-core bridge
and application checks itself. Missing/disabled checks, malformed or skipped
reports, nonzero exit, missing tools and timeout fail closed. `--fault timeout`
or `--fault unavailable` are explicit controlled faults that can never accept. The timeout fixture
runs an actual sleep subprocess under a deadline; it is not a Bend timeout claim.

The protected policy runs the pinned Bend checker with --verdict, builds the
same Admission implementation to admission.mjs, and copies server.ts without
executing a candidate build script. Fixed independent HTTP tests run outside
the candidate process namespace. The candidate service sees read-only source,
baseline and artifact mounts, a disposable database, and no test-report writer.
Its stdout cannot forge the independent test report. Candidate service PIDs
cannot see or signal host driver PIDs through its private /proc namespace.

The evaluator stores actual invocation/exit/stdout/stderr/timeout evidence and
source/build artifact hashes. It captures artifact hashes immediately after build and checks that bytes are
unchanged after the read-only compiled-core bridge and application tests. `gate.py deploy --run RUN --baseline PATH --baseline-sha256
HASH --destination NEW_DEPLOYMENT` accepts only a complete passing record and
unchanged source/artifact, copies exactly those bytes, verifies the copy, and
writes an independent deployment receipt. It does not rebuild. Starting and
smoke-testing this deployment remain separate recorded steps.

## Trust limits

The human/supervisor and evaluator host are trusted; candidate does not receive
write access to their state or APIs. The frozen hash must be retained outside
candidate authority. No signature claim or defense against a malicious host is
made. Host-side checks must be run with a clean Python import environment.

Bwrap creates user/PID/mount isolation with a minimal root and dropped caps.
Only reviewed runtime libraries/toolchains are mounted read-only; the build
output or service database is the only writable host mount. There are no home,
credential, host socket or deployment mounts. Host networking is shared due to
available kernel restrictions. This experiment DOES NOT claim network/localhost
isolation; keep the accepted demo stopped during mutation runs and do not expose
credentialed deployment endpoints. Host kernel, bwrap, Node, OS libraries, Bend
compiler and BendTT/Lean kernel are trusted. Pure admission is proved; parser,
SQLite transactions, HTTP, restart and artifact correspondence are tested.

Wire contract: nonempty string IDs; integer amount within -(2^48-1)..2^48-1.
Out-of-domain/noninteger/malformed envelopes return400 without reserving ID;
oversized bodies return413.
Well-formed integer outcomes return200 and are persisted including rejection.
Existing ID lookup precedes admission: same amount replays original body,
different amount returns409 {"error":"conflict"}. POST /reserve result contains
requestId, amount, success, granted, balance and reason. GET /status has balance.

Run `python3 -m unittest -v test_gate.py` here for evaluator defense unit tests.
No file in this directory asserts that the application or full formal laws have
passed. Freeze requires actual independent review of Model/LAWS/proofs/runner,
source and runtime enforcement, and successful positive/negative checks.

## Portable runtime

On Linux x86_64 with Python3, bubblewrap, tar and zstd, run
`PYTHONDONTWRITEBYTECODE=1 python3 baseline/bootstrap.py` from repository root.
It downloads exact official SHA256-pinned archives into sibling toolchains/
and validates every runtime file against the protected relative-path lock.
No runtime paths or file identities are weakened on relocation. OS libraries
and kernel remain explicit host prerequisites, not a hermetic OS image.
