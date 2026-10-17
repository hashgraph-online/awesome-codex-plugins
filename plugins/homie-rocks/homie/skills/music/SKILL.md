---
name: music
description: "Compose music with the official ElevenLabs MCP and keep arrangement, rights, mastering and scene integration in Homie."
compatibility: Node 22 and the official ElevenLabs plugin in the AI client. Local media processing uses ffmpeg and Chrome where needed.
metadata:
  providers: elevenlabs
---

# Music for the scene

Read the studio's style and the scene's emotional arc. Write a composition brief with
instrumentation, tempo, duration, transitions, loop points and any exact lyrics.
Use original language; preserve the owner's requested musical direction.

Use the official ElevenLabs plugin's MCP creative workflow. Discover current tools first:
`creative_get_flow_node_types` and `creative_get_model_guide` describe supported nodes
and prompting; `creative_get_flow_run_status` follows a submitted flow. Only invoke
music or sound generation if the connected server actually exposes that capability.
The hosted OAuth server's public descriptions vary; never invent a music tool name or
silently substitute speech. If unavailable, explain the missing capability and continue
local composition/placement with a supplied file. The official provider plugin owns any
alternative setup flow; Homie does not install a key-based local server or read CLI auth.

Use the provider's estimate capability where exposed and record credits as quoted or
measured. Read the current account plan's music terms before commercial use. Keep
lyrics, composition brief and generation identifiers beside the song.
Local `scripts/music.mjs` retains `plan`, `analyze`, `master`, `loop`, `add` and `publish`.
Master from the downloaded audio, check clipping and loudness, audition the loop seam,
and verify every sung line by listening. Transcription or stems, if needed, use discovered
official MCP capabilities; neither is assumed available. Add metadata and credits to
`music/manifest.json`, then wire the track to the scene or music page. Publish only when requested.

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
