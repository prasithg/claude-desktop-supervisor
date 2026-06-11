# Public Launch Framing

This note reviews the repo from the perspective of external agents, users, and platform reviewers. The goal is to frame the project as a local, account-bound operator workflow for long-running coding sessions, not as a way to evade product limits, policies, credits, billing, or review.

## Recommended public positioning

Use this core frame:

> Claude Desktop Supervisor is a Hermes workflow for supervising long-running local coding sessions through the same app surfaces a human operator uses: local session logs for state detection, Computer Use for UI verification and prompt submission, git/tests for independent verification, and explicit account boundaries for public release actions.

Short version:

> A local agent-ops pattern for supervising Claude Desktop / Claude Code / Fable-style coding lanes: observe, classify, act only when safe, verify, and hand off.

Social version:

> Not prompt looping. Agent ops for local coding lanes: state detection, UI verification, context handoffs, repo/test checks, and release/account boundaries.

## Wording to prefer

Use:

- local app workflow
- human-in-the-operator-seat pattern
- same surfaces a human uses
- account/session boundaries
- local/reversible work
- explicit scope before external actions
- continuation after verifying idle/done state
- state detection and handoff, not infinite prompting
- respects plan limits and local authentication boundaries
- no public posting, pushing, purchases, secrets, or permission dialogs without explicit human scope

Avoid:

- bypass credits / save credits / avoid paying
- evade limits / get around usage limits / unlimited Claude
- farm Claude / exploit Max / arbitrage accounts
- autonomous posting / auto-push / self-publishing agent
- botting / unattended account use
- jailbreak / workaround / ToS bypass
- anything implying cross-account credential sharing or using one product account to publish as another without explicit ownership

Acceptable but use sparingly:

- babysitter: catchy but informal; pair with serious framing immediately. Prefer "supervisor", "operator", or "air-traffic controller" in README/docs.
- autonomous monitor: okay in templates if bounded by "local-only", "no external side effects", and "explicit scope required".
- restart idle sessions: prefer "continue an idle/done lane after verification" to avoid implying automated evasion or spam.

## Safe README structure for launch

Recommended top-level flow:

1. What it is
   - One paragraph: Hermes supervises local coding lanes via logs, UI verification, git/tests, and handoffs.
   - Include a safety sentence early: it does not grant extra product access, bypass limits, share credentials, or automate external actions.

2. Why it exists
   - Operational failure modes: prompt not submitted, stale UI, final summary mistaken for active work, context lifecycle, wrong account for public release.

3. The pattern
   - Detect -> classify -> optional UI action -> verify -> report/handoff.
   - Separate detection, action, verification, and publishing.

4. What this helps with
   - Local long-running coding sessions, handoffs, repo/test verification, human takeover.
   - Keep examples local and reversible.

5. Prerequisites and boundaries
   - macOS, Hermes, Computer Use permissions, Claude app/CLI installed, authenticated by the user.
   - Mention users are responsible for respecting applicable product terms and plan limits.

6. Quickstart
   - Read-only helper first.
   - Then adapt watcher prompt.
   - Then optional Computer Use steps with running-proof checklist.

7. Safety model
   - No secrets, permission dialogs, purchases, public posts, pushes, or messages without explicit scope.
   - Logs are private local data.
   - Worker lanes do local/reversible work; human/Hermes-controlled release identity owns external actions.

8. Status / limitations
   - Early extraction; GUI automation is brittle; users must adapt to app versions and local policies.

## Specific repo observations

Positive:

- README already frames the project around local workflow, human takeover, logs-first monitoring, git/tests, and account boundaries.
- Safety language is present in README, skill docs, templates, and account-boundaries doc.
- No explicit "bypass credits", "evade limits", or similar ToS-risky phrasing found in the markdown reviewed.
- The repeated "not prompt looping" / "agent ops" distinction is strong and should stay.

Tighten before launch:

- Add an early README sentence: "This does not bypass product limits, grant extra access, share credentials, or remove the user's responsibility to follow the terms and policies of the apps they use."
- Replace or de-emphasize "babysitter/babysitting" in public-facing titles and social copy where possible. Keep it only as an informal hook if followed by serious operator/supervisor framing.
- In skill metadata, consider changing tags from `overnight`, `babysitting`, `autonomous-agents` to safer terms like `supervision`, `local-workflows`, `agent-ops`, `computer-use`, `handoffs`.
- Prefer "continue idle/done lanes after verification" over "restart idle sessions".
- In launch posts, avoid implying unattended all-night work. Say "long-running local sessions" and "human takeover at any time".
- Add a short "Terms and account boundaries" section or callout in README near Prerequisites/Safety.

## Suggested safe replacement snippets

README opening replacement:

> Claude Desktop Supervisor is a local agent-ops workflow for supervising long-running Claude Desktop, Claude Code, and Fable-style coding sessions. Hermes watches local session signals, verifies the app UI when needed, submits continuation prompts only after confirming the lane is idle or ready, checks repo/test state, and preserves handoffs so a human can take over at any time.
>
> It is not a way to bypass product limits, share credentials, or automate external actions. Use it only with accounts, apps, plans, and projects you are authorized to operate, and keep public publishing behind explicit human/Hermes scope.

Account-boundary callout:

> Worker lanes are for local, reversible work: edits, tests, docs, reports, and local commits when appropriate. Public actions such as repo creation, pushing, releases, posts, purchases, credentials, and secrets stay with the human or an explicitly scoped Hermes-controlled account.

Quickstart safety note:

> Start with the read-only helper. Do not enable a watcher to click permission dialogs, type secrets, purchase anything, send messages, post publicly, or push code unless that action is explicitly scoped for the current run.

Social launch one-liner:

> I built a Hermes supervisor for long-running local Claude/Fable coding lanes: logs-first state detection, UI verification, context handoffs, repo/test checks, and explicit account boundaries.

Video voiceover replacement for "So I made Hermes babysit them":

> So I made Hermes supervise them like a careful local operator: check logs first, verify the UI only when needed, and hand control back to me when judgment or external actions are required.

## Suggested docs structure

Keep current files, but order the docs for an external user like this:

```text
README.md                         public overview, quickstart, boundaries
skills/claude-desktop-babysitting/SKILL.md
skills/agent-session-progress/SKILL.md

docs/
  architecture.md                 mental model and data/action flow
  safety-and-boundaries.md         merge/expand account-boundaries + safety model
  failure-modes.md                what can go wrong and how detection works
  context-lifecycle.md            handoff thresholds and fresh-lane policy
  demo-runbook.md                 sanitized demo recipe
  public-launch-framing.md        launch/review copy guidance
  launch-checklist.md             release readiness checklist

templates/
  failsafe-watcher-cron-prompt.md bounded local watcher prompt
  continuation-prompts.md         safe continuation/handoff prompts

examples/
  sample-watcher-cron.md          illustrative local-only watcher config
  sample-report.md                expected output shape
```

The internal video/tooling and social-copy launch notes were moved out of the public repository so the repo stays focused on installable agent workflow materials.

## Launch checklist additions

Add these checks before public release:

- [ ] README contains early terms/account-boundary disclaimer.
- [ ] Search passes for risky terms: bypass, evade, credits, unlimited, exploit, jailbreak, ToS workaround.
- [ ] Public docs avoid raw transcripts, private repo names, screenshots with tokens, and account identifiers.
- [ ] Social/video copy uses local workflow framing and avoids credit/limit claims.
- [ ] Watcher prompts clearly prohibit secrets, permission dialogs, purchases, public posts, messages, and pushes without explicit scope.
- [ ] Demo uses toy/sanitized repos and blurred account/session names.

## Final recommendation

The repo is already mostly safe for public launch. The highest-leverage change is to put the boundary disclaimer in the first 10 lines of README and tune public hooks away from "babysitter/autonomous/overnight" toward "supervisor/operator/local agent ops". Keep the core story: this is a careful way to operate local coding sessions through existing app/account boundaries, with human control and verification rather than prompt spam or limit circumvention.
