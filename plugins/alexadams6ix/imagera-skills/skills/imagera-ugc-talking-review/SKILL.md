---
name: imagera-ugc-talking-review
description: "Someone wants a phone-style video of a creator holding their product and talking about it, lip-synced and captioned. Use when: \"Make a UGC review video of someone holding my serum\", \"I want a testimonial where a creator talks about my product\", \"Create a talking review of my new earbuds, filmed like a phone selfie\", \"ugc review\", \"talking review\", \"review video\", \"product review video\". Runs the Imagera \"Talking product review\" template (a still, a voice, a lip-synced clip of up to 14.8 seconds and captions — a few minutes)."
---

# Talking product review

Puts your product in the hand of a creator in a phone-style selfie, reads your script in their voice, syncs their lips to it and burns in captions. Lip Sync takes 5 to 14.8 seconds of speech, about 14 to 36 words; a free length check stops a script outside that range before anything is bought.

## When to use

Someone wants a phone-style video of a creator holding their product and talking about it, lip-synced and captioned.

## How to run it

- Ask for a product photo and the script in the creator's words, 14 to 36 words; who the creator is and where they film is optional.
- A free Length Check stops the run before anything is bought when the script cannot fit 5 to 14.8 seconds of speech, so count the words first and offer a trimmed version rather than letting it fail.
- The creator is invented from the description: never make a real, named person appear to endorse the product, and never invent results, ratings or claims the user did not write.
- If the same creator must appear across several videos, offer the Character ID skill (/character-id) first; to keep the product identical everywhere, the Object ID skill (/object-id).
- Before handing it over, check the product is unchanged in the still and the captions match the script.

## Inputs

- `product` (image) — a photo of your product
- `script` (text) — what the creator says about it, 14 to 36 words
- `creator` (text, optional) — who the creator is and where they film

## Steps

1. Creator still
2. Voice
3. Lip Sync
4. Captions

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "ugc-talking-review"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/ugc-talking-review` in Superagent, or open it from https://imagera.ai/skills.
