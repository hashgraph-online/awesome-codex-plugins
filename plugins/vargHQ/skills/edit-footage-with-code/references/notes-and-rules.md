# Notes, rules and when to stop

## The watch comes before the notes

Ask the person to watch the whole cut with sound before changing anything, "like an editor's first cut" (@ForwardEditor, @darrrragh), then send everything together. Offer dictation: speaking is easier than typing. While they watch, change nothing.

## Note formats

Rewrite vague notes into these before acting on them, and read the rewrite back when it changes the meaning.

| Note about | Format | Example |
|---|---|---|
| A still | Object + problem + target state | "The person in frame 2: the big-face close-up looks unnatural. Switch to a frontal half-body." (@DZhao63405) |
| Motion | Timecode + problem + wanted change + what stays | "00:28-00:35: six images overlap the old title. Old title exits first, images arrange 3x2. Keep font and color." (@DZhao63405) |
| A join | Timecode + what broke | "At 00:27, the last word is clipped." (@ForwardEditor) |
| Picture on speech | Spoken word + visual state | "When she says 'Until now', the title card begins appearing." (@sara_nambiar) |
| A feel | A ratio on one property | "Slow every zoom and pan to 0.7x." This is speed: durations grow about 1.43x (@jake11moran) |
| Anything | Numbers, never adjectives | "No gap over 0.45 s", not "make it punchy" (@ladprofit) |

Under each note, write what you changed, or why you did not (@ladprofit).

## Change only what the note names

- Freeze approved work by name: "Do not modify Scene 01. Treat it as approved." (@sara_nambiar)
- A timing change moves everything downstream as a set: captions, animation, sound, total length (@bozhou_ai).
- Re-render only the changed range, and re-watch only that range (@elie2222, @finnardley).
- Keep every frame a pure function of time. No `Math.random`, no `Date.now`. Then a bug at 19.0 s stays at 19.0 s (@kodera_ai).

## Turn notes into rules

Keep `rules.md` in the project and read it before every edit. "A note you give once should never need giving twice." (@ladprofit)

- First sighting: proposed. Second sighting: permanent. One user's 325 + 45 notes became about 120 rules (@ladprofit).
- A person approves each rule, so one bad take does not teach the wrong lesson (@cathrynlavery).
- Keep general rules apart from this video's choices (@ForwardEditor).
- One small style file per format, never one giant skill (@ladprofit, @alexgoughcooper).
- **Saved text rules are not enforced.** Turn each numeric rule into a check in your QA, or it decays (`cathrynlavery/yap-studio` says so in its README).

## Style file

Write `style/<format>.md` before the first edit in a new format. Measure 3-5 references of one style, using one main reference per video. Treat the references as inspiration, never a copy (@darrrragh).

```markdown
# Style: <format>
Reference videos: <links, and what each one is for>
Length and shape: <target length, cold open or not>
Cuts: <cuts per minute, shortest shot, measured from the reference>
Pauses: <hold inside a thought, hold after a sentence, the beats to keep>
Framing: <static or punch-ins, zoom levels, longest same frame>
Captions: <words per cue, position, font, size, accent rule>
Motion: <easing, entrances, at most N per minute, what never moves>
B-roll: <share of runtime, kinds allowed, real UI only?>
Sound: <music or none, duck, effects policy, LUFS>
Not this: <the specific looks to avoid, by name>
```

To measure a reference: `hyperframes measure <video>` reports cuts, motion and timing; `scenedetect -i reference.mp4 detect-adaptive list-scenes` gives shot lengths. Numbers an agent reports about a famous creator are not independent measurements, so label them.

## When to stop

**No source we read states a stop rule for human rounds. This one is ours:**

1. Write the acceptance list before the first render: no black or frozen frames, voice complete, captions follow speech, nothing overlaps, text readable on a phone (from @DZhao63405).
2. Self-review at most 3 passes, then show the person and list what is left (video-use).
3. Stop when the numeric checks pass and one full watch with sound produces no note the reviewer would block publishing for.
4. If the same note comes back twice, stop re-prompting. Write a rule or a check, or have a person fix it by hand from the exported timeline.
5. If the notes are taste and no longer point at errors, offer 2-3 options rather than another revision.
6. Show the round count and cost each round. On a new format, flag it at round 5.

Green checks are not approval. @ladprofit sent back 9 of 10 cuts that passed their checks. @heygalatea's version 2 passed with 0 errors and a person still found bugs.

## What stays with the person

Script and story choices; how a caption reads; reaction shots at a story turn; skin tone and color; the music; names, prices and dates on screen; sameness; and the final "would I post this?" (@ladprofit, @darrrragh, @itsohqay, video-use).
