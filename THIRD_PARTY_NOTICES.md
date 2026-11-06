# Third-party notices

## Bend runtime in recorded JavaScript artifacts

Bend 2.0.39 is copyright 2026 HigherOrderCO and is licensed under Apache License 2.0.

The recorded `admission.mjs` files under `runs/`, `verifier-runs/`, and `evidence/prefreeze-evaluator/artifact/`, and the generated `feasibility/smoke.mjs` file, include JavaScript runtime helpers emitted by Bend. Their upstream source is [`bend2/comp.ts` at v2.0.39](https://github.com/bendlang/bend/blob/v2.0.39/bend2/comp.ts). These generated files are preserved as experimental evidence; their bytes have not been changed for this release preparation.

The [Bend license copy](third_party/licenses/bend-v2.0.39-LICENSE) is reproduced verbatim from [the pinned upstream release](https://github.com/bendlang/bend/blob/v2.0.39/LICENSE). It applies to the Bend-derived portions and does not assign an open-source license to ProofGate's original code.

[`evidence/bend-install.sh`](evidence/bend-install.sh) is the archived upstream installer for Bend 2.0.39, originally served at [bend-lang.com/install.sh](https://bend-lang.com/install.sh). It is retained as evidence and belongs to the same upstream project. Public reproduction uses `baseline/bootstrap.py`; it does not execute this archived installer.

## Separately downloaded toolchains

The bootstrap downloads these tools into the ignored `toolchains/` directory. Their binaries are not committed to this repository. Retain their licenses and notices when redistributing them.

| Tool | Pinned version | Upstream license information |
| --- | --- | --- |
| Bend | 2.0.39 | [Apache License 2.0](https://github.com/bendlang/bend/blob/v2.0.39/LICENSE) |
| Lean | 4.34.0 | [Apache License 2.0](https://github.com/leanprover/lean4/blob/v4.34.0/LICENSE) |
| Node.js | 24.22.1 | [Node.js license and bundled third-party notices](https://github.com/nodejs/node/blob/v24.22.1/LICENSE) |

The bootstrap URLs and archive checksums are recorded in [`baseline/bootstrap.py`](baseline/bootstrap.py). The frozen runtime inventory is [`baseline/toolchain-lock.json`](baseline/toolchain-lock.json).
