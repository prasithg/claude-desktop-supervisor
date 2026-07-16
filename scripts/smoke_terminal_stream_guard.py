#!/usr/bin/env python3
"""Behavior-level consumer checks for streamed terminal continuity receipts."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "skills/agent-session-progress/scripts/terminal_stream_guard.py"
PINNED_REVISION = "837659dab007930a4f92dec166722614c0abfe8f"

spec = importlib.util.spec_from_file_location("terminal_stream_guard", MOD)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def invoke(events: list[dict], *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        handle.flush()
        return subprocess.run(
            [sys.executable, str(MOD), str(handle.name), *args],
            text=True,
            capture_output=True,
            check=False,
        )


def read_receipt(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def main() -> int:
    # A dropped Unicode frame must stop append, accept an authoritative snapshot,
    # discard delayed output, and resume without exposing terminal content.
    raw_markers = ["PRIVATE-A", "🙂", "secret-tail", "\x1b[31m"]
    events = [
        {"type": "frame", "data": raw_markers[0], "end_offset": 9},
        {"type": "frame", "data": raw_markers[2], "end_offset": 22},
        {
            "type": "snapshot",
            "data": raw_markers[0] + raw_markers[1] + raw_markers[2],
            "high_water": 22,
        },
        {"type": "frame", "data": raw_markers[2], "end_offset": 22},
        {"type": "frame", "data": raw_markers[3], "end_offset": 27},
    ]
    proc = invoke(events)
    assert proc.returncode == 0, proc.stderr
    receipt = read_receipt(proc)
    assert receipt["status"] == "recovered"
    assert receipt["dispositions"] == {
        "appended": 2,
        "awaiting_replay": 0,
        "discarded": 1,
        "gap": 1,
        "replaced": 1,
    }
    assert receipt["replay_count"] == 1
    assert receipt["expected_end"] == 27
    assert receipt["transcript_utf16_units"] == 27
    assert receipt["contract_revision"] == PINNED_REVISION
    for marker in raw_markers:
        assert marker not in proc.stdout

    # A missing authoritative replay is a fail-closed continuity receipt.
    proc = invoke(
        [
            {"type": "frame", "data": "A", "end_offset": 1},
            {"type": "frame", "data": "RAW-SECRET", "end_offset": 12},
        ]
    )
    assert proc.returncode == 3
    receipt = read_receipt(proc)
    assert receipt["status"] == "blocked_missing_replay"
    assert receipt["dispositions"]["gap"] == 1
    assert "RAW-SECRET" not in proc.stdout

    # A partial-overlap frame after replay is not silently discarded.
    proc = invoke(
        [
            {"type": "snapshot", "data": "truth", "high_water": 5},
            {"type": "frame", "data": "overlap", "end_offset": 8},
        ]
    )
    assert proc.returncode == 3
    receipt = read_receipt(proc)
    assert receipt["status"] == "blocked_missing_replay"
    assert receipt["dispositions"]["gap"] == 1

    # Unknown events and dependency provenance mismatches fail before a pass.
    proc = invoke([{"type": "truncate", "data": "do-not-print"}])
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "do-not-print" not in proc.stderr

    proc = invoke(
        [{"type": "frame", "data": "do-not-print", "end_offset": 12}],
        "--expected-contract-revision",
        "0" * 40,
    )
    assert proc.returncode == 4
    assert proc.stdout == ""
    assert "do-not-print" not in proc.stderr
    assert "contract dependency provenance mismatch" in proc.stderr

    print("smoke_terminal_stream_guard: 5 controls ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
