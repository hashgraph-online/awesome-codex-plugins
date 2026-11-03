# Prompts shown in fal's Kling 4 guide

Source: "Kling 4 | Cinematic Guide and Halloween Music Video", fal, YouTube, 2026-10-30, https://www.youtube.com/watch?v=WzXKggH-0Io (chapters: 4:04 key images, 6:29 bad results, 9:03 intro scene, 12:20 breakdance montage, 14:44 BMX crash, 20:30 Seedance 2.5 vs Kling 4). Text read from the screen recording, spelling kept. All video jobs ran on `fal-ai/kling-video/v4/reference-to-video` at 1080p through fal's agent (Opus 5.5) and key frames on GPT Image 2.5.

## What the author typed vs. what the model got

The author types short prompts in the agent chat and attaches the key frames. The agent expands them into longer, almost JSON-like prompts for GPT Image 2.5 and a few sentences for Kling 4. The typed prompts are the part worth copying; the expansions show the structure.

## 1. Intro dialogue scene (good) — 9:25

Inputs: 2 stills (wide shot: he walks past her pumpkin stall, motion blur; over-the-shoulder on her).

```
Kling 4 Ref to Video 21:9 the man walks by the woman as she places a white pumpkin on the table.
the man says "what does the white one do?" she smiles and smashes the white pumpkin on the top of
the man's head with both hands. The camera shakes and falls to the ground and fades to black.
handheld shaky 16mm documentary style footage. 15 seconds.
```

Result: a multi-cut (not asked for), a little too much room at the start, good dialogue, her voice generated without a sample, a hard cut to her, the camera rolls onto its side as it falls. The ending was used.

## 2. Breakdance montage (good) — 12:22

Inputs: 3 stills of the dancer in different poses and slightly different shots in a crowd ring with a boombox, Washington Square Park arch.

```
the pumkin boy break dances in NYC while everyone bobs their heads to the 90s hip hop beats.
shaky handheld footage. 30 seconds.
```

Expanded prompt (start, as shown): "Shaky handheld 16mm street documentary footage with heavy film grain, low fisheye angle, cinemascope frame. Washington Square Park, New York City, overcast winter…"

Result: 30 s of dancing, some moves bad, a good freeze and head spin, audio with it, a push-in; one shot had six fingers.

## 3. Scooter montage (good) — 13:36

Inputs: 3 stills (rider between yellow cabs, fisheye; overhead drone; steam he rides through).

```
Kling 4 21:9 montage of the pumkin boy riding a scooter and pushing super fast through NYC
traffic. 30 seconds. No slow motion, everything is moving at a high sped with motion blur.
```

"No slow motion" was added because Kling 4 defaulted to slow motion in many first tests. Kling-invented shots in the montage looked a little more "AI" than the shots that came from GPT stills.

## 4. BMX crash montage (good) — 15:45

Inputs: 4 stills (tail whip in front of the bridge, a second trick, take-off, the crash with the girl helping him up).

```
montage of the punkin boy doing BMX tricks on the Brooklyn Banks. tail whip. bar spin. Then we
messes up the trick mid air and crashes to the ground smashing the pumkin head and retruning to a
normal man. the blond girl helps him up. she says "Sick run, want to go again?" 30 seconds.
```

Agent's plan (excerpt): "Crash: he lands on just his back wheel, loops out and falls backwards. The pumpkin head hits the concrete and explodes, leaving the real man lying there." "Ending: I split the last 7 seconds into two shots. First she pulls him up (3s), then a close-up on her face as she says 'Sick run, want to go again?' (4s)."

Follow-up: "same sequence and add this reference of what the girl looks like" (one photo). The retry failed before it started: "The model needs at least one extra photo for each character, and the blonde girl only had your one photo. I added that same photo again as her extra view and resubmitted it." Result: the close-up kept her likeness well enough; Kling picked a telephoto lens although the film was all wide angle.

## 5. Key frame prompt for GPT Image 2.5 — 5:00

See SKILL.md section 4 for the full crash-frame prompt ("Cinematic 21:9 film still, high overhead shot tilted at an angle, ultra-wide fisheye lens…"). Frames were made at 3840×1648 (21:9).

## 6. The "bad" prompt (Seedance-style) — 6:40

Inputs: a character sheet of the pumpkin boy and one Midjourney location image.

```
The character in @Image1 (white pumpkin head with a curled stem, black baseball cap, round black
glasses, big cartoon eyes and smile, black hoodie and pants with a white skeleton bone print,
skeleton-hand gloves, black sneakers) goes trick-or-treating at night. Match his look and 3D
rendering style from @Image1 and @Video1 exactly.

First-person POV of the apartment resident standing inside their doorway. A quick sequence of hard
cuts at three different apartment doors, each with a different hallway and Halloween decorations:
each time the door swings open, the character comes running up to the threshold, out of breath and
excited, holding out an open trick-or-treat bag. The resident's hands reach into frame and drop
computer hardware into his bag: first a boxed high-end graphics card, then sticks of RAM with RGB
lighting, then another graphics card. Every time, the character is overjoyed: he jumps, pumps his
fists, hugs the gift and does a happy little dance before running off down the hall to the next door.

Cinematic handheld POV camera, warm doorway light against dim hallways, playful comedic tone.
Ambient sound and footsteps only, no music.
```

Verdict: good character animation, but "capital S slop": Kling 4's own shots and fill are smooth, the framing is weak, it "feels too AI". The prompt is fine; what is missing is the pre-made shots.
