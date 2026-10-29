# Story structure for short AI videos

Pick a structure for the format, then lay its beats over the timeline (song sections, voice-over lines or plain
seconds). One story beat per section, one sharp action per shot, one camera move per shot. Put `beat` (or `act` +
`campbell`) on every storyboard shot so the previz and the board show it.

## Pick the structure

| format | length | structure | beats |
|---|---|---|---|
| ad / product promo / UGC | 6–30 s | hook → problem → product → proof → call to action | hook 0–3 s, problem, the product enters as the fix, proof (result, reaction, demo), CTA + end card |
| social short / meme / POV | 6–20 s | setup → escalation → twist | a relatable first frame, it gets worse on every beat, the turn lands on the drop |
| explainer | 20–90 s | question → stakes → 3 steps → payoff | ask in the first frame, why it matters, show (not tell) each step, the result |
| trailer / teaser | 15–60 s | world → threat → stakes → montage → title | slow open, the threat on a hit, faces in danger, fast cuts on the beat, title card |
| music video / short film | 60–180 s | Hero's Journey (below) | ordinary world → call → refusal → mentor → tests → ordeal → return |

For ads: the brand or product is never the hero; it is the mentor or the magic aid the hero accepts. The viewer is
the hero.

## Make it work on screen (any format)

- **Hook in 0–3 s**: start in the middle of the action, the hero in frame from frame 1, an impact on a beat, a
  readable text hook ("POV: …") drawn in code.
- **A visible problem**: turn the abstract pain into something with a body (a monster, a broken thing, a crowd,
  a ticking clock), so the camera has something to point at.
- **Stakes and cost**: the hero fails first and pays something (a scar, a lost thing) that stays to the last frame.
- **The talker or singer has a reason**: decide which shots are sung or spoken on camera (they need lip-sync later)
  and which are voice-over.
- **A colour script per act** (e.g. cold → warm → dark with one warm point → bright → calm) and **recurring markers**
  (an object, a scar, a colour) that carry the story across cuts.
- **3–5 film or ad references from one aesthetic**, each tied to a shot: they give the generator a motion vocabulary.
- **Loop**: for social, the last frame cuts to frame 1 so the video replays seamlessly.

## Hero's Journey for 60–180 s

Use Campbell's stages as a checklist: each act gets a section of the song, each stage a shot or two.

| act | stages | what it does |
|---|---|---|
| I | ordinary world on fire → call → refusal | show the pain in the first frame; the hero tries alone and fails |
| II a | allies → meeting the mentor | helpers appear; the hero lets go and accepts the aid |
| II b | threshold → tests, allies, enemies | the aid's power in action; a setback absorbed |
| III | belly of the whale → ordeal → death and rebirth | inside the enemy, the hero does what only they can |
| IV | return with the elixir | calm, changed, the scar stays; loop to frame 1 |

Worked example, "I Don't Wanna Pick" (99 s, 9:16, a song about juggling AI providers): I: a creator-pilot at a 99 %
render, providers die, the antagonist THE 503 (a leviathan of error screens) rises, he flips models by hand and
misses. II a: a squadron of "models" arrives; he lets go of the stick and hands the brief to the agent orb. II b:
Approve; missile spirals; one wingmate dies and another takes its slot; ships hit the monster from all sides, he dives
into its mouth. III: darkness, then the throat lights up; he plays sax on the hull; an engine dies and the agent
reroutes power; the core cracks; a stargate. IV: calm cockpit, the canopy crack still there, wink, end card. Colour
script: red alarm → violet allies → orange agent → red darkness with one orange point → white → calm blue.
Full code of that previz: `templates/previz/examples/space-opera/`.

## Write it down

`treatment.md`: review of the previous cut (if any), logline, hook options, talking/singing plan, beat table with
timings, references, action list, consistency plan (colour script, markers, anchors), production steps with costs.
Then `storyboard.json`.
