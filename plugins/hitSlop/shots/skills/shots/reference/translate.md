# Screenshot Localization

Use `screenshots.translate` to localize an existing screenshot while preserving
the approved visual system.

## Resolve

- Ask for source screenshot id and target locale if missing.
- If the user gives a job id, call `jobs.get`, confirm it is complete, and use
  the generated screenshot id.

## Localize Copy

- Preserve the panel role and product promise.
- Adapt idioms and word order for the locale instead of direct word-for-word
  translation.
- Keep headlines short enough for screenshot readability.
- Do not redesign the campaign unless the user asks for locale-specific
  positioning.

When the user also wants App Store metadata, save localized title, subtitle,
description, and keywords with `apps.update_listing` for the target locale.

## Present

After completion, show screenshot id, CDN URL, and the review link returned or
described by the hosted MCP instructions.
