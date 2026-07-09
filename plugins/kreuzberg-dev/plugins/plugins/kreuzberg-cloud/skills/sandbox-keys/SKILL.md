---
name: sandbox-keys
description: Use when the user wants to try Kreuzberg Cloud without signing up, or needs an ephemeral key for evaluation, demos, or CI integration tests. Covers POST /v1/sandbox/key — the no-auth endpoint, quota, TTL, and cleanup expectations.
---

# Sandbox keys

`POST /v1/sandbox/key` issues ephemeral, anonymous API keys. Use these
for evaluation, demos, and integration smoke tests — never for production
workloads.

## What you get

| Property | Value |
|---|---|
| Format | `sk_sandbox_*` |
| TTL | 24 hours from issue |
| Quota | 50 pages, hard cap |
| Auth required to mint | None |
| IP throttle | 10 keys per IP per 24 hours |

The 50-page quota is per key, not per IP. The IP throttle prevents abuse
of the no-auth mint endpoint.

## Endpoint

```text
POST https://api.kreuzberg.dev/v1/sandbox/key
```

No `Authorization` header — this is the only authenticated-by-omission
endpoint in the API.

## Response (200)

```json
{
  "api_key": "sk_sandbox_ABC123DEF456GHI789JKL012MNO345PQR678STU901VWX234",
  "expires_at": "2025-12-21T10:00:00Z",
  "pages_remaining": 50
}
```

After 24 hours or 50 pages — whichever comes first — the key returns
`401` on every endpoint. The key is not renewable; mint a fresh one.

## Examples

### Mint and use

```bash
KREUZBERG_API_KEY=$(curl -sX POST https://api.kreuzberg.dev/v1/sandbox/key \
  | jq -r .api_key)

curl -sX POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "documents":[{"filename":"hi.txt","mime_type":"text/plain","data":"aGVsbG8="}],
    "options":{"extraction_config":{"output_format":"markdown"}}
  }'
```

### TypeScript SDK

```ts
import { KreuzbergCloud } from "@kreuzberg/cloud";

const client = await KreuzbergCloud.fromSandbox();
const result = await client.extractAndWait({
  file: new Blob(["Hello world"], { type: "text/plain" }),
});
console.log(result.result?.content);
```

`fromSandbox()` mints a key under the hood and configures the client.

### Python SDK

```python
import asyncio
from kreuzberg_cloud import AsyncKreuzbergCloud

async def main() -> None:
    async with await AsyncKreuzbergCloud.from_sandbox() as client:
        job = await client.extract_and_wait(file=b"hello world")
        print(job.status, job.result and job.result.content)

asyncio.run(main())
```

## When to recommend sandbox vs production keys

| Use sandbox | Use production |
|---|---|
| First-time evaluation, no signup yet | Anything user-facing or business-critical |
| Local smoke tests, demos | CI on the main branch |
| One-off doc to test the API surface | Recurring batch pipelines |
| Onboarding flow that bootstraps an SDK | Any workload >50 pages |

If the user already has a production key, do not silently switch to a
sandbox key — production keys carry the right quota, billing, and
project-scoped resources.

## Cleanup

Sandbox keys self-expire after 24 hours. No revocation endpoint exists —
nothing to clean up. Do not commit sandbox keys to version control even
though they're short-lived; treat them like any other credential.

## Errors

| Status | Cause |
|---|---|
| `429` | IP has minted 10 keys in the last 24 hours. Wait or use a production key. |
| `500` | Server-side mint failure; retry with backoff. |
