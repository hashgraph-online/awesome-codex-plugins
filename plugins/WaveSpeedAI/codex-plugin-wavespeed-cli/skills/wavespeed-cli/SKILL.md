---
name: wavespeed-cli
description: Generate, edit, animate, upscale, or transform AI media using the WaveSpeed CLI from Codex. Use when the user asks to create image, video, audio, 3D, TTS, marketing creatives, or to inspect/run WaveSpeed models.
---

# WaveSpeed CLI

Use the `wavespeed` CLI to run WaveSpeed image, video, audio, and 3D models. Every generation uses the same flow: search the live catalog, inspect the model schema, then run the model with explicit inputs.

This plugin also starts the WaveSpeed MCP server. Its tools map one-to-one onto the CLI commands below: `search_models` = `wavespeed models`, `get_model_schema` = `wavespeed schema`, `get_price` = `wavespeed price`, `upload_file` = `wavespeed upload`, `run_model` = `wavespeed run`, `get_prediction` = `wavespeed show`, `get_balance` = `wavespeed balance`. Prefer the MCP tools for single generations; use the CLI when it is installed and the user wants batch or scripted runs. Both share the same login.

## Before Running

Check whether the CLI is available:

```bash
wavespeed --version
```

If it is missing, run this plugin helper:

```bash
./plugins/wavespeed-cli/scripts/install-wavespeed-cli.sh
```

Check auth before generation:

```bash
wavespeed status
```

If the user is not signed in, ask them to run `wavespeed login`. Do not ask the user to paste an API key into chat. For CI or one-off shells, `WAVESPEED_API_KEY` may be set in the environment.

## Standard Flow

```bash
# 1. Search the live catalog.
wavespeed models "nano banana"
wavespeed models --type image-to-video
wavespeed models --type text-to-video
wavespeed models --type text-to-audio
wavespeed models --type text-to-3d

# 2. Inspect dynamic inputs for the selected model.
wavespeed run google/nano-banana-2/text-to-image -h

# 3. Run with --json so Codex can parse outputs.
wavespeed run google/nano-banana-2/text-to-image \
  -p "a cyberpunk skyline at golden hour" \
  -i aspect_ratio="16:9" \
  -i resolution="2k" \
  --json
```

`wavespeed run --json` returns machine-readable fields such as `model`, `prompt`, `outputs`, `saved`, `elapsed_ms`, and `raw`. Use output URLs directly when the user wants links. Add `--download` when the user wants local files.

## Recommended Starting Models

| Use case | Model |
| --- | --- |
| Text to image | `google/nano-banana-2/text-to-image` |
| Image edit | `google/nano-banana-2/edit` |
| Text to video | `wavespeed-ai/minimax-h3/text-to-video` (cheap open-weights default; `bytedance/seedance-2.5/text-to-video` for the highest quality) |
| Image to video | `wavespeed-ai/minimax-h3/image-to-video` (`bytedance/seedance-2.5/image-to-video` for the highest quality) |

These are defaults, not a fixed list. Browse alternatives with `wavespeed models <query>` and inspect each selected model before running it.

## Files

Local file paths are not automatically uploaded. Upload files first, then pass returned URLs into generation commands.

```bash
wavespeed upload ./input.jpg --json
wavespeed run google/nano-banana-2/edit \
  -p "replace the background with a sunlit kitchen" \
  -i images='["https://..."]' \
  --json
```

Save generated outputs locally:

```bash
wavespeed run google/nano-banana-2/text-to-image \
  -p "minimal product photo on a glass table" \
  --download "./wavespeed-output/{index}.{ext}" \
  --json
```

## Project Config

`wavespeed init` creates `wavespeed.json` with shared defaults and aliases.

- `defaultModel` lets `wavespeed run -p "..."` omit the model argument.
- `aliases` bundle a model with default inputs.
- `wavespeed aliases` lists configured aliases.
- CLI flags override alias defaults.

The CLI never rewrites the user's prompt or inputs.

## Pitfalls

- Do not invent model IDs. Confirm with `wavespeed models` or `wavespeed schema <model>`.
- Prefer `--json` for runs, uploads, and any command that will be parsed.
- Use structured inputs via `-i key=value`; inspect model help for exact names and accepted values.
- Some models require uploaded asset URLs, not local paths.
