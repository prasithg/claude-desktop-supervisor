#!/usr/bin/env python3
"""Audit a boot-scoped Hermes scheduler-owner heartbeat.

The only successful evidence result is mechanical owner absence: the machine
rebooted, the exact owner PID is gone, or that PID now identifies a different
process. A stale heartbeat by itself never proves absence.

This tool is read-only. It does not clear receipts, run jobs, or edit cron.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
from typing import Any, NamedTuple

SHA256 = re.compile(r"[0-9a-f]{64}")
METHOD = "boot-scoped-owner-heartbeat-v1"
DEFAULT_HEARTBEAT_MAX_AGE_SECONDS = 300


class ProcessObservation(NamedTuple):
    state: str
    process_start_id: str | None


def _windows_psutil() -> Any:
    try:
        import psutil  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Windows owner audit requires psutil") from exc
    return psutil


def _centisecond_timestamp(value: Any, label: str) -> str:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise RuntimeError(f"Windows returned an invalid {label}")
    return str(int(round(value * 100)))


def parse_aware(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("owner heartbeat must be a JSON object")
    return payload


def load_owner_heartbeat(path: Path, job_id: str) -> tuple[dict[str, Any], str]:
    """Load a direct heartbeat or the exact embedded receipt from jobs.json."""
    document = load_object(path)
    if document.get("kind") == "scheduler_owner_heartbeat":
        return document, hashlib.sha256(path.read_bytes()).hexdigest()

    jobs = document.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("owner receipt must be a heartbeat or Hermes jobs store")
    matches = [job for job in jobs if isinstance(job, dict) and job.get("id") == job_id]
    if len(matches) != 1:
        raise ValueError("jobs store must contain exactly one selected job")
    heartbeat = matches[0].get("scheduler_owner_heartbeat")
    if not isinstance(heartbeat, dict):
        raise ValueError("selected job has no scheduler owner heartbeat")
    active_run = matches[0].get("active_run")
    if not isinstance(active_run, dict):
        raise ValueError("selected job has no active_run receipt")
    active_run_sha256 = hashlib.sha256(
        json.dumps(active_run, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if heartbeat.get("active_run_sha256") != active_run_sha256:
        raise ValueError("owner heartbeat does not match embedded active_run")
    canonical = json.dumps(
        heartbeat, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return heartbeat, hashlib.sha256(canonical).hexdigest()


def current_boot_id() -> str:
    """Return an OS boot identity on Linux, macOS, or Windows."""
    system = platform.system()
    if system == "Linux":
        value = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    elif system == "Darwin":
        proc = subprocess.run(
            ["sysctl", "-n", "kern.bootsessionuuid"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            raise RuntimeError("could not read macOS boot session identity")
        value = proc.stdout.strip()
    elif system == "Windows":
        psutil = _windows_psutil()
        try:
            value = "boot-time-centiseconds:" + _centisecond_timestamp(
                psutil.boot_time(), "boot time"
            )
        except (OSError, RuntimeError) as exc:
            raise RuntimeError("could not read Windows boot identity") from exc
    else:
        raise RuntimeError(
            "boot identity is supported only on Linux, macOS, and Windows"
        )
    if not value:
        raise RuntimeError("OS returned an empty boot identity")
    return value


def observe_process(pid: int) -> ProcessObservation:
    """Observe exact process start identity without treating probe errors as absence."""
    system = platform.system()
    if system == "Linux":
        linux_stat = Path(f"/proc/{pid}/stat")
        try:
            raw = linux_stat.read_text()
        except FileNotFoundError:
            return ProcessObservation("absent", None)
        except OSError:
            return ProcessObservation("unknown", None)
        closing = raw.rfind(")")
        tail = raw[closing + 2 :].split() if closing >= 0 else []
        if len(tail) <= 19:
            return ProcessObservation("unknown", None)
        # /proc/<pid>/stat field 22 (process start ticks since boot).
        return ProcessObservation("running", tail[19])

    if system == "Darwin":
        try:
            proc = subprocess.run(
                ["ps", "-o", "lstart=", "-p", str(pid)],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ProcessObservation("unknown", None)
        if proc.returncode != 0:
            # ps uses exit 1 when the selected PID does not exist. Unexpected
            # diagnostics fail closed rather than being called absence.
            if proc.returncode == 1 and not proc.stdout.strip():
                return ProcessObservation("absent", None)
            return ProcessObservation("unknown", None)
        value = " ".join(proc.stdout.split())
        if not value:
            return ProcessObservation("absent", None)
        return ProcessObservation("running", value)

    if system == "Windows":
        try:
            psutil = _windows_psutil()
        except RuntimeError:
            return ProcessObservation("unknown", None)
        try:
            start_id = _centisecond_timestamp(
                psutil.Process(pid).create_time(), "process start time"
            )
        except psutil.NoSuchProcess:
            return ProcessObservation("absent", None)
        except (psutil.AccessDenied, psutil.ZombieProcess, OSError, RuntimeError):
            return ProcessObservation("unknown", None)
        return ProcessObservation("running", start_id)

    return ProcessObservation("unknown", None)


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def audit_owner(
    *,
    owner_path: Path,
    job_id: str,
    scheduled_for: str,
    active_run_sha256: str,
    as_of: str,
    current_boot_id: str,
    process_observation: ProcessObservation,
    heartbeat_max_age_seconds: int = DEFAULT_HEARTBEAT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    if heartbeat_max_age_seconds < 0:
        raise ValueError("heartbeat_max_age_seconds must be nonnegative")
    if not SHA256.fullmatch(active_run_sha256):
        raise ValueError("active_run_sha256 must be lowercase SHA-256")
    checked_at = parse_aware(as_of)
    occurrence = parse_aware(scheduled_for)
    payload, owner_receipt_sha256 = load_owner_heartbeat(owner_path, job_id)
    if payload.get("schema_version") != 1:
        raise ValueError("owner heartbeat schema_version must be 1")
    if payload.get("kind") != "scheduler_owner_heartbeat":
        raise ValueError("owner heartbeat kind mismatch")
    if payload.get("job_id") != job_id:
        raise ValueError("owner heartbeat job_id mismatch")
    if payload.get("scheduled_for") != scheduled_for:
        raise ValueError("owner heartbeat occurrence mismatch")
    if payload.get("active_run_sha256") != active_run_sha256:
        raise ValueError("owner heartbeat fingerprint mismatch")

    heartbeat_at_value = _required_string(payload.get("heartbeat_at"), "heartbeat_at")
    heartbeat_at = parse_aware(heartbeat_at_value)
    if heartbeat_at > checked_at:
        raise ValueError("owner heartbeat cannot be future-dated")
    if heartbeat_at < occurrence:
        raise ValueError("owner heartbeat predates the scheduled occurrence")

    owner = payload.get("owner")
    if not isinstance(owner, dict):
        raise ValueError("owner must be an object")
    receipt_boot_id = _required_string(owner.get("boot_id"), "owner boot_id")
    pid = owner.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("owner pid must be a positive integer")
    receipt_start_id = _required_string(
        owner.get("process_start_id"), "owner process_start_id"
    )
    observed_boot_id = _required_string(current_boot_id, "observed boot_id")
    if process_observation.state not in {"running", "absent", "unknown"}:
        raise ValueError("process observation state is invalid")
    if process_observation.state == "running" and not process_observation.process_start_id:
        raise ValueError("running process observation requires process_start_id")

    heartbeat_age = int((checked_at - heartbeat_at).total_seconds())
    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "scheduler_owner_observation",
        "job_id": job_id,
        "scheduled_for": scheduled_for,
        "active_run_sha256": active_run_sha256,
        "checked_at": as_of,
        "conclusion": "indeterminate",
        "method": METHOD,
        "heartbeat_at": heartbeat_at_value,
        "heartbeat_age_seconds": heartbeat_age,
        "heartbeat_fresh": heartbeat_age <= heartbeat_max_age_seconds,
        "owner_receipt_sha256": owner_receipt_sha256,
        "receipt_boot_id": receipt_boot_id,
        "observed_boot_id": observed_boot_id,
        "owner_pid": pid,
        "owner_process_start_id": receipt_start_id,
        "observed_process_state": process_observation.state,
        "observed_process_start_id": process_observation.process_start_id,
    }

    absence_reason = None
    if receipt_boot_id != observed_boot_id:
        absence_reason = "boot_changed"
    elif process_observation.state == "absent":
        absence_reason = "process_missing"
    elif (
        process_observation.state == "running"
        and process_observation.process_start_id != receipt_start_id
    ):
        absence_reason = "process_identity_changed"
    elif process_observation.state == "running":
        result["conclusion"] = "present"

    if absence_reason:
        result["kind"] = "scheduler_owner_absence"
        result["conclusion"] = "absent"
        result["absence_reason"] = absence_reason
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-receipt", type=Path, required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--scheduled-for", required=True)
    parser.add_argument("--active-run-sha256", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument(
        "--heartbeat-max-age-seconds",
        type=int,
        default=DEFAULT_HEARTBEAT_MAX_AGE_SECONDS,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        payload, _ = load_owner_heartbeat(args.owner_receipt, args.job_id)
        owner = payload.get("owner")
        if not isinstance(owner, dict):
            raise ValueError("owner must be an object")
        pid = owner.get("pid")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ValueError("owner pid must be a positive integer")
        result = audit_owner(
            owner_path=args.owner_receipt,
            job_id=args.job_id,
            scheduled_for=args.scheduled_for,
            active_run_sha256=args.active_run_sha256,
            as_of=args.as_of,
            current_boot_id=current_boot_id(),
            process_observation=observe_process(pid),
            heartbeat_max_age_seconds=args.heartbeat_max_age_seconds,
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["conclusion"] == "absent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
