#!/usr/bin/env python3
"""Validate terminal frame continuity and emit a metadata-only recovery receipt."""
from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from terminal_recovery import Frame, RecoveryClient, utf16_units

CONTRACT_DISTRIBUTION = "lossless-terminal-recovery-contract"
CONTRACT_REPOSITORY = (
    "https://github.com/prasithg/lossless-terminal-recovery-contract.git"
)
PINNED_CONTRACT_REVISION = "837659dab007930a4f92dec166722614c0abfe8f"
MAX_INPUT_BYTES = 10 * 1024 * 1024
MAX_EVENTS = 10_000


class InputError(ValueError):
    """An untrusted event stream violated the bounded input contract."""


def installed_contract_revision() -> str:
    """Read the immutable VCS commit recorded by a direct-url installation."""

    try:
        direct_url_text = distribution(CONTRACT_DISTRIBUTION).read_text("direct_url.json")
    except PackageNotFoundError as error:
        raise RuntimeError("contract dependency is not installed") from error
    if not direct_url_text:
        raise RuntimeError("contract dependency has no direct-url provenance")
    try:
        direct_url = json.loads(direct_url_text)
        url = direct_url["url"]
        revision = direct_url["vcs_info"]["commit_id"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("contract dependency provenance is malformed") from error
    if url.rstrip("/") != CONTRACT_REPOSITORY.rstrip("/"):
        raise RuntimeError("contract dependency provenance repository mismatch")
    if not isinstance(revision, str) or len(revision) != 40:
        raise RuntimeError("contract dependency provenance revision is malformed")
    return revision.lower()


def verify_contract_dependency(expected_revision: str) -> str:
    expected = expected_revision.lower()
    if len(expected) != 40 or any(char not in "0123456789abcdef" for char in expected):
        raise RuntimeError("expected contract revision must be a full Git SHA")
    installed = installed_contract_revision()
    if installed != expected:
        raise RuntimeError("contract dependency provenance mismatch")
    return installed


def load_events(path: Path) -> Iterable[Dict[str, Any]]:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise InputError("cannot stat event stream") from error
    if size > MAX_INPUT_BYTES:
        raise InputError("event stream exceeds byte guard")

    try:
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                if index > MAX_EVENTS:
                    raise InputError("event stream exceeds event-count guard")
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    raise InputError("event stream contains invalid JSON") from error
                if not isinstance(event, dict):
                    raise InputError("each event must be an object")
                yield event
    except (OSError, UnicodeError) as error:
        raise InputError("cannot read event stream") from error


def require_int(event: Dict[str, Any], field: str) -> int:
    value = event.get(field)
    if type(value) is not int:
        raise InputError(f"event {field} must be an integer")
    return value


def require_text(event: Dict[str, Any]) -> str:
    value = event.get("data")
    if not isinstance(value, str):
        raise InputError("event data must be text")
    return value


def process_events(events: Iterable[Dict[str, Any]], revision: str) -> Tuple[Dict[str, Any], int]:
    client = RecoveryClient()
    dispositions = {
        "appended": 0,
        "awaiting_replay": 0,
        "discarded": 0,
        "gap": 0,
        "replaced": 0,
    }
    event_count = 0

    for event in events:
        event_count += 1
        event_type = event.get("type")
        if event_type == "frame":
            try:
                frame = Frame(require_text(event), require_int(event, "end_offset"))
            except ValueError as error:
                raise InputError("frame offsets violate the contract") from error
            outcome = client.accept(frame)
            dispositions[outcome] += 1
        elif event_type == "snapshot":
            try:
                client.replay(require_text(event), require_int(event, "high_water"))
            except ValueError as error:
                raise InputError("snapshot violates the authoritative replay contract") from error
            dispositions["replaced"] += 1
        else:
            raise InputError("unknown event type")

    if event_count == 0:
        raise InputError("event stream is empty")

    blocked = client.needs_replay
    if blocked:
        status = "blocked_missing_replay"
        exit_code = 3
    elif client.replay_count:
        status = "recovered"
        exit_code = 0
    else:
        status = "continuous"
        exit_code = 0

    receipt = {
        "schema_version": 1,
        "status": status,
        "contract_revision": revision,
        "event_count": event_count,
        "dispositions": dispositions,
        "expected_end": client.expected_end,
        "transcript_utf16_units": utf16_units(client.transcript),
        "replay_count": client.replay_count,
        "raw_terminal_content_emitted": False,
    }
    return receipt, exit_code


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check cumulative UTF-16 terminal frames and snapshots; emit only a "
            "metadata recovery receipt."
        )
    )
    parser.add_argument("events", type=Path, metavar="EVENTS.jsonl")
    parser.add_argument(
        "--expected-contract-revision",
        default=PINNED_CONTRACT_REVISION,
        metavar="FULL_SHA",
    )
    args = parser.parse_args(argv)

    try:
        revision = verify_contract_dependency(args.expected_contract_revision)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 4

    try:
        receipt, exit_code = process_events(load_events(args.events), revision)
    except InputError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
