---
name: managing-cloud-usage
description: Use when the user asks about quota, billing visibility, processed-page counts, or whether a cloud workflow may exceed limits.
license: MIT
---

# Managing cloud usage

Use the usage workflow to show processed pages, document counts, failures, and remaining quota for the current project.

## When to check usage

- before a large batch
- after a large batch
- when a user asks about quota or billing visibility
- after a rate-limit or quota-exhaustion response
- after long crawls where page count was hard to estimate

## Reporting

Keep the report concise:

- pages processed in the period
- documents processed in the period
- failed extractions
- quota limit and remaining quota
- notable MIME-type breakdowns when relevant

Do not report usage after every routine extraction unless the user asked for it.
