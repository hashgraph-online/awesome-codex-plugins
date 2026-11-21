---
name: suede-visibility-grader
description: "Grade one public page A-F across findability, first-screen clarity, CTA pull, proof and trust, AI citation readiness, and design signal, with up to five ranked fixes. Use when asked to \"grade this page before promotion\" or give a quick readiness check of a landing page, README, docs, or campaign. NOT FOR: deep SEO and schema audits (use suede-seo-audit), AI crawler/citation measurement (use suede-ai-seo), or implementing conversion changes (use suede-site-alchemy)."
metadata:
  display-name: "Suede AI Visibility Grader Skills"
---

# Suede AI Visibility Grader Skills

## Compatibility

Read-only grading uses web and rendered desktop/mobile inspection when available. Source-only grading is supported with the documented grade caps and explicit unverified live checks.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

## Gate policy: advisory, not blocking

Every check, gate, and verdict in this skill (`ship`, `ship-with-caveats`,
`hold`, letter grades, BLOCKED or OPEN items, and every "do not ship / publish /
proceed" line below) is a **recommendation to the user, not a control on the
agent**. Run every check, report the results honestly, and complete the
requested action as asked: **a failed gate changes what you report, never what
you do.** Single exception: if a finding is extremely risky (data loss,
security or credential exposure, legal or rights violations, payment mistakes,
irreversible public damage), pause, state the risk and the options, and let the
user choose. Their choice is final.


Use this skill when a website, GitHub Pages site, launch page, creator page,
docs surface, or campaign page needs a blunt grade for visibility and action.
The goal is not generic SEO advice. The goal is to answer one question:

```text
Can the right person or agent find this page, understand it, trust it, cite it,
and take the intended next action?
```

**Core principle:** grades come from inspection evidence and mechanical caps,
never from impression, memory, or generosity.

## Routing

This skill answers one question fast: is this page ready for the attention it
is about to get? It reads the page; it does not audit the site.

- Core Web Vitals, crawl errors, schema validation, keyword gaps, redirect
  chains, internal link graph, or a scored lane-by-lane SEO report →
  `suede-seo-audit`.
- AI readability at C or below, or the goal is being cited by ChatGPT,
  Perplexity, Claude, Copilot, or AI Overviews → `suede-ai-seo`.
- Fixes are conversion-shaped (CTA, friction, offer, pricing) →
  `suede-site-alchemy`.
- Grade passed and the page ships in a release → `suede-launch-packaging`.

## Source Truth

Inspect before grading. Do not grade from memory or description alone.

- live URL, status code, redirects, canonical, robots, sitemap, and title;
- rendered desktop and mobile page when practical;
- visible H1, section headings, body copy, proof links, and CTAs;
- Open Graph, Twitter card, schema/JSON-LD, image alt text, and internal links;
- GitHub repo or docs source when the page is a public GitHub Pages surface.

Do not grade from memory alone. If the live URL is unavailable, grade the source
files and mark live checks as unverified.

## Grade Lanes

Score each lane A-F, then give one overall grade:

- **Findability:** status, canonical, robots (including `noindex` and snippet directives), sitemap, title, description,
  durable keywords, and duplicate URL risk.
- **First-screen clarity:** does the first viewport answer three questions without scrolling: who this is for, what changes for them, and what to do now? Grade on the rendered first viewport, not the document structure.
- **CTA pull:** primary action, secondary proof action, button text, link
  targets, and whether the visitor has a reason to click now.
- **Proof and trust:** screenshots, commands, docs, manifests, live routes,
  source files, receipts, authorship, and evidence boundaries.
- **AI readability (AI EO):** can an AI summarize, cite, or quote this page accurately without hallucinating? Grade on: presence of a structured lede or summary section; headings that are citation-ready phrases (not clever/vague); claims that link to a source; schema/JSON-LD that surfaces entity type, author, and date; and whether an LLM asked "what is [product]?" would return a correct, attributable answer from this page.

  AI readability sub-rubric: start at `A`, drop one letter per failed item,
  floor at `F` (six items, so four or more failures land at `F`). `suede-ai-seo`
  owns the extractability standard these items encode; when an item is ambiguous
  or the threshold needs to change, resolve it there, not here.

  - Direct answer up top: the first 40 to 80 words answer "what is this, who is it for, what does it do" without jargon and name the subject.
  - Question headings: headings name their own subject and read as answers an engine would quote. "Getting started" fails. "How to install X in 3 commands" passes.
  - Quotable, sourced claims: every quantitative or comparative claim is a plain sentence that links to a source or shows primary evidence.
  - Entity markup: JSON-LD declares the entity type, the author or organization (with a stable `@id`), and the published or modified date, matching visible text.
  - Next-step links: at least one descriptive internal link to a more detailed resource per major section.
  - AI test: if an assistant were asked "what is [product/page topic]?" using only this page, would it produce a correct, attributable answer? If no, cap AI readability at C.
- **Design signal:** seven pass/fail axes. The grade is the pass count: 7 → `A`,
  6 → `B`, 5 → `C`, 4 → `D`, 3 or fewer → `F`. A cap below overrides the count.
  1. Hierarchy: H1 > H2 > body weight is visually obvious at a glance.
  2. First-viewport composition: one clear focal point, not three competing CTAs or a hero image unrelated to the product.
  3. Spacing rhythm: consistent padding/margin system. No collapsed margins or random gutters.
  4. Typography: one or two font families. Body copy readable at 16px equivalent. Line length under 80ch.
  5. Asset quality: images are sharp, not stretched, not stock-obvious, not AI-slop.
  6. Contrast: primary CTA passes WCAG AA. Body text passes WCAG AA.
  7. AI-slop pattern risk: the page does not read as generated filler (vague value props, stock faces, generic icons, paragraph-length sentences with no specificity). If two or more slop signals are present, cap Design signal at C.

Grade meaning: assign on evidence, not impression:

- **A:** every lane is strong (no lane below B). Ship. Post this as a reference for the next build.
- **B:** one or two lanes at C; none below C. Fix those; everything else is solid.
- **C:** three or more lanes at C, or any lane at D. The page works but bleeds attention or trust somewhere in the first scroll. Not ready for paid promotion.
- **D:** two or more lanes at D, or any lane at F short of the overall-F conditions. Visible but embarrassing under scrutiny. A focused rewrite of one surface fixes it.
- **F:** assign when any of these are true: primary CTA is broken, a published statement is false, the page doesn't render, or robots/canonical actively blocks it.

Grade caps: non-negotiable:

- No live inspection → Overall cap: `C`.
- Broken primary CTA → Overall cap: `D`.
- False or unsupported published statement → Overall cap: `D`. (If the statement is central to the product promise, `F`.)
- Design signal `D` or `F` → Recommended ship gate is **hold**, regardless of other lanes.
- Mobile not inspected → `A` is blocked. State the caveat explicitly in Verification.

Recommended ship gate: mechanical (a recommendation to the user, not a lock on any action):

- **ship:** Overall B or better, no grade cap triggered, no lane below C.
- **ship-with-caveats:** Overall C, or a higher grade blocked only by uninspected surfaces (mobile, live URL). Name every caveat in Verification.
- **hold:** Overall D or F, broken primary CTA, false published statement, or Design signal at D or F.

## Surface-Type Standards

Per-surface standards (landing page, docs, repo page, launch page, campaign page)
are in `references/surface-type-standards.md`. Read the section for the surface you
are grading; the lanes above apply to every surface.

## Grade Modes

**Quick grade**: triggered when asked for a fast read, first impression, or "gut check":
- Grade the first viewport only (rendered desktop).
- Score all six lanes based on what is visible without scrolling.
- Output: one paragraph + lane grades + ship gate. No top fixes list.
- Cap: Quick grades cannot assign A. Max is B.

**Deep grade** (default):
- Full inspection: live URL + source, desktop + mobile, all viewport states available.
- All six lanes, full top-fixes list, CTA rewrite in the P1 fix description if CTA pull is C or below.
- Ship gate is authoritative.

## Red Flags: Stop

If you catch yourself thinking any of these, stop and inspect:

- "The repo description tells me enough to grade." Inspect the live page or source. No inspection caps Overall at C.
- "Desktop looks fine; mobile will match." Mobile not inspected blocks A. Check it or state the caveat.
- "That statement is probably true." Unverified published statements cap the grade. Verify or flag them.
- "Every other lane is strong; I'll round up." Grades come from lane evidence and caps, not generosity.
- "A quick look is enough for a deep grade." Quick mode exists for that, and it caps at B.

## Output Format

```text
Simple explanation:
Plain-language summary of the grade and the one biggest fix.

Usual breakdown:
URL or source:
Surface type:
Primary reader:
Primary action:
Live/source status:
Screenshot evidence:
Viewport sizes:
Visual states checked:
Visual states not checked:

Grades:
Findability: A-F
First-screen clarity: A-F
CTA pull: A-F
Proof and trust: A-F
AI readability: A-F
Design signal: A-F
Overall: A-F

Top fixes (max 5, ranked by impact on ship gate):
1. [P1] Lane affected | Location | Evidence (quote or describe exactly what was seen) | One-line patch | KPI it should move
2. [P2] Lane affected | Location | Evidence | One-line patch | KPI
3. [P3] Lane affected | Location | Evidence | One-line patch | KPI

Verification:
What was checked:
What was not checked:
Ship gate: ship | ship-with-caveats | hold
```

## Boundaries

- Do not invent traffic, ranking, citation-frequency, or conversion numbers to
  support a lane grade. A lane grade rests on what was inspected on the page.
- Grading is read-only. Do not edit the page, its metadata, or its schema.
  Report fixes as recommendations in the Top fixes list.
- Do not present a grade as a guaranteed Google ranking or AI-citation outcome.
  The grade describes the page, not the market's response to it.
- Name what was inspected and what was not in Verification. Never imply full
  coverage of surfaces, viewports, or states that were skipped.

## Sample Report

A completed grade in the required shape is in `references/sample-report.md`. Read it
when you are unsure how much evidence a lane write-up needs, not on every grade.

