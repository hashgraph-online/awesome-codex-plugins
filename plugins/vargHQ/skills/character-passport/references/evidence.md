# The test behind this skill (2026-11-03)

Small and honest: one character, four shots, one image per cell, two blind AI judges (fresh agents). Read gaps of 1 point or less as
a tie. Every image and clip is linked in `examples/vesna/README.md`.

## Setup

- Film: LAST BUS (the `video-moodboard` example board): late-1990s night drama on Kodak 500T, sodium key from high
  left, cold blue fill from the right.
- Character: Vesna (passport in `examples/vesna/vesna.md`), prop: her umbrella.
- Four shots: wide at the bus stop, close-up in headlights, boarding the bus, hospital break room at 7 a.m.
  (different light, to see whether a moodboard-lit sheet leaks its light).
- Four ways to describe her, same shot lines and look block: the moodboard's one-line subject; the passport only;
  passport + flat-grey sheet as Image 1; passport + moodboard-style sheet as Image 1.
- Model: Nano Banana 2.1 on varg, 16:9, 5 credits an image.
- Judges: two fresh agents with no access to how images were made. They saw anonymised, shuffled stills, the
  written description and the two sheets, and scored each set (same person, matches the description, 1-10) and each
  still (a 14-item passport checklist: yes / no / not visible; film-likeness and look match 1-10).

## Results

| Method | Same person | Matches | Checklist right where visible | Film-likeness | Look match |
| --- | --- | --- | --- | --- | --- |
| One-line subject | 2 | 1.5 | 12% (8/65) | 7.0 | 7.4 |
| Passport only | 5 | 4.5 | 46% (38/83) | 7.0 | 7.4 |
| Passport + grey sheet | 8.5 | 7.5 | 58% (46/79) | 6.6 | 7.3 |
| Passport + moodboard sheet | 7.5 | 7.0 | 63% (49/78) | 6.9 | 7.6 |

Per detail, across the three passport conditions (yes / visible): navy scrub collar 24/24, black scarf 24/24, hair
length and colour 22/24, deep-set eyes with shadows 21/23, freckles and no makeup 11/13, brows almost meeting 19/24,
coat 9/12, nose bump 2/5, plaster on the right index 1/20, scar on the left of the chin 0/14, hair behind the right
ear only 0/23, salt-marked boots 0/12, worn umbrella handle 0/22, missing button never visible (hidden by the scarf).

Lessons: the sheet is what makes a person the same; big features survive, small wear and sides do not; a prop needs
its own sheet in the shot; a passport can contradict itself.

## Expressions

Same turnaround as Image 1, two prompts: adjectives ("neutral, laughing, angry, surprised, sad, smug") vs a cause
+ tells for each panel. Judges: realism 7 / 7 vs 5 / 5; theatricality 4 / 3 vs 6 / 6; identity hold 7 / 8 vs 8 / 9.
Both picked cause + tells for a quiet drama: off-camera eye-lines, asymmetry, feelings held back. Adjectives: "every
emotion at full size straight into the lens".

## Acting in video

Start frame: the close-up shot (moodboard sheet version). Two prompts on Kling 4 (720p, 5 s, 79 credits each) and
Seedance 2.5 (720p, 5 s, 193 credits each):

- Adjective: "She gets angry because the bus did not stop. Emotional, dramatic, cinematic." Kling: no visible
  anger, she turns her head away. Seedance: escalates into a snarl with bared teeth.
- Cause + tells + timing (the acting line in `acting.md`): both models press the lips at about 1 s, hold, follow the
  bus with the eyes and end looking down.

One pair per model: an illustration, not a statistic.

## Voice

Gemini 3.8 Flash TTS, voice Gacrux, 22-word line, measured with `scripts/voice_check.py`: no voice line 144 wpm;
voice line v1 ("slow ... half-second pauses") 92 wpm; v2 ("steady ... about 130 wpm, short pauses only at full
stops") 129 wpm against a 130 target. The accent was not checked by ear in the test.

## Code to image

A three.js blockout (primitives, a lantern prop, four orthographic cameras) edited with Nano Banana 2.1 ("keep its
exact layout, camera angles, proportions, pose, silhouette and the lantern's size and position") came back as a
photoreal four-view sheet with the same pose, proportions and prop placement.

## Cost

23 images $1.15 · 3 voice takes $0.03 · 2 Kling clips $1.58 · 2 Seedance clips $3.86 · total about $6.62.
