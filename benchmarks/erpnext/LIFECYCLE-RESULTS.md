# Disposable-site lifecycle replay

The owner authorized one setup-only repair and one additional hosted evaluation, reusing both valid structured author outputs with no new model calls. Earlier failed report42476751670 and its producer profile remain unchanged. The new source retires each generated database/user after its exact result and source before/after hashes are written, before creating the next fresh site. Pinned Frappe handles the local socket/root credential and no-backup drop/archive; fixed site/database/socket/tmpfs guards restrict the target. Original/intermediate two-site modes retain their lifecycle.

[Run42515664412](https://github.com/deveshkakkar/ProofGate/actions/runs/42515664412) at8f5fcff completed in620.399seconds. All four exact five-test suites completed, with zero errors/skips/expected failures/unexpected successes and matching before/after module/test hashes.

| Variant | Earlier four checks | Read-denial check | Outcome |
| --- | --- | --- | --- |
| Unchanged intermediate source | 4 pass | expected failure reproduced | valid negative control |
| Upstream report | 4 pass | passes | valid positive control |
| Baseline author | 4 pass | passes | passes5/5 |
| Feedback author | 4 pass | passes | passes5/5 |

The result is a **passing tie**: no observed repair advantage from failure feedback for this pair. Both authors received the same explicit requirement, while only feedback received the frozen counterexample. Author outputs were reused unchanged; no additional model calls or human repairs occurred. This does not turn the earlier malformed-output pair or failed setup run into successes.

All four generated database folders and active site directories were reported removed after result capture. The pinned Frappe command drops the database/user and archives generated site files inside the disposable tmpfs. Observed free storage increased after every retirement:

| Variant | Free MiB before | Free MiB after | MiB reclaimed |
| --- | ---: | ---: | ---: |
| Base | 315.18 | 469.46 | 154.29 |
| Upstream | 310.19 | 467.60 | 157.41 |
| Baseline author | 308.61 | 466.03 | 157.42 |
| Feedback author | 307.57 | 464.95 | 157.38 |

The archive retains exact byte values; MiB values above are rounded. This observes workspace reclamation, not a peak-memory measurement. Neither source nor tests were weakened and the4GiB home cap was unchanged. Profile registration independently checked all eight historical producer files against Git8f5fcff, selected case/candidate identities,241-package environment and fixed isolation. `lifecycle-results.json` retains the exact report, canonical record pin and artifact digest; `lifecycle-producer.json` is separate from the unchanged failed structured producer. Private logs/artifact/score are under erp-runtime-preflight-51wrsarb/attempt-42515664412.

Same declared source/image/Frappe/payments pins, uid1001/capdropALL/NNP/readonly-root+driver+inputs,5GiB memory/no swap growth,2CPU/256PIDs,4GiB home/128MiB tmp and30min job limit apply. Network attachments are empty before local MariaDB/Redis/tests. No home-server source execution, images/containers/installs/services or production/backup changes. Archived site configurations remain inside the disposable tmpfs and are excluded from exports. Existing secret redaction and bounded failure capture remain.

## Offline review

Review the actual retained result and separately reviewed producer profile:

```sh
python3 -B -m benchmarks.erpnext.structured_review --attempt lifecycle
python3 -B -m benchmarks.erpnext.structured_review --attempt lifecycle --json
```

The default `--attempt structured` preserves the earlier failed replay. Each reads fixed reviewed repository records without running candidates or contacting a provider. An external `--expected-record-sha256` can override the selected reviewed record pin. A wrong pin or incomplete controls yields no passing summary. Exit0 means valid reproduced controls, not that author candidates necessarily passed; inspect the separate candidate verdicts. Use a trusted reviewed checkout, not candidate-controlled data as its own authority.

The original source-bound JSON proposals, shared prose requirements and feedback difference are frozen. This remains one retrospectively selected known case with possible training contamination and human requirement design, not blind discovery, demand or a population-level comparison. Prior three DRF ties and both earlier ERPNext inconclusive author trials remain visible. No producer authentication, fresh execution by the archive reader, policy admission or release authority is granted. Static guard/scorer fixtures remain separate from the actual archived report and CLI checks. No retry or setup repair after this one run is authorized.


## What this establishes and what comes next

The setup lifecycle now supports this fixed four-site comparison within the existing cap, and both the plain-requirement and feedback-assisted candidates satisfy the same narrow application checks. The framework remains a read-only diagnostic/evidence path; this result supplies no reason to expand repair orchestration. The useful demonstrated guard is the explicit read-denial obligation that the intermediate patch's earlier tests missed. That requirement was known from a historical followup and supplied equally to both authors; no automatic independent requirement discovery is established.

The approved setup repair/run phase is complete and consumed. No further live source/model execution is needed to archive or review this evidence. Additional cases would need their own frozen requirements and bounded execution allowance; a PR merge does not grant that allowance or deployment authority.
