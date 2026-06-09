# SenderKit API contract usage

Do not treat this file as a frozen API reference. SenderKit's current REST contract is published as OpenAPI at:

```text
https://www.senderkit.com/openapi.yaml
```

Fetch that spec before implementing direct REST calls, writing examples, or generating clients. Use this file to remember how to consume the live contract safely.

## Fetch and compare

From a project using this skill:

```bash
python3 <skill-dir>/scripts/fetch_openapi.py
```

From the open-source GitHub checkout:

```bash
python3 skills/senderkit-integration/scripts/fetch_openapi.py
```

Inside the SenderKit app repo, compare the published spec with the checked-in copy:

```bash
python3 <skill-dir>/scripts/fetch_openapi.py --compare public/openapi.yaml
```

If this skill is installed outside the repo, adjust the script path to the installed skill directory.

## How to read the spec

Use the OpenAPI document for:

- `servers` to pick the correct base URL.
- `securitySchemes` for authentication.
- `paths` for endpoint methods, headers, request bodies, responses, status codes, and examples.
- `components.schemas` for exact field names, required fields, enum values, and attachment/channel shapes.
- `components.responses` for reusable errors such as unauthorized and rate limited responses.

When a project has `yq` available, inspect common paths with:

```bash
yq '.servers' /tmp/senderkit-openapi.yaml
yq '.paths | keys' /tmp/senderkit-openapi.yaml
yq '.components.schemas' /tmp/senderkit-openapi.yaml
```

Without `yq`, use the language's YAML parser or read the relevant sections directly.

## Stable integration principles

These are integration principles, not schema guarantees:

- Authenticate with a server-side API key from environment/config.
- Prefer template sends for product messaging and raw sends only for migration staging or highly dynamic content.
- Use idempotency for retryable sends when the current spec supports an idempotency header.
- Render templates before live sends when the current spec exposes a render endpoint.
- Store the returned SenderKit message ID when the app needs later reconciliation.
- Handle rate-limit responses according to the current spec, including any retry headers.

## SDK selection

Before installing a SenderKit SDK, verify the current official package name from docs or package metadata. If docs and examples disagree, use the OpenAPI REST fallback and leave a note in the implementation summary.
