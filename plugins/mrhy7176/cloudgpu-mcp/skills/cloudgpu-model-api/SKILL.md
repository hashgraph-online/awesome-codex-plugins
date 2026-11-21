---
name: cloudgpu-model-api
description: Call a hosted model through CloudGPU's OpenAI-compatible model API at https://cloudgpu.app/v1, without renting a GPU. Use when the user wants to call a hosted model (chat/completions) through CloudGPU, wire CloudGPU into an OpenAI-compatible client or agent framework (OpenAI SDK, LangChain, Cline, Roo Code, Continue, Aider, n8n, Dify), or mentions cloudgpu.app/v1.
---

# CloudGPU model API

CloudGPU (cloudgpu.app) serves hosted models over an OpenAI-compatible API at `https://cloudgpu.app/v1`. No GPU rental is needed.

## 1. Pick a model ID

- Call the `list_models` tool, or `GET https://cloudgpu.app/v1/models` (public, no key needed).
- Never guess or hardcode a model ID. Use one the list returns.

## 2. Authenticate

- Send `Authorization: Bearer $CLOUDGPU_API_KEY`.
- Read the key from the environment. Never print it, and never write it into files that get committed.
- If `CLOUDGPU_API_KEY` is not set, ask the user to create a key at https://cloudgpu.app and set it themselves. Do not ask them to paste it into the chat.

## 3. Set up a client

In any OpenAI-compatible SDK, client or agent framework, set `base_url` to `https://cloudgpu.app/v1` and the API key to the value of `CLOUDGPU_API_KEY`.

Python (OpenAI SDK):

```python
import os
from openai import OpenAI

client = OpenAI(base_url="https://cloudgpu.app/v1", api_key=os.environ["CLOUDGPU_API_KEY"])
resp = client.chat.completions.create(
    model="kimi-k3",  # example only: check list_models or /v1/models first
    messages=[{"role": "user", "content": "Say hello."}],
)
print(resp.choices[0].message.content)
```

The same request as HTTP. Read the key from the environment; do not paste it into the request text you show the user.

- `POST https://cloudgpu.app/v1/chat/completions`
- `Authorization: Bearer` followed by the value of `CLOUDGPU_API_KEY`
- `Content-Type: application/json`
- Body: `{"model":"<id from the model list>","messages":[{"role":"user","content":"Say hello."}]}`

The model id in any example is only an example. Check the model list before using it.

## Prices and balance

Don't quote prices from memory. Current prices are at https://cloudgpu.app/api. The same API key and balance also cover GPU rental (see the `cloudgpu` skill).

## Errors

- **401:** the key is missing or wrong. Check that `CLOUDGPU_API_KEY` is set and valid.
- **404 / model not found:** the model ID is not available. Re-run `list_models` and use an ID from the list.
- **429:** too many requests. Back off, then retry.
