# findings.json

Write the review to `findings.json`, then run `abliterate report --in findings.json`. Fix every error it prints and run it again until it passes. The same file feeds SARIF (GitHub code scanning) and the PR comment.

```json
{
  "version": 1,
  "scope": { "base": "main", "head": "<sha>", "states": ["push", "index", "worktree"], "complete": true },
  "findings": [
    {
      "id": "ABL-1",
      "title": "SQL injection in user search",
      "status": "confirmed",
      "severity": "high",
      "confidence": "high",
      "cwe": ["CWE-89"],
      "snapshot": "push",
      "source": "review",
      "location": { "path": "src/routes/users.js", "startLine": 12 },
      "trace": [
        { "path": "src/routes/users.js", "startLine": 11, "note": "source: req.query.q, any visitor" },
        { "path": "src/routes/users.js", "startLine": 12, "note": "sink: interpolated into db.query text" }
      ],
      "rule": "Values reach SQL only as bound parameters",
      "actor": "Unauthenticated visitor of GET /users",
      "impact": "Reads or alters any table the app's database role can reach.",
      "evidence": "No parameter binding, escaping or allowlist between req.query.q and db.query; the route has no auth middleware.",
      "fix": "db.query('... ILIKE $1', ['%' + term + '%'])",
      "test": "With a fake database adapter and the synthetic name O'Brien, assert that the query text stays constant and that the name is passed as a separate bound value."
    }
  ]
}
```

## Fields

| Field | Values | Rule |
| --- | --- | --- |
| `status` | `confirmed`, `needs-evidence`, `pre-existing` | `confirmed` needs `fix` and `test`. `needs-evidence` needs `decisiveEvidence`: the single fact that would decide it. `pre-existing` = present in the base, not made worse by the change. |
| `severity` | `critical`, `high`, `medium`, `low` | Reason from actor × reach × effect, see methodology.md. |
| `confidence` | `high`, `medium`, `low` | How complete the trace is, not how bad the bug is. |
| `snapshot` | `push`, `index`, `worktree`, `file` | The state in which the finding exists. `file` = a single file reviewed without a Git base. |
| `source` | `review`, `deps`, `variants` | `deps` requires `advisory` (`id`, `ecosystem`, `package`, `version`, optional `fixed`, `aliases`, `kev`, `epss`). |
| `location.path` | relative path | Relative to the repo root, no `..`. Lines are 1-based. |
| `scope.complete` | boolean | `false` when part of the perimeter could not be read: the report then says "review incomplete". |

Only `confirmed` and `pre-existing` reach SARIF. Disproved candidates are not listed at all. Never put secret values in any field: cite location and type only.
