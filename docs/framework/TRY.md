# Try the developer interface

Experimental audience: developers using coding agents to change business logic. This first adapter supports one tenant entitlement contract and a two-file Python interface. It does not check an arbitrary application or generate its requirements. There is no package installation step.

From a checkout of ProofGate, on Linux with Python 3, bubblewrap and an active systemd user manager:

```sh
mkdir demo-entitlement
cp examples/entitlement/app.py examples/entitlement/rule.py demo-entitlement/
python3 -B -m framework check-entitlement \
  --candidate demo-entitlement \
  --output entitlement-first.json
```

Expected result: rule PASS (72 cases), application PASS (80 cases), exit 0. The JSON report is created with owner-only permissions and is never overwritten. Choose a new output name for each run. Exit 1 means an observed mismatch; exit 2 means setup/input/evaluator failure and supplies no passing result. On an execution error, an already reserved report records that evaluation did not complete.

Ask your coding agent to modify `demo-entitlement/app.py` so that it overwrites `resource_tenant` with `subject_tenant` before invoking `allow`. Then repeat with `--output entitlement-changed.json`. The pure rule should pass while the application check fails with a concrete cross-tenant input, expected denial and observed grant. Use that input to diagnose and repair the change, then run again under a fresh report name.

The candidate directory must contain exactly regular `app.py` and `rule.py` files, each at most 256 KiB. Start with inspected local source you own. Execution uses the existing Linux adapter with namespaces and resource controls; hostile candidate programs and exhaustion behavior have not been validated. The Python kernel remains independent of this Linux adapter. The environment is partially fingerprinted and observations are unsigned. No deployment approval or credential freshness guarantee is supplied.

The contract is in `examples/entitlement/experiment.py`, controlled with the evaluator. It covers tenant IDs 0–2 and three booleans only. A business contract outside that domain needs another adapter or an explicitly reviewed contract change. Changing the evaluator to make your implementation pass defeats independent checking.

Before expanding the adapter, try the same defect with your existing tests. Record setup and diagnosis effort and whether the added contract helps. See [the developer trial protocol](DEVELOPER-TRIAL.md) for evidence thresholds and backtracking criteria.
