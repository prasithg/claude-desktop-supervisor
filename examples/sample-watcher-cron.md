# Sample Watcher Cron

```text
cronjob(
  action='create',
  name='Claude Desktop local supervisor',
  schedule='every 2m',
  deliver='local',
  skills=['claude-desktop-babysitting','agent-session-progress','macos-computer-use'],
  enabled_toolsets=['terminal','computer_use','skills','file'],
  prompt=<customized watcher prompt from templates/failsafe-watcher-cron-prompt.md>
)
```

Always run once immediately after creation. Create a separate end-of-window report job.
