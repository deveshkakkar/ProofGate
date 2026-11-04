# Reservation and status real-time history experiment

This development-only experiment records invocations and responses for overlapping
`POST /reserve` and `GET /status` calls, then checks whether some sequential
ordering respects every response-completed-before-invocation edge. It uses the
unchanged accepted ProofGate service and generated admission module. The frozen
baseline, formal core, accepted artifact, and merged crash/replay harness are not
modified. This is finite single-process evidence, not a general proof of
linearizability or distributed correctness.

## Contract and limits

- A fresh 100-credit database is used for each history. One group races three
  distinct reservations with two status reads. Another first persists a 30-credit
  reservation, then races its replay and conflicting amount with a new 50-credit
  reservation and two status reads. A phased group holds one reservation's client
  response pending, completes a separate grant, then reads status before releasing
  the held response. This guarantees a real-time grant-before-read edge inside an
  overlapping client invocation/response interval; it does not assert the server
  was still computing the held reservation. A final status read follows each group.
- `realtime_checker.py` has an independent sequential model for unseen requests,
  persisted rejection, historical replay, conflicts and current status reads. It
  considers all orders consistent with real-time precedence. It accepts at most
  12 completed HTTP operations; failed transports and crashes are outside scope.
- Each positive history must have a valid order. Negative copies change the
  final status read to stale balance 100 in the first two groups. In the phased
  group, they change the status read taken during the held interval, after the
  completed grant, to stale balances 100 and 90. All must be rejected. Unit controls
  also reject stale admission after a completed grant and a replay incorrectly
  reporting the current balance.
- The runner refuses an existing output directory, verifies exact Node and
  accepted artifact hashes before and after, caps rounds at 16 per scenario,
  bounds HTTP waits, reaps child processes and compares final HTTP balance with
  persisted SQLite state. At least one reservation/read interval must overlap.
  It records total reservation/read overlaps separately from overlaps involving
  successful grants, observed intermediate balances, and phased witnesses. The
  result pins the checker, tests, runner, Node binary and accepted artifact hashes.
  CLI paths are resolved before the child changes working directory; a pinned
  container run using relative Node, artifact and output paths also passed.

## Reproduce

Use the pinned image, Node binary and artifact listed in [CRASH_REPLAY.md](CRASH_REPLAY.md).
The host result directory must be new and writable by UID 1000. This command
has no external network or production mounts:

```sh
timeout 180 docker run --rm --network none --read-only \
  --cap-drop ALL --security-opt no-new-privileges \
  --memory 512m --cpus 1 --pids-limit 64 --user 1000:1000 \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --mount type=bind,src="$PWD",dst=/src,readonly \
  --mount type=bind,src="$NODE_DIR",dst=/node,readonly \
  --mount type=bind,src="$RESULTS_DIR",dst=/results \
  --workdir /src --entrypoint /bin/sh \
  ghcr.io/openclaw/openclaw@sha256:0da12cd49983fcb5e4915fd3135ce7a33d82f93649b1df6964946d2c1d1dbcfc \
  -c 'env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 python3 -B supervisor/realtime-history.py --node /node/node --artifact /src/runs/supervisor-resume/accepted-run/artifact --output /results/history --rounds 8'
```

`NODE_DIR` must contain the pinned binary named `node`; `RESULTS_DIR` is an
existing private host directory. The checker tests run without a model or Node:
`python3 -B -m unittest -v supervisor/test_realtime_checker.py`.

## Observed result and next step

On November 4, 2026, the revised network-disabled run passed 24 histories
(eight per scenario), with 104 measured overlapping reservation/read interval
pairs, 72 involving successful grants, and eight phased grant-before-read
witnesses. All histories admitted a real-time order; all 32 stale-read controls
were rejected, including 16 during the held client interval. Intermediate
status reads varied across 10, 20, 30, 60, 70 and 100 as allowed by different
orderings; phased final balance was 60. The earlier 16-history run remains
historical evidence but lacked the phased witness. All four existing
crash/replay cases, eight crash-harness unit tests and 21 frozen-gate unit tests
passed. Results and service logs are owner-only under
`~/.local/share/proofgate-realtime-20261104/`.

The next useful experiment is a client timeout or lost-response history that
contains an uncertain reservation, followed by replay and status reads. The
current checker deliberately requires completed responses, so that case needs
an explicit pending-operation model and must not treat uncertainty as failure.
Keep this as a separate milestone; do not change accepted service or formal laws
based on the finite histories alone.
