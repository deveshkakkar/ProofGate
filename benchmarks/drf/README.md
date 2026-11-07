# Historical DRF shadow replay

This experiment compares a fresh coding-model response with and without executable contract feedback. Both arms receive the same issue, base module, existing test class and prose requirements. The treatment also receives the frozen contract and its failure on the base code. No arm receives upstream patches, later comments or post-change tests. These are researched retrospective cases, not a random blind benchmark or evidence that public code was absent from model training.

Selected changes: [7522](https://github.com/encode/django-rest-framework/pull/7522), [8009](https://github.com/encode/django-rest-framework/pull/8009), and [9934](https://github.com/encode/django-rest-framework/pull/9934). Their intended changes and later history require interpretation; a merge is not a correctness oracle. In particular, 8009 was [reverted](https://github.com/encode/django-rest-framework/pull/9332) after an [anonymous-read compatibility issue](https://github.com/encode/django-rest-framework/issues/9299).

`contracts.py` defines the frozen finite checks. They import real upstream modules and execute only in the experiment's network-disabled source sandbox. Boolean domains cover 16 two-operand OR configurations and 224 model permission/method configurations; the renderer check covers 32 method/permission configurations. Each is one pytest test looping over its domain, stopping on its first failure. Domain sizes are not pytest test counts, and failed runs do not exhaust the remaining inputs. `compatibility.py` is an explicitly post-hoc anonymous-read check, excluded from the frozen paired score.

`score.py` is a portable, dependency-free offline scorer:

```sh
python3 -B -m benchmarks.drf.score benchmarks/drf/results.json
```

It requires both held-out upstream tests and the frozen contract to pass. Original-test results remain informational because some requested behavior changes intentionally revise old assertions. Empty suites, skipped tests, setup errors, timeouts and contradictory observations are inconclusive. The original version must reproduce failure and the upstream comparison version must pass the selected checks before a pair can be counted; otherwise the case stays visible as inconclusive.

The scorer validates observation consistency, not authenticity or completeness against a preregistered inventory. Input JSON and its identities require an independently trusted producer. It does not execute candidates or supply release approval. Published results must retain all planned cases, including failed author sessions and unsupported environments. A small descriptive tie or win is not a population-level causal estimate.

Source checkouts, dependency wheels, private provider output, and prompts stay outside the repository. The experiments use existing authenticated Codex transport in a separate bounded, tool-disabled namespace; evaluated source gets neither authentication nor network. Context separation is observable; training-memory isolation is not. Dependency versions are recorded and may differ from historical originals. Provider transport settings and credentials are not packaged as a public runner. No external project is contacted with findings or modified.

See [the bounded plan](PLAN.md), published results and the framework [state memo](../../docs/framework/STATE.md). These artifacts are an experimental shadow adapter, not automatic DRF support in the entitlement CLI.


## Observed pilot outcome

Both arms passed the held-out class and frozen contract on all three cases: zero treatment wins, zero losses, three passing ties, no inconclusive pairs. This pilot supplies no observed implementation advantage for contract feedback over equivalent prose requirements. The treatment consumed additional input tokens. Do not expand an agent-repair orchestrator on the strength of these results.

The post-hoc anonymous-read check passes on original code and both model repairs, but fails on upstream 8009. This reproduces the already documented regression behind its later revert. It motivates checking compatibility boundaries independently of a changed requirement; it is not a newly discovered vulnerability or a scored treatment win. Both arms preserved this behavior, so it supplies no evidence that contract feedback improved their repairs.

A useful next step is a read-only shadow evaluator that preserves pre-change behavior contracts alongside requested changes and retains actionable evidence. Protected CI transport can follow the same portable observations without entrusting candidate code with checker configuration. User adoption, contract authoring cost and evidence usability remain unvalidated.
