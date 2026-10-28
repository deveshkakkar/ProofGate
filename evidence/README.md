# Raw evidence conventions

The `*.jsonl` CLI captures preserve exact mixed stdout/stderr bytes. Despite that historical suffix, some contain a leading PATH-helper warning followed by valid JSON event records; they are **not guaranteed pure JSONL**. Parse JSON event lines individually and retain non-JSON diagnostic lines. The actual-repair, app-initial and formal-repair1/2 captures each contain one leading warning followed by eight JSON records. Empty failed-preflight stdout files may have corresponding separate stderr files.

`codex-actual-repair.receipt.json` records CLI exit0, actual session ID, duration, prompt/raw-log hashes and no command-tool items. `*.files.json` are parsed non-executable proposals; separate `applied-*.json` records identify exactly what the trusted applier changed. Native injected mutation files are explicitly labeled, never represented as model output.

Resumed Codex session usage snapshots appear cumulative. Do not sum successive snapshots as separate billed usage; no monetary billing data was available. Latest actual repair counter is preserved in both its receipt and codex-usage-snapshots.json.

Historical preflight and initial authoring failures remain failures, not final status. Authoritative final acceptance is `runs/supervisor-resume/accepted-run/result.json`; exact final deployment receipt/smoke are under the sibling deployment directory. The default portable reproduction command also completed all expected cases at `runs/final-reproduction/`.

Authentication/runtime/session-state caches, credential files, SQLite data, installed toolchains and private coordination notes are intentionally excluded from publication. The existing login was mounted read-only for the experiment, not copied into this evidence.
