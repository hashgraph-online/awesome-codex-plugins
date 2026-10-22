---
name: art
description: "Make game and app art using the official fal MCP, studio art direction, local capture and asset checks."
compatibility: Node 22 and the official fal plugin in the AI client. Local media processing uses ffmpeg and Chrome where needed.
metadata:
  providers: fal
---

# Art for this studio

Read the game's or app's style, codex and existing scene before writing a prompt.
Use its palette, shape language, materials, lighting and camera. Keep approved references
and the style revision. Covers must describe what the playable experience really offers.
A frame from the running game is free and often the best cover.

For generated art use fal's `recommend_model` or `search_models`, `get_model_schema`
and `get_pricing`, then `run_model`. Continue a pending request with `check_job` and
`get_job_result`. Use `upload_file` only as documented by the official plugin for references.
Set an explicit image count. Inspect the first result before any dependent generation.

Local `scripts/art.mjs` keeps `check`, `frame`, `cover`, `tile`, `fit` and `sheet`.
Use `cover <game> --from <image>` for a 1600×900 cover and game.json reference;
`fit <image> --out <file>` for phone-sized delivery. Check tile seams with a repeated
2×2 preview, transparency against light and dark, readability at phone size, and
compression after fitting. Do not replace an engine effect with a large image by default.

## Official generation workflow

The owner's AI uses the provider's official plugin/MCP in its own client. Homie never
asks for, stores, reads or prints provider credentials. Read the current provider
skill and discover its available tools and input schemas; host prefixes vary.
Connection instructions and verified sources: [official integrations](../studio-setup/references/OFFICIAL-MEDIA.md).
If tools are missing, connect that official plugin once in the client's browser flow.
Do not fall back to a Homie client, key file, environment key or CLI generation wrapper.

Before spending, state the model, count/duration, estimated cost and remaining approved
budget. Use the owner's existing authorization; ask only if the spend is outside it.
Record the request ID as soon as accepted. Poll that same request; never resubmit to
retry a slow job. Unknown cost is unknown, never zero. Provider billing is authoritative;
Homie's local receipt cannot enforce spending in another client.

## Place and prove the result

Download the completed tool's output using the AI client's file/download facilities.
Keep temporary signed URLs out of committed records. Keep the original in the studio's
art/job folder; put the optimized delivered asset beside its game/app, or in music/ or
videos/ for a published work. Record a receipt with these fields:

```json
{
  "provider": "fal",
  "tool": "run_model",
  "model": "exact endpoint returned by the provider",
  "requestId": "actual request ID",
  "prompt": "the actual prompt, including style constraints",
  "styleRevision": "revision from the studio's style",
  "rights": {"source": "provider/model terms URL", "checkedAt": "YYYY-MM-DD", "commercial": false, "note": "record the actual plan and permitted use"},
  "cost": {"status": "unknown"}
}
```

For ElevenLabs use its actual discovered tool and model, and its flow/session or request
identifier. A measured cost uses `{"status":"actual","amount":1,"unit":"credits"}`;
a quote uses `estimate`. Never claim commercial rights from the fact that generation
succeeded. Read the provider and model terms for the account's plan; record attribution,
reference-image permissions and any restrictions. Mark test fixtures `"fixture": true`.

Wire the delivered path into the scene or manifest, then run:

```sh
npx --no-install homie-studio media import --file <downloaded-file> --receipt <receipt.json> --out games/<id>/assets/<name> --used-by games/<id>/view.ts
```

This copies bytes, verifies a static reference, hashes the asset and records allowlisted
provenance in `media/provenance.json`. Reimporting the same output is idempotent; it
never generates or charges. Include each generation step's receipt for derived assets.
Run the scene and look/listen: a file and static reference are not proof that it renders
or plays. Report the placed path, usage evidence, rights and actual/estimated cost.

The toolkit’s `lib/media-workflows.mjs` declares this skill’s verified tool references.
Validate them against the host’s current tool inventory before execution; tool discovery
is required for generation capabilities that have no stable documented name.
