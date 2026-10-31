---
name: varg-occasion-video
description: >-
  Turns a few photos and the details of an occasion into an AI video on varg: a wedding or birthday invitation and
  save-the-date that unfolds (the names and date printed right), a Christmas, New Year, Diwali, Eid or Lunar New
  Year greeting the family forwards, old family photos brought to life, a love story across the eras for an
  anniversary, and a calm memorial or tribute film. Asks what the occasion needs, makes the stills first (GPT Image
  2.5 prints names and dates), animates them (Seedance 2.5 first and last frames, Kling 4, Wan 3), adds music and
  exports for WhatsApp, a party screen or a service. Use when someone asks for a video invitation, an e-invite, a
  save-the-date, a wedding invitation video for WhatsApp, a holiday or festival greeting video, an animated
  e-card or Christmas card, "bring old photos to life", an anniversary or love-story video, or a memorial,
  celebration-of-life, retirement or farewell tribute. Not for birthdays (use varg-birthday-video) or editing real
  wedding footage (varg-video-editing).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to/make-birthday-and-occasion-videos
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection (https://mcp.varg.ai/mcp).
  ffmpeg for scripts/assemble.sh (joining clips and laying the music).
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(bash:*) Read Write Edit
---

# Invitations, holiday greetings, old photos and tributes

The occasion sets the rules: an invitation must carry the names, the date and the place without a single wrong
letter; a holiday greeting must be forwardable to a family group; old photos must still look like the people;
a tribute must stay calm. Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP
server `https://mcp.varg.ai/mcp` (`generate_image`, `generate_video`, `generate_music`, `call_tool`, `get_job`,
`estimate_cost`). Quote the price before anything runs.

## 1. Which occasion

| Occasion | What people want (searches, Oct 2026) | Format | Reference |
|---|---|---|---|
| **Invitation / save-the-date** | "ai wedding invitation video", "save the date video", "invitation video for whatsapp" (851 suggestions) | A card or envelope that opens onto the names, date and place; 15–30 s, 9:16 | `references/invitations.md` |
| **Holiday greeting** | "ai christmas video", "christmas card video", "ai new year video", Diwali, Eid (386) | An animated card, a snow globe, a lamp-lit story, a family scene; 10–30 s | `references/holidays.md` |
| **Old photos brought to life** | "animate old photos", "bring old photos to life" (222) | Restore, then a gentle motion per photo, cut to music | `references/old-photos.md` |
| **Anniversary / love story** | "ai anniversary video", "ai wedding video" (339) | The couple across the eras, ending where they met | `references/old-photos.md` |
| **Memorial / tribute** | "memorial video ai", "celebration of life video", "retirement tribute video" (254) | Restored photos, slow motion, words from the family | `references/old-photos.md` |

## 2. Ask, then go

- **Exact words:** names as they are written, the date, the time, the place, the RSVP line, the greeting. Read them
  back to the person before you generate anything that prints them.
- **Photos:** the couple or the family (with their agreement), old prints scanned flat, or none (an illustrated
  card needs no face).
- **Style:** pick one look (`references/styles.md`): pop-up card, envelope, illustrated card, snow globe, diya glow,
  1990s film, cozy holiday still, retro home video.
- **Where it goes:** WhatsApp or iMessage (9:16, under 60 s, send as a document to keep quality), Instagram
  story (9:16), a screen at the venue or the service (16:9).
- **Music:** an original track (`eleven_music_v2_5` for a song with words, `mureka_9_5` for an instrumental) or a
  public-domain piece; never a commercial song on a public post.

## 3. Stills first, then motion

1. **Print the words on a still** with `gpt_image_2_5`: quote every word and spell it ("the words "ANNA & LEO" and
   below "12 JUNE 2027 · LISBON", spelled exactly like that"). Read the still at full size; if one letter is wrong,
   regenerate. For anything longer than a line or two, leave the space empty and add real type later (HyperFrames or
   an editor): generated paragraphs smudge.
2. **Make the matching first frame** as an edit of that still (`generate_image` with `reference_image`): the card
   closed, the envelope sealed, the photo still faded. Same table, light and angle.
3. **Animate between them** with `seedance_2_5` first and last frames: `files: [first, last]` and
   `provider_options: {piapi: {input: {mode: "first_last_frames"}}}`. The model moves from the closed card to the
   open one, so the words land exactly as printed. For a single photo, image-to-video on `kling_v4` or `wan_3`.
4. **Music and export** with `scripts/assemble.sh` (scales, joins, lays the track, -14 LUFS, H.264 + AAC).

```bash
curl -s -X POST https://api.varg.ai/v2/video -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"seedance_2_5","duration":8,"aspect_ratio":"9:16","resolution":"720p","audio":true,
       "files":[{"url":"CLOSED_CARD_URL"},{"url":"OPEN_CARD_URL"}],
       "provider_options":{"piapi":{"input":{"mode":"first_last_frames"}}},
       "prompt":"<timed beats: the card opens, the paper scene rises, the names settle; paper sounds>"}'
bash scripts/assemble.sh -s 0 invite.mp4 music.mp3 clip.mp4
```

## 4. Check before you send

- Every name, date and place matches what the person gave you, letter by letter, in the last frame.
- Faces still look like the people (eyes, smile lines, glasses); old photos keep their grain and era.
- Nothing extra appears: no new guests, no rings or logos, no extra pages on a card.
- A festival greeting shows the festival respectfully: lamps, food, family, lights; no deities unless the family
  asks for them.

## Tested

2026-10-30, a fictional couple "Anna & Leo": the open pop-up invitation on `gpt_image_2_5`, 9:16 (22 credits,
the names and "12 JUNE 2027 · LISBON" spelled right on the first try), the closed card as an edit of it (23
credits), then `seedance_2_5` first and last frames, 8 s, 720p, with sound (280 credits): the cover swings open,
the paper arch rises layer by layer, and the names and date land sharp and unchanged in the last frame, with paper
sounds and a music-box chime. https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_e1ac8b0f8d63.mp4

Old photo, a fictional 1962 seaside couple: `nano_banana_2_1` restore and colorize as an edit (5 credits, both faces
kept), then 5 s of gentle motion on `kling_v4` (79 credits: she turns to him and laughs, he smiles down at her, a
slow push-in, the faces and the 1960s color and grain kept).
https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_34e07d214ef1.mp4

## Rules

- Consent: animate a living person's face, or a family's old photos, only with their or the family's agreement.
  Never a celebrity, a public figure or a stranger.
- The dead: no party effects, no making them speak or sing unless the family asks; keep the film private unless
  they want it shared.
- Children: use the family's own photos only, deliver privately, never post a child's face publicly.
- Label realistic AI footage as AI when it is posted on social media.

## Related skills

`varg-birthday-video` (birthdays, the song with the name), `varg-consistent-characters` (the same faces in every
shot), `hyperframes` (real type, envelopes and title cards rendered from HTML), `varg-video-editing` (real
wedding footage), `varg-ai` (models and prices).
