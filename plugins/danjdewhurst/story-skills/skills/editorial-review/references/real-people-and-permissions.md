# Real People and Permissions

**This is a flagging checklist, not legal advice.** Law on defamation,
privacy, publicity rights, and copyright differs by country and changes.
Tell the user so, and recommend a lawyer who advises publishers before
publishing any book this pass flags as high risk. Publishers often
provide a legal read; self-publishers must arrange their own.

## Real-people pass

### 1. List every real or recognisable person and organisation

Include public figures, historical figures, real businesses and
institutions, and invented characters recognisably based on a real,
identifiable person (the author's ex, a former boss, a local figure).
A changed name does not help if the person can still be identified by
job, place, appearance, or events.

### 2. Classify each portrayal

| Portrayal | Typical risk | Action |
|-----------|--------------|--------|
| Long-dead historical figure, documented acts | Low for defamation in many jurisdictions | Research accuracy; mark invented scenes as invented in the author's note if the book presents itself as historical |
| Public figure, background mention or public acts | Low to moderate | Keep to the public record; avoid invented private conduct |
| Living person shown committing a crime, affair, dishonesty, illness, or other discreditable act they did not do | High | Flag for a lawyer; consider fictionalising fully |
| Invented character recognisably based on a private living person | High, and a frequent source of disputes | Change enough identifying details that the person cannot be recognised, not just the name |
| Real business or institution shown as corrupt, negligent, or dangerous | Moderate to high | Invent the organisation, or flag for a lawyer |
| Real person shown sympathetically or neutrally in a plausible way | Lower, but privacy and publicity rights can still apply | Note it; ask the user whether consent was sought |

A disclaimer that "any resemblance is coincidental" does not reliably
protect a recognisable portrayal. Satire and obvious fantasy can be
treated differently; that judgement belongs to a lawyer.

### 3. Record the risk

Open or update a research note per risky portrayal:

```shell
story add research 'Portrayal of the Harbour Board' --accuracy blended --risk defamation --used-in chapter-07
```

Record in the note who is portrayed, what the prose asserts, what is
documented (with sources) versus invented, and the decision taken. After
a legal read, add `publishing lawyer` to the note's `reviewed-by` list
(or the lawyer's name with consent). `story validate .` warns while a note with a `risk`
is used in a final chapter without `reviewed-by`. After you add or edit a note, run `story reindex .`,
`story wordcount . --write`, and `story check .`.

## Permissions for quoted material

### What usually needs permission

- **Song lyrics.** Even a line or two usually needs permission from the
  music publisher, and fees can be significant. Song titles and artist
  names are generally not protected and can be mentioned freely. Suggest
  referring to the song, paraphrasing the feeling, or writing original
  lyrics for an invented band.
- **Poems.** Short poems are whole works; quoting a stanza is a large
  share. Treat as needing permission unless public domain.
- **Prose epigraphs and extracts** from in-copyright works.
- **Images, maps, and artwork** not made by the author or licensed.

### Fair use is not a plan

Fair use (US) and fair dealing (UK, Canada, and elsewhere, generally
narrower) are case-by-case defences, not permissions. Publishers commonly
require written permission for epigraphs and lyrics regardless. Never
tell the user a quotation "is fair use"; say it may need permission and
that a lawyer or the publisher's permissions team decides.

### Public domain depends on place and date

In the United States, the public-domain cutoff for published works moves
forward every January 1; in the UK and EU, protection generally runs for
70 years after the author's death. Translations and new editions can
carry their own copyright. Ask the user to confirm status for their
market; do not assert it from memory.

## Matter-file fields

Each epigraph or quoted page in `matter/` records its state. Create an
epigraph with `story add matter 'Epigraph' --heading=false`, or edit the
scaffolded `heading:` key; never add a second `heading:` line.

```yaml
---
title: Epigraph
placement: front
order: 2
heading: false
permission: pending
rights-holder: "Estate of the poet, via Example Music Publishing"
credit: "Lines from 'Song Title' by Author Name. Used by permission."
---
```

- `permission`: `not-needed` (original text, or the user confirms no
  permission applies), `pending` (requested, not yet granted),
  `granted` (written permission received), `public-domain`.
- `rights-holder`: who granted or must grant it. Required for `granted`.
- `credit`: the exact wording the rights-holder requires; print it where
  they specify (often the copyright page or acknowledgments).

For quotations inside chapters, create a matter page or a research note
to track the permission; keep a table in the author's own notes if
neither fits.

`story validate .` warns when a matter page is `pending` and the story
status is `complete`, and when `granted` has no `rights-holder`.
`story export` and the builds leave a `pending` page out, with a
`permission-pending-left-out` warning, unless `--include-pending` is
given, so the review copy and shared files never carry it.

## Permission request checklist

Help the user draft the request; the user sends it. Include: the exact
text to be quoted, where it appears, the book's title, publisher or
self-published, formats (print, ebook, audio), territories, print run or
expected sales, price, and publication date. Keep the written reply with
the project records outside the manuscript.
