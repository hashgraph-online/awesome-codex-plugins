---
name: models
description: "Search the Wiro AI catalog of 1,000+ models, compare them and read their inputs and prices, for free"
---

# Wiro AI: find models and prices

Request: the text the user typed after the command

This command only reads. It never runs a model and costs nothing. If you cannot see the Wiro MCP tools, the `wiro` server may still be connecting: wait for it and look again. If they are still missing, tell the user to run `codex mcp login wiro` in a terminal and sign in. If there is no `wiro` server, the Wiro AI plugin is not installed: `codex plugin marketplace add wiroai/Wiro-Plugin`, then `codex plugin add wiro-ai@wiro`.

- A job or key words ("upscale", "video with sound", "cheapest text to speech"): call `recommend_model` with two or three key words and `search_models` with the matching category.
- A category (`text-to-image`, `image-to-image`, `image-editing`, `text-to-video`, `image-to-video`, `video-to-video`, `text-to-speech`, `speech-to-text`, `text-to-music`, `text-to-song`, `voice-clone`, `3d-generation`, `llm` and others): `search_models` with that category, `limit` up to 100, sorted by `ratedusercount` unless the user wants the newest (`time`).
- A model (`owner/slug` or a name): `get_model_schema`, then explain what it takes (inputs, options, limits, defaults) and its price at the default settings and at the settings the user cares about.
- `--cheapest`: list the category, compare the prices, and check the two or three cheapest with `get_model_schema` at the settings asked for before you name one. A price shown as a range depends on settings such as resolution or length.
- `--compare a b`: read each one with `get_model_schema` and compare inputs, limits and price at the same settings.
- Empty: `explore`, and show its curated groups.

Answer with a table: the model as `owner/slug` exactly as the tools return it, its name, what it is good for, and the price with its unit (per run, per image, per second, per 1M tokens). Say when a price is only known after the run, or when the run is charged for the time it takes. End with one line naming the command that runs the model they pick, with `--model <owner/slug>`: $wiro-ai:image or $wiro-ai:edit-image for images, $wiro-ai:video for video, $wiro-ai:speech for speech, $wiro-ai:music for music, $wiro-ai:transcribe for speech to text and $wiro-ai:3d for 3D.
