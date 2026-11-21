# Citation-Worthy Content Patterns

Templates for passages answer engines can lift and attribute correctly. They
serve readers first: Google states no special format is needed for its AI
features, so use a pattern only when it is the clearest way to answer the
question on the page.

Every example below uses placeholders. Fill them with verified facts and
sources; never ship a bracket or an invented number.

## Contents

- Answer patterns: definition, direct answer, steps, comparison table,
  pros and cons, FAQ, best-for list
- Proof patterns: sourced statistic, original data, attributed quote,
  evidence sandwich
- Page-type playbooks: product, blog, comparison, docs, local and commerce
- Domain notes: regulated topics

## Answer patterns

### Definition block ("What is X?")

```markdown
## What is [term]?

[Term] is [one-sentence definition naming the category and what it does].
[One or two sentences on how it works or who uses it]. [One sentence on why it
matters, with a sourced fact if you have one].
```

### Direct answer block (any question heading)

```markdown
## How long does [process] take?

[Direct answer with the number or range, conditions, and source]. [Context:
what changes the answer]. [Next step or link to detail].
```

Rules: answer in the first sentence; name the subject instead of "it"; keep
the core answer to roughly 40 to 80 words so it survives being lifted alone.

### Step block ("How to X")

```markdown
## How to [goal]

[One sentence on outcome and prerequisites.]

1. **[Action verb + object]**: [what to do, with the exact setting or value].
2. **[Action verb + object]**: [...].
3. **[Action verb + object]**: [...].

[Expected result and how to confirm it worked.]
```

Use an ordered list, one action per step, real UI labels and values.

### Comparison table ("X vs Y")

```markdown
## [Option A] vs [Option B] for [use case]

| Criterion | [Option A] | [Option B] |
|---|---|---|
| Price (checked [date]) | [$ / interval, source] | [$ / interval, source] |
| [Decision criterion] | [fact] | [fact] |
| Best for | [segment] | [segment] |

**Summary:** [Who should pick A, who should pick B, in two sentences.]
```

Use real `<table>` markup. Rows are the criteria buyers decide on. No
"winner" row. Date and source every price and limit.

### Pros and cons ("Is X worth it?")

```markdown
## Is [option] worth it for [segment]?

[One-sentence verdict with the condition it depends on.]

**Strengths:** [specific capability, who it serves, evidence]
**Trade-offs:** [specific limitation, who it affects, evidence]
```

### FAQ block

```markdown
## [Question phrased the way buyers ask it]?

[Direct answer in the first sentence.] [Two or three sentences of context.]
```

Each question gets a real heading, not a `<summary>` or button, so it stands as
its own retrievable section. FAQPage markup no longer produces Google rich
results (ended May 2026); keep it only if it accurately mirrors visible Q&A
and serves other consumers.

### Best-for list

```markdown
## Best [category] for [segment] ([month year])

How we evaluated: [criteria, method, date, disclosure of any affiliation].

### [Option]: best for [specific need]
[Why, with a checked fact. Where it falls short for other needs.]
```

Read `citations-vs-recommendations.md` before publishing self-ranked lists.

## Proof patterns

### Sourced statistic

```markdown
[Claim]. [Source organization] reported [specific number, unit, scope] in
[month year] ([link]). [What it means for the reader].
```

### Original data (the strongest citation magnet)

```markdown
## [Finding stated as a fact]

We [method: surveyed N, tested N, analyzed N records] between [dates].
[Headline finding with number]. [Second finding]. Full methodology and data:
[link].
```

Publish method, sample size, dates, and limits. Give the finding a stable URL
and a chart with alt text that states the number.

### Attributed quote

```markdown
"[Quote]," said [full name], [title] at [organization], [context of when and
where].
```

Only real quotes with permission. Never fabricate an expert.

### Evidence sandwich

```markdown
[Claim].

- [Evidence 1 with source]
- [Evidence 2 with source]

[What the reader should do with this].
```

## Page-type playbooks

**Product page.** First paragraph: what it is, who it is for, what it does.
Plans, prices, and limits as text on a crawlable page (mirror them in
`/pricing.md` if you publish one). Specific capability numbers with conditions.
FAQ for real buyer objections. Link to docs and comparisons.

**Blog post.** One primary question per post, answered in the opening. Named
author with an author page. Visible last-updated date. At least one original
observation, test, or data point. Links to the product and related posts.

**Comparison or alternative page.** Structured table, sourced cells, dated
pricing, clear "best for" by segment, and no strawman. Build with
`suede-competitors`.

**Documentation.** Task-named headings ("Connect Acme to Slack"), numbered
steps, copyable code, expected output, prerequisites, version and date. Docs
are among the most retrieved pages for "how do I" prompts.

**Local and commerce.** Google's AI features draw on Merchant Center feeds and
Business Profiles. Keep inventory, price, hours, services, and attributes
current; respond to reviews; match the site to the profile.

## Regulated topics

Health, finance, and legal pages need named qualified reviewers, review dates,
citations to primary sources (statutes, regulators, peer-reviewed studies), the
jurisdiction, and clear limits on what the page covers. Do not publish advice
the business is not qualified to give.
