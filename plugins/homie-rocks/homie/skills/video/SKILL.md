---
name: video
description: "Capture and edit studio videos locally, and generate requested shots through the official fal MCP."
compatibility: Node 22 and the official fal plugin in the AI client. Local media processing uses ffmpeg and Chrome where needed.
metadata:
  providers: fal
---

# Video from the studio

Start with the actual running game/app. Plan a short sequence that shows its central
action, one progression moment and a truthful call to action. Capture gameplay locally;
do not pass generated footage off as gameplay. Derive generated shots from the locked
style and approved reference frames, preserving composition and character continuity.

For requested generated footage, use fal's `recommend_model`/`search_models`,
`get_model_schema`, `get_pricing`, then `submit_job`, `check_job` and `get_job_result`.
Specify count, duration, resolution and whether audio is needed. Inspect a first shot
before chaining more. The provider plugin owns uploads and generation.

Local `scripts/video.mjs` keeps capture/record/trailer, beat grids, slices, timing checks,
editing and delivery. Read `references/RECORD.md` for page capture. Check contact sheets,
then watch with audio at speed; verify sync, text legibility, transitions and both phone
and landscape framing. Keep masters in `videos/<slug>/`, export compressed deliverables
and register them in `videos/manifest.json`. Check that the site page plays the delivered
file and credits its inputs. Deployment is a separate requested action.

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
