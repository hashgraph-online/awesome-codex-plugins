# Baseline evidence

A baseline is a ledger record in `.nightshift/evidence/findings.jsonl` with
`domain` `baseline`. It preserves the originating source or evidence so a later
compare can see what changed. Write one per source class before the first fix
that answers that source. Reuse that `id` for every later record from the same
source.

Required fields are the finding schema's required keys. For a baseline, `details`
may carry `command`, `environmentDigest`, `rawDigest`, `scope`, `seen`,
`sourceClass`, and `versions`. Optional finding keys (`message`, `sources`, and
the rest) stay optional.

Never record secrets, private filesystem paths, or conversation content.

```json
{"schemaVersion":1,"id":"b-eslint","domain":"baseline","sourceClass":"eslint","source":"eslint --version","scope":"src/","severity":"info","confidence":"high","impact":"developer","status":"open","ladder":"declared","locator":"src/","digest":"baseline-eslint","firstSeen":"2026-09-09T00:00:00Z","lastChecked":"2026-09-09T00:00:00Z","action":"","host":"local","workTarget":"workspace","details":{"command":"eslint --version","scope":"src/","sourceClass":"eslint","seen":"clean"}}
```
