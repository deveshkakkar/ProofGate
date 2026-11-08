# Intermediate permission patch: frozen retrospective test

Question: can a patch satisfy its submitted tests while missing a separately specified access requirement? The intermediate ERPNext60977 patch already enables permission-aware document queries; the later patch adds an explicit read-permission guard. Select permission and read permission are distinct obligations in this case.

Pinned intermediate source04afe19d8ef067eec3852f4ac8007af42718d0b6 is compared with final report79f6fc3cd720c2ba66e2a33cb97d853164ce0e41, on the intermediate app snapshot. Both receive the same final five-test module, Frappe/payments/image and installed environment in one disposable hosted job. No application fix or test is authored here. Original app_case.json and its recorded original/final experiment remain unchanged.

Static prerequisite: Python AST comparison of the entire intermediate test module equals the final test module after removing exactly `test_select_only_access_does_not_show_invoice_figures`. Imports, fixture helpers, class setup and all four earlier tests are included in that comparison; location attributes are ignored. `intermediate-test-comparison.json` records source SHA256 identities and the method removed. Source is retained privately for license-aware inspection.

[Run42448017599](https://github.com/deveshkakkar/ProofGate/actions/runs/42448017599) at15ae916 completed in378.209seconds and matched the frozen prediction:

| Source report | Four earlier checks | Added select-only read check | Errors/skips |
| --- | --- | --- | --- |
| Intermediate04afe19 | 4 pass | fails: expected PermissionError was not raised | 0/0 |
| Final79f6fc3 | 4 pass | passes | 0/0 |

Both exact five-test inventories completed, with no expected failures or unexpected successes. The intermediate failure log states `PermissionError not raised by execute`; this shows the declared read-denial check failed, not an independently measured production data breach. Source-module and held-out-test hashes match before/after execution. Separate real sites/users/roles/documents ran with empty network attachments, uid1001, read-only root, capability dropALL, no-new-privileges and the unchanged resource caps. Inventory records Python3.14.6 and241 package versions plus binary/tree hashes.

`intermediate-results.json` retains the exact report, canonical record pin, producer revision and artifact ZIP digest. Every producer hash was checked against Git15ae916 (the selected intermediate descriptor is logically recorded as app_case.json); the intermediate report hash also matches the pinned primary source. The reviewed new profile validates through the same archived adapter, and the original successful report remains valid under its original profile. This consumed the single-run allowance; no setup retry, test change or additional author call occurred.

This case was selected with knowledge of the historical followup. This result demonstrates the value of that additional requirement in one report; it does not demonstrate a novel discovery, independent requirement generation, author repair advantage, broad security coverage or product demand. Prior authoring trials remain passing ties. Backend mode excludes frontend lifecycle/build behavior. These are inspected-code diagnostics without producer authentication or release authority.

## Frozen producer compatibility

`producer-profiles.json` stores reviewed case descriptors, historical producer revisions, five verifier hashes and the pure classifier's source-segment hash. The original profile was checked against actual Git objects at7249964 and the successful archived report. Historical reports retain those original hashes even though transport now supports another case. The archive validator binds the selected frozen profile, historical verifier, current validation code and current matching classifier separately through the unchanged kernel. Unknown/ambiguous selected profiles and malformed registry metadata reject. Descriptor semantics remain reviewed trusted registry data.

A new profile is registered only after its actual run and corresponding Git identities are checked. Registration provides archived compatibility, not evidence that a producer executed those bytes. The caller still needs an independently trusted canonical record pin. Unauthenticated report metadata alone cannot create a new profile or grant admission.

Manual transport (the ERPNext job is disabled on normal PR/push):

```sh
gh workflow run ci.yml --ref REVISION \
  -f erpnext_trial=true -f erpnext_profile=intermediate \
  -f shadow_case=none -f shadow_version=original
```

`original` remains the default profile. This command starts a bounded disposable runner; it is not part of the offline evidence inspection command. The experiment recorded here permits only the single run above, without automatic retry.

Offline inspection of the retained new run:

```sh
python3 -B - <<'PYCODE'
import json
from pathlib import Path
from benchmarks.erpnext.app_evidence import inspect
row = json.loads(Path('benchmarks/erpnext/intermediate-results.json').read_text())
result = inspect(row['report'], row['record_sha256'])
print(result['mode'], result['consistent'], result.get('producer_profile'))
PYCODE
```

Expected: `archived-consistency-only True intermediate-15ae916`. This reads the trusted reviewed pin alongside the report; it does not rerun application code. Current66 framework tests and original46 regression/six rejection checks pass. A fresh review of the final evidence accompanies the PR.
