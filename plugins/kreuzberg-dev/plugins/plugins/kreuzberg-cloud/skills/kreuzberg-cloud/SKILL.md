---
name: kreuzberg-cloud
description: Use when the user wants managed document extraction, webhook delivery, presigned uploads, sandbox evaluation, or usage tracking instead of running local Kreuzberg extraction.
license: MIT
metadata:
  author: kreuzberg-dev
  version: "0.1.0"
  repository: https://github.com/kreuzberg-dev/kreuzberg-cloud
---

# Kreuzberg Cloud

Kreuzberg Cloud is the hosted extraction service for documents that should be processed outside the local machine. Use it only when the user explicitly wants a remote extraction workflow or when local extraction is not practical.

Before sending any local file, document bytes, document URL, or extracted content to the hosted API, confirm that the user wants to use the cloud service. For confidential, air-gapped, or no-network work, use the local `kreuzberg` plugin instead.

## Preferred clients

Use the official SDKs when writing executable examples:

- TypeScript/Node.js: `@kreuzberg/cloud`
- Python: `kreuzberg-cloud-sdk`

Raw HTTP request shapes are useful for explaining the API, but avoid creating shell snippets that upload files without an explicit user approval step.

## Authentication

Use the `KREUZBERG_API_KEY` environment variable or the SDK's supported credential configuration. Never commit production or sandbox keys to source control.

## Routing

Use the focused skills for detailed workflows:

- `offloading-extraction` for submitting documents or URLs.
- `tracking-cloud-jobs` for polling status or receiving callbacks.
- `presigned-uploads` for large-file upload flows.
- `managing-cloud-usage` for quota and billing visibility.
- `sandbox-keys` for short-lived evaluation credentials.

## Response handling

Cloud extraction is asynchronous. Treat submit responses as job handles, then retrieve results through the job-tracking workflow or webhook delivery. Do not assume content is ready immediately after submission.
