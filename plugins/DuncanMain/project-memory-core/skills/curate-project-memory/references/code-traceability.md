# Code traceability

Relate knowledge to code with stable repository IDs and relative paths:

```yaml
code_references:
  - repository: service-api
    path: src/auth/service.ts
    relation: implemented-by
    revision: optional-commit
```

Allowed relation values are `affects`, `implemented-by`, `verified-by`, `configured-by`, and `invalidated-by`. Omit revision when the knowledge applies across revisions.

For simple machine-readable retrieval, also include a flat list when code references exist:

```yaml
code_paths:
  - src/auth/service.ts
```

Keep the structured references authoritative; `code_paths` is a portable search index. Update both together.

When changing a referenced file, inspect linked accepted decisions. When a change makes a decision inaccurate, add a conflict or supersession candidate instead of altering the decision silently.
