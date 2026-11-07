# Request and database checks for the frozen QUERY proposal

PR12's initial finite observations used an old Django4.1 module environment. This separate slice uses Django5.2.19, Python3.12.3 (Ubuntu distribution interpreter), pytest9.2.0, SQLite3.45.1 and pinned extracted dependencies. Current DRF declares Django>=5.2; Django documents Python3.12 as a compatible series. This is one local environment, not a supported-version matrix or a claim that the interpreter is the latest upstream micro release.

Sources: [DRF10091](https://github.com/encode/django-rest-framework/pull/10091), [pinned project requirements](https://github.com/encode/django-rest-framework/blob/09518301043788cc9fb25b38bd5b6b48c0bd9233/pyproject.toml), [Django compatibility](https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django). No model author calls or upstream messages were made.

| Check | Frozen base | Frozen proposed head |
| --- | --- | --- |
| Each revision's own permissions/authentication test files | 114 pass | 119 pass |
| Same nine independent request/database checks | 5 pass, 4 fail | 9 pass |
| Head finite observations replayed on Django5.2 | Not rerun | All512 identical to earlier head trace |

All completed pytest runs have zero errors/skips. The own-source upstream files differ between revisions, so their totals are not a held-out comparison. The same independent boundary checks provide the expected missing-feature control. Four checks fail on unchanged base: session QUERY without CSRF, default authenticated model QUERY, anonymous read-only QUERY and explicit database-granted QUERY. They all pass on the head. Existing GET/session access and POST/CSRF rejection remain exercised.

`query_http_probe.py` defines the nine checks. Real session login and middleware CSRF enforcement are separate from force-authenticated permission tests. The latter use real SQLite user/permission tables and Django's permission backend: an explicit QUERY permission denies an ungranted user, permits a granted user, and denies anonymous access. A custom legacy permission map lacking QUERY returns405. The session QUERY test confirms no user row is added by its read-only test handler; this is not a proof that arbitrary QUERY handlers cannot write.

`query-http-results.json` retains all six source-worker attempts with identities and `query-http-dependency-lock.json` records exact wheel URLs/hashes and dependency metadata. The initial command supplied a wrong authentication-test path and ran zero tests with exit4. It remains an invalid/inconclusive setup attempt. The correction changed only the controller's test path. No dependency repair, global install or source modification was needed. Source and dependency manifests were checked unchanged for each run. The sixth and final worker's512-output trace exactly matches the already committed `query-traces.json` head under canonical JSON identity.

Execution reused the existing read-only namespace/resource helper: no network, home or credentials; source/dependencies read-only; aggregate512MiB/32tasks/1CPU/45s; tmp64MiB. Databases were namespace-local/in-memory. These were in-process Django test-client requests, not traffic through a deployed HTTP server. All private logs, scripts, original setup plan and manifests are retained under `~/.local/share/proofgate-framework/drf-query-http-1a90cikb/`. Public probe and records support inspection; this evidence change does not add a one-command acquisition/setup/replay runner.

No full DRF or full PR claim applies: routers, filtering/body merging, production databases, object-permission boundary probes beyond the upstream file, network service behavior and the version matrix remain outside this slice. Host libraries are incompletely fingerprinted; inspected Python can tamper with its own process. Policies still follow the contributor's stated intent rather than universal authorization rules or owner-admitted production contracts. This does not establish new defects, better agent repairs or external demand. The frozen upstream PR's later review/outcome remains external evidence to observe without rewriting this trial.
