# Unified AI System: Self-Hosted AI Gateway & MCP Server

<p align="center">
  <strong>Open-source AI gateway for deterministic prompt enhancement, governed execution, and reproducible verification.</strong>
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">zh-CN</a> |
  <a href="https://happy520ai.github.io/unified-ai-system/">Project Site</a>
</p>

<p align="center">
  <a href="https://github.com/happy520ai/unified-ai-system">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/happy520ai/unified-ai-system?style=flat-square&label=Stars" />
  </a>
  <a href="https://github.com/happy520ai/unified-ai-system/actions/workflows/ci.yml">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/happy520ai/unified-ai-system/ci.yml?branch=master&style=flat-square&label=CI" />
  </a>
  <a href="https://github.com/happy520ai/unified-ai-system/releases/latest">
    <img alt="Release" src="https://img.shields.io/github/v/release/happy520ai/unified-ai-system?style=flat-square" />
  </a>
  <a href="https://registry.modelcontextprotocol.io/v0.1/servers/io.github.happy520ai%2Funified-ai-system/versions/0.5.0">
    <img alt="Official MCP Registry: active" src="https://img.shields.io/badge/Official_MCP_Registry-active-1f883d?style=flat-square" />
  </a>
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/happy520ai/unified-ai-system?style=flat-square" />
  </a>
</p>

<p align="center">
  <img
    src="docs/assets/readme-hero.png"
    alt="Unified AI System — self-hosted AI gateway with 12 governed MCP tools, 900+ tests, 16 blocked attack classes, zero credentials to try"
    width="100%"
  />
</p>

Unified AI System turns a rough request into a structured, reviewable prompt before execution. It gives teams one self-hosted surface for OpenAI-compatible SDKs, MCP, A2A, CLI, and HTTP while keeping provider calls explicit — with the feature set you'd expect from a commercial LLM gateway: virtual keys with token budgets, exact + semantic response caching, reverse MCP governance with REST→MCP generation, and production observability.

## Try Before Installing

<p align="center">
  <a href="https://happy520ai.github.io/unified-ai-system/#enhance?prompt=Build+a+small+API+for+my+team&amp;profile=coding&amp;language=en">
    <img
      src="docs/assets/prompt-enhancement-demo.png"
      alt="Unified AI System turns a rough request into a structured coding prompt"
      width="100%"
    />
  </a>
  <br />
  <sub>The original request stays visible. The local enhancer adds execution requirements, output requirements, and completion criteria.</sub>
</p>

[**Open a ready-to-run coding example in the browser Prompt Lab**](https://happy520ai.github.io/unified-ai-system/#enhance?prompt=Build+a+small+API+for+my+team&profile=coding&language=en)

The link loads a real request and renders the enhanced prompt locally. No
account, API key, or provider call is required.

Run the same proof against the published container:

```bash
docker run --rm ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0 pnpm gateway demo "Build a small API for my team" --enhance --profile coding --evidence
```

The evidence confirms that the original request was preserved, the result is
deterministic, and `providerCalled=false`. Codex, VS Code, Claude Code, Gemini
CLI, OpenCode, Cursor, Cline, Continue, and generic stdio clients can reach the
same gateway through twelve governed MCP tools. The source build also provides a
protocol-tested MCP Streamable HTTP endpoint for clients that connect by URL.

Useful in a real workflow? [Star the repository](https://github.com/happy520ai/unified-ai-system) or [share one reproducible result](https://github.com/happy520ai/unified-ai-system/issues/new?template=usage-verification-report.yml&title=%5BUsage%20Report%5D%20Quickstart).

## The Gateway at a Glance

<p align="center">
  <img
    src="docs/assets/readme-architecture.png"
    alt="Architecture: OpenAI/Anthropic SDKs, MCP clients, A2A, CLI, and HTTP enter one gateway that adds prompt enhancement, virtual keys, exact + semantic cache, reverse MCP governance, observability, and audit — providers stay behind a three-gate whitelist with the fake provider as the credential-free default"
    width="100%"
  />
  <br />
  <sub>Clients keep their native protocols; the gateway adds keys, budgets, cache, and audit. Twelve governed MCP tools are inspectable from any MCP client.</sub>
</p>

## Choose Your First Path

| Your goal | Start here | What you get |
| --- | --- | --- |
| Try it before installing | [Browser Prompt Lab](https://happy520ai.github.io/unified-ai-system/#enhance) | A local, deterministic preview with no account or API key. |
| Verify the published runtime | [60-second Docker demo](#try-it-in-60-seconds) | A disposable fake-provider run with visible evidence and cleanup. |
| Connect an agent client | [Codex and MCP quickstart](https://happy520ai.github.io/unified-ai-system/codex-mcp-docker-quickstart.html) | A pinned MCP container and twelve inspectable tools. |
| Choose a client path | [MCP compatibility matrix](docs/mcp-client-compatibility.md) | Install commands, first checks, and honest evidence boundaries. |
| Integrate with an application | [Prompt enhancement guide](https://happy520ai.github.io/unified-ai-system/prompt-enhancement.html) | CLI, HTTP, SDK, curl, Python, and JavaScript paths. |
| Keep an existing OpenAI client | [OpenAI-compatible API](docs/openai-compatible-api.md) | Point `baseURL` at `/v1` for Chat Completions, function tools, Responses, streaming, and model discovery. |
| Connect another agent | [A2A v1.0 gateway](docs/a2a-protocol.md) | Discover an Agent Card and execute tracked fake-provider tasks over JSON-RPC. |
| Check client runtime certification | [Client runtime certification](docs/client-runtime-certification.md) | Current evidence-backed catalog state: 52 verified, 2,084 pending manual evidence, and 0 failed across 2,136 unique entries. |
| Run mainstream certification one-by-one | [Client runtime certification](docs/client-runtime-certification.md) | Run `node tools/verify-client-runtimes-serial.mjs --client tag:mainstream` for sequential reports and explicit manual evidence states. |
| Run global protocol coverage | [Client runtime certification](docs/client-runtime-certification.md) | Run `node tools/run-global-client-discovery.mjs --source-manifest docs/client-runtime-catalog-sources-worldwide.json --execute --serial --max 0`. |
| Run strict global certification | [Client runtime certification](docs/client-runtime-certification.md) | Add `--require-manual-evidence --manual-evidence docs/client-runtime-evidence.example.json` to fail on missing manual proof. |
| Inspect the enhancement contract | [Credential-free evaluation](docs/prompt-enhancement.md#prompt-enhancement-evaluation) | Eight representative cases for profiles, languages, signals, determinism, and zero provider calls. |
| Diagnose a first-run problem | [Troubleshooting matrix](docs/first-run-troubleshooting.md) | Shell-specific checks without exposing credentials. |
| Verify an MCP client | [MCP client report](https://github.com/happy520ai/unified-ai-system/issues/new?template=mcp-client-report.yml) | Record one Codex, Cursor, Cline, or generic stdio run with a small evidence set. |
| Contribute or report a run | [Usage report](https://github.com/happy520ai/unified-ai-system/issues/new?template=usage-verification-report.yml) or [good first issue #106](https://github.com/happy520ai/unified-ai-system/issues/106) | A reproducible feedback path for users and maintainers. |

## Gateway Capabilities

Everything below runs from the same self-hosted process — opt-in and
fake-provider-first, so you can try every feature with zero credentials:

<p align="center">
  <img
    src="docs/assets/readme-capabilities.png"
    alt="Capability cards: OpenAI + Anthropic APIs, virtual keys and budgets, exact + semantic cache, reverse MCP governance, chat-native observability, local-first RAG, provider governance, and a 16-attack security regression"
    width="100%"
  />
</p>

| Capability | What you get | Docs |
| --- | --- | --- |
| OpenAI + Anthropic + Gemini compatible APIs | `/v1/chat/completions` (SSE streaming, tools), `/v1/messages` with **native Anthropic streaming**, the native **Gemini generateContent** adapter, the Responses API, and model discovery — keep your existing SDK, change only the base URL. | [OpenAI-compatible API](docs/openai-compatible-api.md) · [Gemini](docs/gemini-provider.md) |
| Virtual keys + budgets | Issue `uai-` keys with periodic token budgets (daily/monthly windows), per-key request limits, soft-budget alerts, spend attribution, and instant revocation. Consumers never hold provider keys. | [Virtual keys](docs/virtual-keys.md) · [Spend reporting](docs/spend-reporting.md) |
| Response cache — exact + semantic | Tenant-scoped hot-path caching with byte-identical JSON/SSE replay, an opt-in semantic layer for paraphrased requests, TTL and size caps, and a full audit trail. | [Response cache](docs/response-cache-hot-path.md) |
| Guardrails — deterministic & local | Input/output scans: pasted secrets block, PII redacts, injection phrasings warn, banned terms and size limits enforce — no cloud tier, no extra credentials, <0.2 ms measured overhead, runtime-configurable per rule. | [Guardrails](docs/guardrails.md) |
| Reverse MCP governance | Aggregate upstream MCP servers (Streamable HTTP and stdio) behind one authenticated, audited, allow-listed surface — plus **REST→MCP**: any OpenAPI 3 spec becomes governed MCP tools. | [Reverse MCP governance](docs/reverse-mcp-governance.md) |
| Observability | Chat-specific Prometheus metrics on `/metrics` — tokens per model, cache hit rates, TTFT histograms, virtual-key rejections, guardrail findings — plus an opt-in Langfuse export and a per-key spend report API/CLI. | [Observability](docs/observability-export.md) |
| Vector retrieval | A credential-free deterministic embedding provider and the SQLite vector store activate `mode: "vector"` RAG with strict tenant isolation. | [Providers & knowledge](docs/providers.md) |
| Provider governance | A three-gate whitelist matrix for real providers, a runtime credential store (SHA-256 at rest), request cost guards, circuit breakers, and fallback chains. | [Provider enablement](docs/real-provider-enablement.md) |
| Enterprise governance + security drills | JWT auth, RBAC, tenant isolation with audit hash chains — verified by a repeatable 16-attack live security regression. | [Security drill](tools/security-attack-regression.mjs) |

Published infrastructure benchmark (fake provider, single node): chat JSON p50 **15.6 ms**, SSE TTFT p50 **2.8 ms**, **402 req/s** at concurrency 8, cache hits **5.6× faster** than misses — see the [gateway benchmark](docs/benchmarks/2026-08-gateway-benchmark.md).

## Why People Use It

- Prompt enhancement for teammates who do not write perfect prompts.
- Clean-clone verification without credentials or hidden setup.
- Provider-free HTTP examples for curl and Python's standard library.
- OpenAI SDK, CLI, HTTP API, shared SDK, MCP, Codex, Cursor, Cline, and Continue entry points.
- Clear boundaries: no AGI claim, no L5 claim, no silent provider behavior.
- Protocol-first onboarding: any OpenAI-compatible MCP, A2A, or HTTP client can be onboarded
  via a short setup + reproducible report path; we prioritize verification over marketing claims.

## Try It in 60 Seconds

<p align="center">
  <img
    src="docs/assets/readme-terminal.png"
    alt="Terminal proof: one docker run command prints the enhanced prompt with providerCalled=false evidence and exits clean"
    width="100%"
  />
</p>

Verify the project without signing in:

```bash
docker run --rm ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0 pnpm gateway demo
```

Expected behavior:

- local fake-provider execution
- visible `execution: fake`
- deterministic output
- no API key or account needed
- container exits automatically

One-command natural-language enhancement preview:

```bash
docker run --rm ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0 \
  pnpm gateway demo "Build a small API for my team" --enhance --profile coding --evidence
```

This starts an isolated fake-provider gateway, enhances the request locally,
prints the structured prompt, and cleans up without an API key.

You can also pipe a request directly into the published image without cloning
the repository:

```bash
printf '%s' "Plan a launch for a small API" \
  | docker run --rm -i ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0 \
      pnpm --silent gateway demo --enhance --profile planning --language en --json
```

PowerShell equivalent for a request file:

```powershell
Get-Content .\request.txt -Raw |
  docker run --rm -i ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0 `
    pnpm --silent gateway demo --enhance --profile planning --language en --json
```

The container still uses the disposable fake-provider path and exits after the
result is printed.

Use `--language zh-CN` or `--language en` when the enhancement output should
follow an explicit language instead of automatic detection.

Prompt enhancement example:

Start the gateway first (from a source checkout):

```bash
pnpm gateway serve
```

Then, in another terminal:

```bash
pnpm gateway enhance "Build a small API for my team" --profile coding
pnpm gateway chat "Build a small API for my team" --enhance --profile coding
```

The CLI also accepts a request from stdin, which is useful for shell pipelines
and text files:

```bash
printf '%s' "Plan a launch for a small API" \
  | pnpm gateway enhance --profile planning --language en
cat request.txt | pnpm gateway enhance --profile auto --json
```

PowerShell users can pipe the same path with `Get-Content .\request.txt -Raw`.

### Existing OpenAI SDKs

Start the source gateway with `pnpm gateway serve`, then keep your existing
OpenAI client and change only its base URL:

```js
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://127.0.0.1:3100/v1",
  apiKey: process.env.PME_AUTH_TOKEN || "local-development",
});

const result = await client.chat.completions.create({
  model: "local-fake-model",
  messages: [{ role: "user", content: "Build a small API for my team" }],
});

console.log(result.choices[0].message.content);
```

The credential-free gate verifies this path with the official OpenAI
JavaScript SDK `7.4.0`. With the source gateway running, reproduce it with:

```bash
node docs/examples/openai-sdk-chat.mjs
```

The focused compatibility layer supports text completions, streaming, model
listing, and optional local prompt enhancement. See the
[OpenAI-compatible API guide](docs/openai-compatible-api.md) for Python,
supported fields, auth behavior, and explicit limitations.

Prefer Node.js? The dependency-free example verifies the provider-free response
before printing the enhanced JSON:

```bash
node docs/examples/prompt-enhancement.mjs "Help me plan a small API for my team" --profile planning --language en
```

Prefer Go? The standard-library example checks provider-free readiness and
prints JSON evidence before showing the enhanced prompt:

```bash
go run docs/examples/prompt-enhancement.go "Help me plan a small API for my team" --profile planning --language en
```

For a no-clone prompt-enhancement walkthrough, start the published gateway
image and follow the [provider-free curl example](docs/examples/prompt-enhancement-curl.md):

```bash
read -rsp "Enter a random gateway token (32+ characters): " PME_AUTH_TOKEN
printf '\n'
export PME_AUTH_TOKEN
docker run --rm --publish 127.0.0.1:3100:3100 \
  --env AI_GATEWAY_SERVICE_HOST=0.0.0.0 \
  --env AI_GATEWAY_PROVIDER_MODE=fake \
  --env AI_GATEWAY_REAL_PROVIDER_ENABLED=false \
  --env PME_ENTERPRISE_AUTH_ENABLED=true \
  --env PME_AUTH_TOKEN \
  ghcr.io/happy520ai/unified-ai-system/ai-gateway-service:0.5.0
```

Keep that process running while you send the curl request. The response
includes `metadata.providerCalled=false`. For a credential-free HTTP stream,
use the [curl SSE example](docs/examples/streaming-chat-curl.md) to inspect
`start`, `chunk`, and `done` events with `executionMode=fake`.
The gateway refuses non-loopback listening when authentication is disabled;
see the [critical attack-chain hardening report](docs/security-hardening-attack-chain.md).

## Use It

### Terminal Workflow

After `pnpm install`:

```bash
pnpm gateway serve
pnpm gateway status
pnpm gateway doctor
pnpm gateway chat "Hello from Unified AI System"
```

### MCP / Codex / Cursor / Cline

Published MCP command:

```bash
codex mcp add unified-ai-system -- docker run --rm -i ghcr.io/happy520ai/unified-ai-system/mcp-server:0.5.0
```

Restart Codex, run `/mcp verbose` to verify the twelve tools, then follow the
[60-second Codex MCP quickstart](https://happy520ai.github.io/unified-ai-system/codex-mcp-docker-quickstart.html) for a safe first
prompt-enhancement call and removal command.

For MCP clients that connect by URL, the source build provides a loopback-only
Streamable HTTP endpoint:

```bash
pnpm mcp:http
# http://127.0.0.1:3210/mcp
```

See the [MCP server guide](packages/mcp-server/README.md#streamable-http) for
remote-bind authentication and the published-release boundary.

### Installable Agent Skill

```bash
codex plugin marketplace add happy520ai/unified-ai-system --ref master
npx skills add happy520ai/unified-ai-system --skill unified-ai-gateway --agent codex --copy --yes
```

The plugin pins the [reviewed immutable v0.4.9 MCP image](docs/security/mcp-image-review-0.4.9.md)
and starts it without container networking or Linux capabilities.

Skill hub: https://skills.sh/happy520ai/unified-ai-system/unified-ai-gateway

For local source work:

```bash
git clone https://github.com/happy520ai/unified-ai-system.git
cd unified-ai-system
corepack enable
corepack prepare pnpm@9.15.4 --activate
pnpm install --frozen-lockfile
pnpm verify:public-clone
pnpm gateway demo
```

For a prepared cloud workspace, use [GitHub Codespaces](https://codespaces.new/happy520ai/unified-ai-system?quickstart=1). See the value first:

```bash
pnpm gateway demo "Build a small API for my team" --enhance --profile coding --evidence
```

For the complete credential-free clone check, run `pnpm verify:public-clone`
after the demo. The repository's devcontainer keeps the default path
provider-free. Codespaces availability and usage limits are controlled by
GitHub.

### Docker Compose

For a source checkout, start the gateway with a readiness check:

```bash
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:3100/health/check
```

The service becomes `healthy` only after `/health/check` responds successfully.
When finished, stop it with:

```bash
docker compose down
```

The Compose file treats `.env` as optional and leaves provider behavior explicit;
the credential-free fake-provider path remains the default.

## Share a Verified Result

If the project helps your workflow, run one reproducible path, [star the
repository](https://github.com/happy520ai/unified-ai-system), and share the
smallest useful result through the [structured Usage Report](https://github.com/happy520ai/unified-ai-system/issues/new?template=usage-verification-report.yml).

For a ready-to-review CLI packet, append `--evidence` to the enhanced demo:

```bash
pnpm gateway demo "Build a small API for my team" --enhance --profile coding --evidence
```

Review the original request and output before sharing the generated JSON. The
packet also records `detectedSignals` and the item count for each
`compiledSections` entry, so a reviewer can see which request signals were
carried into the structured prompt without reading internal logs.

For the browser Prompt Lab, use its `Copy evidence` or `Download evidence`
action, then paste or attach the JSON in the optional Prompt Lab evidence field
of the same report.
Use `Copy share link` when you want another browser to reproduce the same local
input, profile, and language; review the prompt first because the URL fragment
contains the input text.

## Next Steps

- [Documentation](docs/README.md) for setup, the CLI, prompt enhancement, and providers.
- [Codex MCP quickstart](https://happy520ai.github.io/unified-ai-system/codex-mcp-docker-quickstart.html) for the fastest agent-tool integration; the [source guide](docs/codex-mcp-quickstart.md) is kept in the repository.
- [Contributing guide](CONTRIBUTING.md) for focused changes and safe verification.
- [Usage Report template](.github/ISSUE_TEMPLATE/usage-verification-report.yml) for reproducible feedback.
- [Cite this project](CITATION.cff), [Roadmap](ROADMAP.md), and [Support](SUPPORT.md).

## Honest Boundaries

We separate what is verified from what is not claimed:

- Clean clone + fake-provider path: **Yes**
- Hosted public API: **No**
- Real provider execution by default: **No**, must be explicitly enabled
- Browser chat UI in this repo: **No** (CLI/API/MCP are first-class)
- Production ready / AGI / L5: **Not claimed**

Real provider calls are disabled by default. Configure safely via `.env.example` and `docs/providers.md`.

## Verify the Project

```bash
pnpm check
pnpm test
pnpm check:public
pnpm verify:public-clone
pnpm verify:mcp
```

CI on `master` runs Linux checks, container startup smoke tests, MCP discovery, and process-cleanup checks.

## Project Links

- [Official MCP Registry entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.happy520ai%2Funified-ai-system/versions/0.5.0)
- [Release v0.5.0](https://github.com/happy520ai/unified-ai-system/releases/tag/v0.5.0)
- [Codex MCP server README](packages/mcp-server/README.md)
- [Roadmap](ROADMAP.md)
- [Vision](VISION.md)
- [Support](SUPPORT.md)

## Star History

If the gateway saves you a proxy migration or an afternoon of prompt cleanup,
[a star](https://github.com/happy520ai/unified-ai-system/stargazers) helps
more people find it.

[![Star History Chart](https://api.star-history.com/svg?repos=happy520ai/unified-ai-system&type=Date)](https://star-history.com/#happy520ai/unified-ai-system&Date)
