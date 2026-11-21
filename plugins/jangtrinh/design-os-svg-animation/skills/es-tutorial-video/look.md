# Look: what only eyes can check

Run `node skills/es-tutorial-video/look.mjs <project>`. It renders every chapter twice per aspect (chapter card at 0.75 bar,
settled content at the midpoint) and the frames on both sides of two shard seams, into one sheet PNG (landscape on top,
portrait below). It measures L1 to L5 itself (header of `look.mjs`) and exits 1 when one fails. The items below are yours.
Open the sheet and answer each one in your hand-over; "checked" without a frame number is not an answer.

1. **Captions readable.** The bilingual caption sits at the bottom, one line pair at a time, no overlap with a card, and
   contrast is sufficient on every background (dark terminal cards included). (R6)
2. **Nothing clipped that the machine cannot see.** A text line cut by its own card's `overflow:hidden`, a code line
   running past the card edge, a Vietnamese diacritic cut at the top of a line.
3. **Wipes do not jump.** In a phase wipe the part keeps its angle, scale and position across the layers. (R12)
4. **Card fan stays on stage.** Stacked or fanned cards keep their order and never leave the stage in 16:9 or 9:16.
5. **Portrait slots.** Each element has the right slot in 9:16 (left column up, right column down, full-width centred) and nothing
   important sits where the caption lives; if a slot is wrong, give that element a `p:` rect in the timeline.
6. **Honest limits are visible.** The limits chapter shows a sentence from the build record, not a paraphrase. (R15)
7. **Seam frames.** The two frame pairs at the end of the sheet are the frames either side of a shard seam; they must look like
   consecutive frames of one shot (same card, same scroll position, no flash).

## Without a browser

`look.mjs` exits 2 and prints `cannot run: ...` when there is no Chrome, no `puppeteer-core` next to the skill, or no ImageMagick
`montage`. In that case do not claim a visual check. Do this instead:
1. Run `validate.mjs` (it needs only node, ffprobe and git).
2. Ask the owner to run `look.mjs` on a machine with Chrome, or to open `out/beat-sheet-*.jpg` from a machine that has one.
3. In the hand-over, write "NOT verified: items 1 to 7 of look.md (no browser)" as the first line.
