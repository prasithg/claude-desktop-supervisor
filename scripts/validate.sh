#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m py_compile skills/agent-session-progress/scripts/agent_progress.py
python3 skills/agent-session-progress/scripts/agent_progress.py --help >/dev/null
python3 scripts/smoke_agent_progress.py
python3 -m py_compile skills/agent-session-progress/scripts/terminal_stream_guard.py
python3 skills/agent-session-progress/scripts/terminal_stream_guard.py --help >/dev/null
python3 scripts/smoke_terminal_stream_guard.py

python3 - <<'PY'
from pathlib import Path
import re

patterns = [
    ("github-token", re.compile(r"gho_[A-Za-z0-9_]{20,}")),
    ("openai-like-token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("slack-like-token", re.compile(r"xox[baprs]-")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
]
private_needles = [
    "/Users/" + "prasithgovin",
]
allowed_phrase_files = {
    "docs/public-launch-framing.md",
    "docs/launch-checklist.md",
    "AGENTS.md",
}
risky = [
    "bypass " + "credits",
    "bypass " + "limits",
    "avoid usage " + "limits",
    "evade " + "limits",
]
bad = []
for path in Path('.').rglob('*'):
    if path.is_dir() or '.git' in path.parts or '.venv' in path.parts:
        continue
    rel = str(path)
    text = path.read_text(errors='ignore')
    for label, pat in patterns:
        if pat.search(text):
            bad.append((rel, label))
    for needle in private_needles:
        if needle in text:
            bad.append((rel, needle))
    if rel not in allowed_phrase_files:
        for phrase in risky:
            if phrase in text.lower():
                bad.append((rel, f"risky phrasing: {phrase}"))
if bad:
    for rel, label in bad:
        print(f"{rel}: {label}")
    raise SystemExit(1)
PY

echo "validate: ok"
