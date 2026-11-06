# Lane Checklists

Detailed checklists for suede-seo-audit Lanes 1–4 and 6–9. Read the checklist
for each lane as you run it. Lane 5 (Schema Markup) lives in
references/schema-templates.md. Grade-drop rules and scoring live in SKILL.md.

## Contents

- [Lane 1: Technical Access](#lane-1-technical-access)
- [Lane 2: Search and Answer Intent](#lane-2-search-and-answer-intent)
- [Lane 3: Metadata](#lane-3-metadata)
- [Lane 4: Structure and Internal Links](#lane-4-structure-and-internal-links)
- [Lane 6: Answer Extractability (generative search)](#lane-6-answer-extractability-generative-search)
- [Lane 7: Copy and Conversion Quality](#lane-7-copy-and-conversion-quality)
- [Lane 8: E-E-A-T Signals](#lane-8-e-e-a-t-signals)
- [Lane 9: Topic Clusters and Site Architecture](#lane-9-topic-clusters-and-site-architecture)

---

## Lane 1: Technical Access

- [ ] HTTP status is 200 on the canonical URL
- [ ] Redirects reach the intended canonical without loops or avoidable chains;
      record every hop and its status rather than claiming a fixed equity loss
- [ ] Canonical URL is self-referencing and matches the intended URL
- [ ] Trailing slash is consistent across all internal links to this page
- [ ] www and non-www resolve to the same canonical (no duplicate indexing)
- [ ] http redirects to https (no mixed-content split)
- [ ] `robots.txt` permits the intended Google crawler. Record `*` and
      `Googlebot` rules separately. Check other named crawlers only when the
      audit asks for them; one crawler's rule does not represent another's.
- [ ] `<meta name="robots">` is absent or set to `index, follow`
- [ ] If the site publishes a sitemap, the canonical URL is represented where
      appropriate; `<lastmod>` is present only when it accurately reflects a
      significant page update. A sitemap is a discovery aid, not a guarantee.
- [ ] Compare raw HTML with the rendered DOM. If primary content depends on
      JavaScript, verify the rendered result with an appropriate browser and,
      when available, Google URL Inspection rather than failing it merely for
      using JavaScript.
- [ ] Bing: site verified in Bing Webmaster Tools (ask; cannot be checked from
      outside), sitemap submitted, `Bingbot` allowed. Copilot grounds on the
      Bing index, so a page missing from Bing cannot be cited there.
- [ ] IndexNow: if the site publishes often, a key file is served at the root
      and the CMS or deploy step pings on change. Optional; Google does not use
      it.
- [ ] Core Web Vitals measurement protocol (see below: never enters the A-F
      grade)

### Core Web Vitals (measure when possible: never part of the A-F grade)

Measurement protocol:

- [ ] Run `curl -o /dev/null -s -w "%{time_total}" <URL>` as a proxy for server
      response time. curl measures server response, not browser rendering: on
      its own it is never a CWV score.
- [ ] If PageSpeed Insights is accessible at pagespeed.web.dev, fetch it.
      Prefer the field data (CrUX, 75th percentile, mobile and desktop
      separately) over the lab run; say which one you report.
      Report LCP, CLS, INP against these thresholds:
      LCP ≤ 2.5s = Good, 2.5–4s = Needs Improvement, >4s = Poor.
      CLS ≤ 0.1 = Good, 0.1–0.25 = Needs Improvement, >0.25 = Poor.
      INP ≤ 200ms = Good, 200–500ms = Needs Improvement, >500ms = Poor.
- [ ] If tooling is unavailable, report each vital as "not measurable" with the
      reason, and record implementation signals to investigate without turning
      them into invented CWV scores: render-blocking work, hero-resource
      priority, image dimensions/compression, font loading, main-thread work,
      long tasks, third-party code, and layout shifts. Do not lazy-load the LCP
      image by rote or prescribe `preconnect`, a format, or code splitting
      without a trace showing the bottleneck.

Do not invent scores; do report observable risks. CWV never enters the lane's
A-F grade.

---

## Lane 2: Search and Answer Intent

- [ ] Name the primary reader in one phrase (e.g., "a creator who wants to
      register a music release")
- [ ] Name the primary query theme (what someone types or asks to land here)
- [ ] Write a standalone definition from the opening section: "[Entity] is
      [what it does] for [who] by [how]." If the page cannot support one,
      report the ambiguity and reader impact. This is a Suede clarity
      diagnostic, not a Google ranking requirement.
- [ ] Name one action the page should earn (install, sign up, read docs, fork
      repo, contact)
- [ ] Check for keyword cannibalization: are there three or more other pages on
      the same site targeting the same primary term? If yes, flag which URL
      should be the canonical topic owner
- [ ] Does the page answer a question a person would plausibly ask aloud?
- [ ] Is the primary intent clear in the opening section without relying on a
      universal word-count cutoff?

---

## Lane 3: Metadata

**Title tag**
- [ ] Present, concise, descriptive, and specific to this page
- [ ] Primary subject or entity is identifiable without forced front-loading
- [ ] Brand naming and separators are accurate and consistent; no separator is
      treated as a ranking requirement
- [ ] Accurately matches the page and visible main heading
- [ ] Does not start with "Welcome to" or the domain name
- [ ] Character count recorded as a preview diagnostic only. Google has no
      fixed title character limit and truncates to fit the result context.

**Meta description**
- [ ] Present and accurately summarizes this page
- [ ] Contains the primary outcome or action, not a feature list
- [ ] Does not duplicate the title
- [ ] Does not contain structured data markup or JSON
- [ ] Character count recorded as a preview diagnostic only. Google has no
      fixed meta-description character limit and may use page content instead.

**Open Graph**
- [ ] og:title and og:description are accurate and preview-tested on the target
      social surfaces; no unsupported universal character cutoff is applied
- [ ] og:image: set and preview-tested at the target platform's current
      recommended dimensions/crop; meaningful content survives cropping
- [ ] og:url: matches canonical URL
- [ ] og:type: set to `website`, `article`, or appropriate type

**Twitter/X card**
- [ ] twitter:card: `summary_large_image` for pages with a hero image
- [ ] twitter:title and twitter:description: set and distinct from OG when
      appropriate
- [ ] twitter:image: set and accessible without authentication

**Other**
- [ ] Informative images have contextual alt text; decorative images use empty
      alt text or equivalent semantics instead of redundant descriptions
- [ ] Author or publisher entity name appears in metadata or schema (not just
      visible copy)
- [ ] Durable entity names are consistent across relevant metadata and visible
      content without requiring repetition in every field

---

## Lane 4: Structure and Internal Links

**Headings**
- [ ] One clear page-level heading or equivalent semantic main heading matches
      the title intent. Multiple H1 elements are not failed solely by count;
      judge hierarchy and accessibility in the actual document.
- [ ] H2s cover the primary sub-topics a searcher would expect
- [ ] H3s are optional but used consistently if present
- [ ] Headings are concise enough to scan and specific enough to identify their
      section; no universal word cutoff is applied

**Retrieval chunking (warning only, never a grade drop)**

Google states its Search AI features need no chunking. This check comes from
Google Cloud's Vertex AI Search, a separate product whose largest configurable
chunk is 500 tokens; Suede uses it as a proxy for how retrieval systems in
general split pages. Report it as a heuristic, never as Google Search behavior.

- [ ] Flag heading sections over ~375 words (about 500 tokens). Measure the
      prose between one heading and the next, excluding `<nav>` and `<footer>`
      chrome.
- [ ] An accordion, tab set, or FAQ whose items are marked up with `<summary>`,
      `<button>`, or `<div>` rather than headings counts as ONE block, however
      many items it holds. Valid FAQPage JSON-LD does not fix this: the schema
      can describe a structure the prose does not have, and a schema-only pass
      is the most common way this defect survives an audit.
- [ ] Each claim worth citing sits inside one chunk together with the heading
      that identifies it. A claim split across a boundary can be retrieved
      without the heading that gives it meaning.
- [ ] Record the largest block's word count and its heading as evidence, not a
      pass/fail alone. A section within ~10% of the limit is worth flagging,
      since routine copy edits push it over.

Chunking check output format:
```
Largest block: [N] words under "[heading]" | limit ~375 | [within/over]
Blocks over limit: [count] of [total headings]
Accordion/FAQ items marked up as headings: [yes/no: N items]
```

**Heading self-sufficiency**
- [ ] Every H2-H6 names its own subject. Discovery Engine carries the ancestor
      headings alongside a chunk OPTIONALLY, so a chunk can arrive holding only
      its own immediate heading. This is NOT the hierarchy check above: a page
      can nest H1 > H2 > H3 perfectly and still have an H3 that identifies
      nothing once detached.
- [ ] No heading is a bare stock phrase: How it works, Pricing, Features,
      Overview, Benefits, FAQ, Get started, Why us, Our process. An H3 reading
      "Pricing" is meaningless away from the H2 that named the subject;
      "How Suede Scan pricing works" survives alone.
- [ ] Single-word headings get the hardest look, since they carry a subject only
      by accident. A heading already holding a proper noun, an acronym, or the
      page's primary subject passes: do not rewrite it.
- [ ] Record each finding with its parent heading, so the fix (folding the
      parent's subject into the child) is visible without opening the page.
- [ ] Warn, never fail, and never drop a grade on this alone. It is a heuristic
      about language. Where bare headings run through the whole page, report one
      finding about the page rather than one per heading.

Heading self-sufficiency output format:
```
Detached heading "[heading]" (H[n], under "[parent]") | [stock phrase/single word] | fix: "[rewritten heading]"
Sub-headings not naming their own subject: [count] of [total]
```

**Table markup**
- [ ] Comparison content uses `<table>`, not CSS grid or flex `<div>`s.
      Discovery Engine parses tables as structured content; a grid-built table
      reads as an undifferentiated run of text, so the row and column
      relationships that make a comparison quotable are lost.
- [ ] Structure carries the finding, never a class name: repeated sibling
      elements with a consistent child count, holding short cell-sized text.
      Confirm the content is genuinely tabular by eye before reporting it.
- [ ] Class names are the weakest signal and prove nothing alone. `flex-row`,
      `grid-rows-*`, `flex-col` and `grow-0` are layout utilities, measured
      against live homepages on 2026-08-22, a substring match on grid|row|col
      fired on four of five.
- [ ] Report as an informational observation, never as a scored failure. CSS
      grid is used for every kind of layout, and a false finding in a paid audit
      costs more than a missing one.
- [ ] A page that already ships a real `<table>` gets the benefit of the doubt:
      the author knows the element, so a grid there is more likely deliberate.

Table markup output format:
```
Unmarked table: [rows] rows x [columns] columns of <[tag] class="[class]"> | tabular by eye: [yes/no]
Page uses <table> anywhere: [yes/no]
```

**Section coverage and order**
- [ ] Opening: what the page is and who it serves
- [ ] Evidence appears near the claims it supports
- [ ] Instructions or explanation follow the reader's natural task order
- [ ] Objections or common questions are addressed when they materially help
- [ ] CTA placement matches the page's funnel stage and does not hide the answer

**Internal links**
- [ ] Internal links use descriptive anchor text that names the destination's
      subject (not "click here", "read more", or "learn more")
- [ ] The page links to its pillar or parent and to the two or three most
      useful next pages for this reader; no arbitrary link quota
- [ ] At least one crawlable `<a href>` from another indexable page points here
      (not only the sitemap, a JS click handler, or search)
- [ ] Click depth from the home page recorded; priority pages within three or
      four clicks
- [ ] Links use the canonical URL (no redirect hops, no parameters, consistent
      trailing slash)
- [ ] No internal links are broken (verify with fetch or curl)
- [ ] High-authority pages (most-linked, most-trafficked) pass links to the
      pages the business most needs found
- [ ] External links go to authoritative sources when making factual claims
- [ ] Link behavior is accessible and predictable. Opening a new tab is a UX
      decision, not an SEO requirement; warn users when a new context opens.

**FAQ (only when useful to the reader)**
- [ ] FAQ section is present only when distinct recurring questions warrant it
- [ ] Each FAQ item is a real question a user or searcher would ask
- [ ] Each FAQ answer is self-contained (the answer makes sense without reading
      the question)
- [ ] Each answer is as short as clarity permits and as long as accuracy needs;
      no unsupported universal word limit is applied

**Topic and entity coverage**
- [ ] The title, H1, and opening make the primary subject unambiguous using
      natural language; exact-match repetition is not required
- [ ] Supporting subjects and entities needed for a complete answer are covered
      where they help the reader
- [ ] No term is repeated unnaturally or inserted solely to manipulate ranking
- [ ] Synonyms and related language are used for clarity, not to satisfy a quota

Coverage check output format:
```
Primary subject "[subject]": title [clear/unclear] | H1 [clear/unclear] | opening [clear/unclear]
Supporting subject/entity "[name]": [covered/missing/not needed] | evidence: [section or selector]
Natural-language check: [clear | repetitive | stuffed] | evidence: [quoted text]
```

---

## Lane 6: Answer Extractability (generative search)

Apply the nine-check extractability table owned by `suede-ai-seo` (direct
answer up top, question headings, self-contained passages, quotable facts,
original information, comparison tables, freshness, attribution, text not
pixels). The items below are the audit-specific evidence for those checks.

**Snippet and access controls**
- [ ] No `nosnippet`, `max-snippet:0`, or `data-nosnippet` on the primary
      answer unless the owner intends to keep it out of AI features
- [ ] Primary answer is in server-rendered HTML text, not only an image,
      canvas, PDF, or client-side widget

**Summary and definitions**
- [ ] The opening section contains a clear answer to the page's primary
      question. The answer can stand alone without surrounding context.
- [ ] The product, skill, or service is defined plainly in the first section,
      not assumed
- [ ] No jargon is used without an inline definition on first use
- [ ] Definitions are written as `[Term] is [concise definition].` not buried in
      nested clauses

**Contrast and comparison**
- [ ] Where the subject has named alternatives, a competing approach, or a
      do-nothing option, the page states at least one difference in its own
      words. Buyers ask comparative questions, and an explicit "unlike X, this
      does Y" sentence gives an answer engine a quotable difference instead of
      leaving it to infer one. Quote the sentence as evidence; the presence of
      the word "unlike" is not the check.
- [ ] Comparative framing the page already promises is delivered in the body. A
      title, H1, or URL containing "vs", "alternative to", "best ... for", or
      "without ..." commits the page to naming the other option and the
      difference. This is the most common way the gap survives an audit: the
      framing sits in the metadata and nowhere in the prose.
- [ ] Segment framing ("best for {segment}") and constraint framing ("without
      {constraint}") appear where the page genuinely serves a narrower reader
      than its category does. Do not add a segment the product does not serve
      or a constraint it does not remove.
- [ ] A page whose subject has no alternatives and no competitors passes with no
      contrast content at all. Mark it N/A and name why in one line. No
      comparison quota is applied, and a page does not improve by acquiring a
      rival it does not compete with.

Contrast check output format:
```
Alternatives in scope: [named list | none: reason]
Contrast statement: [quoted sentence | absent] | location: [section or selector]
Comparison promised by title/H1/URL: [quoted phrase | none] | delivered: [yes/no]
Segment or constraint framing: [quoted | not applicable]
```

**Answer and source quality**
- [ ] Answers use the format that best serves the content: prose, steps, table,
      or list. Do not claim one format receives automatic citation preference.
- [ ] Ambiguous pronouns do not obscure the subject
- [ ] Material factual claims link to a current primary or authoritative source

**Entity signals**
- [ ] Company/product identity is explicit and consistent in the places where
      readers and parsers need it; schema is included only when warranted
- [ ] Organization and Person JSON-LD reuse one stable `@id` per entity across
      the site; bylines link to an author page. Off-site consistency (social,
      directories, knowledge bases) is a `suede-ai-seo` entity sweep, not part
      of this lane.
- [ ] Any `sameAs` links identify the same entity and point only to verified
      external profiles. Omit the property when no verified profile exists.
- [ ] URL is stable and descriptive where practical; an opaque legacy URL is
      not treated as a ranking failure by itself

**Accessible content and optional machine-readable files**
- [ ] Record `llms.txt` or another AI-specific file only when a named consumer
      documents support. State explicitly that Google Search ignores
      `llms.txt`, so it neither helps nor harms Google visibility.
- [ ] Primary content is present in the tested rendered output. Record raw-HTML
      dependence as a cross-client/latency risk, not an automatic Google block.
- [ ] Any paywall or auth gate is documented so the audit does not claim that
      inaccessible content was evaluated
- [ ] Headings identify their subject clearly for readers and assistive
      technology; no unverified citation advantage is claimed

**Hallucination risk**
- [ ] Page does not make vague claims an LLM could cite incorrectly (e.g.,
      "used by thousands" without evidence. State the real proof or remove it.)
- [ ] No stat, partner name, or pricing claim is present without a verification
      source

---

## Lane 7: Copy and Conversion Quality

**Directness**
- [ ] First sentence names the outcome, not the feature (outcome: "Register a
      music release with rights and provenance"; feature: "A platform for music
      metadata")
- [ ] No throat-clearing openers ("Welcome to", "In today's digital landscape")
- [ ] Active voice with a named actor in each key sentence
- [ ] Subhead adds proof, audience, or workflow, not a restatement of the hero

**Proof**
- [ ] At least one real artifact: link, command, screenshot reference, file
      name, live URL, or example
- [ ] No invented stats, testimonials, partner names, pricing, or availability
      claims
- [ ] Proof appears before the CTA, not after

**Claims**
- [ ] Every superlative ("only", "best", "first") is either verifiable or
      removed
- [ ] Legal, payment, privacy, or regulatory claims are accurate and sourced
- [ ] Product capabilities described match what is currently shipped and live

**CTA**
- [ ] The primary action is discoverable at the point the target reader is
      ready for it; no fixed fold placement is assumed
- [ ] CTA text is an action + object ("Install the skill", not "Get started")
- [ ] CTA hierarchy is understandable in rendered desktop/mobile tests; do not
      impose a universal count without observing task confusion

**Trust**
- [ ] If testimonials are present, they are real and attributable
- [ ] If testimonials are absent, copy does not imply them
- [ ] Brand vocabulary matches the actual product (no generic AI-music-app
      language when the product does rights infrastructure)

**Filler removal**: the test: if a sentence can be deleted without the reader
losing information, delete it. Apply to transitions, throat-clearing, hedging,
adverb softeners, and exclamation marks.

Flag and remove:
- [ ] Filler transitions ("Additionally", "Furthermore", "It is worth noting")
- [ ] Exclamation points in body copy
- [ ] Em dashes in public copy (use a comma, period, or recast the sentence)
- [ ] Adverb softeners ("simply", "just", "easily", "seamlessly")

---

## Lane 8: E-E-A-T Signals

Use E-E-A-T as a human quality and trust lens. Google describes E-E-A-T as a
concept used by search quality raters, not a standalone score exposed by its
ranking systems. Do not translate this checklist into a ranking promise.

**Experience**: Does the page show first-hand, real-world use of the product or
topic? Look for: demos, screenshots of real output, case studies with specific
results, personal or company proof.

**Expertise**: Does the content demonstrate deep, accurate knowledge? Look for:
technical depth, correct use of domain vocabulary, specific examples over
generic claims, citations to primary sources.

**Authoritativeness**: Is this site or page recognized as a source in the
space? Look for: backlinks from authoritative sites (note if checkable),
mentions in industry press, author credentials visible, organization About page.

**Trustworthiness**: Can users trust this content and site? Look for: HTTPS,
privacy policy, clear contact and company info, accurate and verifiable claims,
no misleading UI patterns, consistent authorship.

Checklist:

- [ ] First-person or company-specific proof present (E: Experience)
- [ ] Accurate technical claims with no puffery (E: Expertise)
- [ ] Author name and credentials visible when relevant (A: Authoritativeness)
- [ ] Privacy policy, contact page, and HTTPS present (T: Trustworthiness)
- [ ] No misleading UI patterns or dark patterns (T: Trustworthiness)
- [ ] Claims are verifiable and sourced (T: Trustworthiness)

---

## Lane 9: Topic Clusters and Site Architecture

Skip for single-page audits. Also mark N/A when the site's user journeys do not
benefit from a pillar/cluster model; a site is not required to adopt this
content architecture.

**Link graph method.** Crawl from the home page (a crawler, the sitemap plus
fetched pages, or the CMS link table). For each URL record inlinks, outlinks,
and click depth. From that table:

- Orphans: indexable URLs with zero internal inlinks.
- Deep pages: priority URLs more than four clicks from home.
- Hoarders: high-inlink pages that link nowhere useful.
- Redirected or broken internal links: list source and target.
- Search Console cross-check: pages with impressions but few inlinks are the
  cheapest wins; add links from relevant high-inlink pages.

**Pillar page**: one comprehensive page that owns the site's core topic and
routes readers to deeper supporting material. Do not promise that it will rank
for a broad query.

**Cluster pages**: specific, narrow pages that support the pillar by covering
sub-topics in depth. Each links back to the pillar.

When a cluster strategy is warranted, ask:

1. Does a clear pillar page exist for the site's primary topic?
2. Do cluster pages exist for each major sub-topic?
3. Does each cluster page link to the pillar?
4. Does the pillar page link to each cluster?
5. Are there orphan pages (no internal links in or out)?
6. Are there keyword cannibalization risks (two pages competing for the same
   query)?

Output a simple map:

```
Pillar: [page]: [target keyword]
  Cluster: [page]: [sub-topic keyword]
  Cluster: [page]: [sub-topic keyword]
Orphan pages: [list or "none found"]
Pages deeper than 4 clicks: [list or "none found"]
Cannibalization risks: [list or "none found"]
Links to add: [anchor] from [source URL] -> [target URL]
```
