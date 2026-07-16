#!/usr/bin/env python3
"""Dependency-free controls for the scheduler run identity producer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def load_producer():
    path = ROOT / "scripts" / "build_scheduler_run_identity.py"
    spec = importlib.util.spec_from_file_location("build_scheduler_run_identity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("producer module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_env() -> dict[str, str]:
    return {
        "GITHUB_REPOSITORY": "prasithg/claude-desktop-supervisor",
        "GITHUB_RUN_ID": "30000000001",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW": "scheduler-run-identity",
        "GITHUB_WORKFLOW_REF": "prasithg/claude-desktop-supervisor/.github/workflows/scheduler-run-identity.yml@refs/pull/3/merge",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_SHA": "b" * 40,
        "GITHUB_REF": "refs/pull/3/merge",
        "UNTRUSTED_FREE_FORM": "must not enter the subject",
    }


def expect_value_error(callback, match: str) -> None:
    try:
        callback()
    except ValueError as exc:
        assert match in str(exc), (match, str(exc))
    else:
        raise AssertionError(f"expected ValueError containing {match!r}")


def main() -> int:
    module = load_producer()
    payload = module.build_subject(fixture_env())
    assert set(payload) == module.SUBJECT_FIELDS
    assert payload["kind"] == "github_actions_run_identity"
    assert payload["run_id"] == 30000000001
    assert payload["run_attempt"] == 1
    assert "UNTRUSTED_FREE_FORM" not in json.dumps(payload)
    assert "must not enter" not in json.dumps(payload)

    bad_run = fixture_env()
    bad_run["GITHUB_RUN_ID"] = "0"
    expect_value_error(lambda: module.build_subject(bad_run), "positive integer")

    bad_ref = fixture_env()
    bad_ref["GITHUB_WORKFLOW_REF"] = bad_ref["GITHUB_WORKFLOW_REF"].replace(
        "refs/pull/3/merge", "refs/heads/main"
    )
    expect_value_error(lambda: module.build_subject(bad_ref), "workflow ref")

    missing = fixture_env()
    missing.pop("GITHUB_SHA")
    expect_value_error(lambda: module.build_subject(missing), "GITHUB_SHA")

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "scheduler-run-identity.json"
        module.write_subject(output, payload)
        raw = output.read_text()
        assert raw.endswith("\n")
        assert json.loads(raw) == payload
        expect_value_error(lambda: module.write_subject(output, payload), "already exists")

    print("smoke_scheduler_run_identity: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
