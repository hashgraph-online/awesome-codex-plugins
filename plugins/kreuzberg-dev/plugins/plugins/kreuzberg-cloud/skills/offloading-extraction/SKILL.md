---
name: offloading-extraction
description: Use when the user wants to submit documents or URLs to Kreuzberg Cloud rather than extracting locally.
license: MIT
---

# Offloading extraction

Use cloud extraction when local processing is unavailable, when files live behind remote URLs, when server-side parallelism is useful, or when webhook delivery is required.

Always confirm before uploading local files or document contents to the hosted service.

## Submission model

Cloud extraction accepts document files, document URLs, and extraction options. A submit call returns one or more job identifiers. The actual extraction result is delivered later through job polling or webhook delivery.

Use the official SDKs for executable code. A typical SDK flow is:

```text
1. Load the API key from KREUZBERG_API_KEY or a local secret store.
2. Ask the user to confirm cloud processing for local files.
3. Submit a document, URL, or batch with extraction options.
4. Store the returned job identifiers.
5. Hand off to the tracking-cloud-jobs workflow.
```

## Options

The cloud options mirror the local extraction configuration:

- output format: markdown, text, JSON, Djot, or HTML
- OCR backend and language choices
- table and image extraction preferences
- chunking configuration
- webhook delivery metadata

## Webhooks

If the caller provides a webhook destination, include a signing value managed as a secret. The receiver must verify the signature before trusting the payload.

## Errors

Common outcomes:

- bad request: missing document, URL, or unsupported MIME type
- unauthorized: missing or invalid API key
- payload too large: switch to the presigned upload workflow
- rate limited or quota exhausted: use the usage workflow to show current limits
