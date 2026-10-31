---
name: kling-4-action-montage
description: >-
  Turn three or four key frames into a 30-second action montage with Kling 4 (kling_v4): a
  breakdance battle, BMX or skate tricks, a scooter or bike chase through traffic, parkour or a
  sports highlight, with a crash or punchline at the end. A one-line prompt over strong stills,
  "no slow motion", the trick names, the end state as the last still, and how to pick the usable
  seconds. Includes a tested varg call with the reference route pinned. Use when someone wants an
  AI action montage, a dance or trick sequence, an extreme sports clip, a chase, a "fail" ending,
  or fast-cut energy in one Kling 4 generation. For a full story use kling-4-keyframe-film; for
  prompt rules use kling-4-prompting.
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
  (https://mcp.varg.ai/mcp). ffmpeg to cut the pieces you keep.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# A 30-second action montage from key frames on Kling 4

Kling 4 knows what a tail whip, a head spin or a freeze looks like and can string several of them into one 30-second take with its own cuts, camera moves and sound. What it needs from you is the look and the key poses, as stills. The prompt can be one line. This is how the breakdance, scooter and BMX sequences in fal's Kling 4 Halloween film were made ([YouTube, 2026-10-30](https://www.youtube.com/watch?v=WzXKggH-0Io)): "really high level prompt, but extremely guided visually".

Generation runs on varg: REST `https://api.varg.ai/v2` (the `varg-ai` skill) or the MCP server `https://mcp.varg.ai/mcp`.

## 1. Ask, then go

- **Action:** breakdance, BMX, skate, scooter, parkour, a chase, a sport. Name 2–3 moves (tail whip, bar spin, ollie, head spin, freeze).
- **Place:** a real spot with a look (a park arch, bridge banks, a hill with tram rails).
- **Ending:** a landing, a crash, a reaction line ("Sick run, want to go again?"), or none (a pure loop of moves).
- **Frame:** 21:9 for a film, 9:16 for Reels and TikTok. Lens: ultra-wide fisheye is the classic sports-video look.
- **Cost:** 30 s at 1080p ≈ $7.05 (705 credits); 15 s at 720p ≈ $2.36. Expect to keep 5–12 s from a take.

## 2. Three or four stills

Make them on `gpt_image_2_5` with the character and look references ("Image 1 is the rider to match exactly…", see `kling-4-prompting` section 4). Pick:

| Still | What it fixes |
|---|---|
| 1. The opening pose | Look, lens, crowd, where the camera is |
| 2. A peak move (mid-air, upside down) | The hardest pose, so Kling does not invent it |
| 3. A second move or angle (overhead, from behind) | Variety; Kling cuts between the angles |
| 4. The end state (the crash, the landing, the reaction) | Where the take has to arrive |

Rules from the film:
- **Clean anatomy and gear in every still.** A BMX with no seat and a missing peg in the middle still made that trick the weakest part of the take; the take-off from a clean still was "really good".
- Ask for motion blur, steam, dust or spray in the stills: it reads as speed and hides AI smoothness.
- Keep crowds blurred and at the frame edges. In a 30 s take "there's funny business going on" in the background.

## 3. The prompt: one line, the moves, the speed, the end

```
the <character> break dances in <place> while everyone bobs their heads to the 90s hip hop
beats. shaky handheld footage. 30 seconds.
```
```
Kling 4 21:9 montage of the <character> riding a scooter and pushing super fast through
<city> traffic. 30 seconds. No slow motion, everything is moving at a high speed with motion blur.
```
```
montage of the <character> doing BMX tricks on <place>. tail whip. bar spin. Then he messes up
the trick mid air and crashes to the ground. <the other character> helps him up. she says
"Sick run, want to go again?" 30 seconds.
```

- **Always say "No slow motion"** for speed. Kling 4 defaulted to slow motion in many first tests, and in our test a "no slow motion" ollie still floated for two seconds: give the peak and the landing as separate stills when timing matters.
- Name the moves; don't describe them. Kling knows the tricks.
- Put the spoken button line in quotes, last.
- For a fixed order (moves → crash → line), use `multi_prompt` with seconds per shot (see `kling-4-prompting`), all in one place. A cut to a new location inside one take looks like a broken splice: give the new place its own take.
- Trim the first second of every take (the head can twitch while Kling settles in) and cut the montage from 2–5 s pieces; never post a raw take.
- To get a specific real move right, add a 3–30 s clip of it as `@Video1` ("the rider performs the trick from @Video1").

## 4. Run it

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video/call -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "fal:fal-ai/kling-video/v4/reference-to-video",
  "prompt": "<the one-line prompt>",
  "files": [{"url":"STILL_1"},{"url":"STILL_2"},{"url":"STILL_3"},{"url":"STILL_4"}],
  "aspect_ratio": "21:9", "resolution": "1080p", "duration": 30, "audio": true}'
```

Pin the reference route as above: with plain `kling_v4`, one or two stills go to image-to-video as start and end frame (and, before api#239 is live, a third one was dropped). Price with `estimate_cost` / `POST /v2/estimate` on `"model": "kling_v4"` with the same duration and resolution. Draft at 720p first.

## 5. Pick the seconds

Watch the take with the sound off first, the way the author did: mark each piece as usable or not ("bad dance, bad… that is good, that's a good go down… pretty good freeze"). Typical keep rate: a third of the take.

- Keep moves that land and new angles Kling found ("that's a very cool angle, that's a new angle").
- Drop pieces with extra fingers, merged limbs, a board or bike that changes shape, or nonsense tricks ("that bar spin makes no sense").
- Shots that came from your stills look sharper than shots Kling invented; prefer them for the hero moments.
- Cut on the action and join on the beat (`varg-music-video`), or keep the take's own sound for the crash and the line.

```bash
ffmpeg -ss 4.2 -to 8.0 -i take.mp4 -c:v libx264 -crf 16 -c:a aac keep_01.mp4
```

## Tested

2026-10-30, our own scene: a skateboarder bombing a Lisbon hill. The example is one continuous 8 s shot from one `gpt_image_2_5` still: push toward the lens, a snappy ollie over the tram rails, the landing, a close-up and "Again?". Plain `kling_v4` with the still as the start frame, 720p, audio, "One continuous shot, no cuts", "lands in under a second", "no slow motion": 126 credits ($1.26), no cuts, about half a second in the air. https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_0665c41e46ff.mp4

The first try (three stills, a three-shot `multi_prompt` that moved her to a viewpoint, 15 s, 236 credits) failed: a camera fly-through between shots, a two-second floating ollie and a cut that looked like a broken splice. For one trick, one place, one take. Details: `kling-4-prompting/references/test-run.md`.

## Related skills

`kling-4-prompting` (inputs, prompt rules, failure table), `kling-4-keyframe-film` (a whole film from several takes), `varg-character-design` (the rider or dancer), `varg-music-video` (cut the montage to a track), `varg-ai`.
