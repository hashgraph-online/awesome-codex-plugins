---
name: video-script
description: >-
  Write the script for any video before anything is generated: what is said, shown and heard in every beat, sized
  to the clock and the video model. A brief and a facts file in; one script table out (time, spoken line, on-screen
  text, visual, sound), three hooks, and a check that measures pace, hook timing, shot length, unsourced numbers and
  AI-sounding lines. Six structures with one example script each, plus variations for demo and launch videos,
  product reviews, ads and UGC, social shorts and short-form drama, and a loop for testing and improving the skill.
  Use for "write a script", "video script", "ad script", "UGC script", "TikTok, Reels or Shorts script", "YouTube
  script", "voiceover script", "demo or launch video script", "product review script", "short drama episode",
  "skit", "hooks", "how many words for 30 seconds", or any video that has no script yet. Not for the look
  (find-references) or the shot prompts (varg-video-prompting).
license: MIT
metadata:
  author: vargHQ
  version: "1.2.0"
  openclaw:
    requires:
      anyBins:
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/video-script
compatibility: >-
  Works in any agent. scripts/check_script.py needs Python 3 (standard library only). No credits are used.
allowed-tools: Bash(python3:*) Read Write Edit
---

# Video script

Write the script before any voice, image or clip is made: every later step is cut to it. Left alone you drift to the
most probable script, which is the one everybody else gets: a "have you ever wondered" opener, three adjectives, a
narrator describing the picture, a vague happy ending. This skill names those defaults, gives the alternative for
each, and makes you measure the script instead of grading your own taste.

## The output

One file, `script.md`: header lines, one table, `## Hooks`, `## Sources`. Keep this shape exactly; the checker and
the production skills read it.

```
format: ad            ad | demo | review | social | drama | explainer | brand
length: 30s
ratio: 9:16
wpm: 150              narration pace; measure one take of the chosen voice and put its real pace here
max_shot: 10          longest clip the chosen model makes well (see Fit the clock)
facts: facts.md       the only place numbers, names and claims may come from
viewer: who, in their own words
promise: the one sentence the viewer gets from this video
strategy: problem-agitate-solve
cta: one action, or none
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | the line as it is said | the words shown | what the camera sees: one shot, or a cut list | music, effects, silence |

- **spoken:** voice-over in quotes; dialogue as `MARA: "..."`; delivery in brackets, `[whispers]`.
- **One spoken line, one visual.** A line never runs across a cut it does not own; split it instead.
- Write numbers, prices, dates and URLs the way they are said: "forty-five dollars", "patchwork dot dev".
- `## Hooks`: the three best first lines out of ten, the chosen one first. `## Sources`: each fact and where it is from.

## Steps

1. **Brief and facts.** You need: the viewer, the one promise, platform + length + ratio, the facts (product facts,
   data, the real story), the one action, and the production limits (AI video or footage, voice, speakers, model).
   Ask once, in one message, only for what would change the script; assume the rest and say what you assumed. Write
   `facts.md`. Never invent a number, a quote, a review, a customer or an experience; write `[TK]` and ask.
2. **A proven skeleton.** Find what already works for this viewer: top videos in the niche from the last 30 days,
   ads that have run for months. For each, note the hook, the format, how the product appears and the ending. Copy the
   structure, never the words. No time for that? Pick a strategy below.
3. **Promise, ending, ten hooks.** Write `promise:` as one sentence. Write the last line. Then write ten first lines
   of different kinds (formats in `references/social.md`). Cross out the first idea that came to you and anything
   two drafts share; keep the three most specific ones that are still true.
4. **Beat sheet.** One line per beat with its time, and BUT or THEREFORE between beats. Where people appear, answer
   for each beat: who wants what, what happens if they don't get it, why now.
5. **Write the table** by the rules below.
6. **Check.** Run `python3 scripts/check_script.py script.md` and fix every FAIL. Read every spoken line aloud at
   speed. Answer the YES/NO list at the end. Change lines because a check or the person named a problem, not on taste.
7. **Show it.** Show the script and the three hooks and wait for a yes before any voice or video is generated.
8. **After it ships,** log it and read the numbers: `references/improve.md`.

## Rules

1. **One viewer, one promise.** Every beat serves the sentence in `promise:`. An ad that does too much does nothing
   well (Google ABCD); write the headline first (Gallo).
2. **The first frame and line pay off the packaging.** Whatever made them stop (title, thumbnail, first image) is
   delivered at once, as a picture that reads on mute in 3 s or less; the shot, 3–5 words on screen and the spoken
   line say the same thing. A broken promise is the first drop-off (MrBeast doc, YouTube Help, Hoyos, Kallaway).
3. **Open a loop, then pay it off.** Right after the hook, say what is coming. Withhold the answer, never the topic
   or the stakes: the first line says what the video is about ("Plane windows are round because..."), not a riddle
   ("A corner."). Give two plus two, not four. Answer a question only with a bigger one (Stanton, Hoyos, Loewenstein).
4. **But or therefore, never "and then".** If "and then" fits between two beats, the story is boring
   (Parker & Stone; Aristotle called such plots "the worst").
5. **Every beat turns something.** A want meets an obstacle; a value flips (doubt to proof, safe to danger). Start as
   close to the end as possible and cut any line whose removal changes nothing, first and last lines included
   (McKee, Vonnegut, Mamet, Sorkin).
6. **Show it; say only what the picture can't.** Draft it as a silent film first. The voice adds what the picture
   cannot show and never describes it. In a feed, something new appears every 2–3 s (Mamet, Wilder, Roy Lee).
7. **Write for the ear.** One idea per sentence, words a twelve-year-old knows, lengths that vary the way speech does.
   Codes and reference numbers (flight numbers, model numbers, part numbers) go on screen, not in the voice. Read it
   aloud and cut what you would not say to a friend (NPR, Hoyos, Mañalac).
8. **Specific beats general.** A number, a name, a visible detail, the viewer's own words from reviews and comments.
   Replace every word of praise with the fact behind it (Wikipedia: Signs of AI writing; Heath brothers).
9. **Fit the clock.** Size every line to its seconds and every shot to its model (table below).
10. **End on the payoff.** No recap, no wind-down. Ads, demos and reviews end on one action, said and shown; shorts
    cut right after the payoff (Hoyos cut one second and retention went from 83% to 88%).
11. **Tell the truth.** Disclose paid deals at the start, spoken and on screen. An AI presenter never claims to have
    used the product. A shown result must be typical. Offers keep their conditions exactly as given ("20% off your
    first order"), and the product on screen does only what facts.md says it does. Label AI people where the platform
    asks (FTC, TikTok, Meta).

Full sources for every rule: `references/sources.md`.

## Defaults to replace

| You will drift to | Write instead |
|---|---|
| "Have you ever wondered…", "In this video…", "Hey guys" | the result, the conflict or the strangest true detail, shown |
| three adjectives ("fast, simple, powerful") | one fact you can show or measure |
| "It's not just X, it's Y"; "No X. No Y. Just Z." | say Y |
| a narrator describing the shot | the shot alone, or a line that adds what it can't show |
| a vague hopeful ending ("the future is bright") | the payoff, then cut; or one action |
| speakers who all sound formal and alike | a want and a way of talking for each person |
| Sarah, Emily, Elara Voss, Elias Vance | names from the brief, or plain specific ones |
| the first twist that comes to mind | the third idea; drop what two drafts share |
| clipped fragments everywhere ("Simple. Fast. Done.") | mixed sentence lengths, as people talk |
| "a testament to", "seamless", "game-changer", "unlock", "elevate", "delve" | the concrete thing |
| invented stats, "experts say", "studies show" | a fact from facts.md with its source, or nothing |

## Fit the clock

| Length | Spoken words, max at 150 wpm | Beats |
|---|---|---|
| 15 s | 37 | 3–4 |
| 30 s | 75 (60–70 reads better) | 5–7 |
| 45 s | 112 | 6–9 |
| 60 s | 150 (90–120 when the product must be watched) | 7–12 |
| 3 min | 450 | chapters of 3–5 beats |

- **Narration:** 150 words a minute is 2.5 a second (audiobooks run 140–180). Go to 170–190 only for light, fast
  social voice-over. Lip-synced close-ups: under 10 words per 5 s shot. Measure one take of the real voice and set
  `wpm:`.
- **On screen:** at least 0.33 s per word; a 4-word caption stays 1.2 s or longer (BBC subtitle guidelines).
- **Shots:** each generated clip must fit the model's window (Veo 3.1: 4, 6 or 8 s; Seedance 2.5: 4–30 s;
  Kling 4: 3–30 s; check https://varg.ai/models/llms.txt), but runs of 4–11 s obey better and retake cheaper. Set
  `max_shot:`.
- **Hook:** lands by 3 s in feeds, 5 s on YouTube and in demos.

## Strategies

| Strategy | Use for | Beats |
|---|---|---|
| But / therefore | true stories, founder stories, history, anything with a plot | situation → BUT → THEREFORE → BUT → THEREFORE → payoff |
| Question ladder | social shorts, mysteries, lists, skits | hook + what's coming → question → bigger question → twist → cut |
| Problem, agitate, solve | ads to people who know the problem | problem → why it's worse → product as the fix → proof shown → one action |
| Result first | demos, tutorials, app ads | finished result → how, in the fewest steps → payoff moment → one action |
| Misconception first | explainers, science, how it works | question → the common wrong answer → why it seems right → evidence that breaks it → the right model |
| What is / what could be | launches, pitches, brand films | today's pain → the possible → today → the possible, made real → one action |

Sources: Parker & Stone; Hoyos and Stanton; Ogilvy ("above average in sales results"); Peter Cohan's "Do the Last
Thing First"; Derek Muller's PhD (refuting the misconception beat clean exposition); Nancy Duarte's sparkline.
Story Spine, Harmon's circle and Save the Cat are in `references/sources.md` as audits, not molds.

### But / therefore: the Post-it Note (30 s)

```
format: explainer
length: 30s
facts: National Inventors Hall of Fame, Art Fry and Post-it Notes
promise: the sticky note started as a glue nobody could use
strategy: but-therefore
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "This glue failed at its job." | THE GLUE THAT FAILED | a yellow square peels off a page, leaves no mark | soft peel |
| 2 | 0:03-0:09 | "Spencer Silver at Three M made it: sticky, but useless for tape." | SPENCER SILVER · 3M | lab bench, a tape strip lifts away clean | lab hum |
| 3 | 0:09-0:16 | "But in nineteen seventy-four, Art Fry's bookmark kept falling out of his hymnal." | 1974 | church choir; a paper slip slides out and drifts down | choir humming |
| 4 | 0:16-0:21 | "So he made bookmarks with a thin coat of Silver's glue." | | brush on paper; the slip holds to a page, lifts clean | |
| 5 | 0:21-0:26 | "So Three M tried them in four cities, in nineteen seventy-seven." | PRESS 'N PEEL · 1977 | a 1970s shop shelf, small pads | register ding |
| 6 | 0:26-0:30 | "Renamed, they went national in nineteen eighty. Post-it Notes." | POST-IT · 1980 | a wall of yellow notes | pop |

### Question ladder: the crossed-out line (30 s, fiction)

```
format: social
length: 30s
promise: why grandma crossed out the best line in her recipe
strategy: question-ladder
cta: none
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "Grandma crossed out one line here." | ONE LINE CROSSED OUT | old recipe card, one line inked over | pen scratch |
| 2 | 0:03-0:07 | "So I baked her cake both ways." | | two bowls, two tins, oven door shuts | timer ticking |
| 3 | 0:07-0:11 | "Without the line: dry and flat." | WITHOUT IT | cake A sliced, crumbling | knife |
| 4 | 0:11-0:16 | "With it, perfect. So why cross out the best part?" | WITH IT | cake B, tall and glossy; cut back to the card | |
| 5 | 0:16-0:22 | "Under the ink, against the light: a cup of coffee. Don't tell Harold." | DON'T TELL HAROLD | card held to the window, the words show through | |
| 6 | 0:22-0:28 | "Harold, my grandpa, hated coffee. He ate this cake every Sunday for forty years." | 40 YEARS | old photo of grandpa holding a slice | soft piano |
| 7 | 0:28-0:30 | "I'm keeping it crossed out." | | the card goes back in the tin, lid shuts | click, cut |

### Problem, agitate, solve: Ferm proofer (30 s ad, fictional product)

```
format: ad
length: 30s
facts: Ferm keeps dough at 24-28 °C, folds flat, $89, 30-day returns
viewer: home bakers whose sourdough comes out flat in a cold kitchen
promise: a warm, steady place for dough in a cold kitchen
strategy: problem-agitate-solve
cta: link below
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "Fourth flat loaf this month." | #ad · MY 4TH FLAT LOAF | a hand presses a dense loaf; it doesn't spring back | thud |
| 2 | 0:03-0:08 | "Same starter, same recipe. My kitchen is just cold." | 17 °C | thermometer on the counter, breath-cold window | fridge hum |
| 3 | 0:08-0:13 | "I tried the oven with the light on. It melted my bowl." | | warped plastic bowl held up to camera | |
| 4 | 0:13-0:19 | "So now the dough goes in this. Ferm holds it at twenty-six degrees all night." | FERM · 26 °C | box unfolds, dial clicks to 26, bowl goes in | dial click |
| 5 | 0:19-0:24 | "Eight hours later." | | lid lifts: domed dough full of bubbles | soft gasp, music in |
| 6 | 0:24-0:26 | "It folds flat after." | | box folds into a slim panel beside the fridge | |
| 7 | 0:26-0:30 | "Eighty-nine dollars, thirty days to send it back. Link below." | $89 · 30-DAY RETURNS | loaf with a tall ear; finger taps the link | |

### Result first: Sift (25 s, fictional app)

```
format: demo
length: 25s
facts: Sift turns a call recording into decisions, owners and dates in about 30 seconds; tap a line to hear it
promise: an hour-long call in five lines you can trust
strategy: result-first
cta: try your longest call free
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "An hour-long sales call, in five lines." | 58:12 → 5 LINES | a long waveform collapses into five bullet lines | whoosh |
| 2 | 0:03-0:08 | "Who decided what, who owns it, by when." | DECISION · OWNER · DATE | the summary on a phone, three lines highlight in turn | ticks |
| 3 | 0:08-0:14 | "Drop in the recording. Thirty seconds later, this." | 0:30 | screen recording: drag file, progress bar, summary appears | click |
| 4 | 0:14-0:20 | "Tap any line to hear the moment it was said." | | finger taps a line; the clip plays, waveform lit | "...ship it Friday." |
| 5 | 0:20-0:25 | "Sift. Try your longest call free." | sift.app | logo and URL | music out |

### Misconception first: the hammer and the feather (40 s)

```
format: explainer
length: 40s
facts: NASA NSSDC, Apollo 15 hammer-feather drop
promise: why a hammer and a feather hit the Moon at the same time
strategy: misconception-first
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "Hammer or feather: which lands first?" | WHICH LANDS FIRST? | a hand holds a hammer and a feather side by side | wind |
| 2 | 0:03-0:08 | "Most people say the hammer. Heavy things fall faster." | HEAVIER = FASTER? | on grass: the hammer thuds, the feather drifts | thud |
| 3 | 0:08-0:14 | "On Earth the hammer wins, but not because it's heavier. Air holds the feather back." | AIR | slow motion: air currents lift the feather | |
| 4 | 0:14-0:23 | "So Apollo 15's David Scott tried it on the Moon, where there is no air. A hammer and a falcon feather." | 1.32 KG · 0.03 KG | an astronaut on grey dust holds both out at shoulder height | radio static |
| 5 | 0:23-0:28 | "He let go." | | both start to fall | silence |
| 6 | 0:28-0:33 | "They hit the dust together." | SAME TIME | both land at once, a small puff of dust | |
| 7 | 0:33-0:40 | "With no air, everything falls at the same rate. Galileo said it. Scott showed it." | ALL FALL AT ONE RATE | Earth over the lunar horizon | music |

### What is / what could be: Relay (45 s, fictional product)

```
format: brand
length: 45s
facts: Relay answers clinic calls, books the visit in the clinic calendar, texts the patient a confirmation; demo is 15 min
viewer: owners of small clinics
promise: no patient call goes unanswered while staff look after the patient in front of them
strategy: is-could-be
cta: book a 15-minute demo
```

| # | time | spoken | on screen | visual | sound |
|---|---|---|---|---|---|
| 1 | 0:00-0:03 | "This patient is calling. Nobody will answer." | | a phone rings on an empty front desk, full waiting room | ringing |
| 2 | 0:03-0:11 | "The front desk is checking someone in. The call goes to voicemail. The patient books somewhere else." | MISSED CALL | receptionist with a patient; phone shows missed call; the caller dials another clinic | |
| 3 | 0:11-0:16 | "Now picture every call answered on the first ring, at any hour." | FIRST RING. ANY HOUR. | same desk; the phone lights once and a calm voice answers | one ring, "Lakeside Clinic, good morning" |
| 4 | 0:16-0:22 | "Today your staff choose between the person in front of them and the phone." | | receptionist's eyes flick from the patient to the ringing phone | ringing |
| 5 | 0:22-0:32 | "With Relay they don't have to. It answers, books the visit in your calendar and texts the patient." | BOOKED · TEXTED | call transcript, a calendar slot fills, a text lands on a patient's phone | ding |
| 6 | 0:32-0:40 | "Your team stays with the patient in the room. The one on the phone is booked too." | | receptionist laughing with a patient; the day's calendar full | music lifts |
| 7 | 0:40-0:45 | "Relay. Book a fifteen-minute demo at relay dot health." | relay.health | logo and URL | music out |

## Variations

| Making | Read | What changes |
|---|---|---|
| a demo or launch video | `references/demo.md` | result first, villain, headline, value moments, real UI |
| a product review | `references/review.md` | disclosure, frame of reference, own test, the flaw, verdict for whom |
| an ad or UGC ad | `references/ad.md` | opener by awareness level, brand by 5 s, proof, one CTA, compliance |
| a social short or YouTube intro | `references/social.md` | hook formats, foreshadow, rehooks, platform versions |
| a short-form drama or skit | `references/drama.md` | cold open, a cliffhanger per episode, dialogue for lip-sync, series bible |
| better scripts over time | `references/improve.md` | log, read the numbers, test one thing, promote lessons |
| the best of several scripts | `references/judge.md` | code checks, yes/no gates from the brief, pairwise in both orders, calibration |

Test briefs for checking a change to this skill: `references/test-briefs.md`.

## YES / NO before you show it

- Does the first frame and line deliver the promise by 3 s (feeds) or 5 s (YouTube, demos)?
- Could a stranger repeat the promise after one watch?
- Does every join between beats read BUT or THEREFORE?
- Does every beat have a visual that shows it, and does no line describe its own picture?
- Is every number, name and claim in facts.md?
- Is there one ending action (or none, on purpose)?
- Does `check_script.py` report 0 FAIL?
- Would you say every line out loud to a friend?
