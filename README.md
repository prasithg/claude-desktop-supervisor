# Claude Desktop Supervisor

Content hook: Fable Babysitter.

This repo packages a pattern I started using locally: Hermes watches Claude Desktop / Claude Code / Fable sessions like an air-traffic controller.

Claude can do useful coding work in a long-running Desktop session. The annoying part is everything around that work: noticing when it stopped, telling the difference between "running" and "text sitting in the input box," keeping context from rotting, and making sure the right account owns public release actions.

This is not a polished daemon. It is an early, practical extraction of the workflow: logs first, UI for action, git/tests for truth.

## The problem

Long-running coding agents need supervision.

Common failure modes:

- a prompt is typed but never submitted;
- the Desktop UI looks alive, but the lane is idle;
- a final summary says "blocked" even though the blocker was already handled;
- an old handoff session looks like the current lane because it shares the same repo;
- a huge context window tempts you to keep going forever instead of closing out a coherent unit;
- a worker lane has local authority but should not own public GitHub release credentials.

Most naive monitors miss at least one of these.

## The pattern

```text
Claude metadata + JSONL transcripts
        ↓
Hermes supervisor
        ↓
state classifier: running / idle / waiting / blocked / done
        ↓
Computer Use only when action is needed
        ↓
repo + test verification
        ↓
report, handoff, or public release by the right identity
```

Hermes does the supervision. Claude/Fable does local execution. Public release stays with the human/Hermes-controlled personal account.

## What is included

```text
skills/
  claude-desktop-babysitting/SKILL.md
  agent-session-progress/SKILL.md
  agent-session-progress/scripts/agent_progress.py

templates/
  failsafe-watcher-cron-prompt.md
  continuation-prompts.md

docs/
  architecture.md
  failure-modes.md
  context-lifecycle.md
  account-boundaries.md
  demo-runbook.md
  launch-checklist.md
  product-video-tooling.md
  social-and-video-launch-pack.md

examples/
  sample-watcher-cron.md
  sample-report.md

assets/
  architecture.html
```

## Quickstart

Prereqs:

- macOS
- Hermes Agent with Computer Use enabled
- Claude Desktop / Claude Code local session logs
- Python 3

Run the read-only progress helper:

```bash
python3 skills/agent-session-progress/scripts/agent_progress.py --agent claude --limit 10 --json
```

The helper summarizes local Claude/Codex activity without dumping raw transcript text.

Then adapt the watcher prompt:

```text
templates/failsafe-watcher-cron-prompt.md
```

A robust watcher should:

1. read session logs first;
2. map targets by exact title/cwd/session id;
3. use Computer Use only for idle/unknown/blocked lanes or prompt submission;
4. verify a prompt actually posted and the lane became Running;
5. check git/tests/reports before claiming useful work happened.

## Running proof

Do not trust vibes.

Good signals:

- posted user bubble;
- sidebar/title says Running;
- stop-square, spinner, runtime, or token count is visible;
- transcript has fresh assistant/tool activity.

Bad signals:

- prompt text is still in the input box;
- only the orange logo is visible;
- latest visible assistant text is a final summary;
- logs show only a fresh user event with no assistant/tool follow-up.

## Context lifecycle

For Fable-style 1M-context sessions, context percentage is a lifecycle signal, not a panic button.

- <50%: keep going if the work unit is coherent.
- 50-70%: finish the current unit and prepare a handoff.
- >70%: close out; continue implementation in a fresh lane.
- >85%: emergency closeout only.

Closeout is a transition. Do not loop closeout prompts forever in the old session.

## Account boundaries

Recommended model:

- worker lanes: local edits, tests, docs, reports, local commits if appropriate;
- Hermes/human: public GitHub repo creation, push, release, secrets, posting, payment, external actions.

This matters when the worker lane is authenticated through a different account than the one you want to use for public release.

## Safety

Do not auto-click permission dialogs. Do not type secrets. Do not publish raw transcripts. Do not let a watcher post publicly, buy anything, send messages, or push code without explicit scope.

Session logs can contain private prompts, file contents, tool output, and auth-adjacent details. Treat them like local private data.

## Status

Early public extraction from a real workflow. It should be useful as a starting point if you are running Claude Desktop / Claude Code / Fable-style local lanes, but expect to adapt it to your machine, Claude version, and tolerance for GUI automation brittleness.

## License

MIT
