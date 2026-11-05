# ProofGate

ProofGate, POC for proof libraries for integ tests.

A small TypeScript/SQLite reservation service whose **actual admission function is compiled from Bend and checked against four universal laws**. An independent frozen gate checks those laws, the generated executable, and real HTTP/database behavior before allowing the exact tested artifact to be deployed.

## Reproduce

Prerequisites: **Linux x86_64**, Python 3, bubblewrap with unprivileged namespaces, tar and zstd; internet access to the pinned official release downloads. Approximately 4 GB of toolchains plus working space. This pinned gate is not a native macOS build.

```sh
python3 reproduce.py
```

This downloads and hash-verifies isolated Bend 2.0.39, Lean 4.34.0 and Node 24.22.1 toolchains (no system installation), checks the frozen baseline, runs a valid candidate and deliberate negative experiments, deploys only an accepted artifact without rebuilding, and runs private loopback smoke tests. Results go under `runs/reproduce-<timestamp>/`. Repeated runs use new result directories. Existing toolchains must match the lock exactly.

No Codex login, API key, npm package installation or paid service is needed to reproduce the gate. The recorded real Codex implementation/repair experiment is in `evidence/`; the reproduction command does **not** make another model call.

## Run the accepted service

After reproduction, use the deployment directory reported by the run:

```sh
DB_PATH=/absolute/path/to/my-demo.sqlite PORT=8080 \
  ./toolchains/node-v24.22.1-linux-x64/bin/node \
  /absolute/path/to/runs/reproduce-TIMESTAMP/deployment/artifact/server.ts
```

Open `http://127.0.0.1:8080/` **on that host**. The demo binds loopback only. There is no public endpoint and no remotely accessible cloud URL. Smoke processes are stopped after testing; their database is kept separately from the unchanged artifact.

- `GET /status` → current balance.
- `POST /reserve` with `{"requestId":"example-1","amount":30}` → persisted decision.
- A new database begins with 100 credits. Reusing the same ID/amount replays the original decision without charging again; another amount conflicts.
- Well-formed integer rejections are persisted too. Malformed envelopes return 400 and do not reserve an ID.
- Numeric amount domain is `[-(2^48-1), 2^48-1]`; JSON safe-integer validation also applies. See [API details](candidate/README.md).

## Evidence and trust

[Technical report](REPORT.md) · [Acceptance matrix](ACCEPTANCE.md) · [Frozen baseline](baseline/) · [Source](candidate/) · [Raw experiment evidence](evidence/) · [Recorded runs](runs/)

The proof covers mathematical admission, **not** the HTTP parser, SQLite, compiler correctness or deployment infrastructure. Those boundaries have explicit checks/tests and assumptions. This is a single-process local POC, not a production security or distributed-consistency certification. The candidate agent had a read-only/no-command Codex session and could propose only allowlisted candidate files; the separate supervisor held evaluation/deployment authority.

`supervisor/run-codex.*` are archived, environment-specific experiment launchers that reference the original cloud workspace and approved read-only authentication mount. They are not portable user setup scripts and are not used by `reproduce.py`. Do not run them on another machine unchanged.

## Local crash replay check

[Crash/restart experiment and reproduction](CRASH_REPLAY.md) extends the accepted POC with four finite process-crash cases. The accepted server, admission module and frozen baseline are unchanged. This is not a power-loss, distributed-consistency or production-readiness claim.

## Overlapping reservation and status histories

[Real-time history experiment](REALTIME_HISTORY.md) checks finite concurrent
reservation/status histories against an independent sequential model and rejects
deliberately stale-state controls. It runs against the unchanged accepted artifact.

[Lost-response history experiment](PENDING_HISTORY.md) treats a request whose
response was lost at a process-crash boundary as possibly applied or omitted,
then uses post-restart status and replay evidence to distinguish the cases.
