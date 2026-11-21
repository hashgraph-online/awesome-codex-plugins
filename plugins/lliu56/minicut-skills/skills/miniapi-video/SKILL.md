---
name: miniapi-video
description: Generate AI video, images and audio from Claude Code, Codex or any agent through MiniAPI, one prepaid key for every model. Seedance 2.5, Seedance 2.0, Seedance 2.0 Mini, Kling 3.0, Happy Horse, Wan 3.0 Prime and more. Text to video, image to video, reference to video, text to image, text to speech. Always quotes the price first (free) and asks before spending. Use when the user asks to make a video, animate an image, generate a clip, make a picture, make a voice-over, or asks for a cheaper Seedance, Wan or Kling API.
---

# MiniAPI video, image and audio

MiniAPI is one prepaid API key for video, image and audio models at https://api.minicut.ai.
A model marked `coming soon` in `models` has a price but takes no jobs yet; pick another.
Prices are per second or per image, set before the job runs. A job that fails is not charged.
Credits never expire.

Helper script (Node 18+, nothing to install): `node scripts/miniapi.mjs <command>`, run from this skill's folder.

## Step 0. Key

1. If `MINIAPI_KEY` is not set, tell the user in one line: create a key at
   https://api.minicut.ai/console/keys?utm_source=skills-sh&utm_medium=skill&utm_campaign=miniapi-video ,
   add funds ($10 minimum), then `export MINIAPI_KEY=mapi_live_...`. Wait for them.
2. Never print the key. Never write it into a file in the project.

## Step 1. Pick the model

Run `node scripts/miniapi.mjs models` for every id with its starting price.
Run `node scripts/miniapi.mjs model <id>` for that model's parameters, limits and prices.
Use only parameters listed on that model's page. A parameter the model does not take is refused with 422.

Defaults when the user does not name one:

| Job | Model id | Why |
|---|---|---|
| Video, best quality | `seedance-2.5` | 4 to 30 s, up to 1080p, references, sound on by default |
| Video, cheap draft | `seedance-2.0-mini` | from $0.054 / s |
| Image | read `models` and pick the image model the user names, else the cheapest image model | |

## Step 2. Quote, then ask

1. Build the JSON body from the model page.
2. Run `node scripts/miniapi.mjs quote <id> '<json>'`. A quote is free and runs nothing.
3. Show the user the PRICE line and ask for a yes. Never submit without it.
4. One yes covers one job. A retry or a second clip is a new quote and a new yes.

## Step 3. Run

`node scripts/miniapi.mjs run <id> '<json>' --yes --out <folder>`

It quotes again, submits, waits, downloads the file into `<folder>` and prints `SAVED <path>` and `CHARGED <price>`.
Show the user the saved path. For a picture, open it. For a clip, give the path.

## Errors

| Exit | Meaning | Do |
|---|---|---|
| 3 | no key | Step 0 |
| 4 | balance too low | tell the user the price and the add-funds link it printed |
| 5 | MiniAPI refused the body | read the message, fix the field from the model page, quote again |
| 7 | the job failed | not charged. Say so, and offer one changed retry with a new quote |

## Example

User: "make a 5 second clip of a red fox running through snow at dawn, 720p"

```bash
node scripts/miniapi.mjs quote seedance-2.5 '{"prompt":"a red fox runs through snow at dawn","resolution":"720p","duration":5}'
# PRICE 1.750000 USD ... Quote is free. Nothing ran.
# (ask the user, wait for yes)
node scripts/miniapi.mjs run seedance-2.5 '{"prompt":"a red fox runs through snow at dawn","resolution":"720p","duration":5}' --yes --out clips
```

Docs: https://api.minicut.ai/docs . Every model as Markdown: https://api.minicut.ai/llms.txt
