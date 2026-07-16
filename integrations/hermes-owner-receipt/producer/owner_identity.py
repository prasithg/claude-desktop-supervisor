"""Boot-scoped identity for the process that owns a cron dispatch.

The identity is metadata-only and stable for this process lifetime.  Consumers
can distinguish a reboot, a missing process, and PID reuse without inspecting
command lines, prompts, or model output.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path
import platform
import subprocess
from typing import Optional


def _linux_process_start_id(pid: int) -> Optional[str]:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    closing = raw.rfind(")")
    tail = raw[closing + 2 :].split() if closing >= 0 else []
    if len(tail) <= 19:
        return None
    return tail[19]


def _macos_value(command: list[str]) -> Optional[str]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = " ".join(proc.stdout.split())
    return value or None


def _psutil_boot_and_start(pid: int) -> tuple[Optional[str], Optional[str]]:
    try:
        import psutil  # type: ignore

        boot_id = f"boot-time-centiseconds:{int(round(psutil.boot_time() * 100))}"
        start_id = str(int(round(psutil.Process(pid).create_time() * 100)))
        return boot_id, start_id
    except Exception:
        return None, None


@functools.lru_cache(maxsize=4)
def _scheduler_owner_identity(pid: int) -> dict[str, object]:
    boot_id: Optional[str] = None
    process_start_id: Optional[str] = None

    linux_boot = Path("/proc/sys/kernel/random/boot_id")
    try:
        boot_id = linux_boot.read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    if boot_id is not None:
        process_start_id = _linux_process_start_id(pid)
    elif platform.system() == "Darwin":
        boot_id = _macos_value(["sysctl", "-n", "kern.bootsessionuuid"])
        process_start_id = _macos_value(["ps", "-o", "lstart=", "-p", str(pid)])
    else:
        boot_id, process_start_id = _psutil_boot_and_start(pid)

    if not boot_id or not process_start_id:
        raise RuntimeError("scheduler owner identity is unavailable")
    return {
        "boot_id": boot_id,
        "pid": pid,
        "process_start_id": process_start_id,
    }


def scheduler_owner_identity() -> dict[str, object]:
    """Return the current process's boot/PID/start identity.

    The cache is keyed by PID so a forked child cannot inherit its parent's
    owner receipt. Raises ``RuntimeError`` instead of emitting partial evidence.
    The scheduler treats an unavailable identity as an observability failure,
    not as a reason to suppress an otherwise accepted cron execution.
    """
    return _scheduler_owner_identity(os.getpid())
