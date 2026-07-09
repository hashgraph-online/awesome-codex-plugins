# Actionable Persona Format

Most personas in marketing are biographical narratives that produce no useful guidance. "Meet Priya, 28, lives in Bangalore, loves yoga and online shopping, earns 12 LPA" tells you what she looks like — not what she wants, not where to find her, not how to convert her.

The Actionable Persona Format replaces biographical narratives with six questions whose answers directly inform marketing decisions.

## The Six Questions

### 1. What is the primary job they are trying to get done?

Not "they want our product." That is what we want them to want. The actual job is what they want for themselves.

**Weak example:** "She wants to use our project management tool."

**Strong example:** "She wants to stop missing deadlines because her team is using three different tools that nobody syncs."

The job is the outcome the person needs in their life. Use Jobs-to-Be-Done framing: "When [situation], they want to [job], so they can [ultimate outcome]."

### 2. What triggers them to start looking for a solution?

A persona who is not actively looking is not a marketable persona — they are an out-market awareness target. The trigger is the moment the person enters the in-market state.

**Weak example:** "She is always looking for productivity tools."

**Strong example:** "She enters the market the week after a project blew its deadline and she got a difficult email from a client. The trigger is internal pressure to fix the systemic problem before another deadline blows."

Knowing the trigger tells you when and where to be present.

### 3. Where do they search for solutions?

Specific platforms, specific search behaviour, specific information sources.

**Weak example:** "She searches online."

**Strong example:** "She starts with a Google search for 'best project management tool for design agencies'. Then she asks her network on LinkedIn. Then she watches 2–3 YouTube reviews from creators she trusts. Then she revisits Google for 'X vs Y' comparisons. Then she checks G2 and Capterra reviews."

This directly tells you which channels matter (Google Search, LinkedIn, YouTube, review sites) and what content to create (comparison content, reviews, tutorials).

### 4. What criteria do they use to evaluate options?

The decision criteria. What makes one option better than another in their judgment.

**Weak example:** "She wants something that works well."

**Strong example:** "Three criteria, in order: (1) integrates with the design tools her team already uses (Figma, Notion, Slack); (2) implementation time under one week (no time for a long onboarding); (3) per-user pricing under INR 1,000/month per seat."

This tells you exactly what your messaging must lead with — integrations, fast implementation, transparent pricing.

### 5. What would make them choose us over alternatives?

The reason-to-believe specific to your brand vs the alternatives they are considering.

**Weak example:** "Our quality."

**Strong example:** "Specific case study of a similar-size design agency that went from missing 30% of deadlines to under 5% in 60 days using our tool. With named client and quantified outcome."

This tells your sales and content teams exactly what proof points to develop.

### 6. What would make them NOT choose us?

The disqualifiers. What might they discover that would push them to a competitor.

**Weak example:** "Bad reviews."

**Strong example:** "Three things would lose her: (1) no native Figma integration (vs Notion's deep Figma support); (2) any pricing above INR 1,200/seat/month (we exceed her budget tolerance); (3) any onboarding requirement above 5 days (she has no time for a long implementation)."

This tells your product, sales, and pricing teams exactly what objections to address — and what to never make worse.

## Producing personas using this format

Personas in this format live in Core Doc 3.2 (Segmentation Framework), Step 5.

The skill that generates personas (`audience-intelligence/persona-builder` and the Part 3 four-core-documents skill) outputs each persona as a structured markdown block:

```markdown
## Persona: {Persona Name}

**Persona ID:** {unique identifier}
**Target Group:** {which TG this persona belongs to}
**Sub-segment:** {specific sub-segment}
**Priority:** {Primary / Secondary / Tertiary}

### 1. Primary Job to Be Done
{1–3 sentences using JTBD framing}

### 2. Trigger
{1–3 sentences describing the moment that puts this persona into the in-market state}

### 3. Search Behaviour
{Specific platforms, search queries, information sources, in sequence}

### 4. Evaluation Criteria
{Ordered list of 3–5 specific criteria, with weights if known}

### 5. Reasons to Choose Us
{Specific proof points tied to alternatives being considered}

### 6. Reasons to NOT Choose Us
{Specific disqualifiers — what might push them to a competitor}

### Demographics & Context (Reference Only)
{Brief — used only for media planning targeting, not for messaging direction}

- Age range: {if relevant}
- Geography: {city tier, region}
- Income range: {if relevant}
- Profession / role: {especially for B2B}
- Tech sophistication: {if relevant}
```

Notice that demographics come **last and brief**. They are inputs to media targeting (Meta interest targeting, LinkedIn job title targeting), not to messaging direction. The six questions drive messaging.

## How skills consume personas

Every channel skill (Part 9), every creative skill (Part 10, Part 11), every content skill reads the relevant persona before producing output.

A blog post for Persona X opens with the trigger ("If you are a [role] who just had [situation that matches the trigger]..."), addresses the evaluation criteria in the body, and closes with proof points that match Reason #5.

An ad for Persona X uses the search-language from Question 3, leads with the criterion #1, and addresses the top objection from Question 6.

A landing page for Persona X mirrors the search query, demonstrates the evaluation criteria can be met, and pre-empts the disqualifiers.

This is what "actionable" means. The persona document is not a story — it is a brief.

## Personas vs Anti-Personas

Step 14 of Core Doc 3.2 documents anti-personas — who the brand explicitly does not target.

For each anti-persona:

- **Description:** who they are
- **Why they are NOT a target:** misalignment of need, mismatched expectations, unprofitable to serve, brand-misalignment, etc.
- **Implication:** what we do NOT do (e.g., "do not bid on enterprise-procurement keywords; do not show LinkedIn ads to anyone with 'Procurement' in title; do not use 'enterprise-grade' language that would attract anti-personas")

Anti-personas are as strategically valuable as personas. They prevent budget waste and brand-fit drift.

## Related references

- [four-core-documents-spec.md](four-core-documents-spec.md) — Core Doc 3.2 Step 5
- [b2b-decision-making-unit.md](b2b-decision-making-unit.md) — B2B overlay (User / Influencer / Decision-maker / Gatekeeper)
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — where personas fit in the methodology
