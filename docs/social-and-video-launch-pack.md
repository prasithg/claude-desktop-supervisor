# Social and Video Launch Pack

## Positioning

Repo name: `claude-desktop-supervisor`

Content hook: `Fable Babysitter`

One-liner:

> I accidentally built an air-traffic controller for Claude Desktop / Fable coding sessions.

Serious framing:

> A Hermes supervisor pattern for long-running local agent lanes: session-log monitoring, GUI verification, context lifecycle management, handoffs, repo/test verification, and account boundaries.

## X profile update draft

Bio option A:

> Startup CTO building practical agent infrastructure: Hermes, evals, long-running coding agents, assistive AI.

Bio option B:

> Building practical agent infrastructure — Hermes, evals, long-running coding agents, assistive AI.

Pinned post after launch:

> I built a babysitter for Claude Desktop / Fable sessions: logs-first monitoring, GUI verification, context handoffs, and local-agent release boundaries. Repo + demo below.

## X launch thread draft

1/ I accidentally built an air-traffic controller for Claude Desktop / Fable sessions.

Claude can do solid local coding work, but long-running agent sessions need supervision.

2/ The annoying parts are operational:

- did the prompt actually submit?
- is it still running, or idle?
- is “blocked” a real blocker or just a final summary?
- is the context still healthy?
- who is allowed to push publicly?

3/ So Hermes now watches Claude Code session logs, uses macOS Computer Use only when it needs to submit/verify prompts, and treats Claude/Fable sessions as local execution lanes.

4/ The important bit: this is not “loop the prompt.”

It’s agent ops:
state detection, context lifecycle, handoffs, repo/test verification, and account boundaries.

5/ The failure modes are very real:

- text sitting in the input box != running
- the orange logo can be misleading
- final summaries can mention “blocked” even after success
- old handoff sessions look like current lanes
- Desktop can append a user event without assistant follow-up

6/ Fable twist: if you have a huge context window, don’t panic-close too early.

Use context as a lifecycle signal: keep coherent units moving, close out near boundary, and start fresh lanes from handoffs instead of looping closeout prompts forever.

7/ I extracted the workflow into a public repo / Hermes skill:

<repo link>

Early, practical, macOS/Claude Desktop-specific, but this pattern feels like the missing layer for serious local agent work.

## LinkedIn draft

I’ve been testing a practical layer that feels increasingly necessary for long-running AI coding agents: supervision.

Claude Desktop / Claude Code / Fable can do useful local work, but someone still needs to answer operational questions:

- Is the session actually running, or did the prompt stay in the input box?
- Did it finish 3 minutes ago and sit idle?
- Is the “blocker” real, or just text in a final summary?
- Is the context window still healthy, or should this unit hand off to a fresh session?
- Which agent is allowed to make local changes, and which account is allowed to push publicly?

I built a Hermes skill around this pattern.

Hermes reads Claude Code session logs first, uses macOS Computer Use only for prompt submission and verification, manages context/handoff boundaries, and independently verifies git/tests.

The result is closer to an air-traffic controller for agent lanes than a simple prompt loop.

I’m packaging it publicly because I think this “agent ops” layer is going to matter as much as raw model capability.

Repo: <repo link>

## 60-90 second video script

### 0-5 sec: hook

Caption:

> Claude finished 3 minutes ago. Nobody noticed.

Voiceover:

> I kept finding my Claude/Fable coding sessions done, idle, or not actually submitted. So I made Hermes babysit them.

### 5-20 sec: problem

Show: Claude Desktop sidebar / sanitized UI / terminal helper output.

Captions:

- prompt in input box != running
- orange logo != running
- final summary != active work
- long context needs handoffs

Voiceover:

> The hard part is not asking Claude to keep going. The hard part is knowing whether it is actually running, idle, blocked, or ready for a fresh context.

### 20-45 sec: mechanism

Show: `agent_progress.py --agent claude --json`, then a sanitized Computer Use capture or mock.

Voiceover:

> Hermes reads the local Claude Code session logs first. Then it uses Computer Use only when it needs to act: pick the right session, paste a continuation prompt, press Return, and verify the sidebar actually says Running.

### 45-65 sec: architecture

Show: architecture diagram.

Voiceover:

> Claude/Fable is the local execution lane. Hermes is the supervisor and release manager. Logs for detection, UI for action, git/tests for verification, and separate account boundaries for public release.

### 65-90 sec: payoff

Caption:

> Not prompt looping. Agent ops.

Voiceover:

> This is early and still scrappy, but it feels like the missing layer for long-running coding agents: state, context, handoffs, verification, and release boundaries. I’m releasing the Hermes skill today.

## Demo asset decision

Best fast path:

1. Use a toy/sanitized repo or blur private repo names.
2. Record 3 clips: session-log helper, Claude Desktop running proof, architecture diagram.
3. Stitch with captions.
4. Avoid raw transcripts and private work data.
