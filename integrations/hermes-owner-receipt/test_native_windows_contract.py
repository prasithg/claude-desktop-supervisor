from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "contract-sources.json"
PRODUCER = ROOT / "producer" / "owner_identity.py"
CONSUMER = ROOT / "consumer" / "audit_cron_scheduler_owner.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ContractSourceTests(unittest.TestCase):
    def test_exact_producer_and_consumer_snapshots_are_hash_bound(self):
        self.assertTrue(MANIFEST.is_file(), "contract source manifest is missing")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(
            manifest["producer"]["introduced_by_commit"],
            "0c73f2e1d7699cd19448b72d12016c14944a3a4e",
        )
        for key, path in (("producer", PRODUCER), ("consumer", CONSUMER)):
            self.assertTrue(path.is_file(), f"{key} snapshot is missing")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, manifest[key]["sha256"])


@unittest.skipUnless(platform.system() == "Windows", "native Windows contract")
class NativeWindowsOwnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.producer = load_module("hermes_owner_producer", PRODUCER)
        cls.consumer = load_module("hermes_owner_consumer", CONSUMER)

    def audit_identity(self, owner: dict[str, object], heartbeat_at: dt.datetime):
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
            raise AssertionError("producer emitted an invalid PID")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owner-heartbeat.json"
            path.write_text(json.dumps(heartbeat), encoding="utf-8")
            return self.consumer.audit_owner(
                owner_path=path,
                job_id="native-windows-owner-contract",
                scheduled_for=scheduled.isoformat(),
                active_run_sha256=active_sha,
                as_of=dt.datetime.now(dt.timezone.utc).isoformat(),
                current_boot_id=self.consumer.current_boot_id(),
                process_observation=self.consumer.observe_process(pid),
            )

    def test_actual_windows_process_is_consumed_as_present(self):
        owner = self.producer.scheduler_owner_identity()
        now = dt.datetime.now(dt.timezone.utc)
        receipt = self.audit_identity(owner, now)

        self.assertEqual(receipt["conclusion"], "present")
        self.assertEqual(receipt["receipt_boot_id"], owner["boot_id"])
        self.assertEqual(receipt["observed_process_start_id"], owner["process_start_id"])

    def test_stale_heartbeat_never_proves_absence_for_live_exact_process(self):
        owner = self.producer.scheduler_owner_identity()
        receipt = self.audit_identity(owner, dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=10))

        self.assertEqual(receipt["conclusion"], "present")
        self.assertFalse(receipt["heartbeat_fresh"])
        self.assertNotIn("absence_reason", receipt)

    def test_exited_windows_process_is_consumed_as_mechanical_absence(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            owner = self.producer._scheduler_owner_identity(child.pid)
            heartbeat_at = dt.datetime.now(dt.timezone.utc)
        finally:
            child.terminate()
            child.wait(timeout=10)
        for _ in range(20):
            if self.consumer.observe_process(child.pid).state == "absent":
                break
            time.sleep(0.05)

        receipt = self.audit_identity(owner, heartbeat_at)
        self.assertEqual(receipt["conclusion"], "absent")
        self.assertEqual(receipt["absence_reason"], "process_missing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
