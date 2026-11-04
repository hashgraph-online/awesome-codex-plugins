---
name: suede-customer-research
description: "Use when asked \"synthesize these interviews\" or to discover what a defined customer segment says, needs and resists. Suede AI analyzes transcripts, surveys, tickets, reviews and forums into traceable VOC quotes, jobs to be done, personas and buyer questions. NOT FOR: competitor-only profiling (use suede-competitor-profiling), final copy (use suede-copy), or unsupported product prioritization (use suede-product-marketing)."
metadata:
  display-name: "Suede AI Customer Research Skills"
  version: 2.1.1
---

# Suede AI Customer Research Skills

Use this customer-research playbook to ground positioning, product, and copy in traceable customer evidence rather than assumption.

## Compatibility

An agent able to read supplied research files and save evidence captures. New public-source research needs web access; existing-asset synthesis requires no paid research tool.

## Before Starting

Check for `.agents/product-marketing.md` (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and read it if present: the ICP, segment definitions, and what research already exists decide where to look and what counts as a representative sample. Ask only what it does not already answer.

---

## Two Modes of Research

### Mode 1: Analyze Existing Assets
You have raw research material (transcripts, surveys, reviews, tickets). Your job is to extract signal.

### Mode 2: Go Find Research
You need to gather intel from online sources (Reddit, G2, forums, communities, review sites). Your job is to know where to look and what to extract.

Most engagements combine both. Establish which mode applies before proceeding.

---

## Mode 1: Analyzing Existing Research Assets

### Asset Types

**Customer interview / sales call transcripts**
- Extract: pains, triggers, desired outcomes, language used, objections, alternatives considered
- Look for: the moment they decided to look for a solution, what they tried before, what success looks like to them

**Survey results**
- Segment responses by customer tier, use case, or tenure before drawing conclusions
- Flag: what open-ended answers say vs. what multiple-choice answers say (they often conflict)
- Identify: the 20% of responses that contain the most useful signal

**Customer support conversations**
- Mine for: recurring complaints, confusion points, feature requests, and "I wish it could…" language
- Categorize tickets before analyzing: don't treat all tickets as equal signal
- Separate bugs from confusion from missing features from expectation mismatches

**Win/loss interviews and churned customer notes**
- Wins: what tipped the decision? What almost made them choose a competitor?
- Losses and churn: was it price, features, fit, timing, or something else?
- Segment by reason: don't average across different churn causes

**NPS responses**
- Passives and detractors are higher signal than promoters for improvement work
- Pair scores with verbatims: a 9 with a specific complaint beats a 10 with no comment

### Extraction Framework

For each asset, extract:

1. **Jobs to Be Done**: what outcome is the customer trying to achieve?
   - Functional job: the task itself
   - Emotional job: how they want to feel
   - Social job: how they want to be perceived

2. **Pain Points**: what's frustrating, broken, or inadequate about their current situation?
   - Prioritize pains mentioned unprompted and with emotional language

3. **Trigger Events**: what changed that made them seek a solution?
   - Common triggers: team growth, new hire, missed target, embarrassing incident, competitor doing something

4. **Desired Outcomes**: what does success look like in their words?
   - Capture exact quotes, not paraphrases

5. **Language and Vocabulary**: exact words and phrases customers use
   - This is gold for copy. "We were drowning in spreadsheets" > "manual process inefficiency"

6. **Alternatives Considered**: what else did they look at or try?
   - Includes doing nothing, hiring someone, or building internally

### Synthesis Steps

After extracting from individual assets:

1. **Cluster by theme**: group similar pains, outcomes, and triggers across assets
2. **Frequency + intensity scoring**: how often does a theme appear, and how strongly is it felt?
3. **Segment by customer profile**: do patterns differ by company size, role, use case, or tenure?
4. **Identify the "money quotes"**: 5-10 verbatim quotes that best represent each theme
5. **Flag contradictions**: where do customers say one thing but do another?

### Research Quality Guardrails

Label every insight with a confidence level before presenting it:

| Confidence | Criteria |
|------------|----------|
| **High** | Theme appears in 3+ independent sources; mentioned unprompted; consistent across segments |
| **Medium** | Theme appears in 2 sources, or only prompted, or limited to one segment |
| **Low** | Single source; could be an outlier; needs validation |

**Recency window**: Weight sources from the last 12 months more heavily. Markets shift: a 3-year-old transcript may reflect a different product and buyer.

**Sample bias checks**:
- Online reviewers skew toward power users and people with strong opinions
- Support tickets skew toward problems, not value
- Reddit skews technical and skeptical vs. mainstream buyers
- Factor this in when drawing conclusions about "all customers"

**Minimum viable sample**: 5 independent data points per segment (10 is better), drawn from interviews, reviews, tickets, or community posts, before building a persona or drawing a messaging conclusion for that segment. Below 5, present the material as raw signal, not as a finding.

---

## Mode 2: Digital Watering Hole Research

Online communities are where customers speak without a filter. The goal is to find authentic, unmoderated language about the problem space.

### Where to Look

Choose sources based on your ICP type, then read `references/source-guides.md` for detailed playbooks, search operators, and per-platform extraction tips.

| ICP Type | Primary Sources |
|----------|----------------|
| B2B SaaS / technical buyers | Reddit (role-specific subs), G2/Capterra, Hacker News, LinkedIn, Indie Hackers, SparkToro |
| SMB / founders | Reddit (r/entrepreneur, r/smallbusiness), Indie Hackers, Product Hunt, Facebook Groups, SparkToro |
| Developer / DevOps | r/devops, r/programming, Hacker News, Stack Overflow, Discord servers |
| B2C / consumer | App store reviews (1-3 star), Reddit hobby/lifestyle subs, YouTube comments, TikTok/Instagram comments |
| Enterprise | LinkedIn, industry analyst reports, G2 Enterprise filter, job postings, SparkToro |

**Quick decision guide:**
- Have a product category? → Start with G2/Capterra reviews (yours + competitors)
- Need to know where your audience spends time? → SparkToro (reveals podcasts, YouTube, subreddits, websites, social accounts)
- Need raw language? → Reddit and YouTube comments
- Need trigger events? → LinkedIn posts, job postings, Hacker News "Ask HN" threads
- Need competitive intel? → Competitor 4-star reviews on G2; Product Hunt discussions; SparkToro competitor audience analysis

### What to Extract from Each Source

For every piece of content you find:

| Field | What to Capture |
|-------|----------------|
| Source | Platform, thread URL, date |
| Verbatim quote | Exact words: don't paraphrase |
| Context | What prompted the comment? |
| Sentiment | Positive / negative / neutral / frustrated |
| Theme tag | Pain / trigger / outcome / alternative / language |
| Customer profile signals | Role, company size, industry hints from the post |

### Persist Captures Before Synthesizing

Save what you gathered before extracting themes from it: otherwise the
provenance gate below is unenforceable and a re-run repeats the entire
collection. Mirror the raw-evidence convention `suede-competitor-profiling`
uses: one dated folder per run at `customer-research/raw/<YYYY-MM-DD>/`, one
file per source inside it (`reddit.md`, `g2-<competitor>.md`, `app-store.md`),
plus a `captures.csv` whose columns are the capture table above. Create the date
folder fresh each run and never overwrite a prior date's: that is how you diff
what moved in the market. Mode 1 assets (transcripts, tickets, win/loss notes,
NPS verbatims) usually already live somewhere: don't copy them, record each in
`captures.csv` by file path or system identifier plus date and segment, so every
quote resolves to a named record either way.

### Research Synthesis Template

After gathering from multiple sources, synthesize into:

```
## Top Themes (ranked by frequency × intensity)

### Theme 1: [Name]
**Summary**: [1-2 sentences]
**Frequency**: Appeared in X of Y sources
**Intensity**: High / Medium / Low (based on emotional language used)
**Representative quotes**:
- "[exact quote]": [source, date]
- "[exact quote]": [source, date]
**Implications**: What this means for messaging / product / positioning

### Theme 2: ...
```

---

## Persona Generation

### When there are no reviews yet

Early-stage products (or new categories) lack first-party review data. Don't invent personas: walk outward through proxy sources, in order:

1. **Your own differentiator**: what the product does differently defines who feels that difference most; write the hypothesis down as a hypothesis
2. **Direct competitors' reviews**: their customers describe the problem space in their words (note what's praised and what's missing)
3. **Comparable products on marketplaces**: Amazon/app-store reviews for adjacent solutions to the same job
4. **Adjacent brands sharing the audience**: what else this buyer buys; their reviews reveal the buyer's broader language and values

Personas built this way are provisional: tag each with its proxy source, and replace proxy evidence with first-party evidence as real reviews arrive. The minimum viable sample above applies to proxy evidence too.

### Persona Structure

**Read [references/persona-templates.md](references/persona-templates.md) before writing the first persona of a run**: it holds the full fill-in structure (profile, primary job, triggers, pains, desired outcomes, objections, alternatives, vocabulary, how to reach them). Personas written from memory drift field by field and stop being comparable.

### Persona Anti-Patterns

- **Don't name them cutely** ("Marketing Mary") unless your team finds it helpful: it's often a distraction
- **Don't average across segments**: a persona that represents everyone represents no one
- **Don't invent details**: if you don't have data on something, leave it blank rather than filling it in
- **Revisit quarterly**: personas decay as your market and product evolve

---

## Provenance Gate

Run this over the finished deliverable, before it goes out. Boundaries below
forbids fabricated quotes, themes, sample sizes and frequency counts; this is
what makes that checkable rather than aspirational.

- **Every verbatim resolves to a named capture record.** Mode 2: platform, thread URL, and date, per the capture table above. Mode 1: the asset identifier or file, plus date and segment. A quote that cannot be attributed to a capture record is **cut**, never paraphrased into a theme, never rolled into a frequency count.
- **Recount the numbers at the same pass.** "Appeared in X of Y sources" and every High/Medium/Low confidence label are recomputed from the capture records right now, not carried over from a draft. A confidence label that no longer matches the count gets downgraded, not defended.
- **Name the sample.** Source mix, segment, date range, and total captures appear in the deliverable itself, so the reader can judge the base the conclusions sit on.

---

## Deliverable Formats

Default deliverable: a **research synthesis report** (themes, quotes, patterns,
implications) plus a **VOC quote bank** organized by theme. Produce those unless
the user asked for something else.

Offer these instead or in addition when the goal calls for it: a **question
bank for search and AI answers** (the verbatim questions customers asked, in
their words, grouped by theme and buying stage, ready for `suede-content-strategy`
and `suede-ai-seo` to turn into headings, FAQs, and pages), a **persona
document** (1-3 personas), a **jobs-to-be-done map** (functional, emotional,
social jobs by segment), a **competitive intelligence summary** (what customers
say about competitors vs. you), or a **research gap analysis** (what you still
don't know and how to find it).

---

## Questions to Ask Before Proceeding

If context is unclear:

1. **What's the goal?** Improve messaging? Build personas? Find product gaps? Understand churn?
2. **What do you already have?** (transcripts, surveys, tickets, G2 reviews, nothing)
3. **Who is the target segment?** (all customers, a specific tier, churned users, prospects who didn't buy)
4. **What's your product?** (if not in the product marketing context file)

Don't ask all four at once: lead with #1 and #2, then follow up as needed.

---

## Boundaries

- Do not fabricate quotes, themes, sample sizes, sentiment, persona traits, or frequency counts.
- Do not contact participants, record sessions, scrape restricted communities, or expose identifying data without explicit authorization and consent.
- Do not present a convenience sample as representative; state source, segment, dates, sample size, and collection limits.
- Do not decide product priorities or customer truth from synthesis alone; separate evidence, inference, and open questions.

## Routing

- Need final copy from customer language -> use `suede-copy`.
- Need competitor-only evidence -> use `suede-competitor-profiling`.
- Need ICP or positioning synthesis -> use `suede-product-marketing`.
- Need churn, outbound, paid, or content application -> use `suede-churn-prevention`, `suede-cold-email`, `suede-ads`, or `suede-content-strategy`.
- From those skills, route interview design, review mining, and evidence synthesis back to `suede-customer-research`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
