# Prose And Report Workmanship

Use this reference when documentation needs to read like maintainable project material rather than agent-generated filler.

## Prose Cleanup

Remove writing artifacts that do not help the operator:

- Inflated claims without evidence.
- Repeated "not only/but also" constructions.
- Decorative punctuation or emphasis that hides the main point.
- Meta-commentary about how the document is written.
- Long setup before the command, decision, or finding.
- Labels coined during the work (lane nicknames, internal IDs, invented terms)
  and bare identifiers a reader without the code open cannot place. Say what
  each one is or does, unless the caller requires the term.
- Structure the content does not need: bullets around an argument (lists suit
  parallel items; reasoning reads better as connected sentences), a heading over
  a section of a sentence or two, a divider after every section of a short page,
  a table for one or two items, or a callout for an aside that would not derail
  the main line.

Keep the tone direct, concrete, and source-grounded.

## Order Ideas for a Learner

For a tutorial or explanation, decide which concepts the reader already brings.
Explain every other idea, named or not, before a section relies on it, and pick
each next section by what the reader needs next rather than by the order of
source files, notes or commits. When a section needs an idea not yet explained,
explain it earlier or state it as a prerequisite: too many prerequisites shut
readers out, too many early definitions bury the opening. Track what has been
explained in working notes, not a file.

## Diagrams

Decide per section from what it turns on. A flow across steps or components, an
exchange between parties, a lifecycle, a before-and-after data layout or a
decision boundary often reads faster as a picture; a single point, a rename or a
one-field change needs none. Your own prose seeming clear is no reason to skip
one. Place each diagram beside the sentence it supports and keep only the nodes
that sentence needs. The text states every relationship the diagram shows,
because agents and screen readers read the text; when the two disagree, the
text governs and the diagram gets fixed.

## One Live Statement

Within the authorized scope, when a fact or decision changes, rewrite or remove
the old text rather than striking it through or stacking an "Update" note under
it; version control keeps the history. Records whose history is the content
(changelog entries, ADRs, a handoff's failed attempts) keep it. State a rule,
limit or contract in full in one owning document and link to it elsewhere,
adding only what is local; for an external standard, cite it and name only this
project's differences.

## Architecture Report Rules

For codebase reports:

1. Start from the user-facing or operator-facing entry points.
2. Explain the dominant flow before listing files.
3. Name invariants and contracts, not just modules.
4. Separate facts from inferences.
5. End with risks and questions that affect future work.

## Final Pass

Before publishing docs:

| Check | Pass condition |
|---|---|
| Evidence | Claims cite code, commands, or source docs. |
| Brevity | Each section earns its place. |
| Operator value | The next reader can act without rediscovery. |
| No filler | Generic AI prose is removed. |

---

**Source:** Adapted from an external skill corpus / `de-slopify` and `codebase-report`. Pattern-only, no verbatim text.
