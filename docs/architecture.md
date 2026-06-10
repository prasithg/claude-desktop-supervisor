# Architecture

Claude Desktop Supervisor treats long-running coding agents as execution lanes and Hermes as the supervisor/release manager.

```text
session metadata + JSONL logs -> Hermes classifier -> optional UI verification/action -> repo/test verification -> report/handoff
```

The design intentionally separates detection, action, verification, and publishing.

- Detection: session logs and transcript tails.
- Action: Computer Use or safe CLI resume.
- Verification: UI running proof plus git/tests.
- Publishing: human/Hermes-controlled personal account, not a local worker lane.
