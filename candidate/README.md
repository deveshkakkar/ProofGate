# ProofGate candidate

This is an initial local proof-of-concept implementation, with actual proof, compiled-core and application checks recorded outside this candidate directory. Consult the root report and hash-identified gate records for the accepted release identity. The supervisor owns independent review, baseline freezing, acceptance, mutations and deployment. Self-authored checks do not constitute independent acceptance.

## Build and launch

The independently reviewed root runner is authoritative. On Linux x86_64 with Python 3, bubblewrap, tar and zstd, run from the delivery repository root:

```sh
python3 reproduce.py
```

It bootstraps pinned official Bend 2.0.39, Lean 4.34.0 and Node 24.22.1 toolchains into the repository, verifies the frozen baseline, checks formal obligations, builds and tests an artifact, rejects negative experiments, deploys the identical accepted artifact without rebuilding, then runs private loopback smoke tests. No npm dependency installation is needed. See the root report for the recorded real Codex implementation/repair sessions; the reproduction command does not call a model or reuse authentication.

The reproduced artifact directory is printed in the run results. Launch that accepted deployment explicitly using its persistent database path:

```sh
DB_PATH=/absolute/path/to/demo.sqlite PORT=8080 ./toolchains/node-v24.22.1-linux-x64/bin/node /absolute/path/to/deployment/artifact/server.ts
```

The local smoke process is stopped when checks finish. There is no public endpoint or user-accessible cloud URL.

PORT defaults to 8080 and must be an integer from 1 through 65535. Binding is always IPv4 loopback `127.0.0.1`. DB_PATH defaults to `./data/proofgate.sqlite`, resolved against the process working directory. Parent directories are created. Keep the same explicit absolute DB_PATH on restart. Existing state is reopened without resetting its balance. SIGTERM and SIGINT stop the listener and close SQLite; the independent gate exercises real process restart with the same database; arbitrary crash-boundary behavior is not proved.

## API

`GET /status` returns HTTP 200 with `{ "balance": 100 }` for a fresh database. `GET /` provides a minimal local status page. Other routes return HTTP 404.

`POST /reserve` accepts a UTF-8 JSON object containing exactly `requestId` and `amount`. Extra fields are rejected. Request IDs contain 1–128 ASCII characters from letters, digits, dot, underscore, colon and hyphen. Amount must be a numeric safe integer with absolute value at most 281474976710655 (2^48−1). Negative zero normalizes to zero. No coercion occurs. Content-Type is not required; the body must itself be valid JSON.

Malformed JSON or UTF-8, nonobjects, arrays, missing or extra fields, invalid IDs, strings, booleans, null, fractions, unsafe integers and integers outside the runtime bound return HTTP 400 with `{ "error": "invalid_request" }`. Bodies exceeding 16384 bytes return HTTP 413 with `{ "error": "body_too_large" }` and are drained. These envelope failures create no idempotency record and change no credits. Reusing their ID later with a valid envelope is allowed. Envelope validation precedes all ID lookups.

Every valid unseen integer request returns HTTP 200, including rejected decisions. For example, a fresh request for 30 is intended to return:

```json
{"requestId":"example","amount":30,"success":true,"granted":30,"balance":70,"reason":"granted"}
```

This is an API example, not measured execution evidence. Reason is `granted` on core success, `invalid_amount` on rejected nonpositive amounts, and `insufficient_credits` on other rejections. Zero, negative and oversized positive decisions reach the compiled core and are persisted.

Same ID and same normalized amount replays the original stored response body byte for byte, including its historical balance and rejection reason. The balance in a replay is not current status. Same ID with a different valid in-domain amount returns HTTP 409 `{ "error": "conflict" }`, including when the original request rejected. Admission is not called for either replay or conflict. Internal failures return HTTP 500 `{ "error": "internal_error" }` without exposing database details.

## Persistence and execution boundary

A new SQLite state row initializes to 100 once. One synchronous `BEGIN IMMEDIATE` path performs lookup, compiled-core invocation for unseen IDs, state update, outcome insertion and commit. Both accepted and rejected decisions are recorded. Commit precedes sending the response. A transaction failure rolls back; a client that loses a response can retry its ID. SQLite uses WAL, FULL synchronous mode and a five-second busy timeout. Schema constraints bound stored balances and amounts and enforce unique IDs.

The intended deployment is one Node process with one SQLite connection. The synchronous transaction callback contains no await, so concurrent HTTP callbacks cannot interleave its decisions. This is not a distributed or arbitrary multi-process correctness claim. Independent concurrent-ID and real process-restart checks passed; see the root acceptance matrix.

`app/server.ts` imports the generated module's default export and calls `Core.admission`. Signed conversion uses `Nonneg{magnitude:n}` for nonnegative n and `Neg{pred:-n-1}` for negative n. The adapter persists the returned success, granted and balance fields; it contains no admission or balance-update arithmetic. Runtime result-shape checks fail closed on malformed core output. The supervisor supplied the observed module export and constructor/result encoding; the independent compiled-core bridge and service tests exercised this exact encoding.

## Formal scope and recorded evidence

Model uses unbounded natural balances/grants and the signed representation Nonneg(n)=n, Neg(p)=−(p+1). The four universal obligations cover exact successful grant, conservation for all results, invalid/oversized rejection preserving balance with zero grant, and success for every positive affordable request. Model and LAWS are independently reviewed frozen baseline inputs; Admission and PROOF are candidate implementation files. The root BASELINE.sha256 identifies the unchanged reviewed baseline.

The mathematical domain is broader than the wire domain. The 2^48−1 runtime bound follows the supplied generated nat_chk limitation. JSON parsing, numeric conversion, compiler/code generation, HTTP, SQLite transactions, OS/storage durability and artifact binding are trusted or tested boundaries, not established by these admission proofs.

The actual Codex worker authored structured file proposals without command authority; the separate supervisor executed all proofs/builds/tests. Full proof, bridge and application checks passed under the frozen evaluator; deliberate negative cases were rejected; an actual same-session Codex repair passed the same baseline. Exact-artifact deployment and local supervisor-process interruption/resumption evidence are in the root report and `runs/supervisor-resume/`. Initial authoring logs are historical snapshots, not the final status.
