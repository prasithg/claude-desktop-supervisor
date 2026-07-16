# Agent Instructions

This repository packages a local supervision workflow for Claude Desktop, Claude Code, and Fable-style sessions.

## Environment and permission contract

- Python: 3.10+. The progress helper is stdlib-only; the terminal stream guard consumes the full-SHA dependency in `requirements-contracts.txt`.
- macOS GUI control: Accessibility + Screen Recording are required only when using Computer Use to verify or act in Claude Desktop.
- Claude paths assumed by default:
  - `~/Library/Application Support/Claude/claude-code-sessions/**/*.json`
  - `~/.claude/projects/**/*.jsonl`
- Codex path assumed by default: `~/.codex/state_5.sqlite`.
- `agent_progress.py` supports `--home`, `--claude-meta-glob`, `--claude-projects-glob`, and `--codex-state` for tests or nonstandard installs.
- `gh` is optional and only needed for public repo/release actions that the human has explicitly scoped.

## Ground rules

- Treat local session logs as private data.
- Do not print, publish, commit, or paste raw transcripts.
- Summarize status compactly and redact secrets.
- Use logs first; use GUI/Computer Use only when action or verification is needed.
- Never click permission dialogs, type secrets, submit payments, post publicly, push code, create releases, or modify account settings without explicit human scope.
- Map target sessions by exact title, cwd, and/or session id before acting.
- Do not prompt-spam a session that is already running.
- Prefer local, reversible, testable work. Escalate when judgment, secrets, permissions, or external/public actions are required.

## Validation

Run before proposing changes:

```bash
python3 -m pip install --no-deps -r requirements-contracts.txt
bash scripts/validate.sh
```

Equivalent minimal checks:

```bash
python3 -m py_compile skills/agent-session-progress/scripts/agent_progress.py
python3 skills/agent-session-progress/scripts/agent_progress.py --help
python3 scripts/smoke_agent_progress.py
python3 scripts/smoke_terminal_stream_guard.py
```

If tests are unavailable, say so explicitly.

## Repo intent

The skills here are intended for Hermes/Claw-style consumers. Prefer small, public-safe changes that improve installability, validation, docs, examples, and operator-loop clarity.

## Public-safety framing

Say:

- local app workflow
- preserving app history/state and account boundaries
- logs first, UI for action, git/tests for truth
- human can take over any time

Avoid saying or implying:

- bypassing limits or credits
- evading product restrictions
- automated public posting/pushing without explicit approval
- reading or publishing private transcripts
