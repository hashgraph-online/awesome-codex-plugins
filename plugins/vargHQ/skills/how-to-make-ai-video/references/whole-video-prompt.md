# Whole video, start to finish: the prompt

Paste this into your agent when you want a whole video (a launch film, an explainer, a short film, a music video
built from scratch) and not one clip. Fill every `[bracket]`. Delete a step only if you already have its output.

Why this order: without specific references an agent picks the safe, middle version of everything; sound added
last never lines up with the picture; and an agent left alone with paid models can spend a lot on clips that never
make the cut (a 36-minute agent film cost $200+, and "none of the video model clips made it into the video" —
https://x.com/LLMJunky/status/2106411941497389342). Each step below writes one file, and the person approves it
before the next step starts.

The short way: paste the one line below and the agent reads the route itself (https://varg.ai/how-to/make-a-video-in-ten-steps.md, ten guides and ten skills, kept current). Use the long prompt under it when the agent cannot reach the web or you want every step spelled out in the chat.

```text
Make my video in ten steps. Read https://varg.ai/how-to/make-a-video-in-ten-steps.md and follow it: one step at a time, stop for my yes at every STOP, and tell me the cost before anything paid.

The video: [what it is, who it is for, how long, where it will be shown]
```

---

```text
Make a [length, e.g. 45-second] [format, e.g. launch film / explainer / music video] about [subject]
for [audience], shown on [platform] at [aspect ratio, e.g. 16:9 or 9:16].
What it must make people feel or do: [one line].

MONEY
- Spend cap for the whole job: [amount, in credits or dollars]. Do not go over it.
- Allowed paid models: [list, e.g. only the image and voice models I approve]. Ask before any other model.
- Before every paid call, estimate its cost and the running total, and tell me.
- Use video models only for what code cannot draw: real people, crowds, weather, physical motion.
  Everything else (type, UI, charts, graphics, camera moves over stills) is built in code.

WORK IN THIS ORDER. Each step writes one file. At every STOP, show me the file and wait for my answer.

1. References -> refs.md, never.md
   If the find-references skill is installed, follow it. Otherwise read it first:
   https://github.com/vargHQ/skills/tree/main/find-references
   Write the brief, then one query pack per job this piece needs. Light gets the most, then framing, people,
   location, texture, palette, type, motion, music. Run the obvious search first and turn what repeats into
   never.md. Search each source in its own words: no library searches by ratio or Kelvin, so search what is visible.
   Open everything you keep, and prove who made it from records. Never fetch sites that forbid bots (Film-Grab,
   ShotDeck, Shot Cafe, Pinterest): write those searches into links.md for me.
   Each reference gets one job, what not to copy, and a tag: feed, words or look. Any real person is words only.
   Show me three candidates per job. Borrow the look, never characters or logos.
   My own references: [links or "none"].

2. Moodboard -> moodboard.md
   Palette as hex (mark the one accent), light, framing, texture, type, motion,
   and a "Never" list: 5 things this look would never do.
   STOP: I approve the look.

3. Script and storyboard -> script.md + STORYBOARD.md
   Follow the video-script skill: one promise, ten hooks, beats joined by BUT or THEREFORE, one spoken line per
   visual, every line sized to its seconds (about 2.5 words a second), checked with its check_script.py.
   One visual motif that comes back, timings per shot, the camera for every shot, plain narration.
   Write dialogue to be performed: watch the punctuation, break long lines into short ones with pauses,
   put bodily actions between lines (a sniffle, a breath), give each speaker an anchor gesture.
   STOP: I approve the story and the shot list.

4. Sound first -> audio.wav + beats.json
   Lock the voiceover, music and key sound effects before any picture. Offer me 2-3 voice and music
   candidates to pick from. Write beats.json with the time of every cut, hit and word that matters.
   The picture is cut to this file, never the other way round.
   STOP: I approve the sound.

5. Characters and props -> sheets (one image + one "passport" paragraph each)
   For every person, creature, product or prop: one sheet and one paragraph describing it.
   Copy the passport paragraph word for word into every later prompt that shows it.
   STOP: I approve the sheets.

6. Blockout in code -> a three.js (or Blender) scene per shot
   Geometry and camera in code, textures and light from refs.md. Render one still next to its reference
   and fix the gaps, 3 rounds, before touching motion. If it looks like a toy, do a detail pass.
   Refine one area at a time.
   STOP: I approve the blockout stills.

7. Takes -> the shots, built in code (Remotion or HyperFrames), timed to beats.json. Any video-model shot: follow video-animate
   Something should change every 2-3 seconds. Use a video model only for the shots listed in MONEY,
   from approved stills, with the estimate shown first.
   STOP before the first paid video call.

8. Edit -> cut.mp4 + notes.md
   Assemble on beats.json. I give notes with timestamps; you fix exactly those.
   When I approve a look or a fix, save it as a reusable /command so it stays the same.

9. Review: measure, don't grade yourself (the media-judge skill runs these tests) -> review.md
   Run checks that need no opinion: duration and frame rate (ffprobe), black, frozen or broken frames,
   audio levels and sync of every hit against beats.json, spell-check every on-screen word,
   graphics that should move with the scene but are pinned to the screen, dark scenes that will band
   after upload, numbers that jiggle while counting, soft shots that don't match the rest.
   List every finding with its timestamp and fix it. Then show me.
   STOP: I approve the final cut.

10. Keep it
   From the start, keep this project in a private GitHub repo with the video-project-github skill
   (npx skills add vargHQ/skills --skill video-project-github). If you can't install it, follow
   https://github.com/vargHQ/skills/blob/main/video-project-github/references/paste-prompt.md.
   Save a version at every STOP with the step name, and tell me in plain words. Video, audio and images
   are stored by hash outside git. Keys stay out. Any step can be rolled back, and I can get the whole
   project on a new laptop.
```

---

## Which skill goes deeper at each step

| Step | Skill |
|---|---|
| 1-2 References, moodboard | `varg-mockups` (reference board, moodboard, look test), `varg-video-prompting` (look bible) |
| 3 Script, storyboard | `varg-previz` (story structure, shot list, scene grouping), `varg-mockups` (storyboard board) |
| 4 Sound | `varg-ai` (voice, music), `varg-music-video` (song beat grid and word timings), `varg-video-prompting` (dialogue and voice rules), [earshot](https://github.com/Leonxlnx/earshot) (sound critique and timed SFX) |
| 5 Characters, props | `varg-character-design`, `varg-consistent-characters`, `varg-product-lock` |
| 6 Blockout | `threejs-animatic`, `varg-previz` |
| 7 Takes | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) or [remotion-dev/skills](https://github.com/remotion-dev/skills) for code; `varg-video-prompting` + `varg-ai` for video model shots |
| 8 Edit | `varg-video-editing`, `short-form-ffmpeg-cookbook`, `varg-video-edit-library`, `caption-styles` |
| 9 Review | the QA checklists in `varg-video-prompting` and `varg-consistent-characters` |
| 10 Keep it | `video-project-github` (private repo, folders, saved versions, media by hash, undo) |

All `varg-*` skills and the others without a link are in https://github.com/vargHQ/skills
(`npx skills add vargHQ/skills --skill <name>`). Remotion is source-available and most companies need a paid
license; check before using it for client work.

## Where this comes from

- Cheap-looking AI video comes from no real film reference: https://x.com/ScaleWthAI/status/2111821935021863254
- Moodboard from 4-5 inspiration edits: https://x.com/alexgoughcooper/status/2115076988327076296
- Sound first; Claude can't hear its own frames: https://x.com/Asteri_eth/status/2117629600901534024
- Dialogue fixes (punctuation, short lines, bodily actions, anchor gestures): https://x.com/second_bassoon/status/2117307653320007954
- A one-minute short with a $10 cap cost $3.21 in model fees: https://www.reddit.com/r/ClaudeAI/comments/1wogab3/made_entirely_with_opus_55_321_of_openrouter_api/
- Reference picture sets the look, geometry in three.js, still vs picture for 3 rounds: https://x.com/0x_fokki/status/2116289885870981296
- Fixing one frame is the real skill; defects by class: https://x.com/m4lkxx/status/2116504147465757161
- Edit fixes nobody does (pinned graphics, banding, jiggling numbers, soft shots): https://x.com/tetsuoai/status/2115277212824019367
