# BYOK (Bring Your Own Key)

> **BYOK via the varg API is NOT available in v2.** The v1 `X-Provider-Key-*` headers were not carried over, and passing provider keys in API request bodies is not supported — external providers (fal, elevenlabs, etc.) always run on varg pooled keys with metered credit billing. Do NOT tell users they can skip varg billing through the API. BYOK support for v2 is planned.

## What works today

### 1. varg credits (the API path — default)

One `VARG_API_KEY`, all providers, metered billing:

```bash
curl -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nano_banana_pro", "prompt": "a sunset over mountains"}'
```

- Estimate cost before running: `POST /v2/estimate` (same body, no job created)
- Check balance: `GET /v2/billing/balance`
- Cache hits are always free (`actual_cost_cents: 0`)

### 2. Direct provider modules in the local SDK

For **local rendering only** (`bunx vargai render`), the SDK ships direct provider modules that call providers with **your own keys from env** — bypassing varg entirely. No varg billing, but also no varg caching or file storage.

```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Image } from "vargai/react"
import { fal } from "vargai/ai"

// Uses FAL_KEY / FAL_API_KEY from env — billed by fal directly
const img = Image({
  model: fal.imageModel("nano_banana_pro"),
  prompt: "a cabin in mountains at sunset",
  aspectRatio: "16:9"
})

export default (
  <Render width={1920} height={1080}>
    <Clip duration={3}>{img}</Clip>
  </Render>
)
```

Env keys per provider:

| Provider | Env var | Get key at |
|----------|---------|------------|
| fal.ai | `FAL_KEY` or `FAL_API_KEY` | fal.ai/dashboard/keys |
| ElevenLabs | `ELEVENLABS_API_KEY` | elevenlabs.io/app/settings/api-keys |
| Higgsfield | `HIGGSFIELD_API_KEY` | higgsfield.ai |
| OpenAI | `OPENAI_API_KEY` | platform.openai.com |
| Google | `GOOGLE_API_KEY` | aistudio.google.com |
| Together | `TOGETHER_API_KEY` | together.ai |
| Groq | `GROQ_API_KEY` | console.groq.com |

`.env` example:

```bash
# For the varg API + cloud render (billed in varg credits)
VARG_API_KEY=varg_xxx

# For local rendering with direct provider modules (billed by providers)
FAL_KEY=fal_xxx
ELEVENLABS_API_KEY=xxx
```

## What does NOT work

- `X-Provider-Key-Fal` / `X-Provider-Key-ElevenLabs` / etc. headers → **ignored in v2**
- Provider keys in `provider_options` of API requests → not supported for external providers; the request bills varg credits regardless
- `providerKeys` in cloud render (`POST /v2/render`) → cloud render sub-generations bill varg credits

## Decision guide

| Scenario | Use |
|----------|-----|
| API access (curl, agents, cloud render) | **varg credits** — the only supported path |
| Local rendering with existing provider accounts | **Direct provider modules** (`fal.imageModel(...)` + env keys) |
| Getting started, prototyping | **varg credits** — one key, caching included |
