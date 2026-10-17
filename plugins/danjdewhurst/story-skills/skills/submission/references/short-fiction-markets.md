# Short-Fiction Markets

How submitting a short story, novelette, or novella to magazines, anthologies,
and contests differs from querying agents, and how to assemble a story
collection. These are general practices of the English-language market,
mainly US and UK. Every market publishes its own guidelines, and those
always win: ask the user for them, and never state a specific market's pay
rate, rights terms, reading period, or response time from memory. They change
too often to trust.

## How short-fiction submission differs

- The story goes out in full, not a query. Most markets want only a short
  cover letter: the title, the word count, a line or two of publication
  history if the author has any, and thanks. No pitch, synopsis, or comps
  unless the guidelines ask for them.
- The manuscript is the Shunn build with `form: short-story` or `form: flash`
  in `story.md` (see Build the manuscript in `SKILL.md`). When a market reads
  anonymously (its guidelines say so), add `--anonymous` to the Shunn build
  (`story build . --format docx --shunn --anonymous`, or
  `--format shunn --pdf --anonymous`). It leaves out the byline, contact
  block, and the surname in the running head, which keeps the short title
  and page number. Ask the user to check the chapter text for their name,
  and to follow the market's own anonymity rules.
- Word-count limits are the market's own. `word-count-norms.md` gives the
  usual bands for short story, novelette, and novella; a story that sits
  over a market's limit does not go to that market unless the user cuts it
  first, with `revision-continuity`'s
  [length pass](../../revision-continuity/references/pass-checklists.md#length-pass).
- Many markets open only in reading periods or for themed calls. Record the
  window the user gives you in the tracker Notes.

## Simultaneous and exclusive submissions

- **Exclusive:** the market wants to be the only one considering the story.
  The author waits for its answer before sending the story anywhere else.
- **Simultaneous:** the market accepts that the story is out elsewhere at the
  same time. When another market accepts it, the author withdraws it from
  every other market at once. Remind the user; never contact a market
  yourself.
- **Multiple:** more than one story sent to the same market at once. Most
  markets forbid it unless their guidelines say otherwise.

Record which applies on every tracker row. Before suggesting a market for a
story, check the tracker's open rows (`submitted` or `held`) for that story:

- If any open submission is exclusive, the story is not free to send
  anywhere.
- If the new market is exclusive, the story must have no open submissions at
  all; otherwise wait or choose a market that takes simultaneous
  submissions.
- If the market forbids multiple submissions, check that no other story is
  open there.

## Rights

A market buys the right to publish the story, usually for a limited time; the
author keeps the copyright. Common categories:

| Rights | Meaning |
|--------|---------|
| First rights | The first publication anywhere, often limited to a language or region (first English-language, first North American serial). Once used, they are gone |
| Reprint rights | Publication of a story that has already appeared somewhere. Many markets take no reprints; those that do usually pay less and ask where and when it first appeared |
| Audio rights | A narrated version, by a podcast or audio magazine. Some markets buy audio with text rights; some audio markets buy only audio |
| Anthology or collection rights | Inclusion in a book, often after an exclusivity period set by the first publisher |
| Exclusivity period | How long after publication the market holds the story before the author may resell it |

Count anything public as publication when the market says so: many treat a
story posted on a blog, a public forum, or a writing site as published, which
uses up first rights. Ask the user where the story has appeared before
calling it unpublished.

Read the rights terms in an acceptance against the user's records before they
sign, and record what was sold and when the rights revert. Contract terms
themselves belong to the `publishing` skill's `contract-red-flags.md`; this
skill does not give legal advice.

## Response times and status queries

- Markets state a response window, from days to many months. Use the window
  the user gives you; never estimate one.
- Once a submission passes the stated window, a short, polite status query is
  normal. Draft one on request: the title, the date sent, and a question
  whether it is still under consideration. Do not query before the window
  passes, and do not query again soon after.
- Some markets send a hold or shortlist notice before a final decision. A
  held story is still under consideration, and an exclusive hold still blocks
  other markets.
- A rejection needs no reply. Note any personal feedback in the tracker.

## Tracking short-fiction submissions

Use the same `submission/tracker.md` from `tracker-template.md`, with the
short-fiction columns below. Every row still comes from the user. A writer
with many stories may keep one tracker per story project, or one shared
tracker in a plain folder outside any project; ask which they want. A
tracker inside a project keeps the template's frontmatter, with `story` set
to that project's id. A shared tracker covers several stories, so leave out
`story`, title it `# Submission Tracker: Short Fiction`, and let the Story
column identify each row:

```markdown
---
type: submission-tracker
updated: YYYY-MM-DD
---
```

```markdown
| Market | Story | Date Sent | Type | Rights Offered | Status | Response Date | Notes |
|--------|-------|-----------|------|----------------|--------|---------------|-------|
| *No submissions yet* | | | | | | | |
```

- **Market:** the magazine, anthology, or contest, as the user gives it.
- **Story:** the story id, or its title in a shared tracker.
- **Type:** `exclusive` or `simultaneous`.
- **Rights Offered:** what the market's guidelines say it buys, such as
  `first`, `reprint`, or `first + audio`.
- **Status:** use `submitted` for a story sent in full, `held` for a hold or
  shortlist, then `offer`, `declined`, `no-response`, or `withdrawn` as in
  `tracker-template.md`. `offer` covers an acceptance.
- **Notes:** the reading period or deadline, the response window, the date
  of any status query, and any feedback.

Add a publication history section once a story is accepted, so reprints and
collections have their facts to hand:

```markdown
## Publication History

| Story | Venue | Date | Rights Sold | Rights Revert |
|-------|-------|------|-------------|---------------|
```

Fill each field from the user's contract or acceptance; leave a field blank
rather than guess it.

When summarising, report stories out by market, exclusive submissions still
open, holds, entries past their window, and stories with no submission out.

## Assemble a collection

A collection gathers one author's stories; an anthology gathers several
authors' stories, usually under an editor. The steps below fit both. Each
story stays an ordinary Story Skills project; the book is one more project
with each story as a chapter and no `form`. Its `story.md` `labels:` list
holds `chapter-heading: "{title}"`, so each heading shows the title alone. A
`labels` entry in a chapter's frontmatter has no effect. In an anthology, put
the editor in `story.md` `editor` and each story's writer in its chapter's
`author` (a name, or a list for a co-written story), never in the prose:
builds print it under the story's title and keep it out of the word count. Ask the user for every name; do
not guess a byline. Run `story validate .` after setting them.
`docs/series.md`, Short-story collections and anthologies, gives the
layout, the bylines, and the builds.

1. **Choose the stories.** List the candidates with each one's word count,
   form, and publication history from the tracker. Ask the user which to
   include; the total length should suit the publisher or format they have
   in mind.
2. **Find the linking threads.** Read every candidate and note what they
   share: a theme, a setting, a recurring character, an image, a tone, or a
   question the stories answer differently. Offer the user a one-line
   description of what the collection is about, and flag any story that
   pulls against it.
3. **Order the stories.** Open with one of the strongest and most
   representative stories, since it sets the reader's expectations. Close
   with a story that lands with weight. In between, vary length, tone, and
   point of view so neighbours do not blur; separate stories that open or
   end the same way; and place stories that answer each other where the
   reader will feel the echo. A linked collection with a through-line or
   shared timeline orders by that. Present the order with a line on why each
   story sits where it does; the user decides.
4. **Collect the acknowledgements.** Every previously published story needs
   a credit line: the title, the venue, and the year it first appeared, in
   the form the user's publisher asks for, such as
   `"Title" first appeared in {Venue}, {year}.` Take each fact from the
   publication history. Check that each story's rights have reverted, or
   that its first publisher allows reprinting in a collection, and list any
   that need the user to confirm. Never add a credit the user has not given.
   In the collection project, put the credits on a back-matter page:
   `story add matter 'Acknowledgements' --placement back`, then write the
   lines into `matter/acknowledgements.md`, then run `story reindex .`, `story wordcount . --write`, and `story check .`.
5. **Check the stories against each other.** In a linked collection, run
   each story's checks (`story check .`) and compare
   shared names, dates, and facts by reading. Note contradictions for the
   user; fix them with `revision-continuity`.
