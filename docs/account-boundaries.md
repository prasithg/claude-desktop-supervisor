# Account Boundaries

A useful supervisor keeps account authority explicit.

Recommended model:

- Worker lanes: local code edits, tests, docs, reports, local commits.
- Supervisor/Hermes/human: public GitHub repo creation, push, release, social posts, secrets, credentials, payment, external actions.

This protects against accidentally letting a locally authenticated worker lane publish under the wrong identity or touch external systems outside scope.
