# kreuzberg-cloud

Managed Kreuzberg document intelligence on `api.kreuzberg.dev` — async extraction with OCR, URL crawling, presigned uploads for large files, document versioning and diffing, signed webhook delivery, sandbox keys, and per-project usage tracking.

<!-- TODO: screenshot -->

## Install

### From the marketplace (recommended)

Pending review for official Claude marketplace.

Self-host:

```text
/plugin marketplace add kreuzberg-dev/plugins
/plugin install kreuzberg-cloud@kreuzberg
```

### v0.1.0 — skills only

The plugin v0.1.0 ships **skills and documentation only; no MCP server**. The `kreuzberg-cloud` CLI binary with MCP wiring lands in plugin v0.2.0. Agents call the HTTP REST API directly via curl or one of the official SDKs:

- **TypeScript/Node.js**: `@kreuzberg/cloud` ([npm](https://www.npmjs.com/package/@kreuzberg/cloud))
- **Python**: `kreuzberg-cloud-sdk` ([PyPI](https://pypi.org/project/kreuzberg-cloud-sdk/))

### API key requirement

Set the `KREUZBERG_API_KEY` environment variable or write `~/.kreuzberg/cloud.toml`:

```toml
api_key = "sk_live_..."
```

If neither is set, the plugin's SessionStart hook displays a reminder. For evaluation without signup, use sandbox keys (see the `sandbox-keys` skill).

## Skills shipped

| Skill | Trigger |
|-------|---------|
| **kreuzberg-cloud** | Managed Kreuzberg document intelligence at api.kreuzberg.dev. Use when the user wants cloud extraction with webhook delivery, presigned uploads for large files, document versioning and diffing, sandbox keys, or per-project usage tracking — instead of running the local kreuzberg CLI. Covers authentication, the 12 REST endpoints, request/response shapes, error model, and SDK options. |
| **offloading-extraction** | Use when the user wants to extract a document via the cloud rather than the local kreuzberg CLI. Covers POST /v1/extract — JSON vs multipart bodies, URL crawls, options block, webhook attachment, and the async response shape. |
| **tracking-cloud-jobs** | Use when an extraction job has been submitted and the result needs to be retrieved. Covers GET /v1/jobs/{id}, polling cadence with exponential backoff, terminal status detection, and webhook delivery (signature verification, retry semantics). |
| **versioning-documents** | Use when the user wants to retrieve a stored document and its result, list a document's versions, or diff two versions. Covers GET /v1/documents/{id}, /versions, and the sync-with-async-fallback diff at /diff plus its poll endpoint. |
| **presigned-uploads** | Use when the user has files larger than ~50 MB to extract via the cloud, or when base64-encoding the body would be wasteful. Covers the three-step presign / PUT / confirm flow against POST /v1/uploads/presign and POST /v1/uploads/confirm. |
| **managing-cloud-usage** | Use when the user asks about quota, billing visibility, or processed-page counts. Covers GET /v1/usage — query params, response shape, when to report usage proactively to the user. |
| **sandbox-keys** | Use when the user wants to try Kreuzberg Cloud without signing up, or needs an ephemeral key for evaluation, demos, or CI integration tests. Covers POST /v1/sandbox/key — the no-auth endpoint, quota, TTL, and cleanup expectations. |

## MCP tools

MCP wiring lands in v0.2.0. Until then, the v0.1.0 skills document the REST API directly with curl, TypeScript SDK, and Python SDK examples.

## Configuration

### Environment variable

```bash
export KREUZBERG_API_KEY="sk_live_..."
```

### Config file

Create `~/.kreuzberg/cloud.toml`:

```toml
api_key = "sk_live_..."
base_url = "https://api.kreuzberg.dev"  # optional
```

Precedence: CLI argument > environment variable > config file.

## Examples

Submit a document for extraction via curl:

```text
curl -X POST https://api.kreuzberg.dev/v1/extract \
  -H "Authorization: Bearer $KREUZBERG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/document.pdf"}'
```

Poll a job for completion with the TypeScript SDK:

```text
import { CloudClient } from "@kreuzberg/cloud";
const client = new CloudClient({ apiKey: process.env.KREUZBERG_API_KEY });
const job = await client.getJob(jobId);
console.log(job.status);  // "pending" | "processing" | "completed" | "failed"
```

Check quota with the Python SDK:

```text
from kreuzberg_cloud_sdk import Client
client = Client(api_key=os.getenv("KREUZBERG_API_KEY"))
usage = client.get_usage()
print(f"Pages processed: {usage.pages_processed}, Quota: {usage.quota}")
```

## Versioning

The plugin version tracks the marketplace `VERSION` file. See [CHANGELOG.md](../../CHANGELOG.md) for release notes.

## License

MIT.

## See also

- **Marketplace**: [kreuzberg-dev/plugins](https://github.com/kreuzberg-dev/plugins)
- **Upstream**: [kreuzberg-dev/kreuzberg-cloud](https://github.com/kreuzberg-dev/kreuzberg-cloud)
- **Sibling plugins**: [kreuzberg](../kreuzberg/README.md), [kreuzcrawl](../kreuzcrawl/README.md)
