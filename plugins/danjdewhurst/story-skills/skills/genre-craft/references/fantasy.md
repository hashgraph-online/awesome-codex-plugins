# Fantasy Craft

Fantasy promises the reader a world that works differently and a story that
could only happen there. The world itself (places, cultures, histories,
maps) belongs to the `worldbuilding` skill; this pack covers what the plot
owes the reader once that world exists.

## Quest and journey structure

Most fantasy moves: a quest, a flight, a pilgrimage, a campaign. A journey
is not a plot until it changes the travellers.

- **Every leg earns its chapters.** Each stage of the journey must change
  the board: an ally gained or lost, a cost paid, a truth learned, a
  capability tested. A stage that only shows scenery belongs in a summary
  line, not a chapter.
- **The destination is a promise.** Log the quest's goal in
  `continuity/promises/` with its planted chapter and its payoff chapter.
  The climax must engage it: reach it, fail it with consequences, or reveal
  the goal was the wrong one (planted fairly, as with any twist).
- **Distance is plot.** Record routes and travel times in location files
  (see `worldbuilding/references/maps-and-routes.md`), and give the scenes
  on either end of a journey a `date`, `location`, and `characters` (or
  `pov`). `story continuity` then flags a character who crosses the map
  faster than any route allows; it reads scene fields only, so undated or
  chapter-level journeys are not checked.
- **The road back.** The journey home, or the end of the road, shows what
  the quest cost. Pair with the Hero's Journey in
  `plot-structure/references/structure-models.md` when it fits, but the
  pack only requires that the return show change, not every beat.

## Magic rules and payoff

Magic follows the same discipline as sci-fi's speculative element (see
`scifi-pipeline.md`) and horror's monster rules: **state the rules before
the climax exploits them.**

- Write the system's rules, costs, limits, and failure modes in
  `worldbuilding/systems/` (the worldbuilding skill's system template) before
  drafting the chapters that use them. This pack checks those rules against
  the plot; it does not design them.
- **Problems solved by magic need rules the reader already holds.** The
  more a climax depends on magic to resolve, the more clearly its rules
  must be shown in use beforehand. Magic that stays mysterious can create
  wonder and danger, but it cannot solve the story's central problem.
- **Plant every climactic use.** Each spell, artefact, or ability the
  climax relies on appears earlier, even in passing, and ideally fails or
  costs someone once before it succeeds. Log it in `continuity/promises/`
  when the payoff is far from the plant.
- **Rule changes are continuity changes.** If the draft finds a better
  rule, update the system file and re-check every earlier scene that
  assumed the old one.

## Cost and limits

A power with no price generates no plot. Costs and limits are where
fantasy's choices live:

- Give the central magic at least one **cost** (blood, memory, years,
  sanity, a debt owed) and at least one **limit** (range, time, material,
  who can use it). Record both in the system file.
- **The cost must be paid on the page**, and it must rise. A cost waved
  away when it becomes inconvenient breaks the contract.
- Limits drive ingenuity: the best magical climaxes win by using a limit
  cleverly, not by discovering the limit never applied.

## Secondary-world exposition

The reader needs enough of the world to follow the plot, and no more at
any one time.

- Deliver the world through use, conflict, and consequence (see
  `scene-craft/references/exposition.md`). The prologue history lecture and
  the map-tour chapter are the genre's signature info-dumps.
- **Ration invented terms.** Introduce a new name, title, or word only when
  the scene needs it, and anchor each to something concrete. Keep names
  consistent with the world's naming rules
  (`worldbuilding/references/naming-languages.md`), and check each new name
  with `story names '<name>'` to catch clashes and look-alikes.
- Open close to the familiar: a human want or fear the reader recognises
  before the strangeness arrives.

## Chosen-one pitfalls

Prophecies, bloodlines, and destined heroes are conventions, not plots.

- **Destiny cannot replace choice.** The chosen one must still choose, at
  cost, at the climax. A prophecy that guarantees the outcome removes the
  stakes; one that can be misread, refused, or fulfilled at a terrible
  price keeps them.
- **Earned, not granted.** Power that arrives with the title must still be
  learned, tested, and failed with on the page.
- **Prophecies are promises.** Log each in `continuity/promises/`; its
  fulfilment must be planted and fair, whatever twist it takes.
- Supporting characters need goals of their own, not only service to the
  hero's destiny (see `character-management`).

## Fantasy audit (revision)

- [ ] Every leg of the journey changes the board; scenery-only stages are cut or summarised.
- [ ] The quest goal is logged as a promise and engaged by the climax.
- [ ] Magic rules, costs, and limits are in the system file and shown in use before the climax relies on them.
- [ ] No climactic spell, artefact, or ability first appears in the climax.
- [ ] Costs are paid on the page and rise; none is waved away.
- [ ] Invented terms are rationed and anchored; no history-lecture openings.
- [ ] Any chosen one makes a costly choice at the climax; destiny never decides it alone.
