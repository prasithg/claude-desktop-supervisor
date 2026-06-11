# Contributing

Thanks for helping improve Claude Desktop Supervisor.

## What is useful

- Better install docs for Hermes, Claw, and other agent runners.
- Public-safe fixtures and smoke tests.
- Safer state classification rules.
- Clearer watcher prompts and failure modes.
- Better examples that avoid private transcripts and local machine details.

## Before opening a PR

Run:

```bash
bash scripts/validate.sh
```

## Privacy expectations

Do not include raw Claude/Codex transcripts, private project names, credentials, screenshots with account details, or personal local paths in issues or PRs.

Use small synthetic fixtures when adding tests.
