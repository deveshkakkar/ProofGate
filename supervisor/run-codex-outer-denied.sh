#!/bin/sh
# CLI inner sandbox is redundant here: mandatory kernel-enforced outer namespace
# makes all host files read-only and masks host process, socket and home routes.
# Existing auth is read-only mounted only for this approved subprocess; not copied.
set -eu
ROOT=/workspace/scratch/95589aefb3bf/proofgate
mkdir -p "$ROOT/supervisor/codex-runtime"
touch "$ROOT/supervisor/codex-runtime/auth.json" "$ROOT/supervisor/codex-runtime/config.toml"
exec bwrap --unshare-user --unshare-pid --unshare-ipc --unshare-uts --new-session --die-with-parent --cap-drop ALL \
 --ro-bind / / --tmpfs /tmp --tmpfs /run --proc /proc --dev /dev \
 --bind "$ROOT/candidate" "$ROOT/candidate" \
 --bind "$ROOT/supervisor/codex-runtime" /tmp/codex-home \
 --ro-bind /home/agent/.codex/auth.json /tmp/codex-home/auth.json \
 --ro-bind /home/agent/.codex/config.toml /tmp/codex-home/config.toml \
 --tmpfs /home/agent \
 --setenv CODEX_HOME /tmp/codex-home \
 --setenv HOME /tmp \
 --setenv PATH "$ROOT/toolchains/lean-4.34.0-linux/bin:$ROOT/toolchains/bend/bin:$PATH" \
 --setenv BENDTT "$ROOT/toolchains/home/.bend/bendtt/e951a3ff12c837f2/bendtt" \
 --setenv BEND_NO_TELEMETRY 1 \
 --chdir "$ROOT/candidate" codex exec --json -s danger-full-access \
 -c features.apps=false -c features.plugins=false -c features.remote_plugin=false \
 -c features.imagegenext=false -c features.tool_search=false -c 'apps._default.enabled=false' "$@"
