# Local demo walkthrough

This walkthrough first checks the recorded evidence, then reproduces ProofGate's verification gate and starts the accepted reservation service. The service listens on `127.0.0.1` on the machine where it runs.

## 1. Inspect the recorded evidence offline

From the repository root, run:

```sh
python3 -B scripts/check_release.py
```

Use Python 3.10+ on a POSIX host with `/bin/true`, `/bin/false`, and `/bin/sleep`. The checker uses the Python standard library with no pip dependencies. It checks the frozen baseline, recorded artifact hashes and outcomes, and portable checker regressions without downloading toolchains or calling a model. It does not rerun the formal proofs, the compiled core, or the HTTP service. Continue below for fresh evaluation.

## 2. Prepare a Linux environment

Use Linux x86_64 with Python 3.10+, bubblewrap (`bwrap`), `tar`, `zstd`, and xz archive extraction support. Bubblewrap must be able to create the unprivileged namespaces used by the gate. Allow several GB of free disk space and access to the pinned release downloads.

The bootstrap downloads Bend 2.0.39, Lean 4.34.0, and Node 24.22.1 into the repository's `toolchains/` directory. Archive checksums and the runtime file lock are verified before evaluation. It does not replace system tools or need a Codex account, model API key, or npm dependency installation.

The pinned environment targets Linux x86_64. For a macOS, Windows, or ARM host, use a suitable Linux x86_64 machine or VM; this repository does not provide a verified native build for those hosts.

Check host prerequisites before downloading toolchains:

```sh
python3 -B scripts/check_host.py
```

The reproduction runner also performs this preflight before creating its output directory or downloading tools.

## 3. Run the gate

From the repository root, choose a new output directory:

```sh
python3 reproduce.py --output runs/my-first-demo
```

The runner refuses to reuse an existing output directory. Choose another name for the next run, or omit `--output` to use a timestamped directory. An interruption can leave partial evidence in its output directory; it should not be treated as a passing run.

A successful run prints a JSON summary containing `"passed": true`, the results directory, and the accepted artifact hash. Inspect:

| File | Purpose |
| --- | --- |
| `runs/my-first-demo/matrix.json` | The valid case and each deliberately rejected case. |
| `runs/my-first-demo/valid/result.json` | Required check results and accepted source/artifact identity. |
| `runs/my-first-demo/deployment/deployment.json` | Receipt for the copied accepted artifact. |
| `runs/my-first-demo/deployment-smoke.log` | Results of the loopback deployment smoke test. |

The valid candidate should be accepted. Over-allocation, always-reject, double-charge, unavailable-checker, controlled-timeout, changed-law, and disabled-check cases should be rejected. The archived Codex authoring and repair sessions are evidence; this command does not make new model calls.

The smoke test stops its service before returning. To interact with the API, start the accepted deployment yourself.

## 4. Start the accepted service

In the same repository root, use a fresh database path for the examples below:

```sh
DB_PATH="$PWD/demo-data/reservations.sqlite" PORT=8080 \
  ./toolchains/node-v24.22.1-linux-x64/bin/node \
  "$PWD/runs/my-first-demo/deployment/artifact/server.ts"
```

Keep that terminal open. Visit <http://127.0.0.1:8080/> on the same host for the minimal status page, or use a second terminal for the requests below. The demo has no public endpoint.

The database is outside the accepted artifact directory. Reusing its path preserves the existing balance and request records. A new database starts with 100 credits.

## 5. Reserve credits and retry

These are expected responses for a fresh database, not additional recorded test results.

Read the balance:

```sh
curl -sS http://127.0.0.1:8080/status
```

```json
{"balance":100}
```

Reserve 30 credits:

```sh
curl -sS -H 'Content-Type: application/json' \
  --data '{"requestId":"demo-1","amount":30}' \
  http://127.0.0.1:8080/reserve
```

```json
{"requestId":"demo-1","amount":30,"success":true,"granted":30,"balance":70,"reason":"granted"}
```

Repeat the exact request. The service returns the original response and the current balance remains 70. A replay's `balance` field belongs to the original decision; use `GET /status` to inspect the current balance after other requests.

Reuse the ID with a different amount:

```sh
curl -i -H 'Content-Type: application/json' \
  --data '{"requestId":"demo-1","amount":31}' \
  http://127.0.0.1:8080/reserve
```

This returns HTTP 409 with `{"error":"conflict"}` and leaves the balance unchanged.

Try a new request that exceeds the remaining balance:

```sh
curl -sS -H 'Content-Type: application/json' \
  --data '{"requestId":"demo-2","amount":71}' \
  http://127.0.0.1:8080/reserve
```

```json
{"requestId":"demo-2","amount":71,"success":false,"granted":0,"balance":70,"reason":"insufficient_credits"}
```

Valid integer rejections return HTTP 200 and are persisted for consistent retries. Malformed envelopes return HTTP 400 without reserving an ID. See the [full API contract](../candidate/README.md#api) for request IDs, body limits, and numeric bounds.

## 6. Restart without resetting state

Stop the server with Ctrl+C, then repeat the launch command with the same `DB_PATH`. `GET /status` should still report 70 after the example sequence, and retrying `demo-1` with amount 30 should return the original decision without another charge.

This illustrates normal process restart. The dedicated [crash/replay experiment](../CRASH_REPLAY.md) covers selected process-crash boundaries; it does not claim power-loss durability.

## If reproduction stops early

- **Missing prerequisite:** install the reported host tool, then choose a fresh run directory.
- **Namespace permission failure:** use a Linux environment that permits the required bubblewrap isolation. Running without the gate's sandbox is not an equivalent reproduction.
- **Download failure:** check access to the pinned URLs in [`baseline/bootstrap.py`](../baseline/bootstrap.py). A partial archive can remain after an interrupted download; inspect it and replace only the failed download before retrying.
- **Archive or runtime hash mismatch:** keep the lock and baseline unchanged. Use a clean checkout/toolchain directory or investigate the mismatched files.
- **Later check failure:** inspect the named log and that run's `result.json`. Retain the failed run as evidence; its artifact is not an accepted deployment.

Historical `supervisor/run-codex.*` scripts refer to the original experiment's machine and authentication mount. They are not needed for this walkthrough.
