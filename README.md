# Claude Desktop Supervisor

A practical supervision pattern for long-running Claude Desktop, Claude Code, and Fable-style coding sessions.

These models can run for a long time and do useful work. The hard part is that you, the human, are not always sitting there when they stop, get confused, finish a unit, wait for input, or burn through context. This repo packages the workflow I use locally: push a batch of work into a Claude/Fable lane, then have Hermes watch the lane, check whether it is actually running, continue it when appropriate, and report when human attention is needed.

This is not a polished background daemon yet. It is an early public extraction of a working agent-ops loop: logs first, UI only when needed, git/tests for truth, and explicit account boundaries for public release actions.

## The problem

Long-running coding agents need supervision around the actual model call.

Claude Desktop, Claude Code, and Fable-style 1M-context sessions are good at staying with a large task. But in practice a human operator still needs to answer a bunch of operational questions:

- Did the prompt actually submit, or is text just sitting in the input box?
- Is the lane still running, or did it finish ten minutes ago?
- Did it stop because it needs input, because it is blocked, or because it completed a coherent unit?
- Is the latest visible summary current, or is it from an old handoff session?
- Is the context window still useful, or should this be closed out and continued fresh?
- Did the code really change, tests pass, and git state make sense?
- Which identity is allowed to push, publish, create repos, or post externally?

Most simple monitors miss these because they look at only one layer. The Desktop UI can be misleading. Logs can be stale. A summary can say "blocked" even after the blocker was resolved. A typed prompt can look like progress even though the model never started.

## The pattern

```text
Claude/Fable task lane
        ↓
local logs + metadata + exact repo/session mapping
        ↓
Hermes supervisor
        ↓
state classifier: running / idle / waiting / blocked / done / unknown
        ↓
Computer Use only when the UI needs verification or action
        ↓
continue, close out, ask human, or verify repo/tests
        ↓
report and hand off with the right account boundary
```

The division of labor is simple:

- Claude/Fable does the local long-running work.
- Hermes supervises state, continuation, verification, and handoffs.
- The human/Hermes-controlled personal account owns public release actions.

## What this helps with

Use this when you want to push a bunch of work into one or more long-running agent lanes and then step away without losing the thread.

Examples:

- Start Claude Code on a multi-file refactor and have Hermes check whether it is still running.
- Run a long Fable/Desktop session against a repo and have Hermes detect idle/done/blocked states.
- Have Hermes submit continuation prompts only after verifying that the lane is not already running.
- Close out high-context sessions with a useful handoff instead of letting them drift forever.
- Keep public GitHub publishing separate from a worker lane that may be logged into a different account.

## Prerequisites

Recommended setup:

- macOS.
- Hermes Agent installed and configured.
- Hermes Computer Use enabled, with macOS Accessibility and Screen Recording permissions granted.
- Claude Desktop and/or Claude Code installed.
- For Fable-style long-running runs, a Claude Max plan is strongly recommended. These workflows can burn tokens quickly, especially with large context windows and repeated tool use.
- Python 3.
- A git repo or local project for the worker lane to operate on.

Optional but useful:

- `gh` CLI authenticated to the personal GitHub account that should own public repos/releases.
- A separate browser/profile/account boundary if work and personal GitHub identities differ.
- Screen recording tooling for demos. Screen Studio is the fastest polished option; Remotion is better for reusable coded videos; ffmpeg is enough for trimming/stitching.

## Prompts and operating style

The prompts in this repo are optimized for Claude Code and long-running Desktop/Fable operations, not one-shot chat.

They assume the supervisor may need to:

- inspect logs first instead of trusting the visible UI;
- map a lane by exact title, cwd, project, or session id;
- verify running state before sending anything;
- loop when appropriate, but only with checks between iterations;
- avoid prompt-spamming a lane that is already running;
- close out with a handoff when context is high or the work unit is complete;
- ask the human only when the next action has real ambiguity or external side effects.

The important bit is not "keep prompting forever." The important bit is a guarded loop: observe, classify, act, verify, then decide whether another iteration is warranted.

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
3. classify the lane state;
4. use Computer Use only for idle/unknown/blocked lanes or prompt submission;
5. verify that a prompt actually posted and the lane became Running;
6. check git/tests/reports before claiming useful work happened.

## Running proof

Do not trust vibes.

Good signals:

- posted user bubble;
- sidebar/title says Running;
- stop-square, spinner, runtime, or token count is visible;
- transcript has fresh assistant/tool activity;
- repo/test state changed in the expected way.

Bad signals:

- prompt text is still in the input box;
- only the orange Claude logo is visible;
- latest visible assistant text is a final summary;
- logs show only a fresh user event with no assistant/tool follow-up;
- the classifier found a word like `input` inside metadata instead of an actual waiting-for-input state.

## Context lifecycle

For Fable-style 1M-context sessions, context percentage is a lifecycle signal, not a panic button.

- <50%: keep going if the work unit is coherent.
- 50-70%: finish the current unit and prepare a handoff.
- >70%: close out; continue implementation in a fresh lane.
- >85%: emergency closeout only.

Closeout is a transition. Do not loop closeout prompts forever in the old session.

## Account boundaries

Recommended model:

- worker lanes: local edits, tests, docs, reports, and local commits if appropriate;
- Hermes/human: public GitHub repo creation, push, release, secrets, posting, payment, and external actions.

This matters when a worker lane is authenticated through a different account than the one you want to use for public release.

## Safety

Do not auto-click permission dialogs. Do not type secrets. Do not publish raw transcripts. Do not let a watcher post publicly, buy anything, send messages, or push code without explicit scope.

Session logs can contain private prompts, file contents, tool output, and auth-adjacent details. Treat them like local private data.

## Status

Early public extraction from a real workflow. It should be useful as a starting point if you are running Claude Desktop, Claude Code, or Fable-style local lanes, but expect to adapt it to your machine, Claude version, plan limits, and tolerance for GUI automation brittleness.

## License

MIT
