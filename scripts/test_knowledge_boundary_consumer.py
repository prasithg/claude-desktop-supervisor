#!/usr/bin/env python3
"""Downstream contract tests for metadata-only session export receipts."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "skills/agent-session-progress/scripts/agent_progress.py"

spec = importlib.util.spec_from_file_location("agent_progress", MOD)
assert spec and spec.loader
agent_progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_progress)


class KnowledgeBoundaryConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {
                "agent": "claude-code",
                "title": "PRIVATE PROJECT ALPHA",
                "cwd": "/private/worktree",
                "evidence": "/private/transcript.jsonl",
                "last_activity": "2026-07-16T00:10:00-04:00",
            },
            {
                "agent": "codex",
                "title": "PRIVATE PROJECT BETA",
                "cwd": "/private/other",
                "evidence": "/private/state.sqlite",
                "last_activity": "2026-07-16T00:11:00-04:00",
            },
        ]

    def test_private_session_summary_destination_is_accepted_without_content_leak(self) -> None:
        receipt = agent_progress.build_export_boundary_receipt(
            self.rows,
            destination="private",
            as_of="2026-07-16T04:15:00Z",
        )

        self.assertTrue(receipt["allowed"])
        self.assertEqual(receipt["row_count"], 2)
        self.assertEqual(receipt["violation_codes"], [])
        serialized = json.dumps(receipt, sort_keys=True)
        for forbidden in ("PRIVATE PROJECT", "/private/", "transcript.jsonl", "state.sqlite"):
            self.assertNotIn(forbidden, serialized)

    def test_public_export_of_private_session_sources_fails_closed(self) -> None:
        receipt = agent_progress.build_export_boundary_receipt(
            self.rows,
            destination="public",
            as_of="2026-07-16T04:15:00Z",
        )

        self.assertFalse(receipt["allowed"])
        self.assertEqual(
            receipt["violation_codes"],
            ["public_export_denied", "public_export_denied"],
        )

    def test_unknown_agent_source_fails_before_contract_evaluation(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported agent source"):
            agent_progress.build_export_boundary_receipt(
                [{"agent": "unknown-runner", "last_activity": "2026-07-16T00:00:00Z"}],
                destination="private",
                as_of="2026-07-16T04:15:00Z",
            )

    def test_cli_public_export_writes_denial_receipt_without_summary_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_home = root / "home"
            cwd = "/private/consumer-project"
            session_id = "fixture-session"
            metadata = (
                fake_home
                / "Library/Application Support/Claude/claude-code-sessions/fixture.json"
            )
            metadata.parent.mkdir(parents=True)
            metadata.write_text(
                json.dumps(
                    {
                        "title": "PRIVATE CLI TITLE",
                        "cwd": cwd,
                        "cliSessionId": session_id,
                        "model": "fixture-model",
                    }
                ),
                encoding="utf-8",
            )
            transcript = (
                fake_home
                / ".claude/projects"
                / cwd.replace("/", "-")
                / f"{session_id}.jsonl"
            )
            transcript.parent.mkdir(parents=True)
            transcript.write_text(
                json.dumps(
                    {
                        "type": "assistant",
                        "timestamp": "2026-07-16T04:15:00Z",
                        "message": {"role": "assistant", "content": "PRIVATE BODY"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_path = root / "boundary.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(MOD),
                    "--agent",
                    "claude",
                    "--home",
                    str(fake_home),
                    "--json",
                    "--export-destination",
                    "public",
                    "--boundary-receipt",
                    str(receipt_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(result.stdout, "")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertFalse(receipt["allowed"])
            self.assertEqual(receipt["violation_codes"], ["public_export_denied"])
            serialized = json.dumps(receipt, sort_keys=True)
            for forbidden in ("PRIVATE CLI TITLE", "PRIVATE BODY", "/private/"):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
