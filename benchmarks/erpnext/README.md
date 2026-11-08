# ERPNext validation evidence

Separate experiments cover different scopes:

- [Full report controls](FULL-APPLICATION-RESULTS.md): original fails three known checks; final passes all five in real ERPNext/Frappe/MariaDB sites. Earlier setup failures remain recorded.
- [Intermediate patch](INTERMEDIATE-RESULTS.md): intermediate passes its four earlier checks but misses the added select-only read-denial requirement; final passes all five. This is a retrospectively selected known followup.
- [Lifecycle replay](LIFECYCLE-RESULTS.md): all four full-application suites complete under the unchanged cap; both author candidates pass5/5, a passing tie with no observed feedback advantage. Generated sites retire after capture; all prior failures remain separate.
- [Structured author replay](STRUCTURED-RESULTS.md): both edit proposals validate, but database storage exhaustion stops candidate testing; actual paired outcome remains inconclusive. Offline review explains the archived failure without rerunning code.
- [Paired author replay](PAIRED-RESULTS.md): both raw diffs are malformed; paired application outcome is inconclusive, with zero hosted/source runs. At that phase's close the structured edit protocol was prepared but untested; the later structured replay above records provider validation and its separate setup failure.
- The finite arithmetic transfer below: 108 observations per source, isolated helper AST with fixture shims, separate from application execution.

Use the [declared fixture coverage view](OBLIGATIONS.md) to inspect the business meaning, exact pinned test bindings and limits of the five checks. It adds no new execution or acceptance authority.

No experiment establishes novel discovery, improved agent repair, customer demand or release authority. Offline archive inspection and manual hosted execution are documented separately in the linked reports.

## Forecast-helper transfer test

This checks whether the unchanged finite preservation/change evaluator transfers from permission logic to business arithmetic. It reproduces the known forecast defect fixed in merged [ERPNext60977](https://github.com/frappe/erpnext/pull/60977). It is not a new repair author trial, blind discovery or an ERPNext application run.

The source-helper class `ExponentialSmoothingForecast` is selected from the exact base/head module AST and compiled inside a read-only, network-disabled resource-limited worker. Full module imports do not execute. Numeric/date fixture shims model only finite nonnegative numeric values, absent actuals and date objects. Inspected current Frappe helper semantics are retained privately; they are not installed or proven to match the historical dependency version. Third-party source stays outside this repository; source/selected-AST hashes and upstream license link are recorded in `results.json`.

The 108-input domain has three history fixtures, three smoothing constants(0.25,0.5,1), three horizons(1,2,4), two seed modes and two projections. All54 historical projections must match the reference;54 future projections must match an independent Decimal SES oracle frozen before either worker ran. Binary-exact fixture arithmetic needs no comparison tolerance. Missing forecast fields project to0.0; field-presence compatibility is deliberately outside this experiment.

| Source helper | Historical differences | Future expectation differences | Finite proposal |
| --- | --- | --- | --- |
| Unchanged base | 0/54 | 20/54 | Does not match |
| Merged head | 0/54 | 0/54 | Matches |

For three past observations of100, alpha0.5 and four future periods, base returns `[100,50,25,12.5]`; head returns `[100,100,100,100]`. Simple exponential smoothing carries its final smoothed level forward when there are no new actuals. The report's existing initialization is preserved, including the explicit fixed-seed fixture; the experiment makes no claim about choosing an optimal forecasting model. See the independent [SES reference](https://otexts.com/fpp3/exponential-smoothing.html#flat-forecasts).

Reproduce the observation check without running ERPNext or contacting a provider:

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
from framework.change import check
p = Path('benchmarks/erpnext')
spec = json.loads((p / 'proposed-change.json').read_text())
pin = json.loads((p / 'results.json').read_text())['specification_sha256']
traces = json.loads((p / 'traces.json').read_text())
for name, trace in traces.items():
    report = check(spec, pin, traces['base'], trace)
    print(name, report['satisfied'], report['preservation']['violation_count'],
          report['intended_change']['violation_count'])
PY
```

Expected: baseFalse/0/20;headTrue/0/0. The trace checker validates records, not the source execution that produced them. Probe/transport/interpreter identities and private source artifacts/logs are retained under `~/.local/share/proofgate-framework/erp-forecast-uc5tc6tt/`; two source workers completed under existing512MiB/32task/1CPU/45s scopes. No dependency installation, new framework API, model call or upstream message was needed. Inputs, sources, probe, oracle and expected outputs were pinned; no reference/policy outputs were mounted into workers.

The separate document-permission fix bundled in60977 is not checked. Neither are real reports, query aggregation, calendar generation, currency precision, negative demand, real Frappe parsing or the full ERPNext suite. Host libraries are incompletely fingerprinted and source execution remains inspected-code diagnostics. Matching the declared finite proposal grants no policy admission or deployment authority. Existing DRF repair ties remain unchanged, and external demand/superiority remain unvalidated. This shows one narrow arithmetic transfer without expanding the kernel; full application boundaries require their own explicit trial.
