---
name: kling-4-keyframe-film
description: >-
  Make a cinematic short film, music video or story video with Kling 4 the way it works best:
  beat sheet, a cast and look reference, every key shot made as a still on GPT Image 2.5, then one
  30-second Kling 4 reference-to-video take per beat from two to four stills and a short prompt,
  then cut the usable seconds like live-action takes. Includes the still prompt template ("Image 1
  is the man to match exactly…"), the take prompt, dialogue scenes, a fix pass for faces and
  hands, costs and the varg calls. Use when someone wants a short film, music video, Halloween or
  holiday film, comedy sketch, trailer or narrative scene made with Kling 4 (kling_v4), asks how
  to get cinematic Kling 4 results, or says their Kling 4 output looks like AI slop. For prompt
  rules only use kling-4-prompting; for a single action montage use kling-4-action-montage.
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
  (https://mcp.varg.ai/mcp). ffmpeg to cut and join takes.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# A short film with Kling 4: stills first, 30-second takes, cut like live action

Kling 4 animates well and badly frames shots it invents. So the image model does the cinematography and Kling 4 does the acting, motion, voices and the in-between. This is how fal's Kling 4 Halloween music video was made ([YouTube, 2026-10-30](https://www.youtube.com/watch?v=WzXKggH-0Io)): about 18 key stills on GPT Image 2.5, mostly 30-second Kling 4 takes at 1080p 21:9, then an edit that kept the best seconds of each. Prompt rules and the failure table live in `kling-4-prompting`.

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp`. Price every take first (`POST /v2/estimate` or `estimate_cost` with `"model": "kling_v4"`).

## 1. Ask, then go

- **Story:** 3–6 beats, one sentence each (setup, joke or turn, action, payoff, button line). A 60–90 s film is 3–6 takes.
- **Cast:** a photo or sheet per character (`varg-character-design`), the outfit written as a list of details.
- **Place:** a real, named location if possible ("Washington Square Park", "the Brooklyn Banks"). GPT Image 2.5 researches real places well, which Kling 4 text-to-video does not.
- **Look:** aspect ratio (21:9 for cinema, 9:16 for social), lens (ultra-wide fisheye, 35 mm, telephoto), film stock and grade, grain, motion blur. One look image (a frame you like) used as "reference only for color grade".
- **Budget:** a 30 s take at 1080p ≈ $7.05 (705 credits); at 720p about two thirds of that. Plan 2–4 takes per beat.

## 2. Key stills on GPT Image 2.5

One still per moment Kling must hit: the opening of each beat, any shot with a specific angle (over-the-shoulder, overhead), the peak of an action, the end state. Template:

```
Cinematic <21:9> film still, <angle>, <lens and distortion>.
Use the <N> reference images: Image 1 is <person> to match exactly: <face, hair, glasses,
cap, top with text, trousers, shoes>. Image 2 is <person> to match exactly: <…>.
Image 3 is a reference only for <the bike / the prop> (do NOT show <what to leave out>).
Image 4 is a reference only for color grade, <film stock> tone, grain and motion blur; do not
include its people.

Scene: <who is where doing what, in the present tense, mid-motion, with blur on what moves>.
<Background people, blurred, at the frame edges>. <Light>.
<Film look> like Image 4: <highlight color>, <shadow color>, deep blacks, coarse grain, motion
blur. Avoid text overlays, clean digital look, <wrong props>, <wrong time of day>.
```

```bash
curl -s -X POST https://api.varg.ai/v2/tools/image/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{"model":"gpt_image_2_5","prompt":"<still prompt>",
  "files":[{"url":"CAST_1"},{"url":"CAST_2"},{"url":"PROP"},{"url":"LOOK"}],"aspect_ratio":"21:9"}'
```

- Check each still before you animate: hands, the bike or board, faces against the cast photos. A warped object in a still becomes the worst part of the take.
- Block the scene across stills so it makes sense in time: if he walks past her in still 1, he is on her other side in still 2.
- Make the second angle of a dialogue (the over-the-shoulder) as a still too; do not leave it to Kling.

## 3. One take per beat

Pin the reference route (with plain `kling_v4`, two files become start and end frame and a third is not used):

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "fal:fal-ai/kling-video/v4/reference-to-video",
  "prompt": "<beat prompt>",
  "files": [{"url":"STILL_A"},{"url":"STILL_B"},{"url":"STILL_C"}],
  "aspect_ratio": "21:9", "resolution": "1080p", "duration": 30, "audio": true}'
```

The beat prompt is short: what happens in order, the line in quotes, the camera event, the look, the length.

```
21:9 the man walks by the woman as she places a white pumpkin on the table. the man says
"what does the white one do?" she smiles and smashes the white pumpkin on the top of the man's
head with both hands. The camera shakes and falls to the ground and fades to black. handheld
shaky 16mm documentary style footage. 15 seconds.
```

- Order matters when you need it: use `provider_options.fal.multi_prompt` with seconds per shot (see `kling-4-prompting`). Keep each take in one place; a location change is a new take, cut in the edit.
- Dialogue: Kling 4 makes the voice itself. For the same voice in every take, make an element with a `voice_id` (front photo + 1–3 more angles) and write `@Element1 says "…"`.
- Action: add "No slow motion, everything moves at real speed, motion blur."
- Draft at 720p; rerun the chosen take at 1080p with the same stills and prompt.

## 4. Cut it like live action

A 30 s take holds several cuts, retries of the same move and a ramp-up. Watch it at full speed, mark the 2–6 s pieces that work (a clean landing, a good line read, a new angle you did not ask for) and drop the rest. From the film: "I ended up using the ending part of it", "we used that double tail whip… that's the crash we used", "this shot made the final cut".

```bash
ffmpeg -ss 12.4 -to 17.9 -i take3.mp4 -c:v libx264 -crf 16 -c:a aac piece_07.mp4
printf "file '%s'\n" piece_*.mp4 > list.txt && ffmpeg -f concat -safe 0 -i list.txt -c copy film.mp4
```

Lay the music last over the whole cut (`varg-music-video` for beat-synced cuts).

## 5. Fix pass

| Problem in a take | Fix |
|---|---|
| A close-up changed someone's face | "Same sequence, add this reference of what she looks like" + her photo; for a lasting lock make her an element with 2–4 photos. |
| An element job fails at once | The element has one photo. Add more angles (or the same photo twice as a last resort). |
| Shots Kling invented look softer and more "AI" | Make that shot as a still too, or use it only as a short bridge. |
| A trick or dance move is nonsense | Rerun, or add a real reference clip of the move as `@Video1` (3–30 s). |
| Wrong lens on an invented shot | Name the lens for that shot. |
| Odd behaviour in the background crowd | Cut around it; keep crowds blurred at the frame edges in the stills. |

## 6. Kling 4 or Seedance 2.5?

With the same pre-made stills, references and lighting, they are "very comparable"; Kling 4 is sharper and does 30 s takes with dialogue, Seedance 2.5 does better with only sheets and a long prompt. Pick Kling 4 when you have (or will make) the stills; pick Seedance 2.5 when you want the video model to invent the shots.

## Example plan (60 s, 21:9)

| Beat | Stills (GPT Image 2.5) | Take |
|---|---|---|
| Setup + joke line | wide: he walks past her stall; OTS on her | 15 s dialogue, camera falls, fade to black |
| Action 1 | 3 dance poses in the crowd ring | 30 s, "everyone bobs their heads", shaky handheld |
| Action 2 | rider between cabs, overhead, steam | 30 s, "no slow motion, high speed, motion blur" |
| Climax + button | 3 tricks + the crash with her helping him up | 30 s, tricks, crash, her line in quotes |

About 13 stills (≈ $3) and 4 takes at 1080p (≈ $26), more for retries; keep 60 s.

## Related skills

`kling-4-prompting` (inputs, prompt rules, failure table), `kling-4-action-montage`, `varg-character-design`, `varg-consistent-characters`, `varg-music-video`, `varg-ai`.
