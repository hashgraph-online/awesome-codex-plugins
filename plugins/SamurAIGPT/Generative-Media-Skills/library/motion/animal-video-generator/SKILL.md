---
slug: muapi-animal-video-generator
name: muapi-animal-video-generator
version: "1.0.0"
description: Create a hilarious and ultra-realistic video of an anthropomorphic animal acting like a human vlogger in a real-world setting.
acceptLicenseTerms: true
---


# Animal Vlogger Video

**Create a hilarious and ultra-realistic video of an anthropomorphic animal acting like a human vlogger in a real-world setting.**

## Inputs

| Name | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `animal_type` | text | no | monkey | The type of animal vlogging (e.g., monkey, dog, cat, bear). |
| `location` | text | no | busy streets of Noida, India | The setting for the vlog. |
| `clothing` | text | no | a bright red t-shirt | What the animal is wearing. |
| `script` | text | no | क्या यार, कहाँ फंस गया नॉएडा में आके? इससे तो बैंगलोर ही अच्छा था. यहाँ तो बड़ी गर्मी है भाई. पसीने ही छूट गए मेरे तो. | The dialogue for lip-sync. |


## Steps

### Phase A — Generate Vlogger Image

Submit the plan with ONE step to create the base image of the animal vlogger:

1. **Image Generation** — `muapi image generate` (model=`nano-banana` or `nano-banana-pro`):
   - Prompt: `Ultra-realistic, cinematic portrait of an expressive {{animal_type}} wearing {{clothing}}, holding a selfie stick on the {{location}}. The {{animal_type}} is anthropomorphic, walking upright, and looks like a believable vlogger. Sweating slightly in the heat, highly detailed, photorealistic. Background shows a bustling street, people eating at stalls, vibrant urban details.`
   - Aspect ratio: 9:16 (for vertical vlog style)

After generating the image, present it to the user.

### Phase B — Video Generation

Once the image is approved, submit a second the plan with ONE step to animate it with lip-sync:

1. **Video Generation** — `muapi video generate` or `muapi video from-image` (model=`veo3.1-fast-image-to-video`):
   - Reference Image: The generated image from Phase A.
   - Prompt: `Create an ultra-realistic cinematic video featuring a lifelike {{animal_type}} vlogging with a selfie stick on the {{location}}. The film starts in selfie mode, camera slightly wide-angle. The {{animal_type}} is expressive, looks mildly disgruntled, and speaks naturally. Occasional quick zoom-in on the disappointed face. Background features busy street life, vibrant colors. Smooth gimbal-like camera motion.`
   - Dialogue for Lip-Sync (if tool supports audio/lipsync): `{{script}}`
   - Aspect ratio: 9:16

After generation, present the final funny video.

## Trigger Keywords

`animal video`, `funny monkey video`, `animal vlogger`, `vlog video`, `monkey in noida`


---

## Notes for the Executing Agent

- This recipe is LLM-orchestrated: read each phase, gather any missing inputs from the user, then call `muapi` CLI commands. Use `muapi auth configure` first if `MUAPI_API_KEY` is unset.
- For model IDs without a CLI alias yet, fall back to the raw endpoint via `curl -X POST https://api.muapi.ai/api/v1/<endpoint> -H "x-api-key: $MUAPI_API_KEY" -H 'content-type: application/json' -d '{...}'` and poll with `muapi predict wait <request_id>`.
- Substitute `{{input_name}}` placeholders with the user's actual inputs before issuing each call.
