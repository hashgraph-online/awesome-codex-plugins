---
title: Scanning & Attention
impact: MEDIUM
tags: reading, f-pattern, serial-position, banner-blindness, headings
---

**Rule**: People scan before they read, and skip whatever looks like an ad. Put the important words and items first, structure content for scanning, and keep important messages out of ad-shaped places.

**Evidence**: NN/g eyetracking — Nielsen 2006, "F-Shaped Pattern For Reading Web Content", revisited by Pernice 2017 ("F-Shaped Pattern of Reading on the Web: Misunderstood, But Still Relevant (Even on Mobile)") — unstructured text is scanned in an F shape; the F is a symptom to design against, and good structure prevents it. Murdock 1962 (*Journal of Experimental Psychology*) — the serial position effect: first and last items in a list are remembered best. Benway & Lane 1998 — banner blindness: users ignore content that looks like advertising.

### When Building

- **Front-load** headings, list items, buttons, and notifications with the meaningful word ("Invoice overdue: Acme Co" not "Notice regarding the status of an invoice")
- **Structure for scanning** — descriptive headings, short paragraphs, bulleted lists, bold key terms sparingly
- **Most important content top-left** (top-right in RTL locales), and first in lists
- **Order navigation by importance** — key items first and last; the middle of a long list gets the least attention
- **Important messages inline**, next to the affected feature — not in top banners, sidebars, or animated boxes that look like promotions
- **Numbers as numerals** ("3 days left"), which stand out in scanned text

### When Auditing

- Headings that are clever rather than descriptive
- Key information buried mid-paragraph or at the end of a list
- Critical announcements only in a banner, modal on load, or right rail
- Walls of text in onboarding, settings descriptions, or errors

### Incorrect

```tsx
<Banner>Important: we're updating how billing works for some accounts…</Banner>
```

### Correct

```tsx
// On the billing page, next to the affected plan
<InlineNotice>From 1 March, Team plans bill per active seat. <Link>What changes</Link></InlineNotice>
```

### Why This Matters

Most users never read most of a screen. What they need must be in the places scanning lands — or it is effectively not there.

### Alternatives

Long-form content meant to be read (articles, documentation, legal terms) is read differently; good typography and structure matter more than front-loading there. Mirror layout guidance for right-to-left languages.
