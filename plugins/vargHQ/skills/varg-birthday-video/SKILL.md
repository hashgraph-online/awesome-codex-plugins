---
name: varg-birthday-video
description: >-
  Turns a name, an age and a few photos into a personalized AI birthday video on varg: a song that sings their
  name, their photo coming to life as they blow out the candles, a "then and now" montage, an epic trailer
  starring them, a pet's birthday, an animated e-card or invitation. Asks the 5 questions that make it theirs,
  writes the lyrics and prompts, makes the stills first (GPT Image 2.5 spells the name on the cake), animates
  them (Wan 3, Seedance 2.5), makes the song (ElevenLabs Music sings the name), then joins and exports one file
  that plays on WhatsApp and iMessage. Use when someone asks for a birthday video, a happy birthday message, a
  birthday song with a name, a birthday surprise, a video for a friend's, partner's, mom's or dad's birthday,
  a milestone birthday (18, 30, 40, 50, 60, 80), a pet's birthday or a birthday invitation. Not for weddings,
  anniversaries and holiday greetings (use varg-occasion-video) or a business sending birthday videos to every
  customer (make-personalized-videos-at-scale on varg how to).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to/make-a-birthday-video
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection (https://mcp.varg.ai/mcp).
  ffmpeg for scripts/assemble.sh (joining clips and laying the song).
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(bash:*) Read Write Edit
---

# Personalized AI birthday video

A name, an age and one to twenty photos in; a 15–60 s video that is unmistakably theirs out: their name sung on
the hook, their face (or their dog's), the details only their people know. Generic "Happy Birthday" templates
are what everyone already gets; the reason to make one with an agent is that it can be about one person.

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server
`https://mcp.varg.ai/mcp` (`generate_image`, `generate_video`, `generate_music`, `call_tool`, `get_job`,
`estimate_cost`). Quote the price of every clip before it runs.

## 1. Ask five things, then go

1. **Who and how to say it:** the name as they spell it and how it sounds, the age (or "don't say it"), and who
   is sending it (partner, best friend, kids to a parent, a team).
2. **Three true details:** a habit, a place, a joke, a pet, a dream. They go into the song and the scenes.
3. **Photos:** one clear, front-facing photo of the birthday person for a face that must match (more angles
   help), or 6–20 photos across the years for a montage. Ask whether they agree to their face being animated; for
   a surprise, the sender vouches for it. Never animate a stranger's or a celebrity's face.
4. **The format** (section 2) and the tone: funny, heartfelt, epic or cute.
5. **Where it plays:** WhatsApp or iMessage (9:16, under 60 s, under 16 MB), an Instagram story (9:16, 15 s
   parts), or the TV at the party (16:9, 60–120 s). Ask the date: if it is today, pick a format that is done in
   one pass (A or B).

## 2. Pick the format

| | Format | What it is | Made with | Credits (tested) |
|---|---|---|---|---|
| A | **The song with their name** | An original song with the name on the chorus, over their photos or one clip | `eleven_music_v2_5` + photos | ~8–10 per song |
| B | **Their photo comes to life** | Their photo, a cake with the name piped on it, they blow out the candles, confetti | `gpt_image_2_5` still → `wan_3` or `seedance_2_5` | ~22 + 100 (Wan, 10 s) or 339 (Seedance, 8 s, audio) |
| C | **Then and now** | Baby photo to today: each photo becomes the next, the age counting up | photos → `kling_v4` or `seedance_2_5` first/last frames | ~80–200 per transition |
| D | **The trailer of their life** | An epic movie trailer starring them, title card "{NAME}: {AGE}" | face sheet → `seedance_2_5` multi-shot | ~340 per 8 s shot |
| E | **The pet's birthday** | The dog or cat in a party hat, the cake made for dogs, a tiny party | pet photo → `gpt_image_2_5` → `wan_3` | ~120 |
| F | **Animated card or invitation** | A 3D, clay, paper pop-up or watercolor card that opens to the message | `gpt_image_2_5` → `wan_3`, or HyperFrames for the text | ~25–120 |

Formats, the prompts that made the viral examples and their styles: `references/formats.md`,
`references/styles.md`. The song: `references/song.md`.

## 3. Stills first, then motion

1. **Make the key still** with `gpt_image_2_5` (it spells short words right: put the exact text in quotes and
   spell it out, "the words "MAYA 30", spelled M-A-Y-A then 3-0"). With a face, pass the photo as the reference:
   `generate_image { prompt, reference_image }` or `POST /v2/image` with `files`. Look at it at full size before
   spending on video: the face, the hands, the text, no logos.
2. **Animate it** with the still as the first frame (`POST /v2/video` with `files: [{url}]`):
   `wan_3` (best value, 2–30 s) or `seedance_2_5` (native sound: the breath, the cheers, the crackle). Write the
   action in timed beats and say what must not change ("the letters MAYA 30 stay exactly the same").
3. **Make the song** (`references/song.md`) and transcribe it to find where the name is sung.
4. **Join and export** with `scripts/assemble.sh` (below).

```bash
# key still
curl -s -X POST https://api.varg.ai/v2/image -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt_image_2_5","aspect_ratio":"9:16","prompt":"<still prompt>","files":[{"url":"FACE_PHOTO_URL"}]}'
# animate it
curl -s -X POST https://api.varg.ai/v2/video -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"wan_3","duration":10,"aspect_ratio":"9:16","files":[{"url":"STILL_URL"}],"prompt":"<timed action>"}'
# poll: GET https://api.varg.ai/v2/jobs/<id> until status is completed, then output.outputs[0].url
```

## 4. Join, lay the song, export

```bash
bash scripts/assemble.sh -s 9.5 -k birthday.mp4 song.mp3 clip1.mp4 clip2.mp4
```

It scales every clip to 1080×1920 (`-W 1920 -H 1080` for a TV), joins them, starts the song at the given second
(the line before the first sung name), keeps the clips' own cheers under it (`-k`), fades out, normalizes to
-14 LUFS and writes H.264 + AAC with faststart: the file WhatsApp, iMessage and Instagram play without
re-encoding. Cut a clip before it goes wrong with `ffmpeg -i in.mp4 -t 4.6 -c:v libx264 -c:a aac cut.mp4`.

## 5. Check before you send

- The face is theirs in every shot (eyes, hairline, skin, glasses). If it drifts, use fewer seconds per shot or
  `varg-consistent-characters`.
- The name is spelled right on every surface it appears (cake, banner, title) and in the song's transcript.
- Candles: once blown out they stay out. In our Wan 3 test they lit again at 4.8 s; cut before that or ask for
  "the candles stay out, only smoke rises".
- Five fingers, no melted cake, no extra guests appearing from nowhere, no brand logos on the cake or balloons.
- It plays with the sound off: the name and the age are on screen, not only in the song.

## Tested

2026-10-30, a fictional 30-year-old "Maya" (no real person): the key still on `gpt_image_2_5`, 9:16 (22 credits,
"MAYA 30" spelled right on the first try); `seedance_2_5`, 8 s, 720p, with sound, from the still (308 credits: one
breath, the candles stay out, smoke, confetti, hands to the mouth, the face steady, the cheers in the native
audio); `wan_3`, 10 s from the same still (100 credits: the same action, but the candles lit again at 4.8 s, so
that cut ends at 4.6 s); the song on `eleven_music_v2_5`, 32 s (8 credits, every line and the name sung, vocal
from 9.9 s); `lyria_3_5` refused the name "Maya" and the traditional lyric but sang "Lena". Whisper transcription
5 credits. `assemble.sh -s 17.8 -k` put "make a wish, Maya, blow the candles out" on the blow-out (-14.3 LUFS):
https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_7e6d05077855.mp4

## Rules

- Consent: animate a real person's face or clone their voice only with their agreement (for a surprise, the
  sender's word that the person would want it). Never a celebrity, a public figure or a stranger.
- Children: make a child's birthday from drawings, toys, a pet or a cartoon character you invent, not by
  animating the child's real photo. Keep the files private.
- Music: write original lyrics; do not use commercial songs, and do not quote the traditional verse in Lyria.
- If it goes on public social media, say it was made with AI where the platform asks (TikTok, Instagram, YouTube
  label realistic AI content).

## Related skills

`varg-occasion-video` (weddings, anniversaries, holidays, invitations), `varg-music-video` (a full music video
from the song), `varg-consistent-characters` (the same face in every shot), `hyperframes` (lyric captions,
title cards, photo montages rendered from HTML), `varg-ai` (models and prices).
