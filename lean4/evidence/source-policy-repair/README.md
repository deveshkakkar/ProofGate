# Source-policy snapshot repair evidence

`previous-40af8d4/` preserves the exact reviewed hosted receipt and its six logs
from run 43160799909, receipt SHA256
`6e300bd1249bed6211c2388d8ed146a2577f23ddfee1050ed2d1e40f1cb75fa3`.
It remains evidence for that original commit, whose early source-policy race is
recorded in issue #46. It does not approve the repaired evaluator.

The focused regression command is:

```sh
python3 -B lean4/test_snapshot_policy.py --output lean4/evidence/local/focused.json
```

It uses real A→B→A replacements, copying and hashing, with substituted toolchain
and preflight calls. The old evaluate function is preserved verbatim in
`lean4/tests/fixtures/evaluate-40af8d4.py.txt` and hash-pinned by the regression.
These boundary tests demonstrate old preflight reachability and fixed policy
rejection, not a complete malicious Lean admission or any Lean/build execution.
The separate CI step labels and uploads this result independently.

Final repaired-head runs are retained durably under the ignored project directory
`lean4/evidence/local/<full-head-sha>/`: the downloaded hosted bundle contains
actual source snapshots, proof/build/bridge/HTTP logs, controls, accepted-copy and
native artifact bytes. `inspection.json` records verified receipt/artifact/log
hashes, exact commit/dirty state and final CI URLs. The directory is intentionally
outside Git so adding a receipt cannot change the commit that it identifies;
these files persist in the home-server project beyond the hosted seven-day
artifact lifetime. The final PR/issue handoff records their exact location and
hashes. No candidate-writable directory is used to produce this handoff.

Human baseline/evaluator review, restricted Photon execution, protected admission
authority and default-path cutover remain separate gates.
