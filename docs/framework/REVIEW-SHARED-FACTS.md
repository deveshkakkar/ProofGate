# Shared test/source facts

This public historical case changes an ERPNext forecasting report. Required behavior: a fixture user with Sales Invoice Select but without Read must be denied report execution, while four earlier fixture checks keep passing. This is a test/source view, not a release authorization.

The same pinned test file is available [here](https://github.com/frappe/erpnext/blob/79f6fc3cd720c2ba66e2a33cb97d853164ce0e41/erpnext/manufacturing/report/exponential_smoothing_forecasting/test_exponential_smoothing_forecasting.py). The full archived source/context is in [the replay report](../../benchmarks/erpnext/LIFECYCLE-RESULTS.md) and [raw record](../../benchmarks/erpnext/lifecycle-results.json). You may inspect the source; this baseline is not restricted to an exit code or badge.

| Exact test method | Unchanged | Upstream | Baseline author | Feedback author |
| --- | --- | --- | --- | --- |
| test_monthly_qty_forecast_from_sales_orders | pass | pass | pass | pass |
| test_ignores_documents_outside_range_and_other_docstatus | pass | pass | pass | pass |
| test_future_forecast_stays_flat | pass | pass | pass | pass |
| test_report_follows_document_permissions | pass | pass | pass | pass |
| test_select_only_access_does_not_show_invoice_figures | fail | pass | pass | pass |

All four suites have five tests, no errors/skips/xfails/xpasses and matching before/after source/test identities. Both author candidates passed; the repair comparison tied. The test source hash is57bc21891324dd9c099af619b5d0132ad6c507d3f4e887e163d168b1c9b7be6b. The records are inspected diagnostics with finite fixtures, no producer authentication, admission or release authority and no universal security guarantee.

An earlier [failed run](../../benchmarks/erpnext/STRUCTURED-RESULTS.md) has successful base/upstream log fragments, but candidate fixture/site creation failed and no per-variant structured observations were exported. It remains an incomplete record, separate from the later success. Both views receive this same fact.

