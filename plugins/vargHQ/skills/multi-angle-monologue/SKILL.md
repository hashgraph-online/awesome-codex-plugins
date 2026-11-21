---
name: multi-angle-monologue
description: >-
  Make a one-minute character monologue that plays like a filmed scene: one base still, three
  more camera angles of the same moment, one voice track with acting tags, the audio cut into
  parts under 15 seconds at the pauses, each part lip-synced to its own angle with a performance
  prompt, then an edit that changes angle on every part. Includes the angle prompts, the voice
  script format with bracketed directions, the per-shot performance prompt, the varg calls and
  the checks. Use when someone wants a character to deliver a speech, rant, confession, villain
  monologue, "explains X in character" sketch, parody address or documentary-style interview
  with consistent face and voice for 30 to 90 seconds, or says their talking AI character looks
  like a frozen avatar. For a remake of an existing scene use scene-recast-video; for the joke
  and the rules for real people use ai-parody-video; for a two-host show use varg-podcast-video.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). ffmpeg and ffprobe to cut the audio and join the shots.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# A monologue in four angles: one still, one voice, a cut on every pause

A single talking shot reads as an avatar after ten seconds. The same speech cut across four angles of one moment reads as a scene someone filmed with two cameras. The method is from [@Arminn_Ai](https://x.com/Arminn_Ai/status/2109357287282503941) (X, 2026-10-11), who posted the steps and every prompt for a one-minute character monologue:

1. "Generated the base shot with Nano Banana 2.1, then 3 more angles of the same moment from it: wide, close-up and a side-angle medium close-up"
2. "Cloned the voice with Eleven v4 and generated about a minute of dialogue", "using a different tone in each scene" (this skill designs a voice instead, see section 1)
3. "Cut the audio into parts under 15s and fed each part into MiniMax H3 along with its shot"
4. "Put the generated clips together in an editing app, and that's it"

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp`. Price the batch first (`POST /v2/estimate` or `estimate_cost`).

## 1. Ask, then go

- **Who speaks and to whom:** the character (a photo, a sheet from `varg-character-design`, or a description), and whether they look into the lens or at someone beside the camera.
- **The speech:** the topic and the turn. A monologue needs an arc: calm, a shift, a peak, a last line.
- **Where:** one room, one light, one time of day.
- **The voice:** a designed voice or the person's own. A real person's voice only with their consent (see `ai-parody-video`); an impression is written as a description ("low, tired, dry baritone"), not cloned from recordings.
- **Length and format:** 30 to 90 seconds, 16:9 for a scene, 9:16 for a feed.

## 2. Write the speech for the ear, with directions in brackets

Six to eight beats, each one tone. Directions go in square brackets before the words they act on; sounds a person makes are directions too.

```
[low, tired voice, speaking straight to the listener, quiet room late at night] "<line>"
[soft scoff] <line>. It's not magic. It's... [lips smack] <word>.
[measured, like a teacher explaining to a slow student] <line> in the time it takes you to...
[short pause] <button of the beat>.
[tone turning serious, lower] <the shift>.
[quieter, low and intimate] <the detail that lands>.
[a flicker of irritation, slowly building] <line> ATTENTION.
[sharp, raised voice] <line>? [glass set down hard on the table]
[at the absolute peak, every word hammered] <the last line>.
```

- Ellipses and dashes make pauses; a word in capitals takes the stress.
- Plan the cut points now: a `[short pause]` or a sigh every 8 to 14 seconds.

```bash
curl -s -X POST https://api.varg.ai/v2/tools/speech/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{"model":"eleven_v4","text":"<script with tags>","voice":"<voice id>"}'
```

Listen to all of it. Regenerate a beat that reads flat rather than fixing it in the picture.

## 3. Base still, then three more angles of the same moment

Base still on `nano_banana_2_1` (or `gpt_image_2_5`): the medium shot, the character mid-thought, the room readable, practical light named ("warm bedside lamp from frame left").

Then edit that image, one call per angle, with the base as the only reference:

```
Same scene, same moment, same man, same clothes, same room, same warm lamp light as the
reference. Camera moved to a <wide shot from the foot of the bed, full body, hands on knees /
close-up, head and shoulders, eye level / side-angle medium close-up from his right, 45
degrees>. Nothing in the room changes place. Documentary camera on a tripod, natural skin
texture, natural colour. No text.
```

Check the four stills together before any video: glasses, hairline, collar, the lamp, what stands on the table. A prop that moves between angles is the first thing viewers catch.

## 4. Cut the audio at the pauses, one part per angle

```bash
ffmpeg -i voice.mp3 -af silencedetect=noise=-35dB:d=0.35 -f null - 2>&1 | grep silence_
# cut in the middle of a silence; every part 5 to 15 s
ffmpeg -i voice.mp3 -ss 0 -to 11.8 -c:a pcm_s16le part1.wav
```

Assign angles so that no two neighbours match and the size follows the tone: medium to open, medium close-up for the explaining, wide for a gesture or a prop, close-up for the quiet part, medium for the build, close-up for the last line.

## 5. Lip sync each part with a performance prompt

One job per part: the angle still, the audio part, and a prompt that directs the body, not only the mouth. The template, shortened from the posted prompts:

```
<static camera.> @Image 1 speaks the dialogue from @Audio 1, matching its voice, tone, timing
and pauses exactly. <Shot size> on a tripod with the faint natural drift of a documentary
camera operator. Framing, lighting, wardrobe and the room stay as in @Image 1. <Light>, natural
skin texture, natural colour.
He is <who>, talking to someone <just beside the lens / straight into the lens>. <Mood of this
part>. His head and upper body move naturally with his speech: small tilts, a slight nod on
stressed words, his shoulders rising and falling with each breath. His hands <rest below the
frame and gesture now and then, visible as movement in his shoulders / are on his knees>.
"<line 1>" <what the eyes, brows, mouth and head do on it>. "<line 2>" <the action: leans in,
eyes narrow, looks over the rim of his glasses>. "<line 3>" <...>. After the last word he stops
speaking and holds the look, breathing quietly.
Irregular natural blinking, small eye movements, slight asymmetry in the face, a swallow
between lines, lips and jaw moving precisely with each syllable.
```

- Quote every line of the part in order and put its action right after it. The lines tell the model where in the audio each gesture belongs.
- End every prompt with the hold ("stops speaking and holds the look"). It gives the edit a clean out.
- A physical action (clears his throat into a fist, sets a glass down) goes in the wide shot, where hands are in frame.

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "minimax_h3_max",
  "prompt": "<performance prompt>",
  "files": [{"url":"ANGLE_STILL"},{"url":"PART_WAV"}],
  "resolution": "720p", "duration": 12}'
```

Tested on varg on 2026-11-12 with a 14 s speech cut into two parts:

- `minimax_h3_max` with the still and the audio part in `files` keeps your audio as it is (the pauses in the output land on the same milliseconds) and follows the prompt: asked to "turn his eyes to the lens" on the last line, he did. A 6.4 s part at 720p cost $0.56. The output runs about a second longer than the audio, which is the hold you asked for; trim it in the edit.
- `minimax_h3_max_lipsync` takes one image and audio from 5 s up to 15 min and ignores direction: the lips are right, the head barely moves and the eyes stay where the still put them. A 7.8 s part at 480p cost $0.48. Good for a draft of the whole speech on one angle, not for the performance.
- `estimate_cost` shows the worst case for the lip sync model ($3.60 at 480p); the real charge follows the audio length.
- ElevenLabs v4 does not read the bracketed tags aloud; `[sighs]` and `[whispers]` came out as a sigh and a whisper.

Check the model page for current inputs (https://varg.ai/models/llms.txt).

## 6. Join and check

```bash
printf "file '%s'\n" shot1.mp4 shot2.mp4 shot3.mp4 shot4.mp4 shot5.mp4 shot6.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -crf 17 -c:a aac scene.mp4
# then lay the original voice.mp3 over the whole cut so the level and tone are one piece
ffmpeg -i scene.mp4 -i voice.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest final.mp4
```

| Check | How | Fix |
|---|---|---|
| Lips on the words | Watch each cut point at half speed | Rerun that part; shorten it if it is over 12 s |
| The face is the same person in all four angles | Put a frame from each shot in one row | Regenerate the angle still from the base, not from another angle |
| Props and light hold | Same row of frames | Name the prop and its place in the angle prompt |
| The cut jumps | A cut between two similar sizes | Swap one of them for the wide or the close-up |
| Dead eyes, no body movement | The prompt only described speech | Add the per-line actions and the breathing |
| Room tone drops between parts | Listen on headphones | Use the single voice file over the cut (above); add quiet room tone with `video-sound` |

## Cost of a 60-second monologue (estimate before you spend)

| Step | Count | About |
|---|---|---|
| Base still and three angles, with retries | 6 to 8 images | under $1 |
| Voice, two takes | 2 | under $1 |
| Six lip-synced parts of 10 s at 720p on `minimax_h3_max`, one retry each | 12 runs | about $10 (measured: $0.56 for 6.4 s) |

## Related skills

`ai-parody-video` (the joke, the format, the rules for real people and known characters), `scene-recast-video`, `video-script`, `varg-character-design`, `character-passport`, `video-sound`, `caption-styles`, `varg-character-keynote`, `varg-podcast-video`, `media-judge`, `varg-ai`.
