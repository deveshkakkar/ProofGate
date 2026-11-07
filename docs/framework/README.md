# Experimental framework kernel

The first extraction slice adds a pure consistency kernel. It does not replace the frozen reservation gate. Read [the specification](SPEC.md) for scope, trust and subsequent experiments.

Run from the repository root:

```sh
python3 -B -m framework.demo
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_release.py
```

The demo synthesizes two passing observations, then changes the artifact identity: the original inputs pass consistency and the changed inputs fail. It does not execute verifiers, formal proofs or an application. The regression suite exercises identity invalidation and malformed evidence. Neither is a second application demonstration.

Call `framework.verify(contract, expected_contract, inputs, evidence)` with evaluator-controlled data. The caller supplies an independently pinned `expected_contract` SHA256; computing it from arbitrary candidate input would defeat the policy boundary. `identity` computes the bound identity that a trusted evaluator records when it produces check observations. `contract_digest` validates a contract and computes its identity.

`consistent: true` means the supplied observations cover exactly the contract's ordered checks and match the supplied identities. A caller can forge those observations; the library authenticates no producer and supplies no isolation. It must never be used alone to authorize deployment. Logical names and file hashes are supplied manifests, not verified filesystem snapshots. The next adapter slice must hash actual files, preserve verifier output parsing, and enforce snapshot and evidence ownership separately.

The core conservatively invalidates all check observations for any input change. Memoization is deferred until safe dependency declarations can be independently verified. Current durable research state is in [STATE.md](STATE.md).
