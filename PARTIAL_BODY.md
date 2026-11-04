# Partial-body disconnect experiment

This test-only follow-up probes a distinct HTTP framing boundary. The accepted
service, compiled admission artifact, formal core, frozen gate, and prior crash
and concurrency experiments are unchanged. A raw loopback client declares a
complete valid reservation body, sends either only its headers or a 20-byte
prefix, then half-closes. The service must close with HTTP 400. A fresh status
read must remain at 100 credits. After stopping the process, a separate cold
copy of the SQLite image must show no reservation row; inspection must not
modify the original image. An unhooked restart and complete same-ID retry must
grant exactly once, and a second replay must return the exact stored response.

The real-service negative control sends a complete body before the pre-retry
check; the harness must reject it because the balance is 70. Two in-memory
premature-admission mutants are rejected by the exact SQL validator. This
experiment does not test a body whose last byte races a client disconnect, a
power loss, or multiple service processes.

## Reproduce

Use the pinned image, Node binary and artifact documented in
[CRASH_REPLAY.md](CRASH_REPLAY.md). Run from this checkout. `NODE_DIR` contains
the verified binary named `node`, and `RESULTS_DIR` is an existing owner-only
writable host directory. Choose fresh output subdirectories:

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
  -c 'env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 python3 -B supervisor/partial-body.py --node ../node/node --artifact runs/supervisor-resume/accepted-run/artifact --output ../results/partial-positive'
```

Repeat with a new output path and `--negative-control complete-body`; exit 1
with `passed: false` and the expected completed-body classification is success
for that control. Run local guards with
`python3 -B -m unittest supervisor.test_partial_body -v`.

The result includes before/after artifact pins, source hashes, HTTP statuses,
SQL snapshots and original-image hashes. Raw logs and databases stay outside
Git. An existing output directory, altered artifact pin or changed source
during execution fails closed.
