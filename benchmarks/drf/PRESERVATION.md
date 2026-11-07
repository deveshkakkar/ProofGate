# Explicit preservation, separate from intended change

The first three historical paired cases tied. Supplementary whole-file checks also tie: both agent arms and upstream pass155 tests without skips. These are the corresponding files, not the full DRF suite. `fullmodule-results.json` retains the earlier optional-dependency skips and completed observations.

Two fresh documentation-only author sessions generated incompatible anonymous-write checks and omitted the unresolved read policy. `doc-contract-results.json` records every proposed property, source, ambiguity and result. The same eight failures occur on reference and all repaired variants in each sample. This shows why generated checks require review before admission. Django explicitly permits custom authorization for anonymous users: https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#authorization-for-anonymous-users . No generated rule was adopted.

`framework.preservation` instead compares finite observations outside a caller-pinned allowed-change box. Omitted scope dimensions are wildcards; `null` means compare everything. Empty or full-domain exemptions reject. Exact complete input inventories, type-sensitive outputs and a separately supplied policy hash are required. Bounds are4096 inputs and16KiB per output. A matching guard neither implements nor verifies the requested change; even the unchanged reference passes.

The retrospective proposed policy in `proposed-read-change.json` permits differences only for authenticated GET/HEAD. A read-only, network-disabled namespace ran `trace_probe.py` on all448 inputs for reference, both agent repairs and historical upstream. The host compared384 protected inputs;64 were unverified. Upstream has12 anonymous-read differences; both repairs preserve all384. The known regression and proposed scope were selected with historical knowledge. This is no novel discovery or evidence of improved repair performance.

Reproduce the comparison from committed observations (no provider, dependencies or candidate execution):

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
from framework.preservation import compare, policy_id
p = Path('benchmarks/drf')
policy = json.loads((p / 'proposed-read-change.json').read_text())
traces = json.loads((p / 'preservation-traces.json').read_text())
for name, trace in traces.items():
    report = compare(policy, policy_id(policy), traces['original'], trace)
    print(name, report['valid'], report.get('violation_count'))
PY
```

Expected differences: original0, baseline0, contract0, upstream12. For actual admission, obtain the policy hash independently from an approved authority; calculating a hash from untrusted input does not approve it. Public trace replay checks observations only. Actual module execution was local Linux/systemd/bubblewrap with pinned extracted Django4.1 dependencies; identities and diagnostic boundaries are in `preservation-results.json`. Probe mocks documented user/view interfaces and does not exercise database, middleware, concurrency or all custom backends. Source, dependency and verifier manifests were checked unchanged during execution. Reference trace is collected once and reused under a source/domain/probe/runtime identity; the cache is evaluator-owned, unauthenticated and only used within this run. Host libraries remain incompletely fingerprinted. Inspected Python source can tamper with its own process; this is not a hostile-code authority.

The useful next trial must declare preservation and intended-change obligations before authoring, then report both independently. A frozen reference can preserve existing bugs; owner review is required for authoritative policy admission. Differential testing is established prior art: https://crosshair.readthedocs.io/en/latest/diff_behavior.html . No algorithmic novelty or external demand has been established.
