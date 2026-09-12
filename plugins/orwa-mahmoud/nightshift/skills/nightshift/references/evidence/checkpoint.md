# Checkpoint evidence

A checkpoint is a ledger record in `.nightshift/evidence/findings.jsonl` with
`domain` `checkpoint`. It records recoverable intermediate state before a risky
cluster — a migration, a codemod, a provisioning step, anything whose undo is
not obvious. Name the touched paths, the rollback reference when one exists, and
the verification that still remains.

Required fields are the finding schema's required keys. For a checkpoint,
`details` may carry `artifacts`, `baseline`, `head`, `plan`, `rollback`,
`touched`, and `worktreeDigest`. Optional finding keys stay optional.

Never record secrets, private filesystem paths, or conversation content.

```json
{"schemaVersion":1,"id":"c-codemod","domain":"checkpoint","sourceClass":"codemod","source":"codemod plan","scope":"src/","severity":"info","confidence":"high","impact":"developer","status":"open","ladder":"declared","locator":"src/","digest":"checkpoint-codemod","firstSeen":"2026-09-09T00:00:00Z","lastChecked":"2026-09-09T00:00:00Z","action":"","host":"local","workTarget":"workspace","details":{"touched":["src/resolve.ts"],"rollback":"HEAD","plan":"containment before normalize","baseline":"b-eslint"}}
```
