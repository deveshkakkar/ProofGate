# Credential separation: evidence and release gates

The current session is **not** independently separated. These findings come from read-only metadata queries, not from a simulated secure worker. [authentication-inventory.json](authentication-inventory.json) is the public sanitized record; the full OAuth scope-name list is retained privately. Credential values, private-key contents, raw authentication responses and token fingerprints were neither output nor retained.

| Boundary | Observed evidence | Current result | Required future evidence |
| --- | --- | --- | --- |
| Connector identity | Authenticated login `deveshkakkar`; collaborator role admin; connector-specific installation selects all repositories | Not an independent coding principal; integration permissions may still restrict individual APIs | Only the dedicated coding principal is available in worker tools; no owner-context connector fallback |
| Local GitHub CLI | `/user` resolves to human owner, effective repo admin/push; OAuth scope metadata includes repo/workflow | Owner-capable | App installation-scoped identity demonstrated by bot-authored PR and App/installation metadata, not an owner-user token |
| Credential storage | Owner config mode 0600, owner UID 1000; current session UID 1000 can read it | Mode alone does not isolate this session | Fresh worker UID/VM/container has no owner home/config mount or readable owner credential path |
| Git transport | HTTPS origin has no embedded userinfo; GitHub helper delegates to `gh` | Clean URL, but helper reaches owner context | Worker uses only ephemeral App credential channel; owner helper is absent/unavailable |
| Environment and SSH | Standard token/askpass/socket variables absent; no SSH config or default private-key file found | Narrow absence observed, not proof of no credentials | Explicit tool/environment/mount allowlist; denial of owner credential/socket paths and custom key/token fallback |
| App inventory | Connector lists only its own installations; account-wide query denied 403 | No suitable independent App confirmed; inventory incomplete | Owner reviews installed Apps/registrations and supplies App ID/owner/permissions/selected-repository evidence |
| Main enforcement | Main unprotected; no effective rules/rulesets | Not enforced | Live rules readback plus all mandatory actor/approval/direct-push denial tests |

## Proposed worker boundary (not provisioned)

Use a dedicated restricted execution identity in a fresh VM or otherwise enforced process/filesystem/tool boundary. A directory/worktree, `HOME` override, token environment scrub, same-UID shell wrapper or new bot name is insufficient while owner files or owner-authenticated tools remain reachable. Do not change this home server's users/services/Docker state as part of approval preparation.

Required allowlist: the selected project workspace, pinned evaluator tooling, fresh private temporary storage and the coding App's short-lived credential channel. Required exclusions: owner home/GitHub config, SSH/GPG agents and private keys, host Docker socket, unrelated bind mounts, owner browser sessions, owner GitHub connector tools, administrative token issuer/key store and future verifier signer credentials. No escalation to host UID/root, host PID namespace or arbitrary host mounts. An owner-side broker's credentials/tooling must not be visible through files, environment, processes, sockets or callable agent tools.

A future test must try the actual denied paths/tools from the actual worker and capture only booleans/denial metadata—never read a real secret into a result. Use harmless owner-only canary files first, not credential contents. Verify API writes are attributed to `proofgate-coder[bot]` (or the reviewed existing App slug), with the recorded App and installation IDs. Do not assume installation tokens support a user-profile endpoint; PR actor and installation metadata establish the intended App identity.

The owner retains the current administrative route outside the worker. No credential is deleted, rotated, copied or revoked here. Rollback must not “restore” an owner token into the coding environment. If isolation cannot exclude an owner-context route, mark separation **failed** and do not release coder credentials or activate main protections as a verified boundary.

## Known inventory limits

We did not search all of the owner's home, enumerate custom private keys, read key material, inspect unrelated services, mint test tokens or prove a worker boundary. The connector inventory is App-scoped, not a registry of every installed App. The local installation-list endpoint denied the current owner-context token; the exact OAuth-versus-PAT origin was not identified from the scope header alone; a missing public App slug does not rule out private Apps or reserve the name. These limitations are unresolved evidence, not a statement that no other credentials/Apps exist.
