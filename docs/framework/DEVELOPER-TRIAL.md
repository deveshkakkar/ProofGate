# First developer trial

Audience confirmed by owner: developers using coding agents on business applications.
Status: build and recruit a trial; no external user feedback collected.

## User task and hypothesis

A developer changes a tenant entitlement rule with a coding agent and needs to understand whether the rule and its application still satisfy the reviewed behavior. Offer one local command against a small two-file application, a concrete counterexample on failure and a retained JSON record. Hypothesis: this reduces time to diagnose a rule/application mismatch compared with the developer's existing tests. It is unvalidated. Green tests and personal enthusiasm do not establish demand.

## This implementation slice

Add an experimental `python3 -B -m framework check-entitlement` command that accepts an inspected local two-file candidate, calls the existing finite evaluator, prints a useful explanation and writes a new JSON report. Use exit 0 for matching checks, 1 for an observed mismatch and 2 for setup/input failures. Refuse to overwrite an existing output path. Reject symlinks, nonregular inputs, unknown files and source larger than 256 KiB. Preserve the original mutation experiment and historical evidence. No candidate execution on the host outside the existing sandbox.

Support only developer-owned, inspected local source. This is not an adversarial runner: host library trust, same-user interference and exhaustion failure controls remain unresolved. The portable core stays separate from the Linux execution adapter. Protected CI authority and deployment are later slices.

Allowed writes: framework/, examples/entitlement/, tests/, docs/framework/, README.md. No server/service, authentication, firewall, backup, existing baseline or recorded evidence changes. No package installation, live provider calls, external outreach, merge or deployment. Bound: 30 minutes of command execution, 2 GiB new storage, two workers. Stop for changed scope, required privileged infrastructure or unsupported source; retain evidence.

Acceptance: run original and tenant-spoof candidate through the CLI; see a concrete failing input for the latter and a nonzero exit; retain reports without overwrite; test malformed input and failure summaries; retain 11 framework and original release regressions. Fresh review required before PR. Explicitly label mocked/unit checks versus actual local execution.

## Trial protocol

Recruit three to five developers already changing business logic with coding agents; owner handles introductions. Do not send outreach without authorization. Ask each for a recent real regression and their existing verification workflow before showing the demo. Record concrete past behavior rather than whether they like the idea.

Use their existing tests as baseline. Time a small change and diagnosis, then repeat with the adapter. Record setup time, contract/adaptation time, diagnosis time, failures caught by each approach, confusing output, false acceptance/rejection and willingness to use it on another change. Do not infer usefulness from a staged bug the existing suite would also catch at lower effort.

Proposed go/no-go thresholds (experiment design, not observed results): at least three completed trials; two developers independently run a check and explain its result within 15 minutes of setup; two choose a second real change to try; evidence shows a missing boundary check or lower diagnosis/review effort than their baseline. If integration dominates benefit, simplify the interface or change the workflow before adding features. If equivalent ordinary tests are easier, investigate whether reusable contract/check templates alone supply the value. If no repeat use, backtrack the product hypothesis.

## Learning memo

Confirmed: owner-selected audience and technical ability to expose an adapter defect after pure-rule checks pass. Unconfirmed: customer pain frequency, acceptable specification cost, willingness to adopt, comparative advantage, and willingness to pay. Next external evidence requires actual participants and their real changes; implementation cannot manufacture that evidence.
