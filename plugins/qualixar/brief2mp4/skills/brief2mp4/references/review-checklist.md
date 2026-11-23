# Review checklist: the second-reader pass

The maker of a video is the worst judge of it. They know what each frame is supposed to show, so they see it. This pass is a separate step done by a different reader (another agent session, a colleague, or at the very least yourself after a break with the checklist below and none of your notes). It comes after the self-check in SKILL.md section 4 and before delivery.

## How to run it

1. **Give the reader the evidence, not the reasons.** The rendered MP4, key frames, the brief, the beat sheet and this checklist. Not the maker's explanations of why a choice was made.
2. **Review the encoded file.** A preview can look right while the render lost a scene (see `references/render-traps.md`). Pull frames from the final MP4 at every beat and every cut with `scripts/contact_sheet.sh`.
3. **Report every item as PASS, FAIL (time: what) or CANNOT VERIFY.** Never guess. A review that finds nothing did not look at frames.
4. **Fix one class of problem at a time, minimally and locally.** A clarity pass that adds a global blur or deletes elements wrecks a look that was approved. Fix only the named defect, add no global effect, and show one changed chapter before re-rendering the rest.
5. **One audit, no repeats.** Re-check only what changed. Keep the previous version until the new one is confirmed better.

## Run the machines first

```bash
bash scripts/check_delivery.sh final.mp4 --seconds <N>      # spec, loudness, black, flicker, freeze
python3 scripts/check_clutter.py --boxes boxes.json         # or --dom index.html --at <beat times>
bash scripts/ocr_sweep.sh final.mp4                         # placeholder text and leaked paths
```

A passing script is not done. These cover resolution, loudness, flicker, overlap and placeholders; they do not judge whether the picture is the right one or whether the text is legible to a person. A checker is only as good as its negative test: when a check fails, look at the frame before believing it (OCR in particular misreads thin, wide-spaced display type).

## Viewing conditions

| Test | How | Pass when |
|---|---|---|
| Muted | Play the whole film with the sound off | The idea, the hook and the payoff still land; nothing depends on audio to be understood |
| Sound only | Listen without looking | The narration alone carries the story; no dead gaps, no hiss in pauses |
| Phone | View at about 6 cm wide, arm's length | Every line meant to be read can be read |
| 480 px | Scale a frame to 480 px wide | Every line meant to be read still reads; the focus is still the strongest shape |
| Squint | Blur a frame (or step back) | The intended focus is still the strongest shape |
| Stranger | Describe each beat frame in one sentence naming every object | Nothing needs explaining; an object you must explain is a defect |
| Pictures only | Cover the words | The pictures alone still tell the story |

## Items

**Hook and structure**
- The first frame is a complete image and something is moving by frame one; no logo sting, no "welcome".
- A new visual idea arrives on the pacing for the format (`references/motion-doctrine.md` section 13).
- The last 1.5-2.5 s hold still on the final message.
- Each beat serves a line in the beat sheet; anything that does not is cut.

**Clarity**
- One focus per frame. Size, contrast, motion and position agree on the same element. Dim non-focus items to 30-40% rather than deleting them.
- No card on card, no text touching text, at least 24 px between text boxes, at most four text blocks at once, nothing clipped at the frame edge (`check_clutter.py`).
- Text over a photo or busy background sits on a solid or frosted panel. Check contrast on the worst frame, not the clean one.
- Type floors, measured as rendered pixel height on a 1080-tall frame: spoken-line captions at least 56 px, supporting text at least 32 px, no more than five words in a headline and two lines of caption.
- Every claim on screen matches the picture next to it: numbers, names, counts, dates, empty states. Every word is spelled as in the spec.

**Motion**
- Arrivals ease out, exits ease in and are shorter; no overshoot unless the brief asked for playful.
- No lazy scale-breathing, no pop or flash (`check_seams.py`), whole-frame effects rationed.
- Counters do not reflow and end on the exact value.
- The cut or transition at each seam means what the story means at that point.

**Sound**
- Voice is clear against the bed on a phone speaker; the bed ducks under speech and returns in the gaps.
- No hiss or noise in the pauses; no white-noise whooshes.
- Loudness is right on the encoded file (`check_delivery.sh`).

**Truth**
- Real footage shows the whole app or window as a viewer would see it, not a cropped fragment or a hand-faked screen.
- No placeholder content: grey bars, lorem ipsum, stock icons, emoji as design, a missing recording shown as a label.
- No private strings: file paths, emails, keys, names, version badges (`ocr_sweep.sh --extra` adds your own patterns). Mask them before capture; a blur box over private text holds only while the page is still.

## Amateur tells

Things that make a generated film look generated. Any one is worth a fix.

- Every element enters the same way, from the same direction, with the same ease.
- Everything crossfades.
- Bounce or elastic easing on serious content.
- A slow zoom on a still image offered as motion (a slideshow).
- A logo floating small in a big empty box.
- Hand-drawn imitation where a real capture was available.
- Text directly on a busy generated background.
- A transcript on screen that repeats the voice.
- Pie charts, gridlines, tick marks, legends, six-panel dashboards.
- Whole-frame shakes and flashes on every beat.
- A headline that starts fading in the same spot where the last one is still fading out.
- Decoration that serves no idea (particles, gradients, glow with no job).
- A key readout that is gone before it can be read: hold at least (words / 3) + 0.5 s.
- A freeze that was not asked for (`check_seams.py` WARN).
- The same one-sentence hook structure every video.

## Scored critique loop (when a film needs to get better, not just pass)

Render stills at every beat. Score each from 1 to 10 on hook, legibility, motion, composition and look. Write down the three worst. Fix those three. Repeat until every still scores 8 or more. Stop after three rounds and list what is still open.
