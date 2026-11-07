# Finite entitlement extraction experiment

Run `python3 -B examples/entitlement/experiment.py` from the repository root. Requires Linux, Python 3, bubblewrap supporting `--size`, usable namespaces and an active systemd user manager with resource-control support. Failures in those prerequisites stop execution; there is no unsandboxed fallback.

Each variant packages its source unchanged into an artifact in temporary storage, then executes that exact artifact through two independent entry points. A host-side oracle checks 72 pure-rule cases (all modeled tenant pairs and boolean flags) and 80 application cases (those same cases plus eight malformed envelopes). A fresh process handles each batch. The framework consistency kernel is reused without modification.

Expected matrix:

| Variant | Rule | Application |
| --- | --- | --- |
| Original | pass | pass |
| Always deny | fail | fail |
| Always grant | fail | fail |
| Application overwrites resource tenant | pass | fail |

The final variant demonstrates why checking an executable decision function does not establish its correct use by an application. Output includes the contract, manifests, observed results, expected results and framework receipts. Redirect JSON to a new private file to retain evidence. This is finite exhaustive testing, not universal formal proof, persistent authorization or deployment. Supplied entitlement booleans are inputs; credential freshness and replay are outside this stateless model.

The mutation experiment supports the four small evaluator-authored variants. The [developer trial](../../docs/framework/TRY.md) also accepts inspected local derivatives through a separate CLI; adversarial inputs remain unsupported. Bubblewrap hides home directories, uses read-only source and probe mounts, clears environment and isolates networking. Transient systemd user scopes set aggregate memory to 256 MiB, tasks to 16, CPU quota to one CPU and maximum runtime to five seconds. `/tmp` is limited to 16 MiB. Process limits also cap individual output files at 1 MiB, address space at 256 MiB and CPU time at three seconds. The user manager must permit those controls. These settings were exercised on the development host; hostile fork/memory/disk exhaustion and signal-failure controls remain unverified. Do not use this experiment as an adversarial candidate runner.

The same user controls the contract, evaluator, manifests and evidence. The hashes identify bytes but authenticate no writer. The environment manifest identifies interpreter and bubblewrap executables and explicitly marks the host standard library as trusted and incompletely fingerprinted. Same-user concurrent interference and host compromise remain outside assurance. No isolation or production security certification is claimed.
