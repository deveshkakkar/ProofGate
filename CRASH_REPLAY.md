# Process-crash replay experiment

This development-only follow-up tests the next crash/restart question identified in `REPORT.md` against the existing accepted artifact. It does not rebuild or modify the server. The original POC and recorded evidence remain unchanged.

## Scope and observed results

Frozen before implementation: terminate the real Node process immediately before or after the first request transaction COMMIT, then restart the original accepted server against the same SQLite database. Test both an accepted reservation (30 credits) and a persisted rejection (101 credits), starting with 100 credits. A test-only Node `--import` hook instruments SQLite COMMIT; the second COMMIT follows startup initialization. The replay process has no hook.

All four cases passed on 2026-10-30 in a network-disabled, read-only container. Each crash had a matching phase/COMMIT/PID marker, actual SIGKILL exit (-9), and a lost HTTP connection. Normal responses and incidental startup failures are not accepted as crash evidence.

The October 30 run predates the observer repair: its Python SQL observer opened the original crash image before Node restarted. Independent review found that this changed SQLite shared-memory state. The repaired harness was rerun on 2026-11-02: all four cases pass with inspection confined to a separate cold copy of the stopped database, WAL and SHM files. The original file presence, sizes and SHA-256 hashes must match before inspection, after inspection and immediately before the unhooked Node restart; these snapshots are recorded under `crash_image` in each case result. Node is the first SQLite client to reopen the original crash image.

| Crash boundary | Amount | Balance / request rows immediately after crash | Balance after replay and a new 5-credit request |
| --- | ---: | --- | ---: |
| Before COMMIT | 30 | 100 / 0 | 65 |
| Before COMMIT | 101 | 100 / 0 | 95 |
| After COMMIT, before HTTP response | 30 | 70 / 1 | 65 |
| After COMMIT, before HTTP response | 101 | 100 / 1 | 95 |

The checks independently inspect SQLite rows and balances. Repeated replay returns the exact historical response without another charge; a different amount with the same request ID returns 409. After another request changes the current balance, replay must still return the old historical response without changing storage.

Five focused unit regressions pass, including malformed markers, missing persisted rejection, incorrect SQL state and reaping a child that fails startup. Two negative controls are rejected: disabling the crash hook yields an ordinary HTTP 200 and fails; the repository's existing duplicate-charge mutant returns a plausible historical response but changes the actual balance from 70 to 40, which the SQL check rejects. The mutant was tested by an external reviewer wrapper using explicit mutant pins, never by weakening the normal harness pins.

The repaired suite has eight passing unit regressions. The three additional tests use a real stopped WAL fixture to compare original file bytes, reject deliberate observer interference, and check explicit connection closure on both success and failure. All Python SQL observer connections now close explicitly. After Node restarts, live SQL checks still read its original database to verify actual persisted state; only the pre-restart inspection uses the cold copy. This procedure requires the crashed process to be reaped and no other client to access that crash image during inspection.

## Reproduce without model access

Requirements: Docker, the Node 24.22.1 Linux x64 binary, and this repository. No package installation or authentication is needed. Obtain the binary from the official Node archive and verify the SHA-256 below; do not substitute the container's Node version. Set `NODE_DIR` to a directory containing that binary named `node`, and `RESULTS_DIR` to a new writable directory. The following commands assume the container user can read the mounts and write the result directory.

```sh
IMAGE=ghcr.io/openclaw/openclaw@sha256:0da12cd49983fcb5e4915fd3135ce7a33d82f93649b1df6964946d2c1d1dbcfc
NODE_DIR=/absolute/path/to/verified-node-directory
RESULTS_DIR=/absolute/path/to/new-results-directory

timeout 180 docker run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 512m --cpus 1 --pids-limit 64 --user 1000:1000 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --mount type=bind,src="$PWD",dst=/src,readonly \
  --mount type=bind,src="$NODE_DIR",dst=/node,readonly \
  --mount type=bind,src="$RESULTS_DIR",dst=/results \
  --workdir /src --entrypoint /bin/sh "$IMAGE" -c \
  'env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 python3 -B supervisor/test-crash-replay.py -v && env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 python3 -B supervisor/crash-replay.py --node /node/node --artifact /src/runs/supervisor-resume/accepted-run/artifact --output /results/positive'
```

To exercise the missing-hook control, run the harness in the same container with a fresh output directory and `--negative-control no-hook`. Expected exit is 1 with `passed: false`; that rejection is success for the negative control. Existing output directories are refused, so uncertain tests are not silently replayed. Results include commands, timestamps, HTTP receipts, SQL snapshots, markers and before/after pins in `result.json`. Raw logs and databases stay outside source control.

Runtime pins:

- Node version: `v24.22.1`; executable SHA-256: `e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb`.
- Official `node-v24.22.1-linux-x64.tar.xz` SHA-256: `6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6`.
- Accepted manifest ID: `22f322d60be8e88d98c8e2813e6280c9fa2de9966a776164e58b7fb8761615d3`.
- `server.ts` SHA-256: `0a71fd2b140713bd80d253e829694bb0ea5dd53fd9934dee813374ffab93e09d`.
- `admission.mjs` SHA-256: `e842815ab774645585fbd240514dd31fffee919b1c16403fb958bc735ae9d47e`.

## Limits and interpretation

The Python CLI does not itself enforce container isolation; use the invocation above. Only the result mount is writable, with no network, host credentials or production mounts. Node child logs are capped at 64 KiB, HTTP waits are bounded and child process groups are reaped. Startup polling includes bounded HTTP waits and can exceed its nominal five-second polling window; the outer 180-second timeout bounds the experiment.

These are four finite single-process crash tests with test-only runtime instrumentation. They do not establish power-loss durability, filesystem/controller flush guarantees, distributed linearizability, universal history correctness, a formal HTTP/storage proof, or production readiness. The original full Bend/Lean acceptance suite was not rerun: the formal baseline, accepted implementation and its historical results were preserved. No service is deployed by this experiment.
