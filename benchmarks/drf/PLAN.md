# Paired historical replay slice

Base ProofGate: 65817fd. Owner authorizes autonomous progress until a real block, and selected developers using coding agents on business applications. No merge or deployment authority for new PRs is inferred.

## Intended behavior

Turn the private DRF pilot into a repeatable comparison and use the findings to choose the next implementation. Paired author sessions receive the same issue, base source, existing tests and natural-language desired behavior. The treatment additionally receives executable contract details and a frozen counterexample from the unmodified candidate. Both arms have one call, the same configured model, disabled tools and no held-out patch/tests. This tests whether explicit executable feedback adds value beyond an equally specified task, not whether extra hidden requirements improve results.

Initial selected retrospective cases: DRF PRs 7522, 8009, 9934. These are researched historical cases, not a blind random sample. Record semantic changes, inconclusive runs, environment adaptation, false alarms and null results. Do not equate merge with correctness. A model may have seen public code in training. Source issue bodies may have been edited after publication. The requirement author knows the fixes. No claims about novelty, causal population effects or customer demand follow from three cases.

## Allowed writes and bounds

Repository writes: benchmarks/drf/, targeted tests/, docs/framework/STATE.md and an offline CI invocation if useful. Clone original source, dependencies, prompts, model output and full logs only into a new owner-only folder under ~/.local/share/proofgate-framework/. No third-party source, secrets, auth files or raw provider logs in Git. Source and candidate execution occur only under the existing namespace/resource isolation, without provider credentials or networking. Author transport alone uses existing read-only Codex authentication; no keys or provider accounts are provisioned.

At most six new model sessions, 180 wall seconds each, at most two simultaneous sessions, 20 minutes command wall time, 1 GiB new retained storage and two CPUs. Reuse cached pinned dependency wheels. Stop dependent work if authentication is unavailable, supported isolation fails, privileged infrastructure is needed, or these bounds are reached. Record the bound and outcomes; independent safe analysis and review may continue. Do not spend beyond this slice silently.

## Acceptance and learning gates

Publish only a sanitized aggregate and hashes of public inputs. Include the exact revision, contract source, environment, author prompt differences, per-case baseline/treatment/upstream results, and missing checks. Retain fresh provider, actual local test, and mocked/unit evidence separately. A private manual script is not shipped framework support. Fresh independent review and repository checks precede a normal PR.

If both arms succeed, report no observed implementation advantage and focus on boundary checks and evidence usability rather than adding an orchestrator. If treatment wins only through added semantics, label that confound and rerun with equivalent requirements. If upstream fails a plausible contract, investigate whether the requirement is wrong, the change intentionally breaks compatibility, or the implementation is defective before scoring a win. Unsupported cases remain visible; do not drop them to inflate a pass rate.
