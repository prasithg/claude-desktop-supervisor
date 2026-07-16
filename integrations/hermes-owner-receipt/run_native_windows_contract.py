from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "contract-sources.json"
PRODUCER = ROOT / "producer" / "owner_identity.py"
CONSUMER = ROOT / "consumer" / "audit_cron_scheduler_owner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_identity(consumer: Any, owner: dict[str, object], heartbeat_at: dt.datetime):
    scheduled = heartbeat_at - dt.timedelta(minutes=1)
    active_run = {
        "state": "running",
        "scheduled_for": scheduled.isoformat(),
        "queued_at": (scheduled + dt.timedelta(seconds=1)).isoformat(),
        "started_at": (scheduled + dt.timedelta(seconds=2)).isoformat(),
    }
    active_sha = canonical_sha256(active_run)
    heartbeat = {
        "schema_version": 1,
        "kind": "scheduler_owner_heartbeat",
        "job_id": "native-windows-owner-contract",
        "scheduled_for": scheduled.isoformat(),
        "active_run_sha256": active_sha,
        "heartbeat_at": heartbeat_at.isoformat(),
        "owner": owner,
    }
    pid = owner.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int):
        raise RuntimeError("producer emitted an invalid PID")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "owner-heartbeat.json"
        path.write_text(json.dumps(heartbeat), encoding="utf-8")
        return consumer.audit_owner(
            owner_path=path,
            job_id="native-windows-owner-contract",
            scheduled_for=scheduled.isoformat(),
            active_run_sha256=active_sha,
            as_of=dt.datetime.now(dt.timezone.utc).isoformat(),
            current_boot_id=consumer.current_boot_id(),
            process_observation=consumer.observe_process(pid),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay Hermes owner identity on native Windows")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if platform.system() != "Windows":
        print("native Windows is required", file=sys.stderr)
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source_digests = {"producer": digest(PRODUCER), "consumer": digest(CONSUMER)}
    for key, value in source_digests.items():
        if value != manifest[key]["sha256"]:
            print(f"{key} source digest mismatch", file=sys.stderr)
            return 2

    producer = load_module("hermes_owner_producer_runtime", PRODUCER)
    consumer = load_module("hermes_owner_consumer_runtime", CONSUMER)
    now = dt.datetime.now(dt.timezone.utc)

    present_owner = producer.scheduler_owner_identity()
    present = audit_identity(consumer, present_owner, now)
    stale = audit_identity(consumer, present_owner, now - dt.timedelta(minutes=10))

    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        child_owner = producer._scheduler_owner_identity(child.pid)
        child_heartbeat_at = dt.datetime.now(dt.timezone.utc)
    finally:
        child.terminate()
        child.wait(timeout=10)
    for _ in range(40):
        if consumer.observe_process(child.pid).state == "absent":
            break
        time.sleep(0.05)
    absent = audit_identity(consumer, child_owner, child_heartbeat_at)

    ok = (
        present["conclusion"] == "present"
        and stale["conclusion"] == "present"
        and stale["heartbeat_fresh"] is False
        and absent["conclusion"] == "absent"
        and absent.get("absence_reason") == "process_missing"
    )
    receipt = {
        "schema_version": 1,
        "kind": "native_windows_hermes_owner_contract",
        "ok": ok,
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "contract": manifest["contract"],
        "source_sha256": source_digests,
        "present_conclusion": present["conclusion"],
        "stale_live_conclusion": stale["conclusion"],
        "stale_heartbeat_fresh": stale["heartbeat_fresh"],
        "exited_process_conclusion": absent["conclusion"],
        "exited_process_reason": absent.get("absence_reason"),
        "metadata_only": True,
        "safe_for_destructive_recovery": False,
    }
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
