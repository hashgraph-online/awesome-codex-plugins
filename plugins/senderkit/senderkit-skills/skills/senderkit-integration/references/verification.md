# Verification checklist

Use this before finalizing a SenderKit integration.

## Local checks

- `SENDERKIT_API_KEY` is read from environment/config and never exposed to client bundles.
- `.env.example`, deployment docs, or secret manifests mention the new key without real values.
- The code has one local SenderKit client/provider boundary.
- Tests mock the local boundary or HTTP client.
- All migrated flows include stable idempotency keys.
- All migrated flows preserve recipient, template variables, metadata, scheduling, attachments, cc/bcc/reply-to, and unsubscribe/suppression behavior where relevant.

## API checks

Fetch the current OpenAPI contract first:

```bash
python3 <skill-dir>/scripts/fetch_openapi.py
```

When running from the open-source GitHub checkout, use `python3 skills/senderkit-integration/scripts/fetch_openapi.py`.

Run or implement equivalents for:

1. The current spec's workspace/API-key context endpoint with the configured key.
2. The current spec's template render endpoint with representative variables.
3. A test-mode send through the current spec's send endpoint with an idempotency key when supported.
4. Repeat the same send with the same idempotency key and verify no duplicate semantic send is created.
5. The current spec's message-list/status endpoint filtered by template, metadata, or the closest supported query.

If a project cannot call external services in tests, keep network calls out of unit tests and document the manual verification command.

## Runtime checks

- Timeouts are configured.
- `429` reads and respects `Retry-After`.
- 4xx validation errors are logged with stable codes, not secrets or message bodies.
- Background jobs retry safely without duplicate sends.
- Live mode is gated by the right environment/deploy config.
- Observability records the SenderKit message ID and app flow/entity IDs.

## Final response expectations

When reporting completion, include:

- Files changed.
- Which provider flows were migrated or left in place.
- How to set `SENDERKIT_API_KEY`.
- Tests or commands run.
- Any manual SenderKit dashboard/docs step still required, such as creating templates, publishing live versions, or configuring webhooks.
