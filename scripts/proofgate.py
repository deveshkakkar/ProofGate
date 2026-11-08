#!/usr/bin/env python3
"""Pinned checkout entrypoint; invoke with python3 -I -B from an external directory."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework.__main__ import main

if __name__ == '__main__':
    raise SystemExit(main())
