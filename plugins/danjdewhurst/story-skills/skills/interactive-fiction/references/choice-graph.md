# Choice Graph

How to shape a branching book before drafting it: the structure, the
choices, the numbering, and where the paths rejoin and end.

## Structures

Choose with the author; most books mix two.

| Structure | Shape | Cost and fit |
|-----------|-------|--------------|
| Branch and bottleneck | Paths split, then rejoin at key events | Keeps the passage count manageable; flags and state carry the differences. The usual choice |
| Gauntlet | A mostly linear spine where wrong choices end early or loop back | Cheap; suits survival and puzzle stories. Many short endings |
| Time cave | Every choice branches for good | Passages double at each layer; only for short pieces |
| Sorting hat | Early choices pick one of a few long, mostly linear routes | Each route is close to a novella; good for distinct POVs or factions |
| Hub | The reader returns to a central passage and visits the rest in any order | Fits a place with `routes` between locations; needs flags so revisits read differently |
| Loop and grow | The reader replays a stretch, with something changed each time | Needs a clear exit choice; the CLI does not check that a loop can be left |

Count before committing: a time cave three choices deep with two options
each has 15 passages and 8 endings. Set `target-words` for the whole graph,
and plan each path's reading length separately.

## Designing Choices

A choice works when it is:

- **Meaningful:** the options lead to different consequences, or to
  different ways of being the protagonist. Two options that reach the same
  passage with no change are a false choice; cut one or make it matter.
- **Informed:** the reader can guess what each option means from the
  passage. A choice that blindly kills the reader feels unfair.
- **Acknowledged:** the passage it leads to opens by showing the choice was
  made, even in one line.

Write `text` as the reader's action in the book's person and tense
(`Climb the tower to the lamp`). Keep the options parallel in length so
neither looks like the right answer. A single onward link uses
`text: Continue` or a short action.

## Numbering

The lowest number is the start. Number in reading order along the paths:

1. The start and the shared opening.
2. Each branch's passages, one branch after another.
3. Each rejoin after every branch that leads to it.
4. The endings last, or each ending right after its branch.

So every choice leads to a higher number except a deliberate loop back.
Checks that still read chapter numbers (see `path-continuity.md`) then
agree with the paths everywhere except between sibling branches.

## Rejoins

A rejoin (bottleneck) is a passage two or more branches lead to. It saves
writing, and it costs precision: its prose must be true on every incoming
path.

- List what each incoming branch changed: where people are, who is hurt,
  what objects moved, what the reader learned.
- Before the rejoin, converge what must converge: put the injured
  character in the same room, put the object in one hand. The last scene of
  each branch is the place to do it.
- What cannot converge stays out of the rejoin prose, becomes a flag
  in the built Twine or ink file, or means the branches should not rejoin
  there.

## Endings

A chapter with no `choices` is an ending. For each ending decide:

- Its kind: a full ending (`hook: resolution`), an early ending of a
  gauntlet (a failure that sends the reader back to the start), or a cliffhanger ending that
  points at another book.
- What it pays off: the choices on the paths that reach it.
- That a path reaches it: `story links .` warns `unreachable-chapter`
  when none does.

Give the endings comparable weight. If one ending is the true ending, say
so in the plan, and make the others worth reaching.

## Scope Check

Before drafting, confirm with the author:

- Passage count and endings fit the `form` and `target-words`.
- Every passage is reachable and every path reaches an ending.
- Each choice point has at least two meaningful options.
- Each rejoin has a list of what must converge before it.
- The flags in `notes/branch-map.md` are each set before they are read.
