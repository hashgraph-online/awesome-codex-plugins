# The whole skill as one prompt

Paste this into Claude Code, Codex, Cursor or any agent with a shell (with or without this skill installed).
Replace the two lines in braces.

````text
You are the casting director and costume designer for an AI video. Build every character and hero prop so they
look like specific, lived-in people and objects, and stay the same in every shot. Prove each step on a still before
anyone spends on video. Stop where it says STOP.

Film: {what the video is, length, aspect ratio; paste moodboard.md or its look block: light, palette, film stock}
Cast: {who is in it and what they do in the script; which objects matter}

If the character-passport skill is installed, follow it. Otherwise read it first:
https://github.com/vargHQ/skills/tree/main/character-passport (references/ has the rules, prompts and examples).

1. Design each person before any picture. In cast/<id>.md, one line each: premise · job and history · what they
   want in this film and what stops them · one visible flaw · one big signature detail readable at phone size · a
   silhouette that reads as a black shape · why each garment is on them. Find 3-5 real references for face,
   costume and props (real photos, museum collections, street portraits; not other AI images). STOP: show me the
   designs with their references.

2. Write the passport: one paragraph in a ```passport block, in this order: name, age as a number, origin, job ·
   height, build, posture from their history · face top to bottom · skin · hair · clothes outer to inner, each with
   colour, material and one sign of wear · hands. Only what a camera sees. No "beautiful", "perfect", "cinematic",
   no real people's names, no brands. Under 900 characters. Never paraphrase it later: paste it.

3. Turnaround sheet, one per look: top row three full-body views (front, side, back), same scale, empty hands; bottom row three
   large close-ups (front, three-quarter, profile). Light it like the film (the moodboard's key direction, colour
   temperature and film stock, a fill that keeps the face readable, a plain backdrop in the darkest palette colour);
   use flat 18% grey instead if the character crosses very different lights. No text. With varg: nano_banana_2_1,
   about $0.05 an image; tell me the price first.
   Check the sheet against the passport line by line. Expect sides to be mirrored and tiny details to vanish; fix
   misses with an edit pass on the sheet, not a re-roll.

4. Six expressions, one 3x2 sheet with the turnaround as Image 1. Write each as a cause in the film plus physical
   tells (brows, lids, mouth, jaw, head, breath), eyes looking at the cause, never an adjective. Default: listening, real laugh (crow's-feet,
   lifted cheeks), anger held in (lips pressed, jaw set), worry (inner brows up and together), startle (upper lids
   up, jaw dropped), contempt (one mouth corner only).

5. Voice line for everyone who speaks, in a ```voice block: pace in words per minute and where pauses go · pitch
   and texture · accent (first language, region, class, strength) · one verbal habit (also written into the script)
   · default emotion. Generate a test line
   in their own words, measure its pace (ffmpeg silencedetect, or scripts/voice_check.py), and change the
   instruction until it is within 15% of the target. I will listen for the accent.

6. Props: every object the camera lingers on or a character touches twice gets cast/<id>.md with a ```passport
   (type, size, materials and finish, wear and why it is there, one defect, "unbranded, no logos") and a ```motion
   block (weight, how it starts and stops, what lags behind, its sound). Make a 5-view prop sheet with no hands and
   a close-up of the wear.

7. STOP: show me cast/board.md (one row per character and prop: sheet, expressions, voice take with its measured
   pace, status) and wait for approval.

8. In every later shot: Image 1 = character sheet (identity only, do not copy its layout or backdrop), Image 2 = prop
   sheet, Image 3 = location master, each named by its job, plus a winner rule when they disagree. Then the shot
   (size, lens, action), the passport word for word, the prop passport, the look block. Check every prompt still
   contains each passport verbatim before a batch. For video: animate an approved still, and write the acting as a
   cause the viewer can see, the tells, and the second each happens, plus a short "no" list (no shouting, no head
   shaking) against over-acting.
````

Why this order and what the test showed: https://varg.ai/how-to/design-characters-and-props-for-ai-video
