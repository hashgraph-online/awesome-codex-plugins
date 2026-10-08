---
name: runtype-external-agents
description: 'Connect agents that run outside Runtype (Flue, Cloudflare Agents SDK, Vercel AI SDK, LangGraph, OpenAI Agents SDK, Mastra, OpenClaw, Hermes, Pi, custom loops) through OpenTelemetry/OTLP trace export or an A2A or runtype-stream endpoint, to get runs, traces, eval capture, Persona chat, or surfaces; not Runtype-hosted execution.'
user-invocable: true
argument-hint: '[framework and what you want from Runtype: traces, evals, chat UI]'
---

# Runtype for agents that run elsewhere

Runtype is a suite of components, not only a hosted runtime. An agent that runs on the
user's own infrastructure can still use Runtype's Runs and Logs, trace trees, cost
estimates, eval capture, Persona chat UI, surfaces, and the MCP-driven improvement loop.
Pick the lane that serves what the user wants, set it up, and say plainly what each lane
does not do.

If the Runtype MCP server is connected, read
`get_platform_documentation(topic="external-agents")` first. It is the live version of
this skill. Public docs: `https://docs.runtype.com/developer-guides/guides/bring-your-own-agent`.

## Pick a lane (they compose)

| User wants                                                                | Lane                                                                                                 |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| See runs, traces, tokens, cost; capture real runs as eval cases           | **A. Push telemetry in** (OTLP to `https://api.runtype.com/v1/otel`)                                 |
| Test the agent from Runtype, put a Persona chat or surface in front of it | **B. Let Runtype call the agent** (`external` agent, `runtype-stream` or A2A endpoint)               |
| Run an agent authored in Runtype on their own cloud                       | **C. Export** (`export_agent_runtime`, Enterprise plan; do not propose for hackathons or free tiers) |

An exported agent (lane C) reports its runs to Runtype over OTLP with no extra code. Set
`RUNTYPE_API_KEY` (a `TELEMETRY:WRITE` key) on the deployment. `RUNTYPE_TELEMETRY=off`
stops reporting, and `RUNTYPE_TELEMETRY_CONTENT=off` drops messages and tool payloads. The
export call itself needs a key with `RUNTIME:EXPORT`. Guide:
`https://docs.runtype.com/developer-guides/guides/self-hosting`.

Capability matrix to state plainly:

- Eval **capture** (`add_eval_case_from_execution`) needs a transcript on the run: message
  content on the spans (`gen_ai.input.messages` / `gen_ai.output.messages`, or a supported
  framework's own attributes). `@runtypelabs/flue-otel` 0.5 and later sends it by default
  (`content: false` turns it off). Version 0.4 and earlier never did.
- OpenClaw, Hermes, and the Pi coding agent send no conversation content by default. Set
  `RUNTYPE_CAPTURE_CONTENT=true` for OpenClaw and Pi or
  `RUNTYPE_OTEL_CAPTURE_CONTENT=true` for Hermes. If the plugin receives no
  content, the run has no transcript to capture as an eval case. The Pi durable
  binding sends content unless `content: false`.
- Eval **re-run** (`run_eval_suite`) needs Runtype to be able to call the agent. An
  `external` agent over A2A works (recorded-tool replay cases are skipped).
  `runtype-stream` endpoints are not eval targets. Telemetry-only runs cannot be re-run.
- The "fix" step is a change in the user's repository, never `update_agent`.
- `POST /v1/executions/ingest` accepts JSON and produces the same run and trace tree as
  OTLP. Use it only when the agent cannot export OpenTelemetry spans.

## Prerequisites

1. **Fastest path:** the dashboard's **Connect an existing agent** page (`/agents/connect`)
   creates or picks the agent, creates a telemetry key, and shows copy-ready setup for each
   framework. Its **Copy setup prompt** action gives the same setup as markdown for a
   coding agent, with a placeholder instead of the key.
2. Otherwise, an agent record that owns the runs: `create_agent` (a plain agent with a
   model is a fine attribution target) or an `external` agent for lane B. Read the
   `agent_...` id back from `list_agents`.
3. A telemetry API key with the **Telemetry Ingest** permission group (`TELEMETRY:WRITE`,
   append-only), created on the dashboard **API Keys** page (`/settings/api`) or on the
   connect page. Keys with `AGENTS:WRITE` also work. No MCP tool creates API keys. Where the
   account offers `request_api_key`, calling it with `["TELEMETRY:WRITE"]` files a request
   that a human approves. Never paste key values into chat. Write them to `.dev.vars`,
   `wrangler secret put`, or the user's secret store.

## Lane A recipes

**Flue on Cloudflare Workers (zero code).** Workers Observability traces a Flue v2 app
deployed with `@flue/vite` and `@cloudflare/vite-plugin` automatically. It emits
`invoke_agent`, `chat`, and `execute_tool` spans in GenAI semantic conventions, with
conversation content on by default. Export them to Runtype:

1. In the Cloudflare dashboard, open **Workers Observability** and add a destination: type
   Traces, endpoint `https://api.runtype.com/v1/otel/v1/traces`, headers
   `Authorization: Bearer rt_...` and `x-runtype-agent-id: agent_...`. OTLP export needs a
   Workers Paid plan.
2. In `wrangler.jsonc`:
   `{ "observability": { "traces": { "enabled": true, "destinations": ["runtype"], "head_sampling_rate": 1 } } }`
3. Run `npx vite build && npx wrangler deploy`, run one conversation, and confirm it with
   `list_runs` (filter `agent_id`) and `trace_execution`.

To keep prompts and tool payloads out of the export, add
`instrument(createCloudflareTracing({ content: false }))` from `@flue/runtime/cloudflare`
at module scope in `app.ts`. Tell the user this also removes eval capture. Think apps use
the same destination. They store no payloads unless the agent class sets
`storeMessages = true` and `storeTools = true`.

**Cloudflare Agents SDK (`agents`).** Runtype has no dedicated adapter for it. Use the
generic OpenTelemetry setup under **Any other OpenTelemetry-instrumented agent**.

**OpenClaw native plugin.** The plugin sends OTLP itself. Do not add a separate
OpenTelemetry SDK. Review the package and its requested capabilities before
granting conversation access. Install it with
`openclaw plugins install @runtypelabs/openclaw-adapter`.

Set `RUNTYPE_AGENT_ID` and a `TELEMETRY:WRITE` key in `RUNTYPE_API_KEY` on the
Gateway process. `RUNTYPE_OTLP_URL` changes the full OTLP trace URL from its
`https://api.runtype.com/v1/otel/v1/traces` default. Use only a trusted
receiver because it receives the telemetry key. Run
`openclaw plugins enable runtype` and
`openclaw config set plugins.entries.runtype.hooks.allowConversationAccess true --strict-json`,
then restart the Gateway. JSON inspection can expose environment values. Run
`openclaw plugins inspect runtype --runtime` without `--json`.

The `chat` span represents an OpenClaw attempt, not each provider call. The plugin
waits up to one second for pending `llm_output` after `agent_end`, but it has no
durable retry queue. Content is off by default. With `RUNTYPE_CAPTURE_CONTENT=true`, the
plugin sends bounded, redacted messages and tool payloads only when OpenClaw
supplies them. It omits a content value over 32 KiB after redaction, but the
redactor cannot identify every secret. A run without a transcript cannot
become an eval case. This plugin does not make OpenClaw callable from Runtype.

**Hermes native plugin.** The Hermes observer plugin sends OTLP itself. Do not add
a separate OpenTelemetry SDK. Install and enable it with
`hermes plugins install runtypelabs/hermes-runtype-otel --enable`. Set `RUNTYPE_AGENT_ID`
and a `TELEMETRY:WRITE` key in `RUNTYPE_OTEL_API_KEY` on the Hermes process.
`RUNTYPE_OTEL_ENDPOINT` changes the full OTLP trace URL from its
`https://api.runtype.com/v1/otel/v1/traces` default. Use only a trusted
receiver because it receives the telemetry key. Restart a running gateway with
`hermes gateway restart`. For a CLI test, run
`hermes chat --oneshot -q "Reply with one sentence"`.

Content is off by default. `RUNTYPE_OTEL_CAPTURE_CONTENT=true` sends bounded,
redacted messages and tool payloads for transcripts and eval capture. The plugin
limits message text and tool results to 4,096 characters and model input to the
last 16 messages. It omits tool arguments whose redacted JSON exceeds 4,096
characters. The filter cannot identify every secret. This plugin does not make
Hermes callable from Runtype. Hermes can return a provider error before it emits
`on_session_end`; `api_request_error` may recover, so a long-running gateway
cannot immediately export that failed turn as terminal.

**Pi (`@runtypelabs/pi-otel`).** One package, two bindings. Both send OTLP/JSON
themselves; do not add an OpenTelemetry SDK. Each Pi run becomes one Runtype run
(`invoke_agent`, one `chat` per model response, one `execute_tool` per tool result), and
Runtype prices it from the model name. The pi-durable peer is minor-locked to `~1.0.0`, and
pi-durable and `PiHarness` are experimental/beta upstream.

- Pi coding agent: `pi install npm:@runtypelabs/pi-otel`. Set `RUNTYPE_API_KEY`
  (`TELEMETRY:WRITE`) and `RUNTYPE_AGENT_ID` in the shell that starts `pi`;
  `RUNTYPE_OTLP_URL` overrides the full trace URL. Content is off by default because
  sessions carry source code; `RUNTYPE_CAPTURE_CONTENT=true` turns on transcripts and
  eval capture. A run is one prompt until `agent_settled`. `RUNTYPE_DEBUG=true` prints
  why nothing is sent.
- pi-durable, including Cloudflare `PiHarness`: `npm install @runtypelabs/pi-otel`, then
  `observePiDurable(harness, { agentId, apiKey, harnessId })` from `@runtypelabs/pi-otel/durable`
  (`harnessId` is a stable id for the storage, e.g. `ctx.id.toString()` in a Durable Object)
  right after `Harness.open`, then `await observer.recover(context)` before work resumes
  so a run a restart interrupted stays in the same trace. With `PiHarness`, do both
  inside the harness factory before returning the harness; never via `harness.pi()`,
  which resolves after resumed work has started. In the Worker call
  `ctx.waitUntil(observer.flush())` after each prompt. One input submission is one
  run; `unanswered` is a failed run. Content is on by default; `content: false`, per-kind
  switches, `maxChars` and `redact` narrow it.

Report each Pi run through one producer only, or Runtype counts its tokens twice. Neither
binding makes the agent callable from Runtype.

**Flue on Node, Cloud Run, or another host.** Point exactly one Flue instrumentation at
Runtype. Two would double the tokens and cost.

- `@runtypelabs/flue-otel` 0.5 or later: `instrument(createRuntypeFlueInstrumentation())`.
  By default it sends the transcript, the system prompt, and tool arguments and results.
  Each kind has an off switch, and `content: false` sends none. It also sends an exact
  iteration count, a run-level stop reason, and summed usage. Prefer this package: it gives
  eval capture and exact loop structure together.
- `@flue/opentelemetry`: `instrument(createOpenTelemetryInstrumentation())`. It exports the
  conversation by default. Runtype derives the loop structure from Flue's `flue.*`
  attributes, without the exact iteration count or run-level stop reason.

The app owns the OTel SDK: `NodeTracerProvider`, `BatchSpanProcessor`, and
`OTLPTraceExporter({ url: 'https://api.runtype.com/v1/otel/v1/traces', headers: { Authorization: 'Bearer ' + key } })`.
Call `provider.register()`, or every span becomes its own trace. Attribute runs with
`runtypeFlueResourceAttributes({ agentId })` or the `x-runtype-agent-id` header. Call
`await provider.forceFlush()` before a serverless handler returns. The app also installs
`@flue/runtime` itself, which needs Node 22.19 or later.

**Frameworks with OpenTelemetry instrumentation.** Each framework in this table
needs an OpenTelemetry provider and exporter behind its instrumentation.
Instrumentation alone emits spans that nothing sends, and the run never appears.
Runtype reads each framework's own attributes, so no `gen_ai.*` code is needed.
Set the exporter with the env vars below, except for Mastra.

| Framework         | Install                                                                                                      | Enable                                                                                                                                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vercel AI SDK     | `@opentelemetry/sdk-node`, `@opentelemetry/exporter-trace-otlp-proto`                                        | `const sdk = new NodeSDK({ traceExporter: new OTLPTraceExporter() }); sdk.start()`, shut the SDK down before exit, and pass `experimental_telemetry: { isEnabled: true, functionId: 'my-agent' }` per call |
| LangGraph         | `openinference-instrumentation-langchain`, `opentelemetry-exporter-otlp-proto-http`                          | `LangChainInstrumentor().instrument(tracer_provider=provider)`                                                                                                                                             |
| OpenAI Agents SDK | `openinference-instrumentation-openai-agents`, `opentelemetry-exporter-otlp-proto-http`                      | `OpenAIAgentsInstrumentor().instrument(tracer_provider=provider)`                                                                                                                                          |
| Mastra            | `@mastra/core`, `@mastra/observability`, `@mastra/otel-exporter`, `@opentelemetry/exporter-trace-otlp-proto` | An `OtelExporter` in the `Mastra` constructor's `observability` config, and `await mastra.shutdown()` in a `finally` around the run                                                                        |

Mastra's exporter ignores `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS`.
Pass `endpoint` (the full `https://api.runtype.com/v1/otel/v1/traces` path) and `headers`
to `OtelExporter` directly. For `http/protobuf`, install
`@opentelemetry/exporter-trace-otlp-proto` too. Without it, the exporter logs one console
error and sends nothing.

**Any other OpenTelemetry-instrumented agent.** Use the stock env vars, HTTP only (no gRPC):

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.runtype.com/v1/otel
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer rt_...,x-runtype-agent-id=agent_...
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

Runtype reads spans whose `gen_ai.operation.name` is `invoke_agent`, `chat`, or
`execute_tool` (an HTTP root span above them is fine), and the GenAI content attributes.
Attribution per trace, in order: the `runtype.agent.id` resource attribute, the
`x-runtype-agent-id` header, then `runtype.agent.id` on the `invoke_agent` span. Keep one
agent invocation per trace.

Traces create runs. OTLP logs are kept in **Logs** only when they name an agent (resource
attribute or header); unattributed log records get a `partial_success` and are dropped.
Metrics are acknowledged but not stored.

The run detail shows a telemetry chip: **Structure**, **Transcript**, or **Full detail**.
Transcript needs message content on the spans, which eval capture also needs. Full detail
also needs `runtype.adapter.version` and `runtype.tools.reported` on the exporter.

## Lane B recipe

Register the endpoint so Runtype can call it. `create_agent` (MCP) input:

```json
{
  "name": "Support agent (Flue)",
  "agent_type": "external",
  "external_config": {
    "endpoint": "https://my-worker.example.workers.dev/dispatch",
    "protocol": "runtype-stream",
    "framework": "flue",
    "auth": { "type": "bearer", "credentials": "{{secret:MY_AGENT_TOKEN}}" },
    "timeoutMs": 120000
  }
}
```

The REST API (`POST /v1/agents`) and SDK take `agentType` and `externalConfig`; the fields
inside `externalConfig` are the same.

- `auth.type` is `none`, `bearer`, `api_key` (sent in `headerName`, default `X-API-Key`),
  or `basic` (`credentials` goes after `Basic ` as given, so pass the encoded value).
- `timeoutMs` (1,000 to 300,000; default 30,000) covers the connection and the whole
  streamed response. Set it above the slowest turn, or long turns fail partway through.
- `retryCount` (0 to 10; default 3) retries the connection only, never a stream that has
  started.
- `framework` is a descriptive label (`flue`, `langchain`, `vercel_ai`, `crewai`,
  `cloudflare`, `autogen`, or `custom`). It does not change the wire protocol.

**Where to register.** The dashboard's **Connect External** tab on the new-agent page
registers A2A endpoints only. Register a `runtype-stream` agent with `create_agent` or
`POST /v1/agents`.

**`runtype-stream` endpoints.** Runtype sends `POST {endpoint}` with
`{ "messages": [...], "context": { "conversationId": "..." }, "metadata": {...} }`.
`messages` holds the full conversation history (`role` and `content`) on every call. An
endpoint that keeps its own session state, such as a Flue session keyed by
`conversationId`, must dispatch only the newest user message.

The endpoint streams `text/event-stream` frames in Runtype's unified vocabulary:
`execution_start` first, then text and tool frames, then one terminal
`execution_complete` or `execution_error`. Each frame's `id:` mirrors a 0-based `seq`. The
schemas are the `ExecutionStreamEvent` union in the public OpenAPI spec, the same stream
`execute_agent` returns for a hosted agent. Report cost and tokens as `totalCost` and
`totalTokens` on `execution_complete`; the run shows no cost or tokens otherwise. In a
Flue 2 app, the route runs the turn with `init(agent, { id: conversationId })` and
`handle.dispatch(message)`, and maps each chunk from `handle.read(receipt, { onEvent })`
onto a frame.

**A2A endpoints.** Omit `protocol` (or set `"a2a"`). The endpoint's origin must serve an
agent card at `/.well-known/agent-card.json`, or set `agentCardUrl`. Registration fetches
the card and fails with `502` if it cannot. `runtype-stream` endpoints skip this step.

Then run `execute_agent` to test, add the agent to a product as a capability, or run
`generate_persona_embed_code` for a chat widget.

## Improvement loop for an external agent

1. Observe: `list_runs` with the owning agent's `agent_id` (ingested runs have `otel-...`
   execution ids and `source: "ingested"`; timings and cost are what the agent reported),
   or `list_logs`.
2. Diagnose: `trace_execution`. Quote the failing iteration, tool call, or model turn.
3. Capture: `get_eval_capture_preview`, then `add_eval_case_from_execution`
   (`create_eval_suite` first if needed). No capturable content means the export lacks
   message content.
4. Fix: propose the change in the user's agent code and show it.
5. Verify: `run_eval_suite` when Runtype can call the agent over A2A. Otherwise, re-run the
   scenario against the redeployed agent and inspect the new run. The captured cases stay
   the regression record either way.

## Troubleshooting

Lane A (OTLP export):

- `curl -X POST https://api.runtype.com/v1/otel/v1/traces -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"resourceSpans":[]}'`
  returns `200 {}` when the key and endpoint are right.
- `401`: the key is invalid. `403`: the credential is not an API key, or the key has
  neither `TELEMETRY:WRITE` nor `AGENTS:WRITE`.
- `413`: the export is over 8 MiB after decompression, or has more than 10,000 spans or more
  than 100 traces. Lower the exporter's max export batch size.
- `415`: use `http/protobuf` or JSON, with gzip, deflate, or no compression.
- `429`: the account's ingest rate or concurrency limit is reached. Retry after `Retry-After`.
- `503`: Runtype could not accept the export right now, and it was not stored. Retry.
- `200` means Runtype accepted the export; the run can take a short time to appear. If it
  never appears, call `GET /v1/telemetry/ingest-health?traceId=<hex>` with a separate key
  that has `ANALYTICS:READ` or `AGENTS:READ`. A `TELEMETRY:WRITE` key cannot read it.
- Run stuck "in flight": the closing `invoke_agent` span was never flushed.
- `ambiguous_agent_attribution`: two invocations in one trace, or no attribution source.
  Set the resource attribute or header.
- No run after an attributed export: the trace has no GenAI operation, model or inference
  signal, or recognized Runtype execution telemetry. Runtype keeps the trace in Logs.
- Doubled tokens and cost: two instrumentations export to the same endpoint.
- Tool calls appear without arguments or results: tool content capture is off on the
  producer. Check its `content` or tools option.
- `partial_success` in the exporter log: some traces named an agent the key cannot use.
  The other traces were stored.

Lane B (`runtype-stream`):

- "External agent stream is not conformant: [CODE] ...": the stream breaks the event
  structure. The code names the rule, for example `NO_EXECUTION_START_FIRST`,
  `SEQ_NOT_MONOTONIC`, `EVENT_AFTER_TERMINAL`, or `NO_TERMINAL`. Check the event order and
  `seq`.
- "External agent stream ended without a terminal event": send `execution_complete` or
  `execution_error` last.
- Output missing with no error: Runtype drops frames that fail schema validation. Validate
  each frame against `ExecutionStreamEvent`.
- A stream fails when it exceeds 20,000 events, 8 MiB in total, or 1 MiB in one frame.
- A turn fails partway through: raise `timeoutMs`.

## Avoid these mistakes

- Do not promise eval re-runs for telemetry-only or `runtype-stream` agents.
- Do not send both Flue instrumentations to Runtype.
- Do not use `POST /v1/telemetry/ingest`. It is deprecated and produces no run, trace
  tree, or transcript.
- Do not recommend `export_agent_runtime` or self-hosting for an agent that already
  exists elsewhere, or for non-Enterprise accounts.
- Do not put key values in chat, commits, or generated code. Use secrets.
