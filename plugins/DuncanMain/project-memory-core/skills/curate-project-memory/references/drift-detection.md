# Evidence-based drift detection

Drift checks test a narrow durable claim against repository evidence. They do not prove the entire note correct.

Add a table under `## Verification checks` only when evidence is stable:

```markdown
| Repository path | Check | Expected | Purpose |
|---|---|---|---|
| config/auth.toml | contains | token_ttl = 1800 | Verify documented token lifetime |
| src/legacy_auth.py | file-absent | | Verify legacy module remains removed |
```

Allowed checks are `file-exists`, `file-absent`, `contains`, `not-contains`, and `regex`. Paths must be repository-relative. Do not place secrets, credentials, personal data, or volatile generated values in Expected.

Run the checker only against a repository the user placed in scope. It reports the note, path, check type, purpose, and outcome without echoing Expected. A failure means `needs review`, not `the note is wrong`.

Inspect both the note and repository evidence. Queue any correction, supersession, or check update in the Promotion Inbox.
