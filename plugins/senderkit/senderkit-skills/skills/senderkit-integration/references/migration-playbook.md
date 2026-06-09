# Migration playbook

Use this when replacing or augmenting an existing provider.

Two valid end states — confirm which one the user wants before rewiring:

- **Replace** the current provider: SenderKit becomes the sender and the old provider is removed once parity is verified.
- **Route through** SenderKit: the app sends via SenderKit, which can deliver directly or through the existing provider, so the team keeps their provider relationship but removes single-vendor lock-in and gets one unified send/template/status surface.

Either way, the code-side change is the same — move send call sites behind a single SenderKit boundary. The mapping rules and rollout steps below apply to both.

## Inventory first

Create a quick table before changing code:

| Flow | Current provider call | Trigger | Template/content | Variables | Attachments | Scheduling | Metadata | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Include authentication emails, password resets, invitations, receipts, billing notices, product notifications, SMS codes, push notifications, and background jobs.

## Mapping rules

- Provider API key -> `SENDERKIT_API_KEY`.
- Provider template ID or local template component -> SenderKit `template` slug.
- Dynamic template data, substitutions, personalizations, or template variables -> SenderKit `vars`.
- Categories, tags, custom args, message attributes, metadata, or headers used for tracing -> SenderKit `metadata`.
- Provider message ID -> SenderKit response `id`; store it wherever the app reconciles delivery.
- Scheduled send timestamp -> the scheduling field defined in the current OpenAPI.
- Attachments -> email-only `attachments` with base64 `content`, `filename`, and `contentType`.
- Reply-to, cc, bcc -> email-only envelope fields.
- Raw subject/html/text -> SenderKit template if stable, raw email `content` if still migrating.

## Provider notes

### Resend

- Preserve idempotency keys if the app already uses them.
- React Email components usually become SenderKit dashboard templates or `@senderkit/react-email` migration inputs if that package is available.
- Resend examples cover many framework variants; keep each framework's server-side send location rather than moving sends into client code.

### SendGrid

- Map `dynamic_template_data` to `vars`.
- Map `custom_args` to `metadata`.
- Treat categories as analytics taxonomy; do not blindly copy high-cardinality values into category-like fields.
- Preserve event-webhook correlation by storing the SenderKit message ID.

### Postmark

- Map `TemplateAlias` or template IDs to SenderKit template slugs.
- Map `Metadata` to SenderKit `metadata`.
- Postmark webhooks are retried when a non-200 response is returned; keep webhook handlers fast and idempotent during migration.

### Mailgun

- Map `v:*` custom variables to SenderKit `metadata` when used for tracing, or `vars` when used for rendering.
- Preserve domain/from-address configuration and webhook verification behavior until SenderKit live sends are confirmed.

### AWS SES / SMTP

- SES `EmailTags`, message attributes, or SMTP custom headers used for traceability map to SenderKit `metadata`.
- If the current app builds MIME messages directly, migrate one flow at a time and verify attachments/inline images carefully.
- Keep fallback SMTP only if the product requirement calls for a local emergency path.

### SMS and push providers

- Twilio/SNS SMS body templates map to SenderKit SMS templates or raw SMS content.
- FCM/APNs/Expo notification title/body/data map to push templates or raw push content.
- Web push requires the serialized browser `PushSubscription` as `to`.

## Rollout strategy

1. Add SenderKit in test mode without deleting the old provider.
2. Render templates with representative variables and compare output to the old template.
3. Switch one low-risk flow behind a feature flag or config toggle.
4. Send to internal/test recipients first.
5. Store SenderKit message IDs and inspect them through the message/status endpoint defined in the current OpenAPI.
6. Move remaining flows in small batches.
7. Remove old provider configuration only after live parity and rollback plans are clear.

Avoid double-sending to real recipients. If shadow testing is needed, render without sending or send only to controlled test addresses.

## Webhooks

Do not invent SenderKit webhook payload or signature behavior. When adding webhooks:

- Use current SenderKit docs or dashboard examples.
- Verify signatures if SenderKit provides a signing secret.
- Acknowledge quickly and process asynchronously.
- Dedupe events by delivery/event ID if present, otherwise by a stable fingerprint plus timestamp window.
- Keep old-provider webhooks active until all sends for that provider are drained.
