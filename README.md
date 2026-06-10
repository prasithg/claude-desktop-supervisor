# Claude Desktop Supervisor

A practical Hermes skill/project for supervising Claude Desktop / Claude Code / Fable-style local agent lanes.

Content hook: **Fable Babysitter** — an air-traffic controller for long-running coding agents.

## Why this exists

Long-running AI coding agents do not just need bigger prompts. They need operations:

- did the prompt actually submit, or is it just sitting in the input box?
- is the session still running, idle, waiting for a permission, or done?
- is “blocked” a real blocker, or just text inside a final summary?
- is the context window still healthy, or should the lane close out and hand off?
- which agent is allowed to do local work, and which identity is allowed to publish publicly?

This repo packages a working pattern:

1. read local Claude Code session metadata/transcripts first;
2. use GUI automation only for action and verification;
3. continue local/reversible/testable work when a lane finishes;
4. keep account boundaries explicit;
5. produce compact operational reports instead of raw transcript dumps.

## Architecture

```text
Hermes supervisor
  ├─ reads session metadata + JSONL transcripts
  ├─ classifies lanes: running / idle / waiting / blocked / done
  ├─ uses Computer Use to submit + verify prompts when needed
  ├─ checks git/tests/reports independently
  └─ owns public release boundaries

Claude Desktop / Claude Code / Fable lanes
  ├─ do local code/doc/test work
  ├─ write local session logs
  └─ produce handoffs when context or milestone boundaries are reached
```

## What is included

```text
skills/
  claude-desktop-babysitting/SKILL.md   # Hermes workflow for supervising Claude Desktop lanes
  agent-session-progress/SKILL.md       # read-only session-log progress tracking
  agent-session-progress/scripts/agent_progress.py

templates/
  failsafe-watcher-cron-prompt.md       # watcher job prompt template
  continuation-prompts.md               # reusable continuation prompt shapes

docs/
  architecture.md
  failure-modes.md
  context-lifecycle.md
  account-boundaries.md
  demo-runbook.md
  launch-checklist.md

examples/
  sample-watcher-cron.md
  sample-report.md
```

## Quickstart

Prereqs:

- macOS
- Hermes Agent with Computer Use enabled
- Claude Desktop / Claude Code local session logs available
- Python 3

Run the read-only progress helper:

```bash
python3 skills/agent-session-progress/scripts/agent_progress.py --agent claude --limit 10 --json
```

Install/adapt the skills in your Hermes profile, then create a watcher job from `templates/failsafe-watcher-cron-prompt.md`.

Important: do not treat log state alone as ground truth. A robust watcher uses logs first, GUI verification second, and repo/test state as final evidence.

## Safety and boundaries

This is experimental. Claude Desktop UI and local log schemas can change.

Recommended operating model:

- Claude/Fable lanes: local edits, tests, docs, reports, local commits if appropriate.
- Hermes/human: public GitHub push/release, posting, secrets, credentials, account-level actions.
- Never auto-approve secrets, payment UI, 2FA, permission dialogs, or public/external actions.
- Do not publish raw session transcripts; they can contain private prompts and file contents.

## The core insight

This is not “just loop the prompt.” It is agent ops: state detection, context lifecycle, handoffs, verification, and release boundaries.

## Status

Early public extraction from a real local workflow. Useful as a pattern and starting point; not a polished SaaS-grade daemon.

## License

MIT
