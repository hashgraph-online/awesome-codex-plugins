# Metadata Checklist

Retailers, libraries, and search engines know the book only through its
metadata. Fill these `story.md` fields, then run
`story build . --format metadata` and work through its readiness
checklist.

## Fields

Use `authors:` instead of `author:` for a co-written book. `language` is a
BCP 47 tag (`en`, `en-GB`, `es`, `fr-CA`, `pt-BR`). Prefer an ISBN-13; the
checksum is validated. `publisher` is the imprint name, or the author's name
when self-publishing. Keep comments out of the block itself: text after `#`
on a value line becomes part of the value.

```yaml
title: The Last Ember
author: Jane Doe
language: en
isbn: 9781234567897
publisher: Ember Lane Press
publication-date: 2027-03-02
description: "The retailer description, on one line; see the Description section."
keywords:
  - cozy fantasy found family
  - dragon bakery romance
subjects:
  - FIC009000
  - FIC027030
copyright: © 2027 Jane Doe
cover: images/cover.jpg
cover-alt: A lantern-lit bakery on a cliff with a small dragon asleep on the roof.
ai-disclosure: No generative AI was used in writing this book. The cover was designed by a human artist.
```

| Field | Check |
|-------|-------|
| `title` | Matches the cover exactly. Subtitle only if the cover shows it. |
| `author` / `authors` | Matches the cover. Pen names are fine; be consistent across every book. |
| `language` | The edition's language, with region only when it matters (`en-GB` spelling, `pt-BR`). Retailers file the book by it, and builds declare it. |
| `isbn` | Belongs to this format and edition. `story validate` checks the checksum, not ownership. |
| `publisher` | The imprint the ISBN is registered to. With a free retailer ISBN, the retailer sets it. |
| `publication-date` | The on-sale date. Preorder platforms may lock it; moving it later can carry penalties, so check the retailer's current rules. |
| `description` | See below. The sheet counts characters against common limits. |
| `keywords` | Up to 7 (the sheet warns over 7). See below. |
| `subjects` | BISAC codes. See below; Thema codes go elsewhere. |
| `copyright` | `© YEAR NAME`. Year of first publication. |
| `cover-alt` | One or two sentences describing the cover for screen-reader users. Describe the image, not the marketing. |
| `ai-disclosure` | See below. |

Series books also need `series` and `book-number`; retailers link series
pages by them. `series` is a kebab-case id, not the retail name: set
`series-title` (such as `The Ember Cycle`) for the name the metadata sheet
prints, and keep it identical in every book. `book-number` accepts `0` for a
prequel published later and a decimal such as `1.5` for a novella between
books.

## ISBNs

- **One ISBN per format and edition.** Paperback, hardcover, ebook, large
  print, and audiobook each need their own. A new edition with substantial
  changes needs a new ISBN; correcting typos does not.
- **Who issues them** depends on the publisher's country. The agency is
  national: for example Bowker in the US, Nielsen in the UK and Ireland,
  Thorpe-Bowker in Australia, and Library and Archives Canada, which issues
  them free to Canadian publishers. Outside the English-speaking markets,
  for example, AFNIL issues them in France, MVB in Germany, INDAUTOR in
  Mexico, the Cámara Argentina del Libro in Argentina, and the Câmara
  Brasileira do Livro in Brazil. Many countries' national libraries
  issue them free. Agencies and their fees change, so find the current
  agency for the author's country in the International ISBN Agency's
  directory. Buying ISBNs from resellers other than
  the national agency can register the reseller as publisher.
- **Free retailer ISBNs** (KDP, Draft2Digital, IngramSpark in some
  countries) cost nothing but usually list the retailer or "Independently
  published" as publisher, and often cannot be used on other platforms.
  Owning the ISBN keeps the author's imprint on the record and lets one
  ISBN follow the print book to every distributor. Check each platform's
  current terms.
- **Ebooks:** some retailers do not require an ISBN for ebooks (Amazon
  assigns an ASIN). Libraries and some wide retailers expect one.
- **Barcode:** print covers need the ISBN as an EAN-13 barcode, often with
  a price add-on. Printers' cover templates or the ISBN agency can
  generate it.

## CIP and Library of Congress

- In the US, Library of Congress Cataloging in Publication (CIP) data is
  usually unavailable to self-publishers. A self-publisher can apply for a
  Preassigned Control Number (PCN) before publication for print books and
  print the LCCN on the copyright page; the program expects a copy of the
  published book. Check the Library of Congress's current eligibility.
- Some vendors sell publisher-prepared cataloging data (P-CIP). It is
  optional; libraries that want the book can catalog it anyway.
- Other countries run their own CIP and legal-deposit schemes through the
  national library. See `copyright-page.md`.

## Description

- Write it in the book's language. Start from `submission/blurb.md`. The first two lines show before the
  "read more" cut: hook first, no throat-clearing.
- The sheet counts characters against common limits (KDP 4000). Most
  good descriptions run 150-300 words, well under any limit.
- Some retailers accept limited HTML (bold, italics, paragraphs); check
  the platform. Keep a plain-text version in `description`.
- No review quotes, prices, time-limited offers, or other books' titles
  unless the retailer allows them and the author supplied them.

## Keywords

- Think like a reader typing into a search box: sub-genre + trope +
  setting + mood (`enemies to lovers space opera`,
  `small town cozy mystery with cat`).
- Do not repeat words already in the title, subtitle, or categories; most
  search engines already index them.
- Never use other authors' names, other books' titles, trademarks, or
  claims like "bestseller" or "free". Retailers prohibit them.
- Phrases beat single words. Seven slots is the common limit.

## BISAC Subjects

- BISAC codes (`FIC022000` is Fiction / Mystery & Detective / General)
  come from the Book Industry Study Group's list. Look up the current list;
  codes are revised.
- Pick the most specific code that fits. Two or three codes is typical;
  check each platform's current limit.
- Amazon uses its own browse categories and may not take BISAC directly.
  Choose those in the KDP dashboard to match these codes.
- Category and keyword choices should agree: a book in the wrong category
  ranks badly with readers who expected something else.
- BISAC is the North American scheme. `subjects` holds BISAC codes only;
  `story validate` errors on any other shape.

## Thema Subjects

- Thema is the international, multilingual subject scheme maintained by
  EDItEUR. Many retailers and distributors outside North America ask for
  Thema codes instead of, or as well as, BISAC, and in the UK it replaced
  the older BIC scheme.
- Thema codes are letters, with optional qualifiers for place, language,
  time period, and audience; fiction codes start with `F`. Look up the
  current list in the book's language on EDItEUR's Thema site; codes are
  revised.
- `story.md` has no field for Thema. Record the chosen codes in
  `publishing/launch-plan.md` under Decisions and enter them in each
  distributor's form. Keep them consistent with the BISAC codes and
  keywords.
- Keywords work in the language of the store: write them in the book's
  language, as its readers search.

## AI Disclosure

- Ask the author exactly how AI tools were used: writing, editing, cover,
  interior art, translation, narration, marketing copy.
- Retailers distinguish content an AI generated (text, images,
  translations) from AI assistance on work the author wrote. Some require
  disclosure of generated content during upload. Check the retailer's
  current policy.
- Write `ai-disclosure` as one or two plain sentences that would survive a
  reader asking follow-up questions. The same statement serves agents,
  publishers, and grant applications.

## Before Upload

- [ ] `story validate .` has no errors
- [ ] The metadata sheet's readiness checklist is clean
- [ ] Title and author match the cover and the interior title page
- [ ] The ISBN on the copyright page matches the ISBN in the upload form
- [ ] Price set per market (see `launch-plan.md`)
- [ ] Age range or content warnings set where the platform asks
- [ ] Cover meets the retailer's current size and file specs
