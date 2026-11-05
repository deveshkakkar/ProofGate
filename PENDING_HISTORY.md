# Lost-response reservation history experiment

This follow-up models one request whose HTTP response is lost when the real Node
process dies at a transaction boundary. The accepted server and admission
artifact, frozen baseline and merged crash/replay harness are unchanged. The
checker treats the pending reservation as **possibly applied before the process
stopped or omitted**. Later completed status and replay operations constrain
that choice; a timeout or dropped connection is not automatically a rejection.

## Cases and evidence

The test-only hook from [CRASH_REPLAY.md](CRASH_REPLAY.md) kills the process
immediately before or after the first request COMMIT. Each case uses a fresh
100-credit SQLite database, sends a 30-credit reservation, requires a lost HTTP
response and SIGKILL marker, then reaps the child. The original stopped DB,
WAL and SHM files are inspected only through a separate cold copy; their hashes
must match before and after inspection. Both stopped and final SQL snapshots
must match exact request IDs, amounts and stored response bodies, as well as
balances and row counts. The unhooked accepted service restarts
on the original database. A status read precedes request-ID replay, followed by
a new 5-credit reservation, historical replay and final status read.

| Crash point | Post-restart status | Inferred original effect | Wrong-effect control | Final balance / rows |
| --- | ---: | --- | --- | --- |
| Before COMMIT | 100 | Omitted | Forced applied rejected | 65 / 2 |
| After COMMIT, before response | 70 | Applied | Forced omitted rejected | 65 / 2 |

Both real cases passed on November 4, 2026, under the pinned network-disabled
container. Eight pending-checker unit tests cover the two classifications,
replay-alone ambiguity, no duplicate charge, conflicts, persisted rejection,
schema and process-order bounds. The two cases do not establish power-loss
durability or behavior across multiple service processes.

## Reproduce

Use the exact pinned image, Node binary and artifact in `CRASH_REPLAY.md`.
`NODE_DIR` contains the verified binary named `node`; `RESULTS_DIR` is an
existing owner-only writable host directory. The output subdirectory must not
exist. The runner resolves relative CLI paths before launching a child:

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
  -c 'env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 python3 -B supervisor/pending-history.py --node ../node/node --artifact runs/supervisor-resume/accepted-run/artifact --output ../results/pending-history'
```

Run pure checker regressions with
`python3 -B -m unittest -v supervisor/test_pending_checker.py`.
The result JSON, logs, hook and SQLite files remain outside Git under the
private result directory. The runner verifies exact Node/artifact hashes before
and after, pins its own source hashes, refuses an existing output directory and
rejects output inside the accepted artifact. A separate negative invocation
confirmed that guard exits before creating any file.

## Next decision

Status before replay distinguishes the two original effects here. Replay alone
does not: it could observe an existing row or create the row after a pre-COMMIT
crash. The next useful engineering question is whether a delayed or duplicated
response can be associated with the correct request across client reconnects;
that is separate from this finite process-crash experiment. Review this evidence
before selecting or implementing that next milestone.
