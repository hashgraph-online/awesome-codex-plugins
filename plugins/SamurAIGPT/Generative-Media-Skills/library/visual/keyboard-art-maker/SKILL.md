---
slug: muapi-keyboard-art-maker
name: muapi-keyboard-art-maker
version: "1.0.0"
description: Generate artistic top-down photos of keyboard keycaps arranged to spell out custom text messages.
acceptLicenseTerms: true
---


# Keyboard Art Maker

**Generate artistic top-down photos of keyboard keycaps arranged to spell out custom text messages.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `display_text` | text | yes | — | The text you want to spell out with keycaps (e.g., "WORKFLOWS ON VADOO AI"). |


## Steps

### Phase A — Keyboard Art Generation

Submit the plan with ONE step to generate the artistic keyboard image:

1. **Keyboard Art Generation** — `muapi image generate` (model=`ideogram-v3-t2i`):
   - Prompt: `The photograph captures white keycaps, arranged neatly on a dusty black surface to spell "{{display_text}}". Each keycap displays a crisp black letter, with soft, diffused lighting highlighting the subtle shadows, creating a harmonious contrast between the keycaps and their backdrop, while the top-down shot ensures the phrase is clear and in perfect focus. There should be adequate spacing between words. Cinematic quality, professional studio lighting, 8k resolution.`
   - Aspect ratio: 1:1 or 4:3

After generation, present the final keyboard art image to the user.

## Trigger Keywords

`keyboard art`, `keycap text`, `spell with keys`, `keyboard message`, `custom keycap image`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
