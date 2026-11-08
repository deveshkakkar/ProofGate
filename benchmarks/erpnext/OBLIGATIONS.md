# Review the declared fixture coverage

The completed author replay is a passing tie, not evidence that feedback improves repairs. To review what was checked instead of only a5/5 count:

```sh
python3 -B -m benchmarks.erpnext.structured_review --attempt lifecycle --obligations
python3 -B -m benchmarks.erpnext.structured_review --attempt lifecycle --obligations --json
```

The view uses the existing complete archive and the [pinned upstream test file](https://github.com/frappe/erpnext/blob/79f6fc3cd720c2ba66e2a33cb97d853164ce0e41/erpnext/manufacturing/report/exponential_smoothing_forecasting/test_exponential_smoothing_forecasting.py). It links five declared groups to exactly five test methods at held-out source SHA57bc21891324dd9c099af619b5d0132ad6c507d3f4e887e163d168b1c9b7be6b:

| Declared fixture group | Unchanged intermediate | Upstream | Baseline author | Feedback author |
| --- | --- | --- | --- | --- |
| Monthly demand/smoothing fixture | passed | passed | passed | passed |
| May history with draft/boundary records | passed | passed | passed | passed |
| Flat future forecast fixture | passed | passed | passed | passed |
| Document denial/customer restriction fixture | passed | passed | passed | passed |
| Select without Read invoice denial | failed | passed | passed | passed |

Each group includes the fixture scope. For example, the May-history test asserts one bucket equals6 with draft and boundary orders present; that does not establish every other bucket's exclusion. The document-permission method combines Stock User denial and absence of one fixture item for a restricted Sales User. A whole-method failure can stop before later assertions, so the view does not invent per-assertion outcomes or prove every customer row is filtered.

`obligations.json` contains reviewed descriptions of pinned historical tests, not an approved customer policy or independently discovered requirements. A separately supplied metadata pin in the reader code binds those descriptions; `--expected-obligations-sha256` accepts an independently obtained replacement pin. The metadata must have exactly the five named tests, unique IDs/bindings, the right source hash and bounded printable descriptions. Missing/unknown/duplicate/stale/mutated mappings yield no positive coverage. A caller pin is not producer authentication or policy admission; use a trusted reviewed checkout.

The existing archive scorer runs first. Incomplete controls produce no coverage rows. A candidate with incomplete/error/skipped inventory is unknown for every group; no individual green result is inferred from its partial data. Complete failing tests remain failed. Passing means the named finite fixture test passed, not a universal business-policy guarantee. Declared groups never alter checker outcomes or the earlier passing-tie/inconclusive records.

Default output and exit behavior are unchanged without `--obligations`. Requesting an unavailable coverage view exits1 while keeping the underlying archived score separate. `--json` adds the coverage packet, full source/record/metadata pins, per-group verdicts and scope limits. The default `--attempt structured --obligations` retains the earlier setup failure and displays no positive coverage.

Validation: actual successful/incomplete archives and real CLI behavior; synthetic candidate error, malformed/wrong-source/missing/duplicate mappings and wrong pins tested separately. All105 framework tests and existing release checks pass. No new source, provider or hosted execution, runtime/checker/case/manifest/profile/report changes or authority were introduced for this read-only presentation slice.
