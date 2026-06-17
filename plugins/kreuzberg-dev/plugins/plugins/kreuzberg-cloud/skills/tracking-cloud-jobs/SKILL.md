---
name: tracking-cloud-jobs
description: Use after a Kreuzberg Cloud job has been submitted and the user needs status, results, polling guidance, or webhook handling.
license: MIT
---

# Tracking cloud jobs

Cloud extraction is asynchronous. A submit request returns job identifiers, and the final result arrives through polling or webhook delivery.

## Polling

Use exponential backoff with a sensible timeout. Stop when the job reaches a terminal state:

- completed
- partial success
- failed
- cancelled

Surface failed and partial-success states clearly. When a result is available, preserve metadata that helps the user correlate output to the original document.

## Webhooks

Use webhooks when the caller can receive HTTP callbacks or when jobs may run for a long time. Webhook handlers must be idempotent because delivery can be retried.

For production webhooks, require signature verification with a signing value stored as a secret. Reject deliveries whose signature does not match.

## Crawl jobs

Crawl submissions can return crawl job identifiers that later fan out to per-document extraction jobs. Track the crawl job first, then follow each returned document job until terminal.
