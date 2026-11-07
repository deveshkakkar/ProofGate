# Checking the requested change as well as preservation

The frozen live shadow trial uses open DRF [PR10091](https://github.com/encode/django-rest-framework/pull/10091), base `4acc64013b3ca101631efe5ebcacbb18960bbe37`, head `09518301043788cc9fb25b38bd5b6b48c0bd9233`. At selection and the latest metadata check it was open and unmerged. The contributor's description was seen before evaluation; no blind authoring or independent requirement-discovery claim applies.

For two model permission classes, the proposal adds `QUERY` with an empty required permission list while retaining each class's authentication rule. [RFC10008](https://www.rfc-editor.org/rfc/rfc10008.html) specifies safe/idempotent request semantics; it does not decide application authorization. This experimental policy follows the contributor's stated intent. It is not owner-admitted production policy.

The two real source snapshots produced 512 observations each. The new checker separately evaluates:

| Source | Existing methods preserved | QUERY expectations satisfied | Combined finite proposal |
| --- | --- | --- | --- |
| Unchanged base | 448/448 | 16/64 | Fails |
| Proposed head | 448/448 | 64/64 | Matches |

A preservation-only check passes unchanged code. Complete expected outputs inside the declared change region close that gap. The specification pins the exact reference trace, preservation policy, expected outputs and provenance. Missing/extra/duplicate obligations or observations reject. Modified reference or specification rejects under the old pin. Comparisons distinguish JSON booleans and numbers.

`query-results.json` distinguishes actual recorded source observations from synthetic fault controls. An edited POST result fails preservation while satisfying the QUERY expectations; an edited QUERY denial fails the intended-change component; a missing observation is invalid. These edits test evaluator behavior and are not upstream defect discoveries. No model calls or new source workers were used for this composition.

Run the developer command on the committed observations:

```sh
python3 -B - <<'PY'
import json
from pathlib import Path
from framework.change import check
p = Path('benchmarks/drf')
spec = json.loads((p / 'query-proposed-change.json').read_text())
traces = json.loads((p / 'query-traces.json').read_text())
pin = json.loads((p / 'query-results.json').read_text())['specification_sha256']
for name in ('base', 'head'):
    report = check(spec, pin, traces['base'], traces[name])
    print(name, 'matches' if report['satisfied'] else 'does not match')
    print('preservation differences:', report.get('preservation', {}).get('violation_count'))
    print('requested-change differences:', report.get('intended_change', {}).get('violation_count'))
    for component in ('preservation', 'intended_change'):
        examples = report.get(component, {}).get('counterexamples', [])
        if examples:
            print(component, 'first counterexample:', examples[0])
PY
```

For external JSON files use `python3 -B -m framework.change --specification SPEC --expected-specification-sha256 PIN --reference OLD --candidate NEW`. It emits a JSON report and exits 0 for matching finite observations, 1 for a mismatch, and 2 for invalid inputs. Obtain the pin through a trusted review path before using it; hashing an untrusted proposal does not approve it. This command does not execute candidate code or establish that traces came from a particular source artifact.

Actual source execution used bounded network-disabled namespaces with read-only source/dependencies; identities are retained in `query-results.json`. Dependencies were the earlier extracted Django4.1 set. It can import these permission modules, but this is not supported current-DRF application compatibility evidence. Mocked user/view interfaces do not cover object permissions, middleware, database backends, HTTP dispatch, CSRF, routers or filtering. Reports establish finite observations, not reference correctness, producer authentication, universal behavior or deployment authority. Three historical paired repair ties remain unchanged; this live passing slice shows no repair superiority or external demand.
