---
slug: muapi-storyboard-to-cooking-video
name: muapi-storyboard-to-cooking-video
version: "1.0.0"
description: Turn a single photo of a person into a 15-second cinematic pasta-making (or other cuisine) tutorial video. First builds a composite reference sheet (character + kitchen + 9-step action board), then animates the full cooking sequence with audio in a single continuous shot.
acceptLicenseTerms: true
---


# Storyboard to Cooking Video

**Turn a single photo of a person into a polished 15-second cinematic cooking tutorial. The skill first generates a high-end production reference sheet — character look, kitchen environment, and a 9-panel action board — then drives a continuous reference-to-video render that keeps the subject's face, outfit, and kitchen consistent across every frame.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `person_image` | image_url | yes | — | URL of the person photo. Used as identity reference in BOTH the reference sheet and the final video. |
| `dish` | text | no | fresh pasta | The cooking subject (e.g. "fresh pasta", "sushi rolls", "wood-fired pizza", "matcha latte"). Drives the 9-step action board. |
| `kitchen_style` | text | no | warm rustic-modern Italian | The kitchen aesthetic (e.g. "warm rustic-modern Italian", "minimalist Tokyo", "bright Scandinavian", "moody industrial"). |
| `outfit` | text | no | white t-shirt, olive green apron, dark trousers | What the person wears throughout the video. |
| `duration_seconds` | int | no | 15 | Final video duration. Use 15 for the full 9-step arc; 10 collapses to ~6 beats. |
| `aspect_ratio` | text | no | 16:9 | Output aspect ratio. Use `9:16` for vertical/Reels. |
| `resolution` | text | no | 720p | Video resolution. Options: `480p`, `720p`. |


## Steps

Submit the plan with TWO sequential steps. Step 2 depends on the output of Step 1.

### Step 1 — Reference Sheet (Composite Storyboard)

Generate the composite "production reference board" image. This is a single image, NOT a video frame — it bundles character sheet + location reference + 9-panel action board.

**Endpoint:** `gpt-image-v2-edit`
**CLI:**

```bash
muapi image edit \
  --model gpt-image-v2-edit \
  --image "{{person_image}}" \
  --image-size "3840x2160" \
  --quality auto \
  --background auto \
  --moderation low \
  --output-format png \
  --prompt "Create one single composite reference sheet for a {{duration_seconds}}-second realistic {{dish}}-making tutorial video. The image should be a clean, high-end production reference board, not a poster with heavy text. Format: {{aspect_ratio}} wide reference sheet, elegant white margins, clean grid layout, realistic cinematic photography style. Concept: {{dish}} tutorial in a {{kitchen_style}} kitchen.

Top row: motion / choreography guide with 9 numbered cinematic action panels showing the {{dish}} process step-by-step from raw ingredients to final plated dish.

Middle-left: realistic character reference sheet of the uploaded person — preserve their exact face, hair color, hair texture, eye color, skin tone, and all facial features with 100% accuracy. Show the same person in: face close-up, full-body front view, side/action working pose, and back view. Dress them in {{outfit}}. Keep them grounded, approachable, skilled, and cinematic.

Middle-right / background: location reference sheet of an elegant {{kitchen_style}} kitchen with tactile surfaces, natural daylight from a large window, hanging cookware, herbs, and premium cooking atmosphere appropriate to the cuisine.

Style: realistic, cinematic, warm natural light, shallow depth of field, tactile food photography, premium cooking show aesthetic, rich surface textures.

Bottom strip: simple visual icons only for {{duration_seconds}} seconds, {{aspect_ratio}}, realistic, cinematic, tasty, natural camera. Minimal text, no dense paragraphs. Let the visuals do the heavy lifting."
```

Wait for completion and capture the output URL as `{{reference_sheet_url}}`. Show it to the user and confirm the character likeness + kitchen mood before moving to Step 2 — Step 2 is the expensive call.

### Step 2 — Cooking Video (Reference-to-Video)

Animate the full sequence using both the original person photo (identity anchor) and the reference sheet (narrative + environment guide) as dual references.

**Endpoint:** `bytedance-seedance-2-0-reference-to-video-fast`
**CLI:**

```bash
muapi video generate \
  --model bytedance-seedance-2-0-reference-to-video-fast \
  --image "{{person_image}}" \
  --image "{{reference_sheet_url}}" \
  --aspect-ratio "{{aspect_ratio}}" \
  --duration "{{duration_seconds}}" \
  --resolution "{{resolution}}" \
  --generate-audio true \
  --prompt "The person in @Image1 is the subject — preserve their exact face, hair, eye color, skin tone, and all facial features with 100% accuracy throughout the entire video.
Use @Image2 as the visual and narrative guide — follow the cooking steps, kitchen setting, outfit, and atmosphere shown in the reference sheet exactly.
A single continuous cinematic video of the person from @Image1 making {{dish}} in the {{kitchen_style}} kitchen shown in @Image2. They wear {{outfit}} throughout.

VIDEO STRUCTURE
Follow the exact 9-step sequence as shown in @Image2, beat by beat, from raw ingredients through preparation to a final plated close-up.

MOTION STYLE
- Slow, deliberate, satisfying transitions between each step
- Natural hand and body movement with clear culinary intent
- Continuous flow with no jump cuts
- Warm and immersive pacing

CAMERA & CINEMATOGRAPHY
- Close-up shots for hands during mixing, kneading, cutting, plating
- Medium shots showing the person working at the counter
- Pull back slightly for the final plating to reveal the full kitchen
- Shallow depth of field — focus on hands and food, soft background blur
- No abrupt cuts — smooth match cuts and fluid transitions

VISUAL STYLE
- Warm natural daylight from a large kitchen window
- Rich tactile textures matching @Image2's environment
- Full color, warm cinematic color grading

CONSISTENCY RULES
- Same character throughout — face of @Image1 in every frame
- Same outfit across entire video
- Same kitchen environment as shown in @Image2

AUDIO
- Soft kitchen ambience, gentle culinary SFX (chopping, sizzling, pouring), light cinematic underscore
- No dialogue, no narration

OUTPUT STYLE
- Duration: exactly {{duration_seconds}} seconds
- Polished, cinematic, premium cooking show quality
- Ends with a beautiful close-up of the finished plated {{dish}}"
```

After generation:
- Present the final video URL to the user.
- Offer follow-ups: vertical 9:16 re-render for Reels, a longer 30s extended cut, or swap `{{dish}}` for a different cuisine using the same person image.

## Notes

- **Two-image reference is the whole trick.** `@Image1` locks identity, `@Image2` locks choreography + environment. Never drop one — single-reference runs lose either the face or the kitchen.
- The reference sheet at Step 1 must be wide (3840x2160). Smaller resolutions blur the 9 action panels and the video model can't read them.
- `bytedance-seedance-2-0-reference-to-video-fast` natively generates audio when `generate_audio=true`. Always include an audio direction in the prompt; otherwise the soundtrack is random.
- Real human faces ARE supported here because the person photo is the user's own subject and we route through the reference-to-video endpoint (not the restricted i2v variants).
- If the user wants a non-cooking sequence (e.g., latte art, plating tutorial, mixology), keep the same two-step structure — only `{{dish}}` and the 9-step description change.
- For shorter pieces (<= 8s), reduce the action board to 5–6 panels in Step 1; cramming 9 beats into 8s degrades motion quality (single-beat rule).

## Trigger Keywords

`cooking video`, `cooking tutorial`, `pasta video`, `recipe video`, `food video`, `chef video`, `cooking storyboard`, `kitchen tutorial`, `cooking reel`, `tutorial video from photo`, `storyboard to video`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
- Step 1 must complete and return an output image URL before Step 2 fires — pass that URL as the second `--image` to the video step.
