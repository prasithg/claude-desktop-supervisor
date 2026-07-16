#!/usr/bin/env python3
"""Emit a strict metadata-only GitHub Actions run identity subject."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Mapping

REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA1 = re.compile(r"[0-9a-f]{40}")
SOURCE_REF = re.compile(r"refs/[A-Za-z0-9._/-]+")
WORKFLOW_REF = re.compile(
    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/"
    r"[A-Za-z0-9_.-]+\.ya?ml@refs/[A-Za-z0-9._/-]+"
)
SUBJECT_FIELDS = {
    "schema_version",
    "kind",
    "repository",
    "run_id",
    "run_attempt",
    "workflow_name",
    "workflow_ref",
    "event",
    "head_sha",
    "source_ref",
}


def required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def positive_integer(env: Mapping[str, str], name: str) -> int:
    value = required(env, name)
    if not value.isascii() or not value.isdigit() or int(value) <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def build_subject(env: Mapping[str, str]) -> dict[str, object]:
    repository = required(env, "GITHUB_REPOSITORY")
    workflow_name = required(env, "GITHUB_WORKFLOW")
    workflow_ref = required(env, "GITHUB_WORKFLOW_REF")
    event = required(env, "GITHUB_EVENT_NAME")
    head_sha = required(env, "GITHUB_SHA")
    source_ref = required(env, "GITHUB_REF")
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("GITHUB_REPOSITORY must be owner/name")
    if not WORKFLOW_REF.fullmatch(workflow_ref):
        raise ValueError("GITHUB_WORKFLOW_REF is invalid")
    if not SOURCE_REF.fullmatch(source_ref):
        raise ValueError("GITHUB_REF is invalid")
    workflow_path, separator, workflow_source_ref = workflow_ref.partition("@")
    if separator != "@" or workflow_source_ref != source_ref:
        raise ValueError("workflow ref must bind the exact GITHUB_REF")
    if not workflow_path.startswith(f"{repository}/.github/workflows/"):
        raise ValueError("workflow ref must bind the exact GITHUB_REPOSITORY")
    if not SHA1.fullmatch(head_sha):
        raise ValueError("GITHUB_SHA must be a lowercase 40-character Git SHA")
    return {
        "schema_version": 1,
        "kind": "github_actions_run_identity",
        "repository": repository,
        "run_id": positive_integer(env, "GITHUB_RUN_ID"),
        "run_attempt": positive_integer(env, "GITHUB_RUN_ATTEMPT"),
        "workflow_name": workflow_name,
        "workflow_ref": workflow_ref,
        "event": event,
        "head_sha": head_sha,
        "source_ref": source_ref,
    }


def write_subject(path: Path, subject: dict[str, object]) -> None:
    if set(subject) != SUBJECT_FIELDS:
        raise ValueError("subject fields are invalid")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise ValueError("output already exists") from exc
    raw = (json.dumps(subject, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        subject = build_subject(os.environ)
        write_subject(args.output, subject)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, "output": args.output.name}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
