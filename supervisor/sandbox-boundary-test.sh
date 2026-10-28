#!/bin/sh
set -eu
ROOT=/workspace/scratch/95589aefb3bf/proofgate
exec bwrap --unshare-user --unshare-pid --unshare-ipc --unshare-uts --new-session --die-with-parent --cap-drop ALL \
 --ro-bind / / --tmpfs /tmp --tmpfs /run --tmpfs /home/agent --proc /proc --dev /dev \
 --bind "$ROOT/candidate" "$ROOT/candidate" --chdir "$ROOT/candidate" \
 sh -c '
set -eu
printf candidate-write > boundary-test.txt
for op in "touch ../supervisor/denied" "chmod u+w ../supervisor" "mv ../supervisor ../renamed-supervisor"; do
 if sh -c "$op"; then echo "UNSAFE $op"; exit 40; else echo "DENIED $op"; fi
done
if [ -e /home/agent/.codex/auth.json ]; then echo UNSAFE-auth-visible; exit 41; fi
if [ -e /home/agent/.codex/sessions ]; then echo UNSAFE-session-path; exit 42; fi
printf "processes="; ls /proc | grep -E "^[0-9]+$" | tr "\n" " "
printf "\ncapabilities="; grep CapEff /proc/self/status
printf "\nboundary-pass\n"
'
