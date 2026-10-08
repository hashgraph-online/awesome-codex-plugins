# Comedy Craft

Comedy promises the reader laughter that comes out of the story: out of
who the characters are and the trouble they make for themselves, not jokes
pinned to the surface of a scene. Much of comedy's craft is sentence-level
(the pause before a punchline, the word that lands it), and that belongs to
the `line-editing` skill (see *Sentence-level timing* below). This pack
covers the structure that gives the jokes something to land on.

## Escalation

A comic situation is a problem the character makes worse by trying to fix
it. The engine is escalation: each attempt raises the cost of the next.

- **Every step follows from the last.** Absurdity is earned in small,
  logical steps: the lie needs a second lie to cover it, the second lie
  needs a disguise, the disguise needs a borrowed dog. The reader must be
  able to trace the chain back to an ordinary start. A jump straight to the
  absurd is random, and random is rarely funny for long.
- **Escalate by complication, not volume.** Each step closes an exit (a
  witness arrives, the deadline moves up, the one person who must not find
  out walks in) rather than only getting louder. Comedy tightens the way a
  thriller does (`thriller.md`), with embarrassment where the thriller has
  danger.
- **Plan the sequence as a try/fail chain** (see
  `scene-craft/references/try-fail.md`). Each failure is caused by the
  attempt and is worse than the last: record each attempt scene's
  `outcome` as `no-and` or `yes-but`. `story pacing .` warns after three
  `yes` outcomes in a row, where the comedy has stopped pushing back.
- **Commit to the premise.** Once the story sets up a comic situation, play
  it out to its end. A premise dropped halfway, or rescued by coincidence,
  wastes the build.
- **Converge at the peak.** The comic climax collides the threads the book
  has built: every lie, disguise, and misunderstanding in one room at once.
  Plan the peak early, then work back to the set-ups it needs.

## Reversals

Comedy runs on expectation: the reader expects one thing, and the story
delivers another that, in hindsight, was always coming.

- **The plan backfires.** The character's solution causes the next
  problem. The best reversals use the character's own comic flaw as the
  mechanism.
- **Status reversals.** The pompous are brought low, the overlooked come
  out on top, the expert is out-thought by the amateur. Note who holds
  status at the start and end of each comic scene; a scene where status
  never moves is rarely funny.
- **Surprising but fair.** Like a mystery twist (`mystery-fair-play.md`), a
  comic reversal is planted: on a second look, the turn was always
  possible. A reversal that needs new information is a coincidence.
- **Pattern, then break.** If every expectation flips, the reader stops
  forming any. Let some scenes go to plan so the reversals land.

## Comic set-ups and payoffs

Comic payoffs follow the same discipline as any setup: plant first, pay off
later, and never abandon a plant the reader is waiting on.

- **Call-backs.** A line, object, or situation from earlier returns in a new
  context, and the recognition is the laugh. The first appearance works on
  its own (or passes as ordinary detail); the return changes something:
  who says it, where, or what it now means.
- **The rule of three.** Two items set a pattern; the third breaks it. It
  works at every scale: three items in a list, three attempts at a plan,
  three appearances of a running gag across the book.
- **Running gags must move.** A gag repeated unchanged dies by its third
  outing. Escalate, vary, or invert it each time, and end it: its last
  appearance pays off, ideally at the climax, where it can change the plot.
- **Give each set-up one record.** Pick it by use, as the shared
  conventions (`story-maintenance/references/conventions.md`) set out, and
  never copy a set-up into a second place:
  - A running gag, or a call-back or comic set-up the reader is owed a
    payoff on (the borrowed dog that must come back), is a promise in
    `continuity/promises/`:
    `story add promise 'The borrowed dog' --planted chapter-03 --payoff chapter-19`.
    `--planted` records `status: planted` when that chapter has a file,
    even an outline, and `planned` when it has none yet. Pass
    `--status planned` when the chapter has a file but the set-up is not on
    the page yet, and set `status: planted` once it is. `story continuity`
    then reports a payoff before its plant and warns about a planted
    set-up left unpaid. After adding promises, run `story reindex .`,
    `story wordcount . --write`, and `story check .`.
  - A small echo inside one arc that needs no checked payoff (a phrase that
    comes back two scenes later) is a row of that arc's `## Foreshadowing`
    table, which no command reads.
  - In a comic mystery, a clue stays a clue in `continuity/clues/`
    (`mystery-fair-play.md`), even when it is also a joke.
- **The climax pays off the plants.** Each element of the comic climax (the
  prop, the misunderstanding, the person in the wrong room) traces to a
  plant. An element that first appears there is a comic deus ex machina.

## Character-driven humour

The most reliable comedy comes from character: the reader learns what a
comic character will do and laughs when they do it, at the worst moment.

- **The comic flaw.** Give each comic lead one flaw (vanity, pedantry,
  cowardice, greed, an obsession) that is the source of both their humour
  and their trouble. Under pressure, the character does what the flaw
  demands, every time, for reasons that make sense to them. Record the
  flaw in the character file's `## Personality & Traits` section so every
  chapter plays the same one.
- **Characters don't know they are funny.** They take their goal
  seriously; the comedy is the gap between how much it matters to them and
  how it looks to the reader. A character who plays to the audience, or
  narration that nudges the reader to laugh, closes the gap.
- **Straight man and funny man.** Pair the comic character with one who
  reacts as the reader would. The straight reaction measures how far things
  have gone and gives the reader permission to laugh. Every comic scene
  needs someone (a character or the narrator) who sees the situation as
  abnormal; when nobody does, the absurd becomes the norm and stops being
  funny. Swapping the roles at a turning point (the straight man finally
  snaps) is itself a reversal.
- **Comic want vs. need.** The comic lead pursues a want, often petty or
  absurdly specific, with total commitment; the need is what the story
  makes them learn. Map them to the lie and truth in `theme-craft`
  (`theme-craft/references/lie-truth.md`): the comic flaw is often the lie
  played for laughs. A lead who already holds the truth while the world
  around them changes (the innocent whose decency reforms everyone) is a
  `flat` arc. A lead who never learns is different: the flaw stays a fixed
  trait, not a lie the story tests, so give the arc to another character
  (often the straight man) and record that decision in `story.md` notes.
- **Comic relief keeps its dignity.** A supporting comic character needs a
  goal of their own, not only jokes (see
  `character-management/references/supporting-characters.md`).

## Tone management

Comedy needs stakes. If nothing matters to the characters, nothing that
happens to them is funny.

- **Stakes are real to the character.** They can be small to the world (a
  dinner party, a reputation, a lie told to a mother-in-law) but are felt
  at full intensity by the character, as in MG/YA (`mg-ya.md`).
- **Record the tone line.** Decide how far the book mixes comedy with real
  harm, and where comedy stops: grief, cruelty, a death, the black moment.
  Write the decision in the `## Tone & Style` section of `story.md`, which
  `story context` gives the drafting agent for every chapter; it leaves
  out the free-form notes.
- **When to undercut.** A joke after a tense or dark beat releases the
  pressure, as horror's recovery period does (`horror.md`). A joke straight
  after a sincere moment the book has earned (the confession, the
  reconciliation, the loss) tells the reader it did not count. Let earned
  sincere beats play straight; the comedy around them makes them land
  harder by contrast.
- **Keep the threat intact.** An antagonist or obstacle mocked every time
  it appears stops being a threat, and the stakes drain with it. Let the
  opposition win some rounds without a joke.

### Comic sub-genres

Each sub-genre makes a different promise. Record it as `sub-genre` in
`story.md`.

- **Romantic comedy.** The romance contract holds: load `romance-beats.md`
  too, and the HEA/HFN is non-negotiable. The comedy comes from the leads'
  flaws colliding with the no-way obstacle; the black moment plays
  straight.
- **Farce.** Maximum escalation in a confined place and a short span of
  time: doors, disguises, mistaken identity, and lies that need more lies.
  Farce lives on logistics, so track them:
  - **Who is where.** Give each scene a `date`, an exact `time` (`HH:MM`),
    a `location`, and its `characters`. `story continuity` then reports a
    character in two places at the same minute (`route-same-time`), and,
    once the rooms have location `routes`, a dash between them faster than
    the route allows (`route-too-fast`). It skips scenes with no `date`,
    and a named time such as `evening` covers a span, so two scenes at
    `evening` never count as the same minute.
  - **Who knows what.** Record each secret in `knowledge-state` in
    `continuity/state.md` with its `learned-in` chapter, and run
    `story knowledge <id> --at chapter-NN` before drafting a chapter where
    a character might act on it. That check is per chapter: a secret
    learned in scene 5 counts as known in scene 2 of the same chapter. For
    a reveal partway through a chapter, also record it as a `character` and
    `knowledge` entry in the `state-changes` of the scene where it is
    learned; `story context <scene-id>` then gives the POV character the
    secret only in the scenes after that one.
- **Satire.** Exaggerate a real thing to expose it. The target is
  recognisable, and the exaggeration makes an argument (a controlling idea;
  see `theme-craft/references/controlling-idea.md`); mockery with no point
  is only sneering. Aim at power, not at people with less of it. A
  recognisable real person or organisation goes through the
  `editorial-review` real-people pass
  (`editorial-review/references/real-people-and-permissions.md`): satire
  may be treated differently, but that judgement belongs to a lawyer.
- **Cosy.** Low stakes for the world, high warmth, and a community the
  reader wants to return to. The contract is comfort: violence and lasting
  harm stay off the page or away from the beloved cast, and the ending
  restores the community. A comic cosy mystery loads `mystery-fair-play.md`
  too, and its clues still play fair; a cosy mystery not played for laughs
  needs only the mystery pack.
- **Comedy over another genre.** Comic fantasy, science fiction, or horror
  keeps that genre's rules: load its pack too. A world whose rules bend for
  a joke loses the logic comedy needs to escalate.

## Sentence-level timing

This pack stops at the scene. The pause before a punchline, the word that
lands it, the punchline placed at the end of its sentence and paragraph,
and the explanation cut after it are sentence-level timing, and they belong
to the `line-editing` skill. Run its line edit
(`line-editing/references/line-edit-checklist.md`, especially *Rhythm*) and
its read-aloud pass (`line-editing/references/read-aloud-guide.md`):
comic timing is easier to hear than to see. The structural questions stay
here: where in the scene and the chapter the laugh falls, and what it sets
up.

## Comedy audit (revision)

- [ ] Each comic sequence escalates by complication, and every step follows from the last.
- [ ] Each comic lead has one recorded flaw that drives their trouble, and none plays to the audience.
- [ ] Every comic scene has a straight reaction (a character or the narrator) that marks the abnormal.
- [ ] Reversals are planted; none depends on new information or coincidence.
- [ ] Call-backs and running gags change on each return, and every running gag ends in a payoff.
- [ ] Each comic set-up the reader is owed a payoff on has one promise record, and nothing in the climax first appears there.
- [ ] The stakes matter to the characters, the threat survives the jokes, and earned sincere beats play straight.
- [ ] The tone line is recorded in `story.md` `## Tone & Style` and holds across the book.
- [ ] The sub-genre's contract holds (the romcom's HEA, farce's collision, satire's target, cosy's comfort).
