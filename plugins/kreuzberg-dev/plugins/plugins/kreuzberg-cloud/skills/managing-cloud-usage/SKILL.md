---
name: managing-cloud-usage
description: Use when the user asks about quota, billing visibility, or processed-page counts. Covers GET /v1/usage — query params, response shape, when to report usage proactively to the user.
---

# Managing cloud usage

`GET /v1/usage` is the only endpoint for quota and billing visibility.
It returns aggregate counters for the queried period plus the remaining
quota for the project.

## Endpoint

```text
GET https://api.kreuzberg.dev/v1/usage
Authorization: Bearer $KREUZBERG_API_KEY
```

### Query parameters

| Param | Format | Default |
|---|---|---|
| `start` | ISO-8601 date (e.g. `2026-03-01`) | First day of current month. |
| `end` | ISO-8601 date (e.g. `2026-04-01`) | First day of next month. |

Both are optional. Omit both for the current calendar month.

## Response (200)

```json
{
  "period_start": "2026-05-01",
  "period_end": "2026-06-01",
  "total_pages": 5432,
  "total_documents": 87,
  "total_failed": 2,
  "quota_limit": 100000,
  "quota_remaining": 94568,
  "by_mime_type": {
    "application/pdf": { "documents": 65, "pages": 3200, "failed": 1 },
    "image/png":       { "documents": 15, "pages": 1800, "failed": 0 },
    "text/plain":      { "documents":  7, "pages":  432, "failed": 1 }
  }
}
```

### Reading the response

- `total_pages` — pages billed in the period. The unit of cost.
- `total_documents` — files submitted, regardless of page count.
- `total_failed` — extractions that ended in `failed` status. Failed
  jobs do not consume quota.
- `quota_limit` / `quota_remaining` — total and remaining pages on the
  current plan.
- `by_mime_type` — per-MIME breakdown. Useful for identifying which
  document types drive cost.

## Examples

### Current-month usage

```bash
curl -s https://api.kreuzberg.dev/v1/usage \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" | jq .
```

### Specific date range

```bash
curl -s "https://api.kreuzberg.dev/v1/usage?start=2026-01-01&end=2026-02-01" \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" | jq .
```

### Quota remaining as a percentage

```bash
curl -s https://api.kreuzberg.dev/v1/usage \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  | jq '.quota_remaining * 100 / .quota_limit'
```

## When to report usage to the user

Pull usage proactively when:

- A batch job submits more than ~100 documents — report `quota_remaining`
  after submit so the user can see the impact.
- The user asks "how much have I used?" or any quota-shaped question.
- A `429` response includes a quota-exhausted error — surface the usage
  shape so the user can decide whether to upgrade.
- After a long-running crawl finishes, since page count is hard to
  estimate up front.

Don't report usage on every routine extraction — it's noise.

## Errors

| Status | Cause |
|---|---|
| `400` | `start` or `end` not ISO-8601, or `end <= start`. |
| `401` | Bad API key. |
