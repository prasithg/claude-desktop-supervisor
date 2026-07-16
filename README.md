# Claude Desktop Supervisor

A practical pattern for letting Hermes sit in the human operator seat for long-running Claude Desktop, Claude Code, and Fable-style coding sessions.

Claude Code, Claude Desktop, and Fable-style long-context sessions can do real work. Here "Fable-style" means a very long-context Claude lane (for example a 1M-context coding session) that can complete a large work unit before needing review, handoff, or a fresh session. But a human still usually has to operate the loop: check whether the model is running, read the output, decide whether the next prompt is safe, preserve the handoff, verify git/tests, and take over when judgment is needed.

This repo packages the workflow I use locally with [Hermes Agent](https://github.com/NousResearch/hermes-agent): push a batch of work into a Claude/Fable lane, then have a supervisor agent watch the same app/history a human would, check whether it is actually running, continue it when appropriate, and hand control back to the human when needed.

This does not bypass product limits, grant extra access, share credentials, or remove the user's responsibility to follow the terms and policies of the apps and accounts they operate. The intended boundary is local/reversible work first, with explicit human/Hermes scope for public or external actions.

This is not a polished background daemon yet. It is an early public extraction of a working agent-ops loop: logs first, UI for action, git/tests for truth, and human takeover at any time.

## The problem

Long-running coding agents need an operator around the actual model call.

Claude Desktop, Claude Code, and Fable-style 1M-context sessions are good at staying with a large task. But in practice a human operator still needs to answer a bunch of operational questions:

- Did the prompt actually submit, or is text just sitting in the input box?
- Is the lane still running, or did it finish ten minutes ago?
- Did it stop because it needs input, because it is blocked, or because it completed a coherent unit?
- Is the latest visible summary current, or is it from an old handoff session?
- Is the context window still useful, or should this be closed out and continued fresh?
- Did the code really change, tests pass, and git state make sense?
- Can the human take over now and hand control back to Hermes later?
- Which identity is allowed to push, publish, create repos, or post externally?

Most simple monitors miss these because they look at only one layer. The Desktop UI can be misleading. Logs can be stale. A summary can say "blocked" even after the blocker was resolved. A typed prompt can look like progress even though the model never started. The useful loop is not just monitoring; it is operating the lane the way a human would, while preserving enough state that the human can step back in.

## The pattern

```text
human starts or delegates work
        ↓
Claude/Fable task lane does the coding
        ↓
local logs + metadata + exact repo/session mapping
        ↓
Hermes supervisor in the operator seat
        ↓
state classifier: running / idle / waiting / blocked / done / unknown
        ↓
Computer Use only when the UI needs verification or action
        ↓
continue, review, close out, ask human, or verify repo/tests
        ↓
human can take over or hand the lane back to Hermes
```

The division of labor is simple:

- Claude/Fable does the local long-running work.
- Hermes operates the lane: state, continuation, review, verification, and handoffs.
- The human can take over, redirect, and hand control back.
- The human/Hermes-controlled personal account owns public release actions.

## What this helps with

Use this when you want to push a bunch of work into one or more long-running agent lanes and then step away without losing the thread.

Examples:

- Start Claude Code on a multi-file refactor and have Hermes check whether it is still running.
- Run a long Fable/Desktop session against a repo and have Hermes detect idle/done/blocked states.
- Have Hermes submit continuation prompts only after verifying that the lane is not already running.
- Close out high-context sessions with a useful handoff instead of letting them drift forever.
- Let another agent operate Claude Code through the same local app workflow a human uses, preserving app history and account/session boundaries.
- Let the human jump back in, inspect the preserved state, redirect, and hand the lane back to Hermes.
- Keep public GitHub publishing separate from a worker lane that may be logged into a different account.

## Prerequisites

Recommended setup:

- macOS.
- Hermes Agent installed and configured.
- Hermes Computer Use enabled, with macOS Accessibility and Screen Recording permissions granted.
- Claude Desktop and/or Claude Code installed.
- For Fable-style long-running runs, a Claude Max plan is strongly recommended. These workflows can burn tokens quickly, especially with large context windows and repeated tool use.
- Python 3.10+. The progress helper is stdlib-only. The optional terminal continuity guard uses one full-SHA-pinned, dependency-free contract package.
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
- preserve enough history/state that the human can take over and then hand the lane back;
- ask the human only when the next action has real ambiguity or external side effects.

The important bit is not "keep prompting forever." The important bit is a guarded operator loop: observe, classify, act, verify, then decide whether another iteration is warranted.

## What is included

```text
skills/
  manifest.json
  claude-desktop-babysitting/SKILL.md
  agent-session-progress/SKILL.md
  agent-session-progress/scripts/agent_progress.py

scripts/
  install-hermes-skills.sh
  validate.sh
  smoke_agent_progress.py

templates/
  failsafe-watcher-cron-prompt.md
  continuation-prompts.md

docs/
  architecture.md
  failure-modes.md
  context-lifecycle.md
  account-boundaries.md
  public-launch-framing.md
  demo-runbook.md
  launch-checklist.md

examples/
  sample-watcher-cron.md
  sample-report.md

assets/
  architecture.html
```

## 5-minute quickstart

Clone and validate the repo:

```bash
git clone https://github.com/prasithg/claude-desktop-supervisor.git
cd claude-desktop-supervisor
python3 -m pip install --no-deps -r requirements-contracts.txt
bash scripts/validate.sh
```

Check a captured JSONL terminal stream without printing its payload:

```bash
python3 skills/agent-session-progress/scripts/terminal_stream_guard.py EVENTS.jsonl
```

The guard consumes cumulative UTF-16 frame offsets and authoritative snapshot
high-water marks from the pinned
[`lossless-terminal-recovery-contract`](https://github.com/prasithg/lossless-terminal-recovery-contract).
It emits a metadata-only continuity receipt, exits `3` when a detected gap has
not received a replay snapshot, rejects partial overlap, and verifies the
installed contract's exact Git revision before processing the stream.

Run the read-only progress helper:

```bash
python3 skills/agent-session-progress/scripts/agent_progress.py --agent claude --limit 10 --json
```

The helper summarizes local Claude/Codex activity without dumping raw transcript text. Example shape:

```json
[
  {
    "agent": "claude-code",
    "status": "idle-or-done",
    "title": "Fixture session",
    "cwd": "/path/to/repo",
    "model": "claude-fable-5",
    "last_activity": "2026-06-10T22:14:03",
    "latest": {
      "event": "assistant",
      "role": "assistant",
      "items": ["text"],
      "tools": [],
      "usage": {"context_pct_est": 12.4}
    }
  }
]
```

Install the skills into Hermes:

```bash
bash scripts/install-hermes-skills.sh
# or preview first:
# bash scripts/install-hermes-skills.sh --dry-run
# or keep editable symlinks instead of copies:
# bash scripts/install-hermes-skills.sh --mode symlink
# if updating an existing local install after review:
# bash scripts/install-hermes-skills.sh --replace
```

By default this installs into `~/.hermes/skills/`. To install into another Hermes profile:

```bash
HERMES_PROFILE=my-profile bash scripts/install-hermes-skills.sh
```

Then start a fresh Hermes session and ask:

```text
Use the claude-desktop-babysitting and agent-session-progress skills. Watch my Claude Code session for <repo/title>. Read logs first, verify before acting, and do not click permission dialogs or publish anything.
```

For Claw or other agents, copy the directories under `skills/` into that agent's skill/workflow directory, preserving each `SKILL.md` and scripts subdirectory. Also include `AGENTS.md` in context so the consumer sees the safety and validation rules.

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
