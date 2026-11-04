---
name: suede-content-strategy
description: "Use when asked \"plan our content strategy\" or to decide what to publish, refresh or stop. Suede AI maps audience questions, pillars, topic clusters, AI answer gaps and original-data assets to priorities, cadence, distribution and KPIs. NOT FOR: drafting an asset (use suede-copy), SEO audits (use suede-seo-audit), AI visibility measurement (use suede-ai-seo), or social production (use suede-social)."
metadata:
  display-name: "Suede AI Content Strategy Skills"
  version: 2.0.1
---

# Suede AI Content Strategy Skills

Use this Suede content-strategy playbook to plan evidence-backed content that earns search, sharing, trust, or qualified demand.

## Compatibility

Any agent with the product brief and audience evidence. Current search or competitor research needs web access; optional analytics and SEO exports can be supplied as files.

## Before Planning

Read `.agents/product-marketing.md` first if it exists and ask only for what it does not cover; see `suede-product-marketing` for path fallbacks.

Gather this context (ask if not provided):

### 1. Business Context
- What does the company do?
- Who is the ideal customer?
- What's the primary goal for content? (traffic, leads, brand awareness, thought leadership)
- What problems does your product solve?

### 2. Customer Research
- What questions do customers ask before buying?
- What objections come up in sales calls?
- What topics appear repeatedly in support tickets?
- What language do customers use to describe their problems?

### 3. Current State
- Do you have existing content? What's working?
- What resources do you have? (writers, budget, time)
- What content formats can you produce? (written, video, audio)

### 4. Competitors
- Who are your main competitors?
- What content gaps exist in your market?

---

## Searchable vs Shareable

Every piece of content must be searchable, shareable, or both. Searchable is the default first priority because search demand is measurable; treat that as a starting rule, not a universal truth, and reverse it when the user's goal or evidence says otherwise (a category with no search volume, a brand-led launch). Record which order you chose and why: it feeds the weights in "Prioritizing Content Ideas."

**Searchable content** captures existing demand. Optimized for people actively looking for answers.

**Shareable content** creates demand. Spreads ideas and gets people talking.

### When Writing Searchable Content

- Target a specific keyword or question
- Match search intent exactly, answer what the searcher wants
- Use clear titles that match search queries
- Structure with headings that mirror search patterns
- Place keywords in title, headings, first paragraph, URL
- Provide comprehensive coverage (don't leave questions unanswered)
- Include data, examples, and links to authoritative sources
- Write for answer engines and readers at once: answer the question in the opening 40 to 80 words, use question headings that name their subject, state quotable facts with sources, and add one original data point or first-hand observation. The full standard lives in `suede-ai-seo`.

### When Writing Shareable Content

- Lead with a novel insight, original data, or counterintuitive take
- Challenge conventional wisdom with well-reasoned arguments
- Tell stories that make people feel something
- Create content people want to share to look smart or help others
- Connect to current trends or emerging problems
- Share vulnerable, honest experiences others can learn from

---

## Content Types

### Searchable Content Types

**Use-Case Content**
Formula: [persona] + [use-case]. Targets long-tail keywords.
- "Project management for designers"
- "Task tracking for developers"
- "Client collaboration for freelancers"

**Hub and Spoke**
Hub = comprehensive overview. Spokes = related subtopics. Create the hub first, then build spokes, and interlink them. See "Content Pillars and Topic Clusters" below for the structure and the URL guidance.

**Template Libraries**
High-intent keywords + product adoption.
- Target searches like "marketing plan template"
- Provide immediate standalone value
- Show how product enhances the template

### Shareable Content Types

**Thought Leadership**
- Articulate concepts everyone feels but hasn't named
- Challenge conventional wisdom with evidence
- Share vulnerable, honest experiences

**Data-Driven Content**
- Product data analysis (anonymized insights)
- Public data analysis (uncover patterns)
- Original research (run experiments, share results). Original data is the asset answer engines and journalists most need to cite, so give each finding a stable URL, method, sample, and date.

**Expert Roundups**
A selected set of relevant, verified experts answering one specific question.
Distribution depends on contributor permission and actual promotion.

**Case Studies**
Structure: Challenge → Solution → Results → Key learnings

**Meta Content**
Behind-the-scenes transparency. "How We Got Our First $5k MRR," "Why We Chose Debt Over VC."

For programmatic content at scale, route the data and template system to
`suede-programmatic-seo`.

---

## Content Pillars and Topic Clusters

Content pillars are the 3-5 core topics your brand will own; each pillar spawns a cluster of related content. Most of the time all of it can live under `/blog` with good internal linking. Dedicated pillar pages with custom URL structures (like `/guides/topic`) are only needed for comprehensive resources with multiple layers of depth.

### How to Identify Pillars

1. **Product-led**: What problems does your product solve?
2. **Audience-led**: What does your ICP need to learn?
3. **Search-led**: What topics have volume in your space?
4. **Competitor-led**: What are competitors ranking for?

Structure is pillar (hub) → subtopic clusters → articles, each article linking to its siblings and up to the hub. The Topic cluster map in Output Format is the shape to emit.

### Pillar Criteria

Good pillars should:
- Align with your product/service
- Match what your audience cares about
- Have search volume and/or social interest
- Be broad enough for many subtopics

---

## Keyword Research by Buyer Stage

Map topics to the buyer's journey using the modifier set for each stage:

| Stage | Modifiers | Triggered by |
|---|---|---|
| **Awareness** | "what is," "how to," "guide to," "introduction to" | Customers asking basics |
| **Consideration** | "best," "top," "vs," "alternatives," "comparison" | Customers evaluating multiple tools |
| **Decision** | "pricing," "reviews," "demo," "trial," "buy" | Pricing coming up in sales calls |
| **Implementation** | "templates," "examples," "tutorial," "how to use," "setup" | Support tickets showing setup struggles |

Worked example, Consideration stage for a project-management tool: "Best Project Management Tools for Remote Teams," "Asana vs Trello vs Monday," "Basecamp Alternatives." Apply the same pattern per stage using the user's own category nouns, never these ones.

---

## Content Ideation Sources

### Research Surface Check

Before external research, inspect the tools and connected sources that are
currently callable and authorized in this session. Use product analytics, Search
Console or keyword exports, customer material, support data, approved Drive
sources, or a callable browser/search surface only when access actually exists.
Record each source URL or file, owner, retrieval date, and relevant scope.

If no external research surface is available, continue with user-supplied URLs,
exports, transcripts, and known first-party evidence. Otherwise return a compact
manual-research list with exact queries and fields to capture. Label hypotheses
and unverified competitor observations; never imply that a search was run.

### 1. Keyword Data

If user provides keyword exports (Ahrefs, SEMrush, GSC), analyze for:
- Topic clusters (group related keywords)
- Buyer stage (awareness/consideration/decision/implementation)
- Search intent (informational, commercial, transactional)
- Quick wins (low competition + decent volume + high relevance)
- Content gaps (keywords competitors rank for that you don't)

Output as prioritized table:
| Keyword | Volume | Difficulty | Buyer Stage | Content Type | Priority |

### 2. Call Transcripts

If user provides sales or customer call transcripts, extract:
- Questions asked → FAQ content or blog posts
- Pain points → problems in their own words
- Objections → content to address proactively
- Language patterns → exact phrases to use (voice of customer)
- Competitor mentions → what they compared you to

Output content ideas with supporting quotes.

### 3. Survey Responses

If user provides survey data, mine for:
- Open-ended responses (topics and language)
- Common themes, with sample count and observed proportion recorded
- Resource requests (what they wish existed)
- Content preferences (formats they want)

### 4. Forum Research

If an authorized browser or search surface is currently callable, use it to find
recent first-party community evidence. Otherwise ask for relevant URLs or provide
the queries below for manual collection.

**Reddit:** `site:reddit.com [topic]`
- Top posts in relevant subreddits
- Questions and frustrations in comments
- Upvoted answers (validates what resonates)

**Quora:** `site:quora.com [topic]`
- Most-followed questions
- Highly upvoted answers

**Other:** Indie Hackers, Hacker News, Product Hunt, industry Slack/Discord

For each item, capture the source URL, publication date, retrieval date, community
context, and a short evidence excerpt. Distinguish engagement signals from proof
of customer demand.

### 5. Competitor Analysis

Use a currently callable, authorized browser/search surface or user-supplied
competitor URLs. If neither is available, produce a manual research checklist and
do not invent page inventories, rankings, engagement, or gaps.

**Find their content:** `site:competitor.com/blog`

**Analyze:**
- Observable posts and dated engagement signals
- Topics covered repeatedly
- Gaps they haven't covered
- Case studies (customer problems, use cases, results)
- Content structure (pillars, categories, formats)

**Identify hypotheses to validate:**
- Topics you can cover better
- Angles they're missing
- Outdated content to improve on, based on a visible date or stale claim

### 6. AI Answer Gaps

If `suede-ai-seo` has run a prompt panel, its results are a ranked topic list:
prompts where competitors are cited and you are not, prompts where the answer
gets a fact about you wrong, and third-party sources engines rely on. Each
becomes a topic (answer the question better on a page you own) or an off-site
task (earn a mention on the source engines already cite). Bing Webmaster
Tools grounding queries and Search Console queries with impressions but low
clicks serve the same purpose.

### 7. Sales and Support Input

Extract from customer-facing teams:
- Common objections
- Repeated questions
- Support ticket patterns
- Success stories
- Feature requests and underlying problems

---

## Prioritizing Content Ideas

Score each idea on four factors. The weights below are an illustrative starting
point, not a universal truth; change them to match the user's business goal and
record the chosen decision rule.

### 1. Customer Impact (40%)
- How frequently did this topic come up in research?
- What percentage of customers face this challenge?
- How emotionally charged was this pain point?
- What's the potential LTV of customers with this need?

### 2. Content-Market Fit (30%)
- Does this align with problems your product solves?
- Can you offer unique insights from customer research?
- Do you have customer stories to support this?
- Will this naturally lead to product interest?

### 3. Search Potential (20%)
- What's the monthly search volume?
- How competitive is this topic?
- Are there related long-tail opportunities?
- Is search interest growing or declining?

### 4. Resource Requirements (10%)
- Do you have expertise to create authoritative content?
- What additional research is needed?
- What assets (graphics, data, examples) will you need?

### Scoring Template

| Idea | Customer Impact (40%) | Content-Market Fit (30%) | Search Potential (20%) | Resources (10%) | Total |
|------|----------------------|-------------------------|----------------------|-----------------|-------|
| Topic A | 8 | 9 | 7 | 6 | 7.9 |
| Topic B | 6 | 7 | 9 | 8 | 7.1 |

---

## Refreshes and Stop-Doing Decisions

A portfolio compounds only if something leaves it. Every strategy must name what stops, not just what starts. Audit existing assets against dated evidence, traffic, conversions, rankings, and last-updated date, and assign each one of four outcomes:

| Outcome | When | What it means |
|---|---|---|
| **Keep** | Still ranking or converting against its goal, and the claims are current | No action; next audit at the normal cadence |
| **Refresh** | The topic still matters and the URL still has authority, but the piece has decayed: stale data, dated claims, or a slipping position | Rewrite in place, keep the URL, record the new last-updated date |
| **Consolidate** | Two or more pieces target the same intent and split their own signal | Merge into the strongest URL, redirect the others, fold the unique sections in |
| **Kill** | The topic no longer serves a pillar, or two consecutive review windows show no traffic, no conversions, and no strategic use | Propose removal or de-indexing, and stop there, because Boundaries forbids executing it |

Decision rule, in order: duplicated intent → Consolidate; else topic still maps to a live pillar → Refresh; else → Kill. Never refresh a piece whose pillar was retired: that is sunk cost wearing an editorial hat. Every row names the evidence that triggered it (metric, window, source) and the accountable owner; recommending is the whole job, since publishing, deleting, redirecting, and de-indexing all need explicit authorization.

Hand the recurring cadence that keeps this audit running, decay watch, ranking-drop watch, refresh queue, to `suede-marketing-loops`. This skill decides what gets refreshed or killed; that one decides how often the check runs.

---

## Reject these defaults

The generic content strategy writes itself, which is exactly the problem. Do not ship:

- **Pillars that are category nouns**: "Productivity," "Marketing," "Growth." A pillar is a claim the brand can own, in the customer's words.
- **A cluster map that is the pillar list re-indented.** If every spoke is the pillar name plus a modifier, no clustering happened.
- **"The Ultimate Guide to X," "Everything You Need to Know About X," "X 101"**: titles that could sit on any competitor's blog.
- **"10 Best Tools for Y" with the user's product at #1.** That is not a comparison.
- **A cadence with no owner.** "Publish 2x/week" with nobody named is a wish.
- **Topics sourced from the model's general knowledge** rather than the research surfaces above. If none was callable, say so and label the ideas hypotheses.

---

## Output Format

Emit the strategy in exactly this shape:

```
## Content pillars
| Pillar | The claim it owns | Evidence it matters to the ICP | Product connection |
|---|---|---|---|
| [pillar] | [one sentence] | [source + date] | [what it sells] |

## Priority topics
### [Topic title]
- **Type:** searchable / shareable / both: [use-case, hub-and-spoke, thought
  leadership, data-driven, case study, meta]
- **Target query + buyer stage:** [query]: [awareness / consideration /
  decision / implementation]
- **Why this topic:** [the customer-research evidence, with its source and date]
- **Score and owner:** [Impact / Fit / Search / Resources] = [total]; [owner,
  rough effort]
- **KPI:** [the metric this piece should move, e.g. impressions and clicks
  for the query family, AI citation share for the matching prompt cluster,
  assisted conversions] with its source and re-check date

## Topic cluster map
[Pillar]
├── [Cluster]
│   ├── [Article] → links to [Article]
│   └── [Article]
└── [Cluster]
    └── [Article]

## Stop-doing
| Existing asset | Outcome | Evidence | Owner |
|---|---|---|---|
| [URL] | Keep / Refresh / Consolidate / Kill | [metric, window, source] | [who] |

## Open questions
[What could not be evidenced, and what would settle it]
```

---

## Task-Specific Questions

1. What patterns emerge from your last 10 customer conversations?
2. What questions keep coming up in sales calls?
3. Where are competitors' content efforts falling short?
4. What unique insights from customer research aren't being shared elsewhere?
5. Which existing content drives the most conversions, and why?

---

## References

- **[Headless CMS Guide](references/headless-cms.md)**: CMS selection, content modeling for marketing, editorial workflows, platform comparison (Sanity, Contentful, Strapi)

---

## Boundaries

- Do not claim demand, authority, rank potential, or audience fit without naming the current evidence and decision criterion.
- Do not publish, delete, redirect, deindex, or change an editorial calendar or CMS without explicit authorization.
- Do not invent expertise, customer proof, keyword data, or citations to fill a content gap.
- Do not decide legal, rights, or brand-claim questions; flag them for the accountable owner before publication.

## Routing

- Need an individual asset written -> use `suede-copy`.
- Need technical or on-page organic diagnosis -> use `suede-seo-audit`.
- Need scaled page systems -> use `suede-programmatic-seo`.
- Need email or social production -> use `suede-emails` or `suede-social`.
- Need the pipeline staffed as roles with contracts, a handoff record, and one distinct argument per distributed asset -> use `suede-newsroom`. A weekly founder interview or voice note that feeds separate founder and company account lanes uses that skill's founder-led mode.
- Need the refresh, decay, or ranking-drop audit to run on a cadence -> use `suede-marketing-loops`.
- Need the behavioral mechanism behind a title, hook, or CTA, stated as a testable hypothesis -> use `suede-offers` (Persuasion Mechanics).
- From those skills, route portfolio priorities, pillars, clusters, and cadence back to `suede-content-strategy`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
