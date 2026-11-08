# Prepared developer review task — not sent

Purpose: test whether the coverage artifact improves review of a consequential business-rule change over an equally informed test-only view. This is a small qualitative trial, not a market estimate or a comparison of repair models. No participants, responses, timing results or outreach exist yet.

Participants: two developers who use coding agents on business applications and have not worked through this ERPNext case. The packet author and project owner already know the result; their responses cannot substitute for an unfamiliar participant. An owner must explicitly supply/authorize each recipient and channel before any message is sent. Use participant IDs in retained notes; do not request credentials, private customer data or repository access.

The participant-facing presentations are [view A](REVIEW-VIEW-A.md) and [view B](REVIEW-VIEW-B.md); send only the assigned first view. This operator document contains the rubric and must not be supplied before initial answers. Public links make prior access possible: ask and record familiarity; exclude pre-informed responses from comprehension/timing comparisons while retaining qualitative feedback. Use the [response template](REVIEW-RESPONSES-TEMPLATE.md) only for actual responses.

## Shared facts and materials

Both views receive the same requirement: the fixture user with Sales Invoice Select but without Read must be denied report execution, while the four earlier fixture checks keep passing. Both receive:

- [Pinned test source](https://github.com/frappe/erpnext/blob/79f6fc3cd720c2ba66e2a33cb97d853164ce0e41/erpnext/manufacturing/report/exponential_smoothing_forecasting/test_exponential_smoothing_forecasting.py), source identity and the same complete test-name/verdict matrix in [the replay report](../../benchmarks/erpnext/LIFECYCLE-RESULTS.md).
- The unchanged source has four passing tests and the one expected denial failure. Upstream and both author candidates pass all five. No inference that the fifth requirement was independently discovered.
- The same earlier [failed run](../../benchmarks/erpnext/STRUCTURED-RESULTS.md): base/upstream logs exist, candidate fixture/site setup failed and structured observations were not exported. It is inconclusive, not a passing pair.
- The same limits: inspected diagnostics, finite fixtures, no producer authentication or release/admission authority, no broad security proof, no new execution from reading the packet.

**View A — test-only:** the shared facts, pinned test file and complete method-name/verdict matrix. This represents a competent CI review with source/tests available, not just a green badge. Do not hide the requirement, error status or test inventory.

**View B — scope view:** exactly those facts plus the [declared fixture coverage](../../benchmarks/erpnext/OBLIGATIONS.md), including source-bound group descriptions and stated limits. It adds interpretation/organization, not new observations. This trial therefore cannot establish additional detection power.

For local reproduction from a trusted checkout, `python3 -B -m benchmarks.erpnext.structured_review --attempt lifecycle` shows the archived result and `--obligations` adds the scope view. Neither starts a model or source worker. The raw failed attempt remains available with `--attempt structured`.

## Session protocol and predeclared rubric

Allow up to 10 minutes per participant. Show A first to participant 1 and B first to participant 2, then the other view. Record which view was first, familiarity and actual elapsed time or mark time unmeasured. Order/learning effects remain a confound even when counterbalanced; two convenience participants cannot establish population effects.

Ask the same three questions before showing the second view:

1. What specific requirement blocks merging the unchanged intermediate report? Correct: the Select-without-Read fixture does not raise the required permission error.
2. Do the passing records establish that every customer row and every monthly bucket is correct? Correct: no. The permission method checks one fixture-item absence plus denial, and the boundary-order method checks one May bucket; broader cases are unmeasured.
3. Does the earlier failed job supply a passing author comparison or complete before/after identities? Correct: no. The missing structured observations and candidate setup failures remain inconclusive.

After the second view ask whether any answer changed and why. Then ask: what existing review step would this replace, what useful information is missing, and would maintaining the source/test/description bindings be worth the effort on a real PR? Ask for a concrete workflow/rule, not a hypothetical purchase promise. Accept "ordinary test descriptions are sufficient" as a valid result.

Retain factual notes: participant ID/context, order, answers, elapsed time or unavailable, changed decision, an exact workflow/rule volunteered, and maintenance objections. Do not convert skipped questions, nonresponses or politeness into positive evidence. A small preference is not demand, causal speed improvement or willingness to pay. Public-thread responses are public and cannot be promised confidentiality; obtain permission before retaining a redacted summary.

Proceed only to a separately scoped real integration if a participant identifies a specific useful decision improvement and supplies an owned rule/change. If neither view improves correctness/effort, stop expanding the standalone-product claim and retain the tool as an experimental CI aid. Further runtime/source access, policy approval or spending must be explicitly bounded later.

## Unsent invitation

> Could you review a public eight-to-ten-minute example of a business-rule change made with a coding agent? We have two presentations of the same tests and source facts: a normal test-result view and a scope/limitations view. The repair comparison itself tied; we are testing whether the extra explanation helps a real review decision. No installation, credentials or private code are required. "The normal CI view is enough" is useful feedback. May we record anonymized answers about what you understood, how long it took and what you would change?

This is a draft for owner review, not permission to contact anyone. Send only after the owner names/authorizes a recipient and channel. No external issue, comment, message or email has been posted for this trial.
