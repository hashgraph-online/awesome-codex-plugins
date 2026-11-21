# Acting: six expressions and emotion that reads as real

Write every emotion as **a cause in the film + the physical tells**, never as an adjective.

Tested 2026-11-03:

- **Stills.** The same six slots as adjectives ("neutral, laughing, angry, surprised, sad, smug") and as cause +
  tells. Two blind AI judges: cause + tells more real (7 vs 5 of 10), less theatrical (3.5 vs 6); both picked it for
  a quiet drama. Adjectives held the face slightly better (8.5 vs 7.5).
- **Video.** One start frame, two prompts, two models. Adjective ("She gets angry because the bus did not stop.
  Emotional, dramatic, cinematic."): Kling 4 under-acted (turned away, no anger), Seedance 2.5 over-acted (a snarl
  with bared teeth). Cause + tells + timing: both played held-in anger as written and ended looking down.

## The six (default set; swap for what the script needs)

| # | Expression | Cause to write | Physical tells (FACS action units in brackets) |
| --- | --- | --- | --- |
| 1 | Listening, rest face | who speaks, about what | lips closed and soft, eyes steady on the speaker, brows level, chin slightly down, slow blinks |
| 2 | Real laugh | what is funny, to whom | cheeks lifted and crow's-feet at the outer eyes (AU6), lip corners pulled up (AU12), lower lids pushed up, mouth open (AU25/26), head tipped back. Without the eye part (AU6) a smile reads as posed |
| 3 | Anger held in | what was done to them | brows down and together (AU4), a hard stare: upper lids raised (AU5), lower lids tight (AU7), lips pressed thin (AU23/24), jaw set, nostrils slightly flared; no shouting |
| 4 | Worry / grief | the news, the loss | inner brow ends raised and pulled together (AU1+4), a vertical crease between them, lip corners slightly down (AU15), eyes unfocused or wet |
| 5 | Startle / fear | the sudden thing | brows up (AU1+2), upper lids raised showing white above the iris (AU5), lips stretched or jaw dropped (AU20/26), head pulled back, a sharp breath in |
| 6 | Contempt | who they look down on | one mouth corner tightened and raised on one side only (unilateral AU14), eyes flat, lids half down, head tilted or chin raised |

Optional swaps: disgust (nose wrinkled AU9, upper lip raised AU10), pride (chin up, small closed smile, chest
open), shame (gaze down, head lowered, lips pressed), relief (long breath out, shoulders drop, eyes close briefly).

Our tested sheet said "eyes narrowed" for anger and "lower lip pulled sideways" for worry; FACS puts an
upper-lid raise in anger and the sideways lip stretch in fear, so the table above is corrected.

**Eyes off the lens, at the cause.** The judges' main reason for preferring cause + tells: her eyes look
off-camera at what causes the feeling, one side of the face moves more than the other, and the feeling is partly held
back. The adjective sheet played every emotion full size into the lens, "like an acting-class exercise".

**Held back reads as real.** People mostly hide what they feel; a pressed mouth carries more than a shout. Write
the attempt to hide it: "she holds it in", "he smiles, but his eyes don't".

## Expression sheet prompt

```text
Expression sheet of the <woman/man> in Image 1, in the same film look as Image 1 (<texture, key, fill, backdrop>),
no text, no labels. A 3x2 grid of large head-and-shoulders close-ups from the same camera angle. Identical face,
hair and outfit in every panel; only the expression changes. Each panel is a moment with a cause.
1: <cause>: <tells>. 2: ... 6: <cause>: <tells>.
```

## The acting line in a video prompt

Shape that worked on Kling 4 and Seedance 2.5 from the same start frame:

```text
<The cause, visible or audible in the shot>. <She/he> <holds it in / lets it out>: at <t> s <tells>; at <t> s
<one breath: in / out, where>; <eye-line: where the eyes go, for how long>, then <the end state>. No <the model's
usual over-acting: shouting, head shaking, tears, mugging>. <Camera, lens, one move or static>.
```

Rules:

1. One emotion per shot; a change of emotion is a cut or a clearly timed turn.
2. The cause is in the shot (a bus passing, a text on a phone, a line of dialogue), so the viewer sees why.
3. Tells timed in seconds (models follow "at 1 s" better than "then").
4. One breath. Breathing is the most human signal and models leave it out unless asked.
5. An eye-line. Where the eyes go (and for how long) does more than the mouth.
6. A short "no" list for over-acting, especially on Seedance.
7. For dialogue: the voice is approved first; the face acts to the take, not the other way round.

## Checks

- Eyes take part in every real smile (crow's-feet, lifted cheeks).
- Brows, lids and mouth agree (a sad mouth with neutral brows reads as fake).
- Asymmetry where it belongs (contempt, a held-back smile); symmetry everywhere else reads as a mask.
- The emotion arrives on the second you wrote (scrub the clip; check frames at each "at t s").
- Identity holds: compare the face to the sheet in the frame with the strongest expression; extreme expressions
  drift first.

## From people with finished work (verbatim in x-evidence.md)

- Write the body, not the label: "Instead of "angry", you can do: "His teeth stay clenched the entire clip, the jaw
  locked hard..."" ([@heavypulp](https://x.com/heavypulp/status/2080007439185776733)). Keep everything except the
  performance text identical between takes.
- Body actions as punctuation between lines (a sniffle, a breath) "gave the biggest improvement BY FAR"; split long
  dialogue so characters have time to react ([@second_bassoon](https://x.com/second_bassoon/status/2117307653320007954)).
- FACS action-unit codes instead of emotion words in close-ups; valence-arousal for how the feeling changes over the
  shot; Laban terms (weight, time, space, flow) for body movement ([@aimikoda](https://x.com/aimikoda/status/2052124669050843453)).
- Decide whether the body agrees or disagrees with the feeling; the mismatch is acting
  ([@RobertAnim8er](https://x.com/RobertAnim8er/status/1922835836518928445), The Last of Us Part I).
- A hard look: the head turns first, then the eyes ([@JulesMurot](https://x.com/JulesMurot/status/2102752597375590586)).
- Same physical action written word for word in the prompts for both angles of a dialogue, so the cut matches
  ([@heavypulp](https://x.com/heavypulp/status/2079629064688517622)).
- When the performance must be exact, act it yourself and transfer it; expect an interpretation, not a copy
  ([@Uncanny_Harry](https://x.com/Uncanny_Harry/status/2087589869354672222)).
- Watch for default smiles in serious beats and over-big teeth; prompt them out.

## Evidence (sources and quotes in craft-evidence.md)

- Seedance's official guide: "Use specific physical details to express emotions, replacing abstract words";
  "Prioritize slow, gentle, coherent subtle movements"; "Specify the inertia and continuity between preceding and
  following actions" ([BytePlus](https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide)).
- A frozen upper face during speech "exaggerates the uncanny", significantly for fear, sadness, disgust and surprise
  ([Tinwell et al. 2011](https://vbn.aau.dk/ws/files/63140615/Facial_expression_of_emotion_and_perception.pdf)).
  Check three frames during speech: brows or lids must differ.
- A posed smile lacks the cheek raise (AU6) and "may drop off the face too abruptly"
  ([Paul Ekman Group](https://www.paulekman.com/blog/science-of-smiling/)).
- Surprise is the shortest emotion: never hold it for a whole clip. Contempt is the only one-sided expression.
- Listeners act: nods, brief brow raises, a glance away while thinking; a frozen listener is a tell.
- Asking for "angry" or "sad" can shift the face older and male ([arXiv 2602.00032](https://arxiv.org/html/2602.00032)):
  keep the identity locked with the sheet when changing emotion.
