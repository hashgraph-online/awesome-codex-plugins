---
name: best-practices
description: "Use when the user wants state-of-the-art knowledge, best practices, or evidence-based analysis of ANY topic — technology, health, fitness, nutrition, finance, design, psychology, architecture, productivity, learning, or any field where humanity has accumulated knowledge. Use when user says best practices, state of the art, most effective, optimal, evidence-based, how should I, what's the best way to, pros and cons, comparison, or /best-practices."
argument-hint: "<topic>"
user-invocable: true
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Best Practices — Universal State-of-the-Art Research

ultrathink

**Announce:** "Researching **$ARGUMENTS** — gathering state-of-the-art knowledge from authoritative sources."

Read `references/research-strategy.md` in this skill's directory. Keep its frameworks active throughout.

## Core Philosophy

In every field, humanity accumulates knowledge: some approaches prove demonstrably superior under real-world constraints. These "best practices" are not just social consensus — they emerge because physics, biology, economics, and psychology impose hard constraints that reward certain approaches and punish others.

This skill systematically surfaces that accumulated wisdom. The process: understand what counts as evidence in this domain → gather it from the strongest sources → assess its quality → synthesize into honest, actionable knowledge.

**The agent is not an encyclopaedia. It is an epistemic filter.** Its job is to separate signal from noise — evidence from marketing, mechanism from anecdote, validated from fashionable.

## MANDATORY: Progress Updates

Output a short status line BEFORE launching tools at each phase:

| Phase | Message |
|-------|---------|
| 0 | `Phase 0/4 — Domain analysis and epistemological setup...` |
| 1 | `Phase 1/4 — Designing research questions...` then list them |
| 2 | `Phase 2/4 — Gathering evidence ({N} queries across {N} agents)...` |
| 3 | `Phase 3/4 — Assessing evidence quality and confidence...` |
| 4 | `Phase 4/4 — Synthesizing report from {N} sources...` |

## Temporal Calibration

Set from system context:
- `TODAY`, `CURRENT_YEAR`, `PREV_YEAR`, `RECENCY_WINDOW` = `{PREV_YEAR} {CURRENT_YEAR}`

| Age | Label | Default treatment |
|-----|-------|-------------------|
| < 12 months | **Current** | Full weight |
| 12-24 months | **Recent** | High weight, note year |
| 2-4 years | **Established** | Medium weight, verify not superseded |
| > 4 years | **Foundational** | Only if seminal; mark as historical |

**Domain-adjusted recency:** These defaults shift by field. Technology: 2-year-old may be stale. Medicine: 5-year-old meta-analysis may be gold standard. Architecture: 50-year-old principles may be timeless. Calibrate in Phase 0.

## Argument Parsing

- **No arguments**: Ask "What topic would you like me to research?" STOP.
- **Arguments present**: Set `TOPIC` = `$ARGUMENTS`

---

## PHASE 0: EPISTEMOLOGICAL SETUP

Before searching, understand HOW to evaluate evidence for this topic. This phase produces a **domain profile** that drives all subsequent phases.

### Step 1: Domain Detection

Classify `TOPIC` into its field. Not a rigid taxonomy — many topics span fields. Identify the PRIMARY discipline and any secondary ones.

Examples of domain → primary discipline mapping:
- "best chest exercises" → Exercise science (+ biomechanics, anatomy)
- "optimal ETF portfolio" → Finance (+ statistics, behavioral economics)
- "how to furnish a 30sqm apartment" → Interior design (+ ergonomics, spatial planning, materials)
- "best way to learn a new language" → Cognitive science (+ linguistics, education research)
- "microservices vs monolith" → Software engineering (+ distributed systems, organizational theory)
- "Mediterranean diet for longevity" → Nutrition science (+ epidemiology, metabolic physiology)

### Step 2: Evidence Profile

Determine WHAT COUNTS as strong evidence in this domain. Ask:

1. **Does this field have a peer review system?** (Medicine: yes, strong. Interior design: weaker. Cooking: mostly empirical testing.)
2. **What's the evidence gold standard?** (Medicine: systematic review of RCTs. Fitness: RCTs + long-term practitioner outcomes. Design: documented case studies + user research. Tech: production experience + benchmarks.)
3. **How fast does knowledge change?** (Tech: fast. Anatomy: slow. Nutrition: medium — new studies, stable fundamentals.)
4. **What are the dominant failure modes of bad advice?** (Fitness: broscience, influencer culture. Finance: survivorship bias, sales disguised as advice. Tech: hype cycles, resume-driven development.)

### Step 3: Reality Constraints

Identify the hard constraints from physics, biology, economics, or psychology that bound the solution space. These are more reliable than any expert opinion because they don't change with fashion.

Examples:
- **Biomechanics**: A squat must load the kinetic chain through specific joint angles — this constrains which exercises are "best" for quads
- **Thermodynamics**: Weight loss requires caloric deficit — no diet circumvents this
- **Spatial geometry**: A 30sqm apartment has hard constraints on furniture dimensions
- **Cognitive load**: Working memory holds ~4 items — this constrains learning method design
- **Compound interest**: Time in market dominates timing the market — this constrains investment strategy
- **Latency physics**: Speed of light sets a floor on distributed system response time

List the reality constraints relevant to `TOPIC`. These act as **hard filters** during synthesis: any recommendation that violates a reality constraint is wrong regardless of how many experts endorse it.

### Step 4: Context Variables

Identify what the answer DEPENDS ON. Many "best practices" have a validity envelope — they're best GIVEN certain conditions.

Common context variables:
- Experience level (beginner vs. advanced)
- Goals (strength vs. hypertrophy vs. endurance; growth vs. preservation vs. income)
- Constraints (budget, time, space, equipment, health conditions)
- Risk tolerance
- Time horizon
- Individual variation (genetics, preferences, local conditions)

**If `TOPIC` is ambiguous on critical context variables**: Note them and either ask the user or produce conditional recommendations ("If goal is X, then... If goal is Y, then...").

### Step 5: Mandatory Sources (Domain-Conditional)

**If `TOPIC` relates to Claude Code** (skills, hooks, subagents, CLAUDE.md, plugins, MCP, agentic coding): Fetch ALL Claude Code mandatory sources in parallel:

| Source | How |
|--------|-----|
| superpowers (`~/Documents/ai/superpowers`) | Read local. Fallback: WebFetch GitHub |
| Claude Code releases | WebFetch `https://github.com/anthropics/claude-code/releases` |
| Official docs | WebFetch `code.claude.com/docs/en/best-practices`, `/skills`, `platform.claude.com/.../agent-skills/best-practices` |
| claude-code-tips (`~/Documents/ai/claude-code-tips`) | Read local. Fallback: WebFetch GitHub |
| claude-code-best-practice (`~/Documents/ai/claude-code-best-practice`) | Read local. Fallback: WebFetch GitHub |

**For ALL topics**: Identify 2-3 domain-specific anchor sources to prioritize in Phase 2. These are the sources a domain expert would consult first. Don't hardcode them — derive them from the evidence profile.

---

## PHASE 1: RESEARCH DESIGN

Formulate 4-6 **research questions** — not vague "angles" but specific questions a domain expert would investigate. Each question should target a different aspect:

1. **Mechanism**: WHY does the recommended approach work? What's the underlying science/principle?
2. **Efficacy**: WHAT has been shown to work, with what effect size, in what population?
3. **Trade-offs**: What are the costs, risks, and downsides of each approach?
4. **Failure modes**: What goes wrong? What are the common mistakes, myths, or dangers?
5. **Practical implementation**: HOW do you actually do it? What's the protocol, procedure, or workflow?
6. **Current frontier**: What's changing? New research, evolving consensus, emerging alternatives?

---

## PHASE 2: EVIDENCE GATHERING

### Search Battery (10 queries, domain-adaptive)

Construct these queries, adapting vocabulary to domain. Use `{RECENCY_WINDOW}` in all.

| # | Pattern | Purpose |
|---|---------|---------|
| 1 | `"{TOPIC}" best practices evidence-based {RECENCY_WINDOW}` | Current consensus |
| 2 | `"{TOPIC}" comparison "pros and cons" trade-offs` | Decision framework |
| 3 | `"{TOPIC}" study results systematic review meta-analysis` | Scientific evidence |
| 4 | `"{TOPIC}" mistakes myths misconceptions common errors` | Failure knowledge |
| 5 | `"{TOPIC}" site:{domain_authority_1} OR site:{domain_authority_2}` | Domain authorities |
| 6 | `"{TOPIC}" guidelines recommendations standards official` | Institutional guidance |
| 7 | `"{TOPIC}" book recommended essential reading` | Deep literature |
| 8 | `"{TOPIC}" {domain_specific_experts_or_institutions}` | Field leaders |
| 9 | `"{TOPIC}" practical guide how to protocol` | Implementation |
| 10 | `"{TOPIC}" {RECENCY_WINDOW} new research developments` | Emerging knowledge |

For queries 5 and 8, substitute domain-appropriate authority sites and expert names identified in Phase 0. Consult `references/research-strategy.md` for domain-specific examples.

**Execution:** Run in parallel batches of 3-4 using Agent subagents.

### Source Classification (during gathering, not after)

As results come in, classify each by evidence quality using the universal hierarchy from `references/research-strategy.md`:

| Tier | Meaning |
|------|---------|
| **S** | Primary evidence: peer-reviewed research, official standards, foundational works |
| **A** | Leading institutions/practitioners with demonstrated excellence |
| **B** | Recognized experts with verifiable track record |
| **C** | Curated community resources with quality control |
| **D** | Quality community discussion with first-hand experience |

### Hard Quality Gates

Every resource must pass these gates. Failure = silently dropped.

**Universal gates (all domains):**
- Author/source has verifiable authority in the relevant domain
- Not older than 4 years (unless foundational/seminal)
- Not marketing, sponsored content, or affiliate-driven
- Not AI-generated summary content
- Not anecdote presented as evidence
- Not overclaiming beyond what the evidence supports

**Evidence-specific gates:**
- Scientific claims: peer-reviewed, adequate sample, study design appropriate to claim
- Professional recommendations: verifiable credentials and institutional backing
- Product/tool recommendations: independent testing or evidence, not manufacturer claims
- Books: multiple editions, significant citations, or recommended by 2+ independent authorities
- Tech repos: ≥1,000 stars AND active within 6 months (both required)

**Anti-BS detection (reason about these, don't just pattern-match):**

| Red flag | What to check |
|----------|---------------|
| **Cherry-picking** | Does the source cite ALL relevant studies, or just the ones supporting its thesis? |
| **Survivorship bias** | Does it only look at successes? What about the failures using the same approach? |
| **Conflicts of interest** | Who funds this? Who profits from this recommendation? |
| **Overclaiming** | Does the confidence of the claim match the quality of the evidence? |
| **Appeal to nature/tradition** | "Natural" ≠ better. "Traditional" ≠ validated. |
| **False equivalence** | Treating a blog post and a meta-analysis as equal evidence |
| **Recency bias** | Assuming newer = better without checking if older work was superseded |
| **Guru pattern** | Single charismatic authority with no peer validation |

Select **top 10-15 URLs** for deep fetching.

---

## PHASE 3: EVIDENCE ASSESSMENT

**This is the epistemological engine.** Before synthesizing, explicitly evaluate what you found.

### Step 1: Evidence Quality Map

For each major claim or recommendation that will appear in the report, classify its evidence strength:

| Level | Marker | Meaning | Example |
|-------|--------|---------|---------|
| **Strong** | `[strong]` | Multiple high-quality sources agree; mechanism understood; replicated | "Progressive overload drives hypertrophy" (dozens of RCTs, clear mechanism) |
| **Moderate** | `[moderate]` | Good evidence but limited scope, or expert consensus without strong RCTs | "5x5 is effective for beginners" (practitioner consensus, some studies, plausible mechanism) |
| **Emerging** | `[emerging]` | Promising but limited evidence; recent research, not yet replicated | "Blood flow restriction training for hypertrophy" (growing evidence, mechanism proposed, needs more data) |
| **Contested** | `[contested]` | Experts disagree; evidence points both ways; context-dependent | "Low-fat vs. low-carb for weight loss" (both work; individual response varies) |
| **Insufficient** | `[insufficient]` | Not enough evidence to recommend for or against | "Optimal meal timing for muscle growth" (conflicting data, effect size likely small) |
| **Convention** | `[convention]` | Widely practiced but evidence basis is weak or absent | "3 sets of 10 reps" (works, but the specific numbers are tradition not optimization) |

### Step 2: Consensus Map

Identify:
- **Where authorities agree** → These become the core recommendations
- **Where authorities disagree** → Present both sides with evidence quality for each
- **Where evidence is absent** → State the gap honestly

### Step 3: Reality Constraint Check

For each major recommendation, verify it doesn't violate the reality constraints identified in Phase 0. Any claim that contradicts physics, biology, or economics should be flagged regardless of source prestige.

### Step 4: Context Sensitivity Check

For each recommendation, ask: "Is this true for everyone, or does it depend on [context variable]?" Tag context-dependent recommendations with their conditions.

---

## PHASE 4: SYNTHESIS

Produce the final report. Write as a domain expert communicating to an intelligent non-specialist.

### Output Format

```markdown
# State of the Art: {TOPIC}

> **Research date:** {TODAY}
> **Domain:** {detected domain}
> **Sources assessed:** {N} sources across {tiers represented}
> **Evidence quality:** {overall: strong / moderate / mixed}

---

## TL;DR

[3-5 bullets. What a top expert would tell you in 30 seconds.
Each bullet tagged with evidence level: [strong], [moderate], etc.]

---

## 1. Why This Works the Way It Does

[The science/mechanism. Not just WHAT works, but WHY.
Reality constraints that bound the solution space.
Mental models that experts use to reason about this topic.]

---

## 2. What the Evidence Says — Best Practices

[Numbered list. Each entry:
- The practice [evidence level tag]
- Why it works (mechanism + evidence)
- How to apply it (specific, actionable)
- Validity envelope: for whom, under what conditions
- Source(s)]

---

## 3. Decision Framework

[When multiple valid approaches exist, provide a decision matrix.
Criteria, options, and WHEN each option wins.]

| Situation / Goal | Recommended approach | Why |
|------------------|---------------------|-----|
| ... | ... | ... |

---

## 4. What to Avoid

[Mistakes, myths, dangerous practices. Each with:
- The mistake
- Why people believe it (the seductive logic)
- What the evidence actually shows
- The correct alternative]

---

## 5. Practical Protocol

[Adapt section title and content to domain:
- Fitness: "Training Protocol" with sets/reps/frequency/progression
- Nutrition: "Meal Framework" with macros/timing/food selection
- Finance: "Implementation Strategy" with allocations/accounts/rebalancing
- Design: "Design Specifications" with dimensions/materials/layout
- Tech: "Architecture & Implementation" with patterns/tools/config
- General: "Step-by-Step Application"

Include specific, actionable details. Not "exercise regularly" but "3-4 sessions/week, compound movements, progressive overload targeting 5-30 rep range for hypertrophy."]

---

## 6. Where Experts Disagree

[Contested topics where evidence is mixed or context-dependent.
Present both sides with evidence quality for each.
State what the answer depends on.]

---

## 7. Current Developments ({RECENCY_WINDOW})

[What's changing. New research, evolving consensus, emerging approaches.]

---

## 8. Resources & Deep Dives

### Key References
| Resource | Type | Why it matters |
|----------|------|----------------|

### Books
| Title | Author | Year | Key insight |
|-------|--------|------|-------------|

---

## Sources

[All sources, grouped by evidence tier.
For scientific sources: journal, year, study type, sample size.]
```

---

## RULES

1. **Evidence hierarchy is law.** Systematic review > RCT > cohort > case study > expert opinion > anecdote > tradition. State the evidence level for every major claim.
2. **Reality constraints trump expert opinion.** If physics/biology/economics constrain the answer, no amount of authority overrides that.
3. **Cite inline.** Every factual claim references its source.
4. **Be opinionated where evidence is strong.** Don't false-balance when 8/10 authorities agree based on strong evidence.
5. **Be honest where evidence is weak.** "We don't know" is valuable. "Insufficient evidence" is a finding, not a failure.
6. **Concrete over abstract.** Numbers, ranges, protocols, dimensions — not "some" or "moderate" or "appropriate."
7. **Context-conditional over absolute.** "Best for X given Y" over "best overall." If the answer depends on variables, say which ones.
8. **Separate evidence from convention.** Clearly distinguish research-backed from "everyone does it this way." Both may be useful; the reader must know which is which.
9. **No AI summaries of AI summaries.** Primary sources only. Skip AI-generated content.
10. **Language matching.** Write in the same language the user used.
11. **Hard quality gates are non-negotiable.** If applying gates leaves a section empty, write "No sources met the quality bar" — don't lower standards.
12. **Signal over noise.** Every sentence adds information. No filler. No "it depends" without specifying on WHAT.
