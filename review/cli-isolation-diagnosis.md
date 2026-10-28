# Independent CLI launch diagnosis

2026-10-28 20:57 UTC. Inspected supervisor/run-codex.sh, mounted preflight stderr/JSONL, bwrap-smoke.log, installed `codex exec --help`, configuration schema and generated app-server JSON schemas. No new authenticated launch or ptrace attempt was performed.

## Observed cause

The outer wrapper starts `codex exec -s workspace-write`. Codex's nested filesystem helper attempts a bwrap network namespace/loopback setup while loading AGENTS.md and fails with `NETLINK_ROUTE ... Operation not permitted`. This is before thread creation/model work. The workspace-write network_access override did not avoid that helper path. Do not treat this as rejected user credentials.

CLI sandbox choices are read-only, workspace-write and danger-full-access. App-server turn/start supports a structured externalSandbox policy, but thread/start accepts only those three modes. An invented CLI external-sandbox argument is not a supported repair.

## Conditional next step

The outer wrapper presently bind-mounts host root read-only, candidate writable, temporary Codex state writable and existing auth/config read-only. The observed supervisor write EROFS is useful but does not cover host PID/proc/socket paths. Before relying solely on this outer boundary:

- Add isolated PID namespace with fresh proc, new-session, die-with-parent and dropped capabilities.
- Mask original Codex home, the denied session path, host runtime sockets and unnecessary command/control channels without reading their contents. Retain only specifically approved auth/config read-only mounts.
- Disable app/connector/browser tool routes and hooks in this isolated candidate session. Local filesystem isolation is not sufficient if candidate tools can ask an external service to mutate protected state.
- Keep current host-enforced network and syscall restrictions. Do not create expanded network access, change system security or route around denied operations.
- Run nonauthenticated boundary probes: candidate write succeeds; protected supervisor write/chmod/rename fails; host process access and inherited descriptor escape are absent; source/law files cannot be changed; no deployment authority is available.

If the resulting outer sandbox passes these tests, `-s danger-full-access` is the CLI's supported way to omit its redundant inner command sandbox. It must never be run outside the tested mandatory outer boundary, and it must not be combined with the global flag that bypasses approvals. Treat this as a conditional engineering recommendation, not unconditional approval of the current wrapper or permission to expand host access.

A failed outer isolation test is a blocker. No amount of manifest hashing alone meets the user's requirement that candidate repair lack baseline write authority. Retain the shell test evidence and final wrapper hash before the next bounded CLI attempt.

## Remaining limits

This review does not certify protection against every OS-level adversarial escape or credential exfiltration. Authentication is explicitly approved for the scoped CLI runtime, but deployment credentials must remain unavailable. The compiled candidate execution boundary must receive its own review before formal baseline freeze. The global environment's denied paths and network restrictions remain binding.

## Policy result supersedes conditional danger-mode recommendation

At 20:58 UTC, inspected preflight-codex-hardened.stderr: environment requirements explicitly disallow danger-full-access with default never approval. Do not change approval policy or requirements to evade this denial. The conditional approach above is now unavailable in this environment.

A narrower supported diagnostic is read-only CLI plus project_doc_max_bytes=0 (schema permits zero), with shell_tool/unified_exec/code_mode/apps/connectors/browser routes disabled and outer candidate mount read-only. Carry applicable project/user instructions in the prompt. This changes no host security setting or sandbox requirement and asks the model to return text/structured candidate files rather than mutate the filesystem. One bounded test may establish whether skipping instruction discovery avoids the failed helper; no guarantee until executed. If the helper still fails, stop this route.

If this route works, the trusted supervisor validates returned candidate-relative paths (no traversal, absolute paths, symlinks or protected targets) and applies content only to the mutable candidate tree. The coding agent never controls the writer or acceptance policy. Disabling apply_patch_freeform may only change its representation; do not treat it alone as disabling write capability. The enforced read-only mounts/sandbox remain the boundary. Preserve the denied danger-mode log and distinguish model output from actual verified implementation.
