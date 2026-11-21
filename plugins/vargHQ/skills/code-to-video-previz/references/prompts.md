# Prompts to paste

Fill in the angle brackets. Each works in Claude Code or Codex. The master prompt works with no skill installed; the
others assume the agent can run the tools in this skill.

## The master prompt

```text
Build a 3D prototype of this video in code, as a guide for a later AI video generation. Don't generate any video.

BRIEF: <what happens, in your own words, voice-dictated is fine>
FORMAT: <16:9 or 9:16>, <seconds> s, 24 fps
REFERENCE: <path to a video, painting or still; or "none">
TOOL: <Three.js in a single HTML file with no build step | headless Blender with bpy | "you choose and tell me why in one line">

Work in this order and stop where I say.

1. BEATS. Before any code, write beats in seconds and metres: who, where, which way they face, what happens, what state
   it ends in, and one camera move per beat with its job. If a reference exists, read it first: split it into shots
   with ffmpeg, look at the first, middle and last frame of each, and lay a grid over them to read positions as
   fractions of the frame. Show me the beats. Pick no more than one camera idea I didn't ask for.

2. BLOCKING. Real metres, ground at zero, a 1.75 m person beside anything without a familiar scale. People are a capsule, a
   ball head and a small nose in the same tone as the head, to show their facing. Boxes and spheres for everything else. Build as little as
   explains the action, but keep openings, contact surfaces and anything that tells you which way a thing faces. Don't
   model hero objects, faces, hands or textures. Flat light, no shadows, no text, labels, outlines or UI anywhere in the frame.
   Keep the scene as data separate from a small engine, so a change doesn't rewrite the engine. Everything on screen must be a pure
   function of time t: no clocks, no unseeded random, no state between frames.

3. CAMERA. Name the lens in mm per shot. Write orbits as arcs so they can't pass through the subject. Vary the moves.

4. CHECK WITH NUMBERS. For the first, middle and last frame of each shot, compute: is each subject's head in frame, does anything
   block it, is the camera inside any object. Fix every failure. Then check brightness: in greyscale, anything that passes in front of something else must still
   clearly differ from it, or the shapes merge.

5. LOOK. Render those frames as a contact sheet and actually look at it. Tell me in plain words what each shot shows.
   Fix one thing at a time, at most 3 rounds. Don't call a shot fine without having seen it. If a reference exists, overlay your
   render on it at 50% and report what doesn't line up. Then stop and show me the sheet. Wait for my notes.

6. RENDER. After I approve, render the MP4 frame by frame with headless rendering and ffmpeg, never by screen recording. Confirm
   duration and frame count with ffprobe, then export it in greyscale for the video model.

7. HANDOFF. Write the video prompt: the clip is rehearsal footage, take only camera path, framing, timing and positions from
   it and none of its shapes, colours or lighting. Describe every shot as it appears in the clip. Name each camera move
   in words. Give an end state per beat. Never mention boxes, capsules or stand-ins.

Be honest in your report: what you looked at, what you only measured, what is still wrong. You can't watch video, so tell me which
parts I need to judge by playing it.
```

## Which tool should I use?

```text
Here is the shot: <description>. Find the one hard thing in it. Then tell me the cheapest prototype that pins that down:
no prototype, storyboard stills, a 2.5D timing conte, Three.js, Blender, a phone act-out, or something else. One
recommendation, one line of reasoning, and what would change your mind.
```

## Three.js, one shot, exact (after atsu_mada)

```text
Make a previz of this cut in Three.js and export it to mp4. Show people as different coloured boxes and spheres, no fine
shapes. 1280x720, 24 fps, no sound.

Cut: <the bartender takes a bottle from the top shelf> (<3.4> s)
Camera: <behind the customer's left shoulder, slightly above, facing the bartender, locked>
Motion:
- <0.9> s: <the right arm starts to extend>
- <1.25> s: <the hand reaches the bottle, about 1.1 m from the shoulder>
- <1.4> s: <leaves the shelf with the bottle>
- <2.0> s: <tilts the bottle over the shaker and holds to the end>

At the end, return a table of what happens at what second.
```

The seconds and metres are the point: "the parts you can't write are the parts that are vague in your own head."

## Blender, in steps (after PJ Ace's public guide)

```text
Using the Blender connector, build a blockout of this scene at real-world scale (metres, Z up). Orientation: <compass
directions or named walls>. Scale sheet: <list>. Layout: <where everything is and which way it faces>. Use simple stand-ins for
people at their real heights. Save it as a new version and tell me when it's ready for me to check.
```

```text
Add one camera per shot: <shot list with shot size, lens, facing, height and move>. Name each camera and add a matching
timeline marker so playback cuts between them. Frame for <aspect ratio> and keep screen direction consistent. Look through
every camera, fix anything that isn't faithful, logical or well composed, save a new version and tell me when it's ready.
```

```text
Render a fast Workbench video at 24 fps of the whole timeline, cutting between the cameras. Also render stills through each shot camera: 2 to 4 frames per
shot showing the start, peak and end of the action, and lay them out on storyboard pages with a title, a camera line (facing,
lens, height, move) and a one-line caption per frame.
```

## Copy this reference shot

```text
Copy the camera and staging of this shot, not its look: <reference.mp4, start and end time>.
1. Run scripts/shots.py and look at the sheet. Run scripts/measure_shot.py on the shot and read the size, direction and
   easing of the move.
2. Run scripts/grid.py on the first and last frames. Read the positions of the subjects, the horizon and the big masses.
3. Estimate lens and camera height from something of known size. Write staging.json from picture coordinates using
   scripts/place.py. Add pins for the main subjects.
4. Run check_staging.py, render first and last frames and compare them with the reference through scripts/compare.py.
   Look at the overlays. Fix the worst gap, then the next, at most 3 rounds.
5. Render the clip, run measure_shot.py on it, and show me a table of reference vs yours: pan, tilt, zoom, roll, easing.
```

## Stage this painting

```text
Stage this painting as a 3D scene I can move a camera through: <painting.jpg>. Follow references/paintings.md in the
code-to-video-previz skill. Read the picture with a grid, get lens and eye height from a person's known height, place
figures and masses by picture coordinates, then one hard light with flags so the main shadow edge falls where the painter put
it. Report pin errors, show me the overlay and say where the staging disagrees with the painting. Then propose one slow camera move through it.
```

## No reference: three camera options (after eijo_AIart)

```text
Scene: <two people walk toward each other and pass. A looks back, B doesn't. Then we see B walking toward us with A stopped far behind.>
Give me 3 named camera options for each cut as moving stand-ins, each a real choice: different size, angle, or which
character the camera favours. Render them on one contact sheet with a line on what each option makes the viewer feel.
Recommend one. Don't polish anything until I pick.
```

## The fresh reviewer

Open a new session or subagent for this, so it doesn't defend its own work.

```text
You did not build this. Here are the beats, the contact sheet and the reference. Name the single biggest gap between the
frames and what the beats ask for, then the next two. Say "I can't tell from stills" for anything about motion. No scores
and no praise.
```

## Save tokens

```text
Don't rewrite the engine. Change only the scene data. Tell me the one number you changed and why.
```

## Rules behind these

Numbers and named bans do more than adjectives ("cinematic" gets you dark navy, a halo ring, bloom and particles). A "do
not add" list stops scope creep, and a stop rule stops loops. Plan and check are separate steps. One-prompt results hold up only in
forgiving styles: mrdoob, who created Three.js, took 22 iterations on his own release film.
