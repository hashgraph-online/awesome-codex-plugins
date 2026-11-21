---
name: varg-previz
description: >-
  Plan and pre-visualise any multi-shot AI video before spending credits on varg - music videos, ads and product promos, UGC-style spots, trailers, short films, explainers. Collect film references into a moodboard, write the story (Hero's Journey, hook-problem-payoff, 3-act), lock character/product/vehicle sheets and one master plate per location, group shots into master scenes, block every camera in a three.js grey-box previz on the timeline (auto cameras from plain storyboard words like "MCU, 3/4 left, push in"), then export clean previz clips as @video1 references for Seedance 2.5 video-to-video and run one short generation per scene. Any aspect ratio, with or without a song; lock voice, music and beats before picture. Use when the user asks for a previz, a 3D animatic, camera blocking or approval, shot lists, scene grouping, character or product sheets, story structure for a clip or ad, or a Seedance video-to-video pack, a moodboard or references for a video.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      bins:
        - python3
    homepage: https://varg.ai
compatibility: >-
  The previz app needs python3 (local server) and a browser; three.js is vendored, no npm.
  Clip capture needs bun + playwright-core + Chrome/Chromium; the pack build needs ffmpeg.
  Generation needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY.
allowed-tools: Bash(python3:*) Bash(bun:*) Bash(bunx:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(curl:*) Bash(shasum:*) Read Write Edit
---

# varg previz: refs → story → sound → anchors → 3D previz → Seedance v2v

AI video models redraw the world on every call. A previz fixes what they are worst at, camera, geography, scale and
timing, for free before the paid step. It is a cheap grey-box: it approves cameras and blocking, never the look.

Built on a 36-shot, 99 s music video ("I Don't Wanna Pick", 9:16, 133.8 BPM) and tested on a 6-shot product ad.
The app is in `templates/previz/`; `scripts/new_previz.py` sets it up in a project.

## Pick the depth first

| project | do |
|---|---|
| 1–3 shots, simple camera | skip the previz: a short moodboard (step 1), audio lock if there is a line (step 4), anchors (step 5) + image-to-video |
| 4–15 shots, one or two places, ad / UGC / promo | steps 1–5, auto cameras from the storyboard, a quick approval pass in the previz, pack |
| music video, trailer, short film, anything with geography, scale or many places | everything below |

Step 4 (audio lock) applies at every depth when there is voice-over, dialogue or a song; skip it only for silent
pieces.

## The pipeline (in this order)

1. **References and moodboard**: before the story, collect 3–5 frames from one aesthetic (Film-Grab, ShotDeck,
   Shot Cafe, Eyecannndy, Pinterest). Search by feeling and by attribute, not by subject; pick the specific,
   recognisable edge on purpose; borrow the look, never characters or logos. `refs.md` says what each frame gives
   (palette, framing, lens, light, texture, motion); `moodboard.md` writes the look in words plus a "Never" list of
   5 things it would never do. Without it the agent picks the safe middle version
   (https://x.com/ScaleWthAI/status/2111821935021863254). → `references/references-and-moodboard.md`
2. **Story**: pick a structure for the format and map it onto the timeline (song sections, VO beats or seconds).
   One story beat per section, the hook in the first 2–3 s. → `references/story-structure.md`; write and check the
   lines themselves with the `video-script` skill (word budget per beat, hooks, checker).
3. **Storyboard**: `storyboard.json` is the single source of truth for timing. Every shot gets `id, start, end, scene,
   set, picture, action, camera`, plus `line` (lyric/VO), `beat`, `overlay`, `source` as needed. Cuts on downbeats
   when there is a song; this is a draft that step 4 re-times to the locked track. → schema in
   `references/threejs-previz.md`
4. **Audio lock** (any VO, dialogue or song): sound and voice are approved before any picture. Write the lines with
   pauses, breaths and small actions (five dialogue fixes from
   https://x.com/second_bassoon/status/2117307653320007954); audition 2–3 voices on the hardest line and let the
   person pick; render the lines, make or measure the music; write `beats.json` with every beat, line, pause and SFX
   timestamp; re-time the storyboard so every cut lands on this track. → `references/audio-lock.md`
5. **Anchors**: character sheet, product/vehicle sheet with a human for scale, antagonist sheet if any, ONE master
   plate per location, all in the moodboard's look. Close-ups are generated from the master. Once the previz exists,
   make plates by image-editing a previz render ("keep camera and geometry exactly") instead of from text.
   → `references/character-sheets.md`
6. **Master scenes**: group shots by location; each scene becomes one or more 4–11 s Seedance runs.
   → `references/scene-grouping.md`
7. **3D previz**: `python3 <skill>/scripts/new_previz.py <project>` then `python3 <project>/previz/serve.py`.
   Build one grey-box set per location, check every auto camera against the locked track, fix the bad ones in the UI,
   approve each shot, save, export the camera plan. Check frames in headless Chrome. → `references/threejs-previz.md`
8. **Seedance pack**: `build_pack.py --check`, capture clean clips, build the pack (one @video1 per run + only the
   stills of what is in frame + prompts), review the board, estimate, then generate. → `references/seedance-v2v.md`

Spend nothing before step 8 except cheap voice auditions and the music bed (step 4) and cheap anchor stills (step 5),
each estimated and approved first. Steps 1, 2, 3, 6 and 7 are free, and the director's notes cost least there.

## Hard rules learned the expensive way

- **Sound first, picture second.** Once the track is locked, every cut, hit and lip-sync shot is timed to
  `beats.json`. A changed line after the lock is a re-time of the storyboard and the previz, not a quick fix.
- **One location = one master plate = one set.** Wide and close coverage of a place share the same set and refs, or
  faces, layouts and lighting drift between shots.
- **References only for what is in frame.** A sheet that also shows the monster pulls the monster into a shot that
  should not have it, so crop. Never use an exterior still as a ref for an interior scene. When a shot is rewritten,
  its old still is stale: flag it (`needs_new_still`), do not feed it to the model.
- **Narrow frames hide things.** Horizontal half-FOV = atan(tan(vFOV/2)·W/H). At 9:16 and vFOV 55° a subject 17°
  off-axis is out of frame. Check every camera in the map view: cameras end up inside walls, behind headrests, or
  inside a subject that walks into them.
- **Scale is explicit.** Put a human on every vehicle/product/creature sheet and state the ratio in every prompt
  (car ≈ 2.5× a person, ship ≈ 5×, monster ≈ hundreds of ships); otherwise models draw a man as big as his ship.
- **No text from the model.** "No text, letters, numbers, logos or UI" in every prompt. Lyrics, captions, prices,
  HUD and logos are drawn later in code (HyperFrames). Text labels are hidden in exported reference clips.
- **Price before you promise.** Run `estimate_cost` on one real request, quote it as the ceiling, report the billed
  cost after (`get_job_cost`). Check `check_balance` and which team the connection bills (`get_current_team`).
- **Ask before spending and before switching the billing team.** Uploading and generating are outward actions.
  Test one short run before a batch (`build_pack.py … --runs <key>`).
- **Record the director's words verbatim** in `brief.md` with the date; apply each note to the storyboard, scene
  table, treatment and previz in the same pass so they never disagree.

## Deliverables

- `refs.md` (frames and what each gives), `moodboard.md` (palette, light, framing, texture, type, motion, "Never"
  list)
- `brief.md` (the director's words, dated, and the chosen voice), `treatment.md` (logline, structure with timings,
  colour script, recurring markers, references)
- `lines.md`, `assets/audio.wav` (the locked track), `beats.json` (beats, lines, pauses, SFX timestamps) when there is
  sound
- `storyboard.json` + `scenes.md` (scene table: shots, cut time, gen length, refs, cost)
- `previz/` (three.js app, `config.json`, `data/edits.json`, `camera_plan.md`)
- `previz/seedance/` (`pack.json`, `video/video_XX__<run>__<shots>.mp4`, `refs/`, `PROMPTS.md`, `requests.json`,
  `index.html` board, `jobs.json` once submitted, `out/` results)

## Related skills

`video-animate` (what to do once the previz is approved: code or AI, which model, cheap pass, takes, sound, plates for motion design),
`varg-ai` (single generations, rendering), `hyperframes` (text, captions and graphics drawn in code on top of the
clips, final assembly), `varg-music-video` if installed (song measurement, lip-sync pass, platform masters).
