---
slug: muapi-storyboard
name: muapi-storyboard
version: "1.0.0"
description: Generate N keyframes for a short story or scene sequence (image only, no video).
acceptLicenseTerms: true
---


# Storyboard Generator

**Generate N keyframes for a short story or scene sequence (image only, no video).**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `premise` | text | yes | — | One-line story premise (e.g. "lonely robot finds a tiny mechanical bird friend"). |
| `scenes` | int | no | 6 | Number of keyframes to produce. |
| `style` | text | no | cinematic, photoreal, soft lighting, 16:9 | Visual style tags applied to every keyframe. |


## Steps

Use the plan to dispatch all N keyframes in a single parallel layer.

1. Decompose `premise` into `{{scenes}}` story beats with a clear arc:
   setup → inciting moment → escalation → climax → resolution.
   - Each beat gets a one-paragraph visual description.
   - Maintain character / object continuity across beats (same character
     appearance, same world).
2. For each beat, create a `muapi image generate` node (model=nano-banana-2, aspect_ratio=16:9):
   - Prompt = `"<beat description>. {{style}}"`.
   - Tier: balanced (these are reference keyframes, not finals).
   - Aspect ratio: 16:9.
3. Run the plan in parallel (no `depends_on` between keyframes).
4. Return the asset ids in beat order with a one-line caption per scene.

## Notes
- Don't animate, upscale, or add audio — this skill is keyframes only.
  If the user wants video, suggest the `music-video` skill afterward.
- For consistency, repeat character description verbatim in every prompt
  ("a small rusty humanoid robot with…") rather than relying on the model
  to remember.

## Trigger Keywords

`storyboard`, `keyframes`, `scene sequence`, `story panels`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
