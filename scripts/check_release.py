#!/usr/bin/env python3
"""Offline integrity and regression checks; does not replay the formal gate."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "baseline")]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_integrity():
    gate = load_module("release_gate", ROOT / "baseline/gate.py")
    baseline = ROOT / "baseline"
    expected = (ROOT / "BASELINE.sha256").read_text().strip()
    frozen = gate.assert_baseline(baseline, expected)
    policy = gate.read_json(baseline / "policy.json")
    gate.check_policy(policy)
    lock = gate.read_json(baseline / "toolchain-lock.json")
    require([(x["host_relative"], x["guest"]) for x in lock] ==
            [(x["host_relative"], x["guest"]) for x in policy["runtime_mounts"]],
            "toolchain lock does not cover the policy mounts")
    lock_sha = gate.digest(gate.canonical(lock))
    print(f"PASS: frozen baseline ({len(frozen['files'])} files), policy and toolchain-lock metadata")

    def check_record(folder, accepted):
        record = gate.read_json(folder / "result.json")
        require(record.get("accepted") is accepted, f"unexpected outcome: {folder}")
        if "baseline_sha256" in record:
            require(record["baseline_sha256"] == expected, f"baseline mismatch: {folder}")
            require(record["toolchain_sha256"] == lock_sha, f"toolchain lock mismatch: {folder}")
        for field, directory in (("source_files", "source"), ("built_files", "artifact")):
            if field in record:
                actual = gate.files_manifest(folder / directory)
                require(actual == record[field], f"{directory} bytes changed: {folder}")
        if "source_files" in record:
            require(gate.digest(gate.canonical(record["source_files"])) == record["source_sha256"],
                    f"source identity mismatch: {folder}")
        for row in record["checks"]:
            for stream in ("stdout", "stderr"):
                log = folder / "logs" / f"{row['id']}.{stream}"
                require(gate.digest_file(log) == row[f"{stream}_sha256"], f"log changed: {log}")
            if row["status"] == "passed":
                check = next(c for c in policy["checks"] if c["id"] == row["id"])
                parsed = gate.parse_check(check, (folder / "logs" / f"{row['id']}.stdout").read_bytes())
                require(row.get("exit_code") == 0 and parsed == row.get("parsed"),
                        f"recorded successful check is inconsistent: {folder}/{row['id']}")
        if accepted:
            require([(c["id"], c["status"]) for c in record["checks"]] ==
                    [(c, "passed") for c in gate.REQUIRED_CHECKS], f"incomplete acceptance: {folder}")
            require(record.get("fault_injection") is None, f"accepted fault run: {folder}")
            actual = gate.files_manifest(folder / "artifact")
            require(set(actual) == set(policy["artifact_files"]) and actual == record["artifact_files"],
                    f"accepted artifact bytes changed: {folder}")
            require(gate.digest(gate.canonical(actual)) == record["artifact_sha256"],
                    f"artifact identity mismatch: {folder}")
        return record

    def check_deployment(folder, record):
        receipt = gate.read_json(folder / "deployment.json")
        require(receipt.get("rebuilt") is False, f"deployment was rebuilt: {folder}")
        for key in ("baseline_sha256", "source_sha256", "artifact_sha256", "artifact_files"):
            require(receipt[key] == record[key], f"deployment {key} mismatch: {folder}")
        require(gate.files_manifest(folder / "artifact") == record["artifact_files"],
                f"deployed artifact bytes changed: {folder}")
        smoke = gate.read_json(folder / "smoke.json")
        require(all(smoke.get(k) is True for k in ("passed", "artifact_unchanged", "process_restart")),
                f"recorded deployment smoke did not pass: {folder}")
        require(smoke.get("rebuilt") is False and smoke.get("private_binding") == "127.0.0.1",
                f"unexpected deployment smoke scope: {folder}")
        for key in ("source_sha256", "artifact_sha256"):
            require(smoke[key] == record[key], f"smoke {key} mismatch: {folder}")

    accepted_dir = ROOT / "runs/supervisor-resume/accepted-run"
    accepted = check_record(accepted_dir, True)
    # Reconstruct exactly the source selection used by the frozen evaluator.
    candidate = {name: gate.digest_file(ROOT / "candidate" / name) for name in policy["source_files"]}
    candidate.update({target: gate.digest_file(baseline / name)
                      for target, name in policy["protected_overlays"].items()})
    require(candidate == accepted["source_files"], "current candidate differs from the accepted source")
    check_deployment(ROOT / "runs/supervisor-resume/deployment", accepted)
    checkpoint = gate.read_json(ROOT / "runs/supervisor-resume/checkpoint.json")
    require(checkpoint["accepted_result_sha256"] == gate.digest_file(accepted_dir / "result.json"),
            "resume checkpoint no longer matches the accepted record")
    require(checkpoint.get("evaluation_replayed") is False, "unexpected recorded resume behavior")
    print("PASS: accepted source, artifact, log hashes, deployment and resume checkpoint")

    outcomes = {
        "valid": [(c, "passed") for c in gate.REQUIRED_CHECKS],
        "overallocation": [("formal", "failed")],
        "always-reject": [("formal", "failed")],
        "duplicate-charge": [("formal", "passed"), ("build", "passed"),
                             ("bridge", "passed"), ("application", "failed")],
        "unavailable": [("formal", "failed")],
        "timeout": [("formal", "failed")],
        "removed-law": [],
        "disabled-check": [],
    }
    for name in ("initial-matrix", "final-reproduction"):
        folder = ROOT / "runs" / name
        matrix = gate.read_json(folder / "matrix.json")
        require([row["case"] for row in matrix] == list(outcomes), f"unexpected matrix inventory: {name}")
        for row in matrix:
            case = row["case"]
            record = check_record(folder / case, case == "valid")
            require(row["accepted"] is record["accepted"] and row["checks"] == record["checks"] and
                    row["exit_code"] == (0 if case == "valid" else 1), f"matrix/result mismatch: {name}/{case}")
            require([(c["id"], c["status"]) for c in record["checks"]] == outcomes[case],
                    f"unexpected rejection stage: {name}/{case}")
            if case in ("unavailable", "timeout"):
                require(record["fault_injection"] == case, f"missing fault label: {name}/{case}")
            if case in ("removed-law", "disabled-check"):
                require("baseline content altered" in record.get("error", ""),
                        f"missing frozen baseline rejection: {name}/{case}")
            if case == "valid":
                check_deployment(folder / "deployment", record)
    print("PASS: 2 recorded matrices, 8 expected outcomes each; source/artifact/log consistency")

    review = gate.read_json(ROOT / "review/final-acceptance-review.json")
    require(len(review["rows"]) == 25 and set(review["rows"].values()) == {"PASS"},
            "recorded 25-row acceptance review changed")
    for key in ("baseline_sha256", "source_sha256", "artifact_sha256"):
        require(review[key] == accepted[key], f"review {key} mismatch")
    print("PASS: recorded acceptance review contains 25 passing rows with matching identities")


def check_regressions():
    paths = ["baseline/test_gate.py", "supervisor/test-crash-replay.py",
             "supervisor/test_realtime_checker.py", "supervisor/test_pending_checker.py",
             "supervisor/test_partial_body.py"]
    suite = unittest.TestSuite()
    for index, path in enumerate(paths):
        module = load_module(f"release_tests_{index}", ROOT / path)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    require(result.wasSuccessful() and not result.skipped, "regression suite failed or skipped tests")
    print(f"PASS: {result.testsRun} existing regression tests across {len(paths)} suites")

    # The archived test-applier.py assumes its original absolute workspace and
    # creates an app symlink there. Run its six rejection cases with only the
    # imported module's candidate location redirected to a disposable directory.
    applier = load_module("release_applier", ROOT / "supervisor/apply-codex-files.py")
    def payload(path):
        return {"summary": "test", "files": [{"path": path, "content": "x"}],
                "checksToRun": [], "limitations": []}
    cases = [payload("../trusted/LAWS.bend"), payload("/tmp/x"),
             payload("formal/LAWS.bend"), {"files": []}]
    duplicate = payload("app/server.ts")
    duplicate["files"] *= 2
    cases.append(duplicate)
    with tempfile.TemporaryDirectory(prefix="proofgate-applier-") as directory:
        applier.CANDIDATE = Path(directory).resolve()
        def rejected(value):
            try:
                applier.validate(value, applier.REPAIR)
            except ValueError:
                return
            raise ValueError("applier accepted a prohibited file proposal")
        for value in cases:
            rejected(value)
        (applier.CANDIDATE / "app").symlink_to(applier.CANDIDATE.parent, target_is_directory=True)
        rejected(payload("app/server.ts"))
    print("PASS: 6 archived applier rejection cases in temporary storage")


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required")
    if os.name != "posix" or not all(Path(p).is_file() for p in ("/bin/true", "/bin/false", "/bin/sleep")):
        raise SystemExit("The existing regressions require a POSIX host with /bin/true, /bin/false and /bin/sleep")
    try:
        check_integrity()
        check_regressions()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("\nOffline release checks passed. No downloads or formal-toolchain execution occurred.")
    print("Recorded results were checked for consistency; they are not a fresh formal proof or HTTP run.")
    print("For fresh formal/build/bridge/HTTP verification, run: python3 -B reproduce.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
