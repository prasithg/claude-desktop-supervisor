# Security and Privacy

This project is designed for local agent supervision. It may inspect local Claude/Codex metadata and transcript tails to classify whether a lane is running, idle, blocked, or done.

Those local files can contain private prompts, source code, command output, file paths, and auth-adjacent details.

## Rules for users and agents

- Do not publish raw transcripts.
- Do not paste unredacted helper output into public issues.
- Do not commit screenshots or captures unless they have been reviewed for secrets, account names, private project names, and local paths.
- Do not click permission dialogs, type secrets, post publicly, push code, or create releases unless the human explicitly scoped that action.
- Prefer compact status summaries over transcript text.

## Reporting security issues

Please open a minimal issue if the report can be public-safe. If it involves private data exposure or credentials, contact the repository owner privately instead of posting details in an issue.
