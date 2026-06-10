# Failure Modes

Real issues this pattern is meant to catch:

1. Prompt is typed but not submitted.
2. The UI looks alive but the session is idle.
3. A final summary mentions “blocked” even though the task completed.
4. A prompt appends a user event to logs but no assistant turn starts.
5. Desktop prompt overlay becomes stale and Return does nothing.
6. Sidebar rows reorder after a session becomes Running.
7. Old handoff sessions share cwd/title with fresh current sessions.
8. Context closeout gets looped into the same old session.
9. Logs lag behind GUI verification by one tick.
10. Public release credentials are accidentally delegated to the wrong agent/account.
