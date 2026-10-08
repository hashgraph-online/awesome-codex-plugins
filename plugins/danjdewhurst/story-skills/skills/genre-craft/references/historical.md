# Historical Craft

Historical fiction promises the reader a real past, felt from inside. The
facts belong to the `research` skill; this pack covers how the story
carries the period and what it owes the real people in it.

## Period voice vs. readability

The reader wants the period's texture, not its difficulty.

- **Choose a register and record it.** Decide how far narration and
  dialogue lean toward period speech, and write the decision in `story.md`
  notes and the style sheet (see the `voice-style` skill). Common choices:
  modern narration with period-flavoured dialogue, or a lightly archaic
  register throughout. Either works; switching between them mid-book does
  not.
- **Flavour through vocabulary and worldview, not spelling.** Period nouns
  (objects, trades, money, titles) and period assumptions do more than
  thee-and-thou or phonetic dialect, which tire the reader fast. Use
  archaic grammar sparingly and consistently.
- **Characters think in their time.** Attitudes, fears, and blind spots
  belong to the period. A heroine with a modern outlook nobody around her
  remarks on is an anachronism of mind, which readers notice more than a
  wrong button.
- Use character `voice-words` and `voice-avoid` lists to keep each
  speaker's register checkable with `story voices .`.

## Anachronism checks

Anachronisms come in three kinds; check all three.

- **Things:** objects, foods, technologies, materials, and institutions
  that did not exist yet, or not in that place or class. Verify each one
  the plot leans on with a research note (`accuracy: must-be-accurate`).
- **Words:** words and idioms coined later (*okay*, *teenager*, *scientist*
  before their time). Add known offenders to `watch-words` in
  `style-sheet.md` so `story prose .` counts them, and to a character's
  `voice-avoid` so `story voices .` flags them in dialogue.
- **Ideas:** concepts, values, and knowledge the period lacked (germ
  theory, modern psychology, present-day politics in period dress).
- **Dates and travel:** record `setting-era` in `story.md`, keep real
  events on their real dates in `plot/timeline.md`, and record routes with
  period travel times. Give the scenes on either end of a journey a
  `date`, `location`, and `characters` (or `pov`) so `story continuity`
  checks the journey against them; undated or chapter-level journeys are
  not checked.

## Invented vs. real people

- **Prefer invented protagonists among real events.** An invented
  character can act freely; a real one is bound by the record. When a real
  person leads, keep their documented acts accurate and mark where the book
  invents.
- **Record every real person** with a research note: `accuracy: blended`
  for real people in invented scenes, with the invented parts listed under
  `## Story Use`. A changed date or merged character is a deliberate
  departure and belongs there too, so a later fact-check doesn't "fix" it.
- **Gaps in the record are space, not licence.** Invent where the record
  is silent, not where it contradicts the story's needs. If the story
  must contradict the record, record that decision and say so in the
  author's note.

## Ethics of the real past

- **Recently dead and living people carry real risk.** Run the
  `editorial-review` skill's real-people pass
  (`editorial-review/references/real-people-and-permissions.md`) for anyone
  living, recently dead, or with living descendants who could be harmed,
  and set `risk: defamation` on their research notes.
- **Cultures and atrocities.** Portraying a real culture, faith, or
  historical atrocity carries `risk: cultural`: research from the
  community's own sources where they exist, and consider a sensitivity
  reader (`editorial-review/references/sensitivity-reader-brief.md`).
  Period prejudice may be depicted; the narrative should not endorse it by
  accident.
- **The author's note.** A historical novel usually ends with a note on
  what is real, what is invented, and what was changed. Draft it from the
  research notes' `## Story Use` sections.

## Historical audit (revision)

- [ ] The register is recorded and holds across the book.
- [ ] Every fact the plot leans on has a verified research note.
- [ ] Anachronistic words are on `watch-words` or `voice-avoid`, and `story prose .` and `story voices .` are clean of them.
- [ ] Characters' attitudes belong to the period, or the story addresses why they don't.
- [ ] Every real person has a research note, with invention recorded under `## Story Use`.
- [ ] Living or recently dead people have been through the editorial-review real-people pass.
- [ ] The author's note matches the deliberate departures recorded in research.
