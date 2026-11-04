# Case C: no reference at all

With no reference, agents reach for their defaults: "dark navy space, a glowing halo ring, bloom, particles". One skill author's
reference-free creatures came out as "generic toys". So make a reference first, or make the choice cheap.

Try the ladder first: "Perhaps the order is: say in words what it means and why it matters, and only if that fails does the idea of images, references, and
then previz come up" (@IntLab0000, translated). Also try generating first and using your best output as the reference (@akuai33).

## Option 1: three camera options, and pick

Ask for 3 named options per cut as moving stand-ins, on one contact sheet, each a real choice of size, angle or whose side the
camera is on. You don't need to know camera language. You need to know which one you like. (Reported by @eijo_AIart: 11 s, 2
cuts, one generation, on a custom three.js tool.) The prompt is in `references/prompts.md`.

## Option 2: generate the reference

1. Find or generate a look reference: `find-references`, `video-moodboard`.
2. Generate one key frame per story beat as a still, with an image model. Stills are the cheap place to find out it's wrong.
   Keep it rough if it will go to a video model: black-and-white roughs keep angle, travel and cut order, and finished images tend to come back as a "moving storyboard".
3. Treat the approved stills as references: stage them with `references/paintings.md`. Now you're in Case B.

## Option 3: borrow a structure, not a film

Ask for a grammar you can name: "the first reveal in a heist film", "a Hitchcock zoom", "an Ozu dialogue at low height
with static shots". Have the agent write a beat sheet with timestamps and camera angles first, then block it.

## Staging from nothing: questions to answer before any code

Every one of these has to end in a number or a name:

- What's the one image the viewer remembers? Build toward it.
- Who has power in this shot? Height and size in frame show it: low angle for power, high for smallness.
- Where is the eye at each moment? One centre of interest per beat. Motion, contrast and faces pull the eye.
- Which way is everyone looking, and on which side of the 180° line is the camera?
- What's in the foreground, the middle and the background? Depth layers are what make a move feel like a move.
- What's the shape of the composition: diagonal, triangle, frame within a frame, or a lot of empty space?
- Where does the light come from, and what stays dark?

## Then

The rest is the same loop: beats in seconds and metres, `staging.json`, numbers, stills, a fresh reviewer, the person's yes.
