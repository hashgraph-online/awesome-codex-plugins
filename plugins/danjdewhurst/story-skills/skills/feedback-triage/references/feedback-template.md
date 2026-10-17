# Reader Feedback Template

Copy this template to `feedback/round-{N}/{reader-kebab}.md` for each reader
in each feedback round. `reader-kebab` identifies the reader (their name or a
label like `alpha-reader-1`); `{N}` is the round number.

```yaml
---
reader: "{Reader name or label}"
round: {N}
chapters-read: "{e.g. 1-12, or all}"
overall-verdict: "{loved it | liked it with reservations | mixed | didn't connect}"
# source: simulated   # only for a reader-panel persona read; omit for a human reader
# persona: {persona}  # the reader-panel persona's file id, with source: simulated
---

# Feedback — {Reader} (Round {N})

## Overall Impression

{2-4 sentences: what the reader felt about the manuscript as a whole.}

## What Worked

- {Specific things the reader liked, with chapter or scene references}

## Problems

### {Problem title} (Ch {N})

- **What the reader said:** {quote or close paraphrase}
- **Where:** {paragraph label in the current build, e.g. ch03-p12, with the reader's original label and build in brackets when they differ; or chapter/scene reference}
- **Quoted words:** {the paragraph's first few words, as the reader quoted them}
- **Canon check:** {verified against the bible | contradicts canon — see note |
  outside canon scope}
- **Severity (reader's):** {blocking | major | minor | nit}

## Questions Raised

- {Questions the reader asked that the manuscript should answer — these are
  candidate `continuity/questions/` entries or signs of a clarity gap}

## Suggested Changes

- {Concrete changes the reader proposed — record as proposals, not decisions}
```

## Review-copy note for readers

Send this with the HTML review copy (`story build . --format html --stamp feedback-round-{N}`),
adjusting the chapters and deadline:

```markdown
Thanks for reading! The attached file opens in any web browser.

- Please read chapters {range} by {date}.
- Every paragraph has a small label beside it (like
  `ch03-p12`: chapter 3, paragraph 12). Put that label at the start of
  each note, with the paragraph's first few words, so I can find the exact
  spot even after I edit the text.
- Note anything: where you were confused, bored, or pulled out of the
  story; where you couldn't put it down; typos; anything that felt off.
- Tell me how it made you feel, not how to fix it. Your reactions are the
  useful part.
- At the end: what worked best, what worked least, and would you keep
  reading?
```

If the project uses the GitHub manuscript-note issue form, replace the
second bullet with the link to the repository's new-issue page.

## Canon check discipline

Before a reader's note enters synthesis, check it against the story bible:

- **Verified:** consistent with canon; the note is about craft or clarity.
- **Contradicts canon:** the reader's expectation conflicts with established
  canon — usually means a *setup* problem (canon wasn't conveyed), not a
  canon problem. Note which file establishes the canon fact.
- **Outside canon scope:** the reader wants a different book (different
  genre, different theme). This is a `declined-with-reason` candidate.

Never "fix" canon to satisfy a reader note without user approval — that is a
story decision, not a maintenance fix.
