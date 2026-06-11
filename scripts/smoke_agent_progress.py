#!/usr/bin/env python3
"""Dependency-free smoke tests for the local progress helper."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "skills/agent-session-progress/scripts/agent_progress.py"

spec = importlib.util.spec_from_file_location("agent_progress", MOD)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def assert_eq(actual, expected):
    if actual != expected:
        raise AssertionError(f"expected {expected!r}, got {actual!r}")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + "\n")


def main() -> int:
    latest_with_usage = {
        "event": "assistant",
        "role": "assistant",
        "items": ["text"],
        "usage": {"input_tokens": 1000, "output_tokens": 200},
    }
    assert_eq(m.classify(999, latest_with_usage), "idle-or-done")

    blocked = {
        "event": "assistant",
        "role": "assistant",
        "items": ["text"],
        "message": "waiting for user approval",
    }
    assert_eq(m.classify(999, blocked), "blocked-or-needs-review")
    assert_eq(m.classify(30, latest_with_usage), "active")

    with tempfile.TemporaryDirectory() as td:
        fake_home = Path(td)
        session_id = "fixture-session"
        cwd = "/tmp/fixture-repo"
        meta = fake_home / "Library/Application Support/Claude/claude-code-sessions/fixture.json"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps({
            "title": "Fixture session",
            "cwd": cwd,
            "cliSessionId": session_id,
            "model": "claude-fable-5",
            "completedTurns": 1,
        }))
        transcript = fake_home / ".claude/projects" / cwd.replace("/", "-") / f"{session_id}.jsonl"
        write_json(transcript, {
            "type": "assistant",
            "timestamp": "2026-06-10T00:00:00Z",
            "cwd": cwd,
            "message": {
                "role": "assistant",
                "content": "done",
                "usage": {"input_tokens": 1000, "cache_read_input_tokens": 2000, "output_tokens": 100},
            },
        })

        rows = m.tail_jsonl(transcript, 10)
        assert_eq(len(rows), 1)
        assert_eq(rows[0]["type"], "assistant")

        proc = subprocess.run(
            [sys.executable, str(MOD), "--agent", "claude", "--home", str(fake_home), "--json"],
            check=True,
            text=True,
            capture_output=True,
        )
        data = json.loads(proc.stdout)
        assert_eq(len(data), 1)
        assert_eq(data[0]["title"], "Fixture session")
        assert_eq(data[0]["latest"]["usage"]["context_limit_est"], 1_000_000)

    print("smoke_agent_progress: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
