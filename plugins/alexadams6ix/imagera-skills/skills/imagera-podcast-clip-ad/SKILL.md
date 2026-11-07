---
name: imagera-podcast-clip-ad
description: "Someone wants a podcast-style clip ad: a host at a microphone talking about their product, lip-synced and captioned. Use when: \"Make a podcast-style ad for my headphones\", \"I want one of those podcast clip ads with my product on the desk\", \"A host at a mic talking about my skincare brand\", \"podcast ad\", \"podcast clip\", \"podcast style\", \"podcast video ad\". Runs the Imagera \"Podcast clip ad\" template (a studio still, a voice, a lip-synced clip of up to 14.8 seconds and captions — a few minutes)."
---

# Podcast clip ad

A host at a studio microphone talks about your product, which sits on the desk in front of them: a still built from your product photo, your script in their voice, lip-synced and captioned. Lip Sync takes 5 to 14.8 seconds of speech, about 14 to 36 words; a free length check stops a script outside that range before anything is bought.

## When to use

Someone wants a podcast-style clip ad: a host at a microphone talking about their product, lip-synced and captioned.

## How to run it

- Ask for a product photo and the host's words, 14 to 36 words; who the host is and the studio look are optional.
- Count the words before running: a free Length Check stops a script outside the lip-sync window, so offer a trimmed version instead of letting it fail.
- The host is invented from the description: never make a real, named person appear to endorse the product, and never add results, ratings or claims the user did not write.
- For the same host across several ads, offer the Character ID skill (/character-id) first. For a phone-selfie review instead of a studio, offer the Talking product review skill (/ugc-talking-review).
- Before handing it over, check the product on the desk is unchanged and the captions match the script.

## Inputs

- `product` (image) — a photo of your product
- `script` (text) — what the host says about it, 14 to 36 words
- `host` (text, optional) — who the host is and what the studio looks like

## Steps

1. Host still
2. Voice
3. Lip Sync
4. Captions

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "podcast-clip-ad"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/podcast-clip-ad` in Superagent, or open it from https://imagera.ai/skills.
