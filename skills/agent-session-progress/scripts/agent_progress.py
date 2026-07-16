#!/usr/bin/env python3
"""Read local Claude Code and Codex session stores and print compact progress summaries.

Read-only. Does not print raw transcript text by default.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import importlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()
CLAUDE_META_GLOB = str(HOME / "Library/Application Support/Claude/claude-code-sessions/**/*.json")
CLAUDE_PROJECTS_GLOB = str(HOME / ".claude/projects/**/*.jsonl")
CODEX_STATE = HOME / ".codex/state_5.sqlite"

KNOWLEDGE_CONTRACT_REVISION = "52bbea3cfde10f60e78c7c74e82dee00e7dcc6ba"
SESSION_SOURCE_POLICIES = {
    "claude-code": {
        "id": "claude-session-store",
        "enabled": True,
        "sensitivity": "private",
        "public_reuse": False,
    },
    "codex": {
        "id": "codex-session-store",
        "enabled": True,
        "sensitivity": "private",
        "public_reuse": False,
    },
}

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|bearer|cookie)\s*[:=]\s*\S+"
)


def scrub(s: Any, max_len: int = 240) -> str | None:
    if s is None:
        return None
    text = SECRET_RE.sub(r"\1=<REDACTED>", str(s))
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def iso_from_mtime(path: str | Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")
    except OSError:
        return None


def age_seconds_from_mtime(path: str | Path) -> float | None:
    try:
        return max(0.0, dt.datetime.now().timestamp() - os.path.getmtime(path))
    except OSError:
        return None


def classify(age: float | None, latest: dict[str, Any] | None) -> str:
    if age is None:
        return "unknown"
    if age <= 120:
        return "active"
    if not latest:
        return "unknown"
    # Keep this deliberately conservative. The compact latest summary includes
    # fields such as usage.input_tokens, so generic words like "input" create
    # false blockers for normal completed assistant turns.
    text = json.dumps({k: v for k, v in latest.items() if k != "usage"}, default=str).lower()
    if any(x in text for x in ["permission", "approval", "error", "failed", "waiting"]):
        return "blocked-or-needs-review"
    if age <= 300:
        return "recently-active"
    return "idle-or-done"


def build_export_boundary_receipt(
    rows: list[dict[str, Any]],
    *,
    destination: str,
    as_of: str,
) -> dict[str, Any]:
    """Validate an export destination without copying session content into the receipt.

    The optional consumer dependency is imported only for this explicit boundary
    check, so the default read-only progress helper remains stdlib-only.
    """
    evaluate_contract = importlib.import_module(
        "knowledge_ingestion_contracts"
    ).evaluate_contract

    if destination not in {"private", "internal", "public"}:
        raise ValueError(f"unsupported export destination: {destination!r}")

    sources: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    items: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        agent = row.get("agent")
        if not isinstance(agent, str):
            raise ValueError(f"unsupported agent source: {agent!r}")
        policy = SESSION_SOURCE_POLICIES.get(agent)
        if policy is None:
            raise ValueError(f"unsupported agent source: {agent!r}")
        source_id = policy["id"]
        if source_id not in source_ids:
            sources.append(dict(policy))
            source_ids.add(source_id)
        slug = f"session-summary-{index:04d}"
        items.append(
            {
                "source_id": source_id,
                "slug": slug,
                "observed_at": as_of,
                "expires_at": None,
            }
        )
        claims.append(
            {
                "id": f"export-row-{index:04d}",
                "destination": destination,
                "evidence": [{"source_id": source_id, "slug": slug}],
            }
        )

    contract = {"sources": sources, "items": items, "claims": claims}
    violations = evaluate_contract(contract, as_of)
    return {
        "schema_version": 1,
        "contract": "agent-knowledge-boundary-contracts",
        "contract_revision": KNOWLEDGE_CONTRACT_REVISION,
        "destination": destination,
        "row_count": len(rows),
        "allowed": not violations,
        "violation_codes": [entry["code"] for entry in violations],
        "violations": violations,
    }


def tail_jsonl(path: str | Path, max_lines: int = 20) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    # Simple bounded tail good enough for summaries; avoids dumping file contents.
    data = p.read_bytes()[-256_000:]
    lines = data.splitlines()[-max_lines:]
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def claude_project_path(cwd: str | None, cli_session_id: str | None) -> str | None:
    if not cwd or not cli_session_id:
        return None
    candidate = HOME / ".claude/projects" / cwd.replace("/", "-") / f"{cli_session_id}.jsonl"
    if candidate.exists():
        return str(candidate)
    # Fallback for schema/path drift.
    for p in glob.glob(CLAUDE_PROJECTS_GLOB, recursive=True):
        if Path(p).stem == cli_session_id:
            return p
    return str(candidate)


def summarize_usage(usage: dict[str, Any] | None, model: str | None = None) -> dict[str, Any] | None:
    if not isinstance(usage, dict):
        return None
    input_tokens = int(usage.get("input_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    cache_create = int(usage.get("cache_creation_input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    # Claude Code reports most prior context as cache_read_input_tokens. Treat
    # read + newly-created + current input as an approximate context footprint.
    context_tokens = input_tokens + cache_read + cache_create
    # Practical heuristic: many modern models behave best before roughly
    # 50% of context length; Fable is treated as a 1M-token context
    # model for lifecycle decisions unless better metadata is discovered.
    context_limit = 1_000_000 if model and "fable" in model.lower() else 200_000
    return {
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_create,
        "output_tokens": output_tokens,
        "context_tokens_est": context_tokens,
        "context_limit_est": context_limit,
        "context_pct_est": round(context_tokens / context_limit * 100, 1) if context_limit else None,
    }


def summarize_claude_event(obj: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    content = msg.get("content")
    item_types: list[str] = []
    tools: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                t = item.get("type")
                if t:
                    item_types.append(str(t))
                if t == "tool_use" and item.get("name"):
                    tools.append(str(item.get("name")))
    elif isinstance(content, str):
        item_types.append("text")
    return {
        "timestamp": obj.get("timestamp"),
        "event": obj.get("type"),
        "role": msg.get("role"),
        "items": item_types,
        "tools": tools,
        "usage": summarize_usage(msg.get("usage"), model),
        "cwd": scrub(obj.get("cwd"), 160),
        "gitBranch": scrub(obj.get("gitBranch"), 80),
    }


def discover_claude(limit: int) -> list[dict[str, Any]]:
    metas = sorted(glob.glob(CLAUDE_META_GLOB, recursive=True), key=lambda p: os.path.getmtime(p), reverse=True)
    rows = []
    seen: set[tuple[str | None, str | None]] = set()
    for meta_path in metas:
        try:
            meta = json.loads(Path(meta_path).read_text())
        except Exception:
            continue
        key = (meta.get("cwd"), meta.get("cliSessionId"))
        if key in seen:
            continue
        seen.add(key)
        transcript = claude_project_path(meta.get("cwd"), meta.get("cliSessionId"))
        events = tail_jsonl(transcript, 20) if transcript else []
        model = meta.get("model")
        latest = summarize_claude_event(events[-1], model) if events else None
        age = age_seconds_from_mtime(transcript) if transcript else age_seconds_from_mtime(meta_path)
        rows.append({
            "agent": "claude-code",
            "status": classify(age, latest),
            "title": scrub(meta.get("title"), 120),
            "cwd": scrub(meta.get("cwd"), 180),
            "model": scrub(model, 80),
            "last_activity": iso_from_mtime(transcript) or iso_from_mtime(meta_path),
            "completed_turns": meta.get("completedTurns"),
            "latest": latest,
            "evidence": transcript,
            "metadata": meta_path,
        })
        if len(rows) >= limit:
            break
    return rows


def summarize_codex_event(obj: dict[str, Any]) -> dict[str, Any]:
    if "payload" in obj and isinstance(obj.get("payload"), dict):
        payload = obj.get("payload") or {}
        content = payload.get("content")
        return {
            "timestamp": obj.get("timestamp"),
            "event": obj.get("type"),
            "payload_type": payload.get("type"),
            "role": payload.get("role"),
            "content_items": len(content) if isinstance(content, list) else None,
        }
    content = obj.get("content")
    return {
        "timestamp": obj.get("timestamp"),
        "event": obj.get("type") or obj.get("record_type"),
        "role": obj.get("role"),
        "content_items": len(content) if isinstance(content, list) else None,
    }


def codex_unavailable_row(reason: str, error: Exception | None = None) -> dict[str, Any]:
    return {
        "agent": "codex",
        "status": "unknown",
        "title": reason,
        "cwd": None,
        "model": None,
        "provider": None,
        "last_activity": None,
        "latest": None,
        "evidence": str(CODEX_STATE),
        "error": scrub(error) if error else None,
    }


def discover_codex(limit: int) -> list[dict[str, Any]]:
    if not CODEX_STATE.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        con = sqlite3.connect(f"file:{CODEX_STATE}?mode=ro&immutable=1", uri=True)
    except sqlite3.Error as e:
        return [codex_unavailable_row("Codex state unavailable", e)]
    try:
        q = """
            select id, rollout_path, updated_at_ms, source, model_provider, cwd, title, model, tokens_used
            from threads
            order by updated_at_ms desc
            limit ?
        """
        for thread_id, rollout_path, updated_ms, source, provider, cwd, title, model, tokens in con.execute(q, (limit,)):
            events = tail_jsonl(rollout_path, 20) if rollout_path else []
            latest = summarize_codex_event(events[-1]) if events else None
            age = age_seconds_from_mtime(rollout_path) if rollout_path else None
            rows.append({
                "agent": "codex",
                "status": classify(age, latest),
                "title": scrub(title, 120),
                "cwd": scrub(cwd, 180),
                "model": scrub(model, 80),
                "provider": scrub(provider, 80),
                "last_activity": iso_from_mtime(rollout_path) if rollout_path else (dt.datetime.fromtimestamp(updated_ms / 1000).isoformat(timespec="seconds") if updated_ms else None),
                "tokens_used": tokens,
                "latest": latest,
                "evidence": rollout_path,
                "thread_id": thread_id,
                "source": source,
            })
    except sqlite3.Error as e:
        return [codex_unavailable_row("Codex state unreadable or schema changed", e)]
    finally:
        con.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize local Claude Code/Codex session progress without raw transcript text.")
    parser.add_argument("--agent", choices=["all", "claude", "codex"], default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human text")
    parser.add_argument("--home", type=Path, help="override HOME for tests or nonstandard installs")
    parser.add_argument("--claude-meta-glob", help="override Claude Desktop metadata glob")
    parser.add_argument("--claude-projects-glob", help="override Claude project transcript glob")
    parser.add_argument("--codex-state", type=Path, help="override Codex sqlite state path")
    parser.add_argument(
        "--export-destination",
        choices=["private", "internal", "public"],
        help="validate the summary destination with agent-knowledge-boundary-contracts",
    )
    parser.add_argument(
        "--boundary-receipt",
        type=Path,
        help="write a metadata-only export boundary receipt (requires --export-destination)",
    )
    args = parser.parse_args()

    global HOME, CLAUDE_META_GLOB, CLAUDE_PROJECTS_GLOB, CODEX_STATE
    if args.home:
        HOME = args.home.expanduser()
        CLAUDE_META_GLOB = str(HOME / "Library/Application Support/Claude/claude-code-sessions/**/*.json")
        CLAUDE_PROJECTS_GLOB = str(HOME / ".claude/projects/**/*.jsonl")
        CODEX_STATE = HOME / ".codex/state_5.sqlite"
    if args.claude_meta_glob:
        CLAUDE_META_GLOB = args.claude_meta_glob
    if args.claude_projects_glob:
        CLAUDE_PROJECTS_GLOB = args.claude_projects_glob
    if args.codex_state:
        CODEX_STATE = args.codex_state.expanduser()

    results: list[dict[str, Any]] = []
    if args.agent in ("all", "claude"):
        results.extend(discover_claude(args.limit))
    if args.agent in ("all", "codex"):
        results.extend(discover_codex(args.limit))

    results.sort(key=lambda r: r.get("last_activity") or "", reverse=True)

    if args.boundary_receipt and not args.export_destination:
        parser.error("--boundary-receipt requires --export-destination")
    if args.export_destination:
        as_of = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            receipt = build_export_boundary_receipt(
                results,
                destination=args.export_destination,
                as_of=as_of,
            )
        except (ImportError, ValueError) as exc:
            print(f"export boundary unavailable: {exc}", file=sys.stderr)
            return 3
        if args.boundary_receipt:
            args.boundary_receipt.parent.mkdir(parents=True, exist_ok=True)
            args.boundary_receipt.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if not receipt["allowed"]:
            if not args.boundary_receipt:
                print(json.dumps(receipt, sort_keys=True), file=sys.stderr)
            return 3

    if args.json:
        print(json.dumps(results, indent=2, default=str))
        return 0

    if not results:
        print("No Claude/Codex session activity found. This is normal on a fresh machine or unsupported client version.")
        return 0

    for r in results[: args.limit if args.agent == "all" else len(results)]:
        latest = r.get("latest") or {}
        print(f"[{r.get('status')}] {r.get('agent')} — {r.get('title') or '(untitled)'}")
        print(f"  cwd: {r.get('cwd')}")
        print(f"  model: {r.get('model') or r.get('provider')}")
        print(f"  last_activity: {r.get('last_activity')}")
        print(f"  latest: {latest}")
        print(f"  evidence: {r.get('evidence')}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
