---
name: codex-image-plugin
description: Generate or edit raster images through an OpenAI-compatible image API. Use when the user provides an image API URL and key, asks to use a configured image model, lists available image models, or requests new images, reference-image edits, compositing, masks, cleanup, mockups, or illustrations.
---

# Codex Image Plugin

Use `scripts/image.py` as the API wrapper. It accepts an explicit endpoint URL, API key, and model, or reads them from `OPENAI_BASE_URL`/`OPENAI_API_KEY`/`IMAGE_MODEL` and the active Codex provider in `~/.codex/config.toml` (`base_url`, `OPENAI_API_KEY`, `image_model`). The selected `--model` is passed through unchanged, so the endpoint can expose any compatible image model. Do not print, persist, or reuse a Codex session bearer token as an image API key.

## Workflow

1. Decide whether the request is `models`, `generate`, or `edit`.
2. If the user supplied a URL and key, pass them with `--base-url` and `--api-key` or use environment variables. Prefer environment variables when the key should not appear in shell history.
3. Use `models` to inspect the endpoint before choosing a model.
4. For edits, obtain the actual input files first. Keep source images unchanged and write new results by default.
5. Save user-facing results under `outputs/` unless the user requests another path, then inspect the result and report exact paths.

## List available models

```bash
python3 <plugin-root>/skills/codex-image-plugin/scripts/image.py models \
  --base-url "https://api.example.com/v1" \
  --api-key "$OPENAI_API_KEY" \
  --image-only
```

The command prints model IDs only; it never prints the key.

## Generate with any selected model

```bash
python3 <plugin-root>/skills/codex-image-plugin/scripts/image.py generate \
  --base-url "https://api.example.com/v1" \
  --api-key "$OPENAI_API_KEY" \
  --model "gpt-image-2" \
  --prompt "A clean product photo of a ceramic mug on a white studio background" \
  --out outputs/mug.png \
  --quality high \
  --size 1024x1024 \
  --force
```

`--model` is not hardcoded. `gpt-image-2` is only an example; use an ID returned by `models` or the model name documented by the endpoint.

## Edit one or more images

```bash
python3 <plugin-root>/skills/codex-image-plugin/scripts/image.py edit \
  --base-url "https://api.example.com/v1" \
  --api-key "$OPENAI_API_KEY" \
  --model "gpt-image-2" \
  --image work/input.png \
  --prompt "Change only the background. Preserve the subject exactly: same shape, pose, proportions, colors, lighting, and details." \
  --out outputs/edited.png \
  --force
```

Repeat `--image` for multiple references. Use `--mask mask.png` for localized edits. A mask must be a PNG with alpha: transparent pixels are editable and opaque pixels are preserved. `--mask-ring` creates a temporary ring mask for a square image.

## Prompting and validation

Separate mutable and protected content. For a localized edit, describe exactly what may change and preserve the subject's shape, pose, proportions, colors, lighting, and details. For a new image, specify the asset type, subject, setting, composition, style, lighting, exact text, and constraints. Use `--dry-run` to validate a request without making an API call. Model-specific limits such as supported sizes, masks, formats, or transparency are determined by the endpoint; report API errors without hiding them.
