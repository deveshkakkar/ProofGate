#!/usr/bin/env python3
"""Check host prerequisites without downloads, model calls, or proof evaluation."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile


class HostCheckError(RuntimeError):
    """The host cannot run the pinned experiment as configured."""


def check_host(*, bootstrap: bool = True) -> dict:
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        raise HostCheckError("The pinned experiment requires Linux x86_64.")

    for path in ("/usr/bin/bwrap", "/usr/bin/python3"):
        if not os.access(path, os.X_OK):
            raise HostCheckError(f"Missing executable required by the frozen gate: {path}")
    if bootstrap:
        missing = [name for name in ("tar", "zstd", "xz", "python3") if not shutil.which(name)]
        if missing:
            raise HostCheckError("Missing bootstrap prerequisites: " + ", ".join(missing))

    # Match the gate's namespace flags and host-library mounts. In particular,
    # the recorded gate shares host networking; --unshare-all is not equivalent.
    argv = [
        "/usr/bin/bwrap", "--unshare-user", "--unshare-pid", "--new-session",
        "--die-with-parent", "--cap-drop", "ALL", "--proc", "/proc",
        "--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/etc",
        "--dir", "/opt", "--dir", "/work",
    ]
    for path in ("/usr", "/bin", "/lib", "/lib64", "/etc/ld.so.cache", "/etc/localtime"):
        if Path(path).exists():
            argv += ["--ro-bind", path, path]

    with tempfile.TemporaryDirectory(prefix="proofgate-host-") as temporary:
        root = Path(temporary)
        for name in ("source", "baseline", "output"):
            (root / name).mkdir()
        argv += [
            "--ro-bind", str(root / "source"), "/src",
            "--ro-bind", str(root / "baseline"), "/baseline",
            "--bind", str(root / "output"), "/out", "--chdir", "/src",
            "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
            "/usr/bin/python3", "-B", "-c",
            "from pathlib import Path; Path('/out/probe').write_text('ok')",
        ]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HostCheckError(f"Bubblewrap host probe could not complete: {exc}") from exc
        if result.returncode:
            detail = result.stderr.strip() or f"exit {result.returncode}"
            raise HostCheckError(
                "Bubblewrap cannot run the gate's namespace configuration: " + detail
                + "\nUse a Linux host that permits these namespaces; the experiment requires its sandbox."
            )
        if (root / "output" / "probe").read_text() != "ok":
            raise HostCheckError("The sandbox output mount did not pass the host probe.")

    return {
        "passed": True,
        "scope": "host prerequisites and gate-style namespace/mount support only",
        "bootstrap_prerequisites_checked": bootstrap,
        "toolchains_downloaded": False,
        "formal_checks_executed": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check_host(), indent=2))
    except HostCheckError as exc:
        print(f"Host preflight failed: {exc}", file=sys.stderr)
        sys.exit(1)
