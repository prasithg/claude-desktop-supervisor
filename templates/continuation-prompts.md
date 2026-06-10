# Continuation Prompts

## Generic direct continuation

```text
Continue from the current state; do not use /loop. Use existing context and do a quick continuation scan: git status, current diff, recent tests, and the relevant docs/files.

Act as a high-agency local build partner. Finish the current milestone. If it is complete and context is healthy, choose the next highest-leverage adjacent local/reversible improvement and build it. Run focused tests and summarize exactly what changed.

Avoid secrets, live external services, public/user-facing actions, and permission dialogs. If a step needs those, build the local stub/spec/runbook instead and report the enablement step.
```

## Closeout/handoff prompt

```text
Close out this lane; do not start a new large implementation slice. Run focused checks, summarize what now works, changed files, tests/reports, blockers, context concerns, and the exact next prompt for a fresh session. If appropriate, make a local commit; do not push publicly.
```
