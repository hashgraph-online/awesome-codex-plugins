# Source notes

This skill was built from:

- SenderKit open-source skills repository: `https://github.com/senderkit/senderkit-skills`
  - Reusable integration skill folder: `skills/senderkit-integration/`
  - License: MIT.
- SenderKit public site: `https://www.senderkit.com/`
  - Describes SenderKit as a CMS for transactional notifications.
  - Shows template-slug sends with variables.
  - Mentions multi-channel templates, versioning, locales, SDKs, CLI, and webhooks.
- SenderKit OpenAPI contract:
  - Official published URL: `https://www.senderkit.com/openapi.yaml`
  - Local app repo copy: `public/openapi.yaml`
  - Treat the published URL as source of truth and compare the local copy when working in the SenderKit repo.
- SenderKit README from this repo: `README.md`
  - Documents the TypeScript quickstart, `@senderkit/sdk`, `@senderkit/cli`, `@senderkit/react-email`, and OpenAPI source of truth.
- Resend docs and skill examples:
  - Multi-language quickstarts and examples are useful as a pattern for broad framework coverage.
  - The public Resend skill highlights idempotency keys, webhook verification, language detection, and common mistakes.
- Postmark webhook docs:
  - Useful webhook reliability pattern: protect webhook endpoints, acknowledge correctly, and account for provider retries.

Prefer the current published OpenAPI and SenderKit docs over this source note when they differ.
