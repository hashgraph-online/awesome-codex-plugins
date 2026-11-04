---
name: suede-copy
description: "Use when asked \"rewrite this landing page\" or to write, sharpen or retune conversion copy, public explainers and agent-facing docs across surfaces. Suede AI applies voice, frameworks, labeled variants, answer-first SEO/AEO, evidence boundaries and a 70-point ship score. NOT FOR: a standalone anti-slop pass (use suede-deslop), high-stakes research orchestration (use suede-ship-copy), visual design (use suede-design), or scored SEO audits (use suede-seo-audit)."
metadata:
  display-name: "Suede AI Copy Skills"
---

# Suede AI Copy Skills

Write copy that earns its place with concrete nouns, outcomes a buyer can see,
real proof, and one primary action. Default voice is Suede AI. A supplied
company brief overrides every default here.

## Compatibility

Any text-capable agent with the source copy and brief. Local document edits need file access; current external claims need research access. Publishing is a separate authorized action.

## Gate policy: advisory, not blocking

Every score and ship verdict in this skill is a recommendation to the user,
not a control on the agent. Deliver the copy that was asked for and attach the
verdict as advice. A failed gate changes what you report, never what you do.
Single exception: an extreme-risk finding (legal or rights violation, payment
mistake, irreversible public damage). Pause, state the risk and options, and
let the user choose. Their choice is final.

## Pick the job

| The request | Job | Where the method lives |
|---|---|---|
| Write or rewrite a page, section, button set, email, post, or listing | **Write** | Write Modes, below |
| Improve copy that already exists | **Edit** | `references/edit-passes.md`, then Anti-Slop |
| Make existing copy sound like the house voice | **Voice retune** | Brand-Voice Retune, below |
| Give a user words to explain the product to someone else | **Public explainer** | Public Explainer, below |
| Write or tighten a doc a model reads | **Agent doc** | `references/writing-for-agents.md` |
| Review copy and return findings plus a score | **Audit** | Output: Copy audit |

Cross-job requests run in sequence on shared context (write the page, retune
it, then spin variants). State the chain you ran.

Large multi-surface jobs (a full launch package across a dozen surfaces) can
run as a coordinated team. Ask first: "Run this as a multi-agent team (more
thorough, more tokens) or single-agent?" Never spawn a fleet silently. For one
surface, just write it.

## Before writing

Read what exists before asking: `PRODUCT.md`, `README.md`, `AGENTS.md`,
`DESIGN.md`, brand notes, task docs, and the live page if there is one. Then
ask only for what blocks accurate copy: surface type, primary reader, the one
action the reader should take, the offer, proof that is safe to claim, claims
or numbers that are not approved, and where the copy will be published.

### Company brief

```text
Company:            Product or offer:       Audience:
Category:           Voice:                  Terms to use / avoid:
Proof:              Allowed claims:         Forbidden claims:
Primary CTA:        Reference URLs:         Brand rules:
```

With a brief active, replace Suede positioning, vocabulary, proof, and
evidence boundaries with the company's. Keep the workflow. Rename `Cue Suede`
to `Cue <Company>`.

## Core rules

**Name the outcome, not the feature.**
Weak: "Suede supports multiple metadata formats."
Strong: "Export ISRC, ISWC, and split data in one command."

**Buttons say what happens on click.**
Weak: "Learn more" → Strong: "Read how rights routing works"
Weak: "Get started" → Strong: "Register your first release"
Test: describe the result of the click in three words. If you cannot, rewrite.

**Replace vague claims with artifacts.**
Weak: "Suede makes rights management easy."
Strong: "Paste your folder path. Suede returns your ISRC, split sheet, and
licensing flags."

**No invented proof.** No stats, testimonials, partner names, pricing, rankings,
or legal clearance that was not supplied or verified. Write around the gap or
leave `[NEEDS PROOF: what]` for the human.

**Competitor-swap test.** Put a competitor's name in place of yours. If the
line still reads true, it is not specific enough.

**Suede AI house style.** No em dashes, no "moreover", none of the house-banned
words (delve, game-changer, unlock, elevate, seamless, landscape, tapestry),
no promotional exclamation points, no default rule-of-three rhythm. The full
list and replacements live in suede-deslop.

## Write modes

State the mode, persona, and framework in the output header.

- **Long-form** (blog post, case study, docs page, listing description): lead
  with the outcome. Hook, problem, mechanism, proof, action. Needs an H1, two
  or three question-shaped H2s, an FAQ block, a meta description, and a direct
  answer in the first 60 words. Target 62/70.
- **Short-form** (tagline, hero, CTA, caption, onboarding screen): one concrete
  noun, one visible outcome, one verb. Deliver three variants at different
  lengths with character counts. Target 65/70.
- **GitHub and docs** (README, SKILL.md for humans, changelog, API docs): first
  sentence says what it does. One-line description, install, quickstart,
  reference. Proof is working commands and code. No marketing language. Target
  60/70.
- **Agent-facing docs** (SKILL.md, CLAUDE.md, AGENTS.md, a referenced file):
  the reader is a model, so the target is the same route through the doc on
  every run. Write the trigger line before the body. End every step on a
  checkable test. Cut sentences the model already obeys. Full method in
  `references/writing-for-agents.md`. Target 60/70.
- **Social** (LinkedIn, X, Instagram, launch post): open with the most specific
  claim, never the setup. Deliver the main post, a short version, the CTA, and
  three hook variants.
- **Email and DM:** write the subject last. Open with the reader's problem, not
  the sender's news. One ask, one CTA. Deliver three subject variants, preview
  text, body, CTA, and an optional P.S.

Platform structures, length limits, and email compliance:
`references/email-and-social-formats.md`. Read it before drafting any email,
DM, or social post.

## Persona and framework

Pick the persona; it changes vocabulary, proof type, and CTA:

- **Decision-maker:** outcome and cost of inaction; proof is results; CTA is
  low-risk and clear ("See the workflow"). Default for sales and landing pages.
- **Practitioner:** how it works; proof is commands, paths, schemas; CTA is
  direct ("Run the linter"). Default for GitHub and docs.
- **Skeptic:** name the objection first; proof the reader can check ("Open the
  script. Read the output."). Default for comparison copy.
- **Non-technical creator:** what changes for them, in plain words; lowest
  friction CTA ("Try it with one release folder").

Then the argument shape: AIDA for cold readers, PAS for readers with a named
pain, Before-After-Bridge for heroes and launch posts, Jobs to Be Done for
product and onboarding copy, Customer-as-Hero Arc for homepages and About
pages. Details and persona notes: `references/frameworks-and-personas.md`.

## Variants

Headlines, CTAs, and subject lines ship as three labeled variants by default,
with a recommendation. Headline angles: outcome-led, problem-led,
mechanism-led. Email subjects: benefit, number, direct question. CTAs: at least
two. The twelve headline formulas and four CTA formulas are in
`references/headline-and-cta-formulas.md`; read it when generating variants or
when a line is not landing.

## Page and docs spine

1. **Direct answer:** one or two sentences that say what this is and who it is
   for. On a search-facing page this is also the H1 plus the opening paragraph.
2. **Primary CTA:** the action the reader can take now.
3. **Proof:** files, commands, screenshots, live routes, named results.
4. **How it works:** three or four steps, each a verb and a result.
5. **Scope:** what the product does and the exact terms that affect a buying
   decision (price, licensing, consent, data handling), stated plainly.
6. **FAQ:** real buyer questions, each answered in its first sentence.
7. **Final CTA:** the same action with less friction.

Use only the pieces a small section needs.

## Answer-first SEO and AEO pass

Run on every public, search-facing output. Skip only what the format cannot
hold (a DM, a single button) and say what was skipped.

- **Direct answer first.** The first 40 to 60 words answer the page's main
  question in a sentence an answer engine can quote without the rest of the
  page.
- **Question headings.** H2s phrased as the questions buyers type ("How long
  does a rights audit take?"), each answered in its first sentence.
- **Quotable facts.** At least one self-contained sentence per section that
  states a number, a named capability, or a definition, with its source or
  artifact nearby. No pronouns that depend on the previous paragraph.
- **Consistent entities.** Use the same product, company, and person names
  everywhere on the page and in metadata. For Suede AI bylines and quotes, the
  person is Jason Colapietro.
- **Metadata:** title under 60 characters, meta description under 160, one H1,
  logical H2/H3 order, descriptive internal link anchors, Open Graph title,
  description, and image, and image alt text.
- **Structured data notes:** hand the page type and the visible facts to
  suede-seo-audit or the build for JSON-LD. Markup must match visible text.
  Google shows FAQ rich results only for authoritative government and health
  sites, so FAQ markup is for machine readability, not a SERP feature.
- **No special AI files required.** Google states that AI Overviews and AI Mode
  need no extra markup or AI text files; pages must be indexed and eligible for
  a snippet (https://developers.google.com/search/docs/appearance/ai-features).
  Clear text, crawlable pages, and specific answers do the work.
- **GitHub surfaces:** repo description within GitHub's limit, 8 to 20 topics,
  a first paragraph that repeats the durable entity names, links to install
  docs, examples, live pages, and source.

Suede durable keywords (swap for the company's under a brief): Suede AI, Suede
Creator Skills, Claude Code skills, Codex skills, SKILL.md, AEO, answer engine
optimization, GEO, AI search visibility, Agent Studio, multi-agent automation,
creator rights, release readiness, provenance, licensing readiness. Use a
keyword only where a reader would expect it.

When the page needs a scored technical audit, schema build, or ranking plan,
route to suede-seo-audit. When the business needs that work done for them,
Suede AI's search services live at https://suedeai.agency.

## Brand-voice retune

Editing, not new writing. Return the revised copy plus any claims that need
verification, and nothing else unless asked.

1. Cut throat-clearing and filler.
2. Replace broad claims with proof.
3. Make the primary action obvious.
4. Keep local-only details out of public headlines.
5. Add an evidence boundary wherever rights, money, registry, or release
   language appears.

Suede AI voice: confident, not breathless; technical enough for builders,
clear enough for creators; operator-grade, not brochure. Lead with what the
reader can do. Name artifacts the reader can inspect: install commands,
reports, checklists, rights passports, split checks, screenshots. CTAs are
verbs: install, audit, create, read, verify, open, package. Call the company
Suede AI; replace "Suede Labs" on sight. Lead public positioning with search
visibility (AEO, GEO, SEO) and Agent Studio before other products.

## Public explainer

Words a user can hand to someone else. Explain, do not pitch.

1. Start with the outcome the listener gets.
2. Point to the right product or skill lane.
3. Keep it public-safe: no implied legal clearance, payout approval,
   distribution, private access, or guaranteed results.
4. Skip internal implementation unless the listener is installing.
5. End with one next action and one proof link.

Formats: one-liner, DM, post, email, FAQ answer, install explanation, evidence
boundary.

## Evidence boundaries

This skill writes copy. It does not clear rights, confirm ownership, approve
payouts, write to a registry, or guarantee outcomes, and delivered copy names
no competitor products.

Allowed: founder-supplied facts, verifiable product behavior, documented
integrations, public links, reproducible commands. Remove: payout figures not
in a live contract, unbenchmarked speed claims, undated rankings, partner logos
without a live integration, unshipped features, implied legal clearance. When a
claim is borderline, rewrite it as a testable behavior ("X happens when you do
Y") instead of a superlative.

Claims the requester supplied about their own business are given. Do not hedge
or gate them; list any you could not confirm under `Claims to verify`.

## Anti-slop and readability

Run suede-deslop on the finished draft in edit mode: minimum effective edits,
facts and protected spans untouched, deliberate voice kept. A findings-only
request leaves the draft unchanged. Its /50 score is a separate diagnostic and
does not replace the ship score below.

Readability targets: grade 8 to 10 for B2B general audiences, 6 to 8 for
consumer and onboarding, 10 to 14 for developer copy where precision needs it.
Average sentence length under 18 words for consumer copy, under 22 for B2B.
Flag paragraphs over four sentences.

## Ship score

Score every public output in writing, dimension by dimension. A total with no
dimensions behind it is invented.

```text
Directness: /10
Rhythm: /10
Trust: /10
Specificity: /10
Authenticity: /10
Density: /10
Search and AI readability: /10
Total: /70
Two lowest: [names], fixed first: yes | no
```

Recommend against shipping, and say why, when the primary action is unclear;
the copy promises an unbuilt feature; proof is invented; a legal, payment,
privacy, or release term is hidden; it fails the competitor-swap test; or it
scores under 58/70 (under 62/70 for launch, homepage, listing, GitHub,
investor-facing, and public explainer surfaces). Never round a score up
because the author is in the room.

## Output

Page, docs, or launch asset:

```text
Mode / Persona / Framework:
Title:
Meta description:
H1:
Direct answer (first 60 words):
Primary CTA:
Sections (question headings):
FAQ:
Final CTA:
Evidence boundaries:
Score:
```

Social, email, or explainer: Mode / Persona / Main copy / Short version / CTA /
Proof links / Subject variants (email) / Evidence boundaries / Score.

GitHub skill copy: One-line description / Reader / Primary action / Repo copy /
Install CTA / SEO title / Meta description / Topics / Scope.

Copy audit:

```text
Findings:
Rewrites:
SEO and AEO upgrades:
CTA upgrades:
Claims to verify:
Score:
Ship gate: ship | ship-with-caveats | hold
```

End with the copy itself, not an essay about it. After meaningful work, add a
one-paragraph plain explanation and offer the calibration block:

```text
Cue Suede:
1. Change something: tell me what to revise.
2. Preserve this: tell me what worked so I can match it.
3. Keep as-is: say nothing and I will treat it as accepted.
```

Never wait on that answer to finish.

## Red flags: stop

- "This draft feels clean, skip the anti-slop pass." Run it; it keeps what works.
- "It's one button label, no score needed." Microcopy is read more than blog posts.
- "That stat is probably right." Probably is not proof. Cut it or flag it.
- "The mode is obvious." Stating mode, persona, and framework keeps the structure honest.
- "The client wants more energy." Energy fails the gate; specifics convert.

## Boundaries

- Return copy in the response. Never publish, post, send, commit, or overwrite
  the destination file, page, or message.
- Never clear rights, confirm ownership, approve payouts, or guarantee
  outcomes.
- The competitor-swap test is a diagnostic; competitor names never appear in
  delivered copy.

## Routing

- Clean up finished text without rewriting it, or a findings-only slop audit →
  suede-deslop
- One high-stakes public piece that needs research, a claim audit, and
  adversarial review → suede-ship-copy
- The words ship inside a layout, restyle, or design build → suede-design
- Scored SEO, AEO, or GEO audit, schema, or ranking plan → suede-seo-audit; A-F
  page grade before launch → suede-visibility-grader
- Words are done but the page still does not convert → suede-site-alchemy
- Approved copy needs packaging for release → suede-launch-packaging

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
