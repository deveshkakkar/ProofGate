# Fixed report controls reproduced in a real application runtime

[Run42443539018](https://github.com/deveshkakkar/ProofGate/actions/runs/42443539018) at7249964 completed both full five-test suites in373.933seconds. Original source produced exactly the three expected regression failures; the upstream fix passed all five. Neither suite had errors, skips, expected failures or unexpected successes. Report-module and held-out-test hashes matched before/after each suite.

| Attempt | Revision | Outcome |
| --- | --- | --- |
| [42441614137](https://github.com/deveshkakkar/ProofGate/actions/runs/42441614137) | a9de5d1 | Bench crontab access denied by nonroot/read-only isolation; zero tests, inconclusive |
| [42442011121](https://github.com/deveshkakkar/ProofGate/actions/runs/42442011121) | 1034d18 | Nested banking frontend install hit ENOSPC under temporary-storage caps; zero tests, inconclusive |
| [42442801084](https://github.com/deveshkakkar/ProofGate/actions/runs/42442801084) | 25b7850 | Backend setup completed; empty root credential caused noninteractive site creation EOFError; zero tests, inconclusive |
| [42443539018](https://github.com/deveshkakkar/ProofGate/actions/runs/42443539018) | 7249964 | Temporary credentials and socket provisioned separate sites; exact original/fixed controls reproduced |

The three original failure identities are `test_future_forecast_stays_flat`, `test_report_follows_document_permissions` and `test_select_only_access_does_not_show_invoice_figures`. Existing monthly forecast and document/date/status exclusion checks pass. The repaired-source document-permission test reaches both the Stock User read denial and Sales User customer restriction assertions. The original test stops at its first failed assertion, so this run does not independently demonstrate every later assertion on original source.

This is actual pinned ERPNext/Frappe code, MariaDB documents/users/roles and report execution, beyond the earlier extracted arithmetic class. It is still five tests for one report, not the full ERPNext suite, arbitrary deployments, external demand, novel discovery or improved agent repair performance. Source archives and module substitutions are explicit: a pinned ERPNext base app plus either original or upstream report module and the same frozen upstream test file. Frappe/payments/image pins form a newly declared environment, not reconstruction of the author's historical dependency environment.

The successful artifact includes241 Python package versions, package-tree and binary hashes, Python3.14.6, Bench5.31.0, Node24.17.0, MariaDB10.11.14 and Redis7.0.15. Network attachments were empty before service/tests; actual recorded controls include uid1001, read-only root, capability dropALL, no-new-privileges, memory/swap both5GiB and256PIDs. Controller arguments additionally fix2CPU,4GiB home tmpfs and128MiB tmp. No home-server image/container/package/service operation occurred. Databases/configs/raw credentials are excluded from exports; generated test credentials lived inside tmpfs and were registered for redaction.

The backend-only mode uses NODE_ENV=production and disables Yarn install scripts, omitting nested frontend setup. Frontend package lifecycle/build/UI behavior is not validated. Earlier ENOSPC artifacts did not retain mount-specific usage; do not infer which temporary mount filled. Earlier failures remain inconclusive and are never counted as candidate rejection. Host libraries are incompletely fingerprinted; in-process source/tests are inspected diagnostics rather than a hostile-producer authority.

The owner separately authorized the one backend-only retry and then a phase of up to3 setup-only repairs/runs. The first attempt of that latter phase succeeded, so setup work stops; its two unused attempts do not authorize other trials. All original reports/inventories/sanitized logs remain privately under `~/.local/share/proofgate-framework/erp-runtime-preflight-51wrsarb/attempt-RUNID/`, with exact reports retained in `app-results.json`. Source and fixture identities are unchanged across failed/successful setup attempts except explicitly recorded verifier changes.

## Archived consistency through the unchanged ProofGate kernel

`app_evidence.py` consumes the actual fixed-case report using an independently supplied canonical record pin. It rechecks exact original/fixed outcomes, case/source/held-out identities, current producer verifier bytes and fixed isolation/environment shape, then reuses `framework.kernel` unchanged to bind source/archive/verifier/environment inputs. A passing original-control check means its known failures were reproduced; it does not accept original source.

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
from benchmarks.erpnext.app_evidence import inspect
rows = json.loads(Path('benchmarks/erpnext/app-results.json').read_text())['attempts']
row = next(row for row in rows if row['run_id'] == 42443539018)
result = inspect(row['report'], row['record_sha256'])
print(result['mode'], result['consistent'])
print(result.get('receipt'))
PY
```

Expected mode is `archived-consistency-only`, consistentTrue. For a standalone record, use `python3 -B -m benchmarks.erpnext.app_evidence --report FILE --expected-record-sha256 PIN`; JSON result exits0 only for consistent archived controls. Obtain the pin from a trusted reviewed record, not by hashing arbitrary untrusted input and approving itself. Producer authentication, fresh source execution, policy admission and release authority remain false. This checker validates archived claims and hashes; it cannot authenticate that source execution produced them. It is conservative: a changed producer verifier requires the corresponding frozen evaluator rather than restamping old data with a new implementation.

Current validation includes the actual archived run, altered/missing-control/source/pin/verifier/profile rejection controls, all earlier inconclusive records, and independent review. No extra source workers or author calls were used for archive integration. PR17 merge remains separate owner-approved work.
