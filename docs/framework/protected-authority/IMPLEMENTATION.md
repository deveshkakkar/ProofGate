# Executable milestone 1 components

`proofgate_authority/scope.py` implements canary binding, installation, token-request and redacted-grant validation. It rejects production/default/extra repository scope, wrong installation/App/account, suspended or unknown installation state, excess/missing permissions and invalid/expired/excess-lived grants. It makes no network call, mints no token and never authenticates supplied metadata. Its output explicitly grants no admission or merge eligibility. The issuer must load the human-reviewed binding from outside candidate control and obtain real GitHub metadata independently; this library alone does not supply that boundary.

Offline CLI (redacted metadata only):

```sh
python3 -I -B /path/to/ProofGate/scripts/check_canary_scope.py \
  --binding /owner-reviewed/canary-binding.json \
  --installation /redacted/installation.json \
  --repositories /redacted/installation-repositories.json
```

Add `--grant-metadata /redacted/grant.json` to validate permissions/repositories/UTC expiry. Never save a raw token response for this command: a `token` field is rejected. A successful request output is data only (`request_executed:false`); it does not authorize a POST. No `gh` fallback or owner authentication lookup exists in this code. Binding requires exact repository/name, positive non-production repository ID, approved App ID and installation ID. No binding/identity is invented from the unbound proposal.

`proofgate_authority/isolation.py` plus the fixed `worker_probe.py` executes a real process diagnostic using the existing bounded bwrap/systemd profile. The controller establishes a harmless outside fixture is readable on the host, then checks it is unavailable inside; checks PID/mount/network namespaces, environment clearing, read-only source and absent host home/run. No real credential contents are read. Unexpected output types/fields are withheld from exported observations. The actual helper is restricted to disposable hosted CI; local tests mock the executor.

This process probe cannot prove that a coding agent's external tool catalog lacks the owner connector, that a provider client cannot reach an administrative issuer, or that an App token exists/is restricted. `coding_agent_tools_verified`, `github_principal_verified` and `credential_release_authorized` remain false even when all process observations pass. Host Python libraries remain trusted. No full-agent isolation or hostile-source containment claim follows from the diagnostic.

The `Authority process isolation diagnostic` PR workflow runs the fixed credential-free probe with read-only repository permissions and no owner/App secrets. It changes only the disposable runner's packaged namespace profile/user scope, not this home server or repository governance. No App, key, token, canary repository, rule or trusted admission check is created.

Evidence at implementation: 138 offline framework tests plus release checks pass; scope cases are synthetic metadata, process-controller tests use mocks, and the trusted CLI test performs no network operation. Actual hosted process evidence is pending in the implementation PR. A14, independent coding identity, complete credential separation, protected registry/verifier and merge-time enforcement remain unverified. Issue28 remains open.
