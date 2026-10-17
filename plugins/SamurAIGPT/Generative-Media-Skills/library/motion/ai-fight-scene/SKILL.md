---
slug: muapi-ai-fight-scene
name: muapi-ai-fight-scene
version: "1.0.0"
description: Generate a high-cut-density action / fight scene by first composing a 16-cell storyboard image, then driving Seedance 2.0 image-to-video off that storyboard. Stacks GPT-Image-2 (character sheet + storyboard), Nano-Banana-2 (environment concept), and Seedance 2.0 i2v.
acceptLicenseTerms: true
---


# AI Fight Scene Generator

**Generate a high-cut-density action / fight scene by first composing a 16-cell storyboard image, then driving Seedance 2.0 image-to-video off that storyboard.**

The core idea: **action tension comes from cut density, not single-shot quality.** Forcing the video model to follow a pre-drawn 4×4 storyboard grid gives you 16 distinct shots in a 15-second clip — landing punches, reverse angles, ECUs, whip-pans — that no t2v prompt could choreograph on its own.

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `character_description` | text | yes | — | Full physical description of the fighter(s). Asymmetric details (eye colour, scar side, holster on left hip) help the model preserve identity across panels. |
| `environment_description` | text | yes | — | The scene setting — e.g. "cyberpunk wet back-alley, neon kanji signage, Stray-game aesthetic, rain on chrome." |
| `action_script` | text | yes | — | The action beat — prose or numbered beats. E.g. "Hero is cornered → blocks first punch → counter-elbow → throw opponent into trash cans → finisher." |
| `style_direction` | text | no | cinematic action film, anamorphic lens, high contrast, motion blur on hits | Aesthetic / look tags applied to every frame. |
| `duration` | int | no | 15 | Final video length in seconds. The storyboard's 16 cells map roughly 1 shot per second at default. |
| `aspect_ratio` | text | no | 16:9 | Output aspect — `16:9` cinematic, `9:16` vertical, `1:1` square. |


## Steps

### Phase A — Character Sheet

Generate a clean turnaround-style character sheet using `muapi image generate` (model=`gpt-image-2-text-to-image`):

- Prompt: `Character reference sheet of {{character_description}}. Three views — front, 3/4, profile — on a neutral grey backdrop. Studio lighting, full body, no text overlays, photoreal. Asymmetric identifying details preserved on the correct side. {{style_direction}}.`
- Aspect ratio: `3:2`

Present the character sheet and confirm identity details look right before proceeding. **This image becomes reference #1 for later phases.**

### Phase B — Environment Concept

Use `muapi image generate` (model=`nano-banana-2`) to design the scene/world:

- Prompt: `Wide establishing shot of {{environment_description}}. No characters in frame — environment only. Strong perspective lines, depth, atmospheric haze. {{style_direction}}. Production-design concept art.`
- Aspect ratio: `{{aspect_ratio}}`

Nano-Banana-2 is chosen here for its reasoning-driven composition — it's better than text-to-image-only models at producing locations with believable spatial logic (chokepoints, cover, sightlines) that an action scene can use. Present for approval. **This becomes reference #2.**

### Phase C — 16-Cell Storyboard

Compose the action onto a single 4×4 storyboard image using `muapi image edit` (model=`gpt-image-2-image-to-image`):

- Reference Images: the character sheet from Phase A **and** the environment plate from Phase B.
- Prompt:
  ```
  Compose a 4×4 storyboard grid (16 numbered cells) for the following action sequence:
  {{action_script}}

  CHARACTER (use reference image 1 identity throughout, asymmetric details preserved):
  {{character_description}}

  LOCATION (use reference image 2 spatial layout):
  {{environment_description}}

  Each cell labels: SHOT # (1–16) · SIZE (WIDE / MS / CU / ECU) · CAMERA-MOVE arrow (push, pull, whip, dolly, crash-zoom, handheld) · 1-word RHYTHM note (BEAT / IMPACT / RECOVERY / RESET).

  Vary shot size aggressively — never two WIDEs in a row. Land every IMPACT on a CU or ECU.
  Hand-drawn comic-book ink-and-wash style, monochrome with selective red accents on hits.
  Numbered cells, clear gutters between panels.

  Aesthetic: {{style_direction}}.
  ```
- Aspect ratio: `1:1` (square works best for a 4×4 grid)

Present the storyboard to the user. Confirm:
- The 16 shots read clearly
- Identity stays consistent cell-to-cell
- Cut density / shot-size variation looks aggressive enough

If a panel reads poorly, regenerate just the storyboard with that cell's note bolded ("CELL 7 must be an ECU on the right fist").

### Phase D — Storyboard → Video (Seedance 2.0)

Hand the storyboard to `muapi video from-image` (model=`seedance-v2.0-i2v`):

- Reference Image: the 16-cell storyboard from Phase C.
- Prompt:
  ```
  Generate a {{duration}}-second action sequence that strictly follows the 16-cell storyboard reference image, cell-by-cell, top-left to bottom-right.

  - Honour each cell's labelled SHOT SIZE and CAMERA-MOVE — match cuts to the storyboard's rhythm notes.
  - Strong cinematic feel and shot language. Exaggerated dynamics. Hits land hard with motion blur and impact frames.
  - Camera language: anamorphic, handheld where the storyboard calls for it, locked-off where it doesn't.
  - Native audio: impact sfx on every IMPACT cell, footsteps, fabric/Foley, restrained low score under the action.

  Action being rendered: {{action_script}}.
  Aesthetic: {{style_direction}}.
  ```
- Duration: `{{duration}}` (default 15)
- Aspect ratio: `{{aspect_ratio}}`

After generation, present the final video. If the cut density feels too low or shots don't match the storyboard, regenerate Phase D first (cheaper than rebuilding the storyboard) with the prompt emphasising "strict cell-by-cell adherence" more aggressively.

## Notes

- **Why the storyboard image and not a text storyboard?** Seedance 2.0 i2v anchors its motion plan to the visual reference. A grid of 16 drawn cells gives it 16 visual targets to hit — text descriptions of shots get averaged into mush.
- **Asymmetric character details matter.** Without something like "scar over the right eyebrow" or "leather glove on the left hand only", identity drift between cells is the #1 failure mode.
- **Use `seedance-2.0-i2v-480p` to draft.** Cheaper preview pass before committing to the full-res `seedance-v2.0-i2v` run.
- **For longer fights**, chain two runs: first run uses storyboard A (cells 1–16, beats 1–15s); second run uses storyboard B (cells 17–32, beats 15–30s) with the last cell of A as a continuity anchor in B's first cell.
- **Language**: Both English and Chinese prompts work in all four models, so the storyboard cell labels can be in either language.

## Trigger Keywords

`fight scene`, `action sequence`, `storyboard to video`, `cut density`, `cinematic action`, `combat choreography`, `seedance 2 storyboard`

## Pipeline at a Glance

```
character_description ──► [GPT-Image-2 t2i]   ─► character sheet ──┐
                                                                    │
environment_description ─► [Nano-Banana-2 t2i] ─► environment plate ┼─► [GPT-Image-2 i2i] ─► 16-cell storyboard ─► [Seedance 2.0 i2v] ─► 15s action video
                                                                    │
action_script + style_direction ───────────────────────────────────►┘
```

---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Phase C uses TWO reference images (character sheet + environment plate). When calling `gpt-image-2-image-to-image`, pass them as a list under `images_list` (or the model's documented multi-ref field).
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
