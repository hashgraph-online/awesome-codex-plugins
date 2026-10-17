---
name: models
description: "Make coherent 3D assets through the official fal MCP, then optimize, register and check them in the studio."
compatibility: Node 22 and Tripo models through the official fal plugin in the AI client. Local media processing uses ffmpeg and Chrome where needed.
metadata:
  providers: fal tripo
---

# Models that fit the game

Start with Homie's CC0 starter library (`homie-studio assets`) when it fits. Read the
locked style, character proportions, scale and performance budgets before generating.
For a new prop, generate and inspect one clean concept first, then a mesh. For a
character, specify a full body A-pose, readable silhouette and the required skeleton.
Use a coherent family; avoid mixing unrelated material styles and proportions.

Use fal's `recommend_model`/`search_models`, `get_model_schema` and `get_pricing` for
each image, mesh and rig step. No model or price is permanently pinned in Homie.
Use `run_model` for the concept and `submit_job`, `check_job`, `get_job_result` for 3D.
Inspect the concept before paying for a mesh. Request only schema-supported rig fields.

Import a completed GLB with `homie-studio assets add`; use its current `--help` for
scale, rig and clip options. Retain original generation receipts and register the
optimized result's licence and provenance. `scripts/models.mjs import` also accepts
an already completed connector receipt and local GLB; it never runs a provider.
For a completed connector job, the local import command is:

```sh
node <path-to-models.mjs> import <id> <asset> --receipt <job.json> --file <model.glb>
```

If a registered asset is deliberately not placed, mark it accurately with
`homie-studio assets use <id> <asset> unused`. Never report an unused model as visible.

Inspect bounds, normals, textures, silhouettes and pivot; run `assets check`, check
triangles/draw calls/texture memory on a phone, and test animation in the actual scene.
A generated rig is not proof that Homie's clips retarget correctly.

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
