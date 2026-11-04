---
name: suede-product-marketing
description: "Suede AI Product Marketing Skills: versioned audience, ICP, positioning, alternatives, objections, verbatim customer language, proof, goals, and entity facts. Use when asked \"create our product marketing context\" or to update .agents/product-marketing.md from supplied records or a codebase. NOT FOR: campaign writing (suede-campaign-in-a-box), new interviews (suede-customer-research), contested positioning (suede-marketing-council), or publishing claims."
metadata:
  display-name: "Suede AI Product Marketing Skills"
  version: 2.2.0
---

# Suede AI Product Marketing Skills

## Compatibility

Requires read access to supplied product materials; persistent context needs file write access. Works without a connected marketing stack. New research or publishing requires its own authorized sources/tools.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI Product Marketing maintains the shared evidence layer for audience,
positioning, objections, customer language, and proof. The Suede growth suite
reads this context so each downstream skill starts from the same verified
product story.

The document is stored at `.agents/product-marketing.md`.

## Workflow

### Step 1: Check for Existing Context

First, check if `.agents/product-marketing.md` already exists. Also check `.claude/product-marketing.md` and the legacy filename `product-marketing-context.md` (in either `.agents/` or `.claude/`) for older setups, if found anywhere other than `.agents/product-marketing.md`, offer to move it to the canonical location.

**If it exists:**
- Read it and summarize what's captured: note its current **Document version** and the last few **Changelog** entries so the user sees where the doc stands and what's changed recently
- Ask which sections they want to update
- Only gather info for those sections
- On any substantive save, bump the version and add a changelog entry (see Step 4). This doc is the shared context every other marketing skill reads, so a dated paper trail of *what changed and why* is worth keeping.

**If it doesn't exist, offer two options:**

1. **Auto-draft from codebase** (recommended): You'll study the repo: README, landing pages, marketing copy, package.json, etc., and draft a V1 of the context document. The user then reviews, corrects, and fills gaps. This is faster than starting from scratch.

2. **Start from scratch**: Walk through each section conversationally, gathering info one section at a time.

Most users prefer option 1. After presenting the draft, ask: "What needs correcting? What's missing?"

### Step 2: Gather Information

**If auto-drafting:**
1. Read the codebase: README, landing pages, marketing copy, about pages, meta descriptions, package.json, any existing docs
2. Draft only what the sources actually say. **Every auto-drafted field carries its source** in the form `[src: path/to/file.md]`, the file the claim came from. A field with no source is not drafted: leave it empty and mark it `[unverified]`.
3. Never source a field from inference. If the README implies a differentiator without stating it, if a competitor is guessed from the category, or if a testimonial-shaped sentence in marketing copy has no attributed customer, that field is `[unverified]`, not a draft with a hedge. Differentiation, Competitive Landscape, Proof Points, and Customer Language are where this rule earns its keep; a fabricated entry there propagates to every skill that reads this doc.
4. Present the draft and say plainly how many fields are sourced versus `[unverified]`, then ask what needs correcting or is missing
5. Iterate until the user is satisfied. A field the user confirms in conversation is sourced as `[src: user]`

**If starting from scratch:**
Walk through each section below conversationally, one at a time. Don't dump all questions at once.

For each section:
1. Briefly explain what you're capturing
2. Ask relevant questions
3. Confirm accuracy
4. Move to the next

Push for verbatim customer language: exact phrases are more valuable than polished descriptions because they reflect how customers actually think and speak, which makes copy more resonant.

---

## Sections to Capture

### 1. Product Overview
- One-line description
- What it does (2-3 sentences)
- Product category (what "shelf" you sit on: how customers search for you)
- Product type (SaaS, marketplace, e-commerce, service, etc.)
- Business model and pricing

### 2. Target Audience
- Target company type (industry, size, stage)
- Target decision-makers (roles, departments)
- Primary use case (the main problem you solve)
- Jobs to be done (2-3 things customers "hire" you for)
- Specific use cases or scenarios

### 3. Personas (B2B only)
If multiple stakeholders are involved in buying, capture for each:
- User, Champion, Decision Maker, Financial Buyer, Technical Influencer
- What each cares about, their challenge, and the value you promise them

### 4. Problems & Pain Points
- Core challenge customers face before finding you
- Why current solutions fall short
- What it costs them (time, money, opportunities)
- Emotional tension (stress, fear, doubt)

### 5. Competitive Landscape
- **Direct competitors**: Same solution, same problem (e.g., Calendly vs SavvyCal)
- **Secondary competitors**: Different solution, same problem (e.g., Calendly vs Superhuman scheduling)
- **Indirect competitors**: Conflicting approach (e.g., Calendly vs personal assistant)
- How each falls short for customers

### 6. Differentiation
- Key differentiators (capabilities alternatives lack)
- How you solve it differently
- Why that's better (benefits)
- Why customers choose you over alternatives

### 7. Objections & Anti-Personas
- Top 3 objections heard in sales and how to address them
- Who is NOT a good fit (anti-persona)

### 8. Switching Dynamics
The four switching forces:
- **Push**: What frustrations drive them away from current solution
- **Pull**: What attracts them to you
- **Habit**: What keeps them stuck with current approach
- **Anxiety**: What worries them about switching

### 9. Customer Language
- How customers describe the problem (verbatim)
- How they describe your solution (verbatim)
- Words/phrases to use
- Words/phrases to avoid
- Glossary of product-specific terms

### 10. Brand Voice
- Tone (professional, casual, playful, etc.)
- Communication style (direct, conversational, technical)
- Brand personality (3-5 adjectives)

### 11. Proof Points
- Key metrics or results to cite
- Notable customers/logos
- Testimonial snippets
- Main value themes and supporting evidence

### 12. Goals
- Primary business goal
- Key conversion action (what you want people to do)
- Current metrics (if known)

### 13. Entity and Search Facts
The canonical facts search engines and AI assistants should repeat about the company. Every downstream skill (site copy, schema, press, directories, comparison pages) reuses these exactly, so mentions accrue to one entity instead of several spellings.
- Official company name and product names, exact spelling and capitalization
- One-sentence description (under 30 words) used everywhere
- Founder or spokesperson name and title for bylines and quotes
- Official profile URLs for sameAs (LinkedIn, X, YouTube, GitHub, Crunchbase, app store listings, Wikidata if one exists)
- The 10 to 20 questions buyers ask search engines and AI assistants about the category, in their words
- Which pages currently answer each question, or "none"

---

## Step 3: Create the Document

After gathering information, create `.agents/product-marketing.md` with this structure:

```markdown
# Product Marketing Context

**Document version:** v1
**Last updated:** [date]
**Status:** complete | partial: missing: [required sections still empty]

*Every field ends with its source: `[src: README.md]`, `[src: interview
2026-05-04]`, `[src: user]`, or the marker `[unverified]` if nothing on record
supports it. An unsourced field is empty by definition; do not fill it to make
the document look finished.*

## Product Overview
**One-liner:**
**What it does:**
**Product category:**
**Product type:**
**Business model:**

## Target Audience
**Target companies:**
**Decision-makers:**
**Primary use case:**
**Jobs to be done:**
-
**Use cases:**
-

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| | | | |

## Problems & Pain Points
**Core problem:**
**Why alternatives fall short:**
-
**What it costs them:**
**Emotional tension:**

## Competitive Landscape
**Direct:** [Competitor]: falls short because...
**Secondary:** [Approach]: falls short because...
**Indirect:** [Alternative]: falls short because...

## Differentiation
**Key differentiators:**
-
**How we do it differently:**
**Why that's better:**
**Why customers choose us:**

## Objections
| Objection | Response |
|-----------|----------|
| | |

**Anti-persona:**

## Switching Dynamics
**Push:**
**Pull:**
**Habit:**
**Anxiety:**

## Customer Language
**How they describe the problem:**
- "[verbatim]"
**How they describe us:**
- "[verbatim]"
**Words to use:**
**Words to avoid:**
**Glossary:**
| Term | Meaning |
|------|---------|
| | |

## Brand Voice
**Tone:**
**Style:**
**Personality:**

## Proof Points
**Metrics:**
**Customers:**
**Testimonials:** *(verbatim only: a quote with no attributable source is `[unverified]`, never paraphrased into existence)*
> "[quote]": [who] [src: where this quote was published or collected]
**Value themes:**
| Theme | Proof |
|-------|-------|
| | |

## Goals
**Business goal:**
**Conversion action:**
**Current metrics:**

## Entity and Search Facts
**Official names:**
**One-sentence description:**
**Spokesperson / byline:**
**sameAs profiles:**
-
**Buyer questions (search and AI assistants):**
| Question | Page that answers it |
|----------|---------------------|
| | |

## Changelog
*Newest first. One line per revision: what changed and why.*
- v1 ([date]): Initial context.
```

---

## Step 4: Confirm, Version, and Save

- Show the completed document
- Ask if anything needs adjustment
- **Check the v1 floor before saving.** Six sections must be non-empty and sourced for the document to be trustworthy as shared context: Product Overview, Target Audience, Problems & Pain Points, Differentiation, Customer Language, and Goals. Everything else is optional by product type. If any of the six is empty or entirely `[unverified]`, set `Status: partial` and list exactly which ones on that line. Never save a partial document as `complete`.
- **What a partial document means downstream.** A consuming skill that reads `.agents/product-marketing.md` and finds `Status: partial` must ask the user for the named missing sections before generating anything that depends on them, and must not infer them from the rest of the doc. Say this in the save message so the user knows why they will be asked again.
- **Set the version and changelog**: this is the paper trail for a doc every other skill reads:
  - **New document:** set `Document version: v1` and a single Changelog entry: `- v1 ([today]), Initial context.`
  - **Updating an existing document:** increment the version (v2 → v3 …), update `Last updated` to today, and **prepend a new Changelog entry** at the top of the list (newest first) summarizing *what changed and why* in one line. Never rewrite or reorder past entries.
  - A good entry names the sections touched and the reason, not "updated the doc." Examples:
    - `- v3 (2026-07-16): Repositioned from "email tool" to "deliverability platform"; added RevOps to the ICP.`
    - `- v2 (2026-06-02): Rewrote value prop and objections after 5 customer interviews; added competitor Acme.`
  - Use today's date in ISO form (YYYY-MM-DD) for the entry and `Last updated`.
  - **Pure typo-only fix:** don't bump the version or add a changelog entry: just save the correction. Every other change bumps the version and gets an entry. When the change is a real repositioning, say so plainly, downstream skills will now generate against the new context.
- Save to `.agents/product-marketing.md`
- Tell them: "The Suede growth suite will now use this context automatically.
  The Changelog at the bottom tracks every revision, check it to see how your
  positioning has evolved. Run `/suede-product-marketing` anytime to update it."

---

## Tips

- **Skip what doesn't apply**, outside the six-section v1 floor in Step 4: not every product needs Personas (B2C), Switching Dynamics, or a Glossary. Skipping one of the six is not a skip: it is a `partial` document.

## Boundaries

- Do not overwrite an existing context file without reading it, preserving
  supported facts, and showing the user the material changes.
- Do not invent customer language, differentiation, proof points, market
  position, or durable brand rules; label hypotheses and missing evidence.
- Do not publish external copy or mutate product, CRM, analytics, or campaign
  systems. This skill owns the shared context document only.

## Routing

- Use `suede-customer-research` to gather new customer evidence.
- Use `suede-competitor-profiling` for evidence on named competitors.
- Use `suede-marketing-plan` to turn approved context into a channel plan.
- Use `suede-campaign-in-a-box` to package an approved campaign.
