# Edit Note Format

The author must be able to accept or reject each change in seconds. Every
proposed edit shows where it is, what it was, what it becomes, and why.

## One edit

```markdown
**ch03-p12** · clarity
> Before: It was the sound of the bell that she heard first, ringing out over the water.
> After: The bell rang out over the water.
Why: moves the subject forward and cuts the filter verb *heard*.
```

- **Location:** paragraph label in the form the HTML build uses
  (`ch03-p12`: chapter 3, paragraph 12). Take the label from
  `story build . --format html`; only the build's labels are
  authoritative. Do not count paragraphs by hand: the build drops
  comment-only blocks and headings such as `## Chapter Text`, so a hand
  count disagrees. A label is a position in that build, so any edit earlier
  in the chapter renumbers the ones after it; rebuild after edits before
  citing labels.
- **Category:** one of `clarity`, `precision`, `economy`, `rhythm`,
  `pov`, `voice`, `dialogue`, `grammar`, `punctuation`, `consistency`,
  `typo`.
- **Before/After:** the smallest span that shows the change in context,
  usually one sentence. For a cut, After is `(cut)`.
- **Why:** one line naming the effect. Never "sounds better" or "flows
  better": say what is clearer, cut, or restored.

## A batch

Present edits in paragraph order within a chapter, about 20 at a time,
with the highest-impact edits flagged first in a short summary:

```markdown
## Chapter 3 · line edit (light) · 14 edits

Main patterns: filter words in the dock scene (5), two pronoun
ambiguities between Maren and Ilse, echo of *water* in p12-p15.

1. **ch03-p04** · pov ...
2. **ch03-p07** · clarity ...

Reply with the numbers to accept, reject, or discuss (e.g. "accept all
but 6 and 11").
```

Pure mechanical corrections (a typo, an avoided spelling from `story
prose .`) may be listed compactly, one line each, and applied together
when the author accepts the batch.

## Queries instead of edits

When the fix depends on the author's intent, ask rather than edit:

```markdown
**ch05-p22** · query
> "She'd never seen the lighthouse dark."
Query: chapter 2 has her watching it go dark in the storm. Is this a
continuity slip, or does she mean dark by choice?
```

Continuity queries go to `revision-continuity` once the author answers.

## Applying and recording

1. Apply only accepted edits, directly in the chapter markdown.
2. Note rejected edits whose reason is a rule (a deliberate fragment, a
   character's grammar) and record the rule in `style-sheet.md` or the
   character file, so the same edit is not proposed again.
3. Report at the end: edits applied, rejected, queries open, and files
   changed (chapters, style sheet, character files).
