#!/bin/sh
# Both CLI and candidate mounts are read-only. Model output is a JSON file proposal.
exec python3 /workspace/scratch/95589aefb3bf/proofgate/supervisor/run-codex.py "$@"
