---
name: product
description: Create or refine PRODUCT.md.
---
# $product — Interactive PRODUCT.md Generation

> **Loop position:** move 1 (shape intent) of the [operating loop](../../docs/architecture/operating-loop.md) — defines the PRODUCT.md that anchors what counts as in-scope intent before discovery shapes a capability.

> **Purpose:** Guide the user through creating a `PRODUCT.md` that unlocks product-aware reviews in `$pre-mortem` and `$validate`, including the default quick-mode inline paths.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

**CLI dependencies:** None required.

## Execution Steps

Given `$product [target-dir]`:

- `target-dir` defaults to the current working directory.

### Step 1: Pre-flight

Check if PRODUCT.md already exists:

```bash
ls PRODUCT.md 2>/dev/null
```

**If it exists:**

Use AskUserQuestion:
- **Question:** "PRODUCT.md already exists. What would you like to do?"
- **Options:**
  - "Overwrite — start fresh" → continue to Step 2
  - "Update — keep existing content as defaults" → read existing file, use its values as pre-populated suggestions in Step 3
  - "Cancel" → stop, report no changes

**If it does not exist:** continue to Step 2.

### Step 2: Gather Context

Read available project files to pre-populate suggestions:

1. **README.md** — extract project description, purpose, target audience
2. **package.json / pyproject.toml / go.mod / Cargo.toml** — extract project name
3. **Directory listing** — `ls` the project root for structural hints
4. **Existing product/release docs** — if present, read `PRODUCT.md`, `GOALS.md`, release notes, comparison docs, and recent `.agents/research/` or `.agents/plans/` artifacts for PMF, positioning, and evidence context

Use what you find to draft initial suggestions for each section. If no files exist, proceed with blank suggestions.

### Step 3: Interview

Ask the user about each section using AskUserQuestion. For each question, offer pre-populated suggestions from Step 2 where available.

#### 3a: Mission

Ask: "What is your product's mission? (One sentence: what does it do and for whom?)"

Options based on README analysis:
- Suggested mission derived from README (if available)
- A shorter/punchier variant
- "Let me type my own"

#### 3b: Target Personas

Ask: "Who are your primary users? Describe 2-3 personas."

For each persona, gather:
- **Role** (e.g., "Backend Developer", "DevOps Engineer")
- **Goal** — what they're trying to accomplish
- **Pain point** — what makes this hard today

Use AskUserQuestion for the first persona's role, then follow up conversationally for details and additional personas. Stop when the user says they're done or after 3 personas.

#### 3c: Core Value Propositions

Ask: "What makes your product worth using? List 2-4 key value propositions."

Options:
- Suggestions derived from README/project context
- "Let me type my own"

#### 3d: Competitive Positioning

Ask: "What alternatives exist, and how do you differentiate?"

Gather for each competitor:
- Alternative name
- Their strengths (where they win)
- Your differentiation (where you win)
- Feature-level comparison (specific capabilities, not just vibes)

Then ask: "What is the market trend you're betting on that competitors are ignoring?"

This produces the Strategic Bet section — the contrarian thesis that justifies your product's existence. Examples:
- "We bet that AI agents will need institutional memory, not just prompts"
- "We bet that local-first tools will win over cloud-dependent ones"

If the user says "none" or "skip" for competitors, write "No direct competitors identified" but still ask about the strategic bet.

#### 3e: Evidence (Traction + Impact)

Ask: "What evidence do you have that this product works?"

Gather what's available:
- **Usage data** — stars, downloads, clones, active users, installs
- **Measured impact** — bugs caught, time saved, regressions prevented, outcomes achieved
- **User feedback** — testimonials, retention signals, community activity

**Auto-gather if possible:**
- If the project has a GitHub remote, pull real metrics: `gh api repos/{owner}/{repo} --jq '{stars: .stargazers_count, forks: .forks_count, open_issues: .open_issues_count}'`
- If `.agents/` exists, count learnings, council verdicts, and retros as usage evidence
- If `GOALS.md` exists, pull fitness score as a quality metric

If the project is new with no evidence yet, write "Pre-traction — evidence to be gathered" and list what metrics to track.

#### 3f: Known Product Gaps

Ask: "What's broken, missing, or embarrassing about the product right now? Be honest."

This section is the most valuable one for internal product docs. It prevents the doc from being marketing copy. Gather:
- **Missing capabilities** — features users ask for that don't exist
- **Broken promises** — things the README claims that don't fully work
- **Onboarding friction** — where new users get stuck
- **Technical debt** — known limitations that affect product quality

If the user says "nothing", gently challenge: "Every product has gaps. What would a frustrated user complain about?" Push for at least 2 honest gaps.

#### 3g: Product Sense Pass

Ask: "What would give your target audience a 10-star experience?"

Use this as a mandatory product judgment pass. Do not name-drop frameworks in the final document unless useful; translate them into concrete product decisions.

For each lens, gather or infer the answer:

| Lens | Question to answer | Output it should shape |
|------|--------------------|------------------------|
| **Chesky 10/11-star experience** | What would make the first meaningful use feel unexpectedly great, not merely functional? | `10-Star Experience` section and first-value path. |
| **Rahul Vohra / Superhuman PMF** | Which narrow segment would be very disappointed if this disappeared? Who should we ignore for now? | `PMF Wedge`, target personas, and anti-personas. |
| **April Dunford positioning** | What is the real alternative, where does it win, and what context makes this product obviously better? | Competitive positioning and strategic bet. |
| **Teresa Torres discovery** | What recurring customer touchpoints or experiments will keep this honest? | Evidence and discovery metrics. |
| **Marty Cagan outcomes** | What user/business outcome matters beyond shipped features? | Core value propositions and known gaps. |
| **Gibson Biddle DHM** | How does the product delight users in ways that are hard to copy and sustainable to keep improving? | Product strategy and moat. |
| **Elena Verna PLG** | Can the user reach value without human glue or heavy setup? Where is friction too high? | 10-star experience and onboarding gaps. |
| **Melissa Perri build-trap guardrail** | Are we listing features or making strategic choices tied to target conditions? | Product strategy and prioritization. |
| **Shreyas Doshi product sense** | What motivation, friction, satisfaction, and nudges decide whether usage repeats? | Value props, activation, and retention loop. |

Capture:
- **PMF wedge:** the narrow segment to optimize for now
- **Anti-personas:** who the product should not optimize for yet
- **10-star first experience:** the user's first 30-60 minutes, step by step
- **Retention loop:** what makes the next session or next use better
- **Moat:** what becomes harder to copy over time
- **Friction:** the setup or comprehension costs that would kill adoption

#### 3h: Validated Principles (Auto-discovered)

**Do not ask the user.** Scan the project for extracted principles:

1. Check `.agents/planning-rules/` — compiled planning principles
2. Check `.agents/patterns/` — battle-tested patterns from usage
3. Check `.agents/learnings/` — accumulated learnings

If any exist, count them and note their source (e.g., "7 planning rules extracted from 544K agent messages"). These will be included in the output as "Validated Principles" — principles proven through usage, not just design assumptions.

If none exist, skip this section in the output.

### Step 4: Generate PRODUCT.md

Write `PRODUCT.md` to the target directory with this structure:

```markdown
---
last_reviewed: YYYY-MM-DD
---

# PRODUCT.md

## Mission

{mission from 3a}

## Vision

{one-sentence aspirational framing — what the world looks like if the product succeeds}

## Target Personas

### Persona 1: {role}
- **Goal:** {goal}
- **Pain point:** {pain point}
- **Gap exposure:** {which product gaps this persona feels most}

{repeat for each persona}

## PMF Wedge

{The narrow segment to optimize for now, who would be very disappointed without the product, and who is intentionally out of scope.}

## 10-Star Experience

{A concrete first-use or core-use journey that would feel unexpectedly great. Describe the first 30-60 minutes, the evidence of value, and what makes the next use better.}

## What the Product Actually Is

{Describe the product's concrete layers/components. Not marketing copy — what it literally does.
 Organize by architectural layer, not by feature list. For each layer, explain what gap it closes.}

## Core Value Propositions

{bullet list from 3c — each value prop should map to a specific gap or outcome it closes}

## Product Strategy

{Summarize the product choices through these lenses:
- Delight: what creates user love
- Hard to copy: what compounds or differentiates
- Sustainable: what can keep improving without unsustainable service/manual work
- Outcome: what target condition matters more than feature count
- Retention loop: why the product gets more valuable on repeat use}

## Design Principles

{If validated principles were discovered in 3g, include them here:}

**Validated Principles (from {source count} {source description}):**

1. **{Principle name}** — {one-line description with link to source}

{If no validated principles exist, include design principles from the interview.}

**Operational principles:**

{List the principles that govern how the product works, not just what it does.}

## Competitive Positioning

| Alternative | Where They Win | Where We Win |
|-------------|---------------|--------------|
{rows from 3d — honest about both sides}

## Product Sense Review

| Lens | Decision |
|------|----------|
| 10-star experience | {first-use delight decision} |
| PMF wedge | {narrow segment decision} |
| Positioning | {alternative/category/context decision} |
| Continuous discovery | {how evidence will stay fresh} |
| Outcome over output | {target condition} |
| PLG friction | {self-serve/onboarding decision} |
| Build-trap guardrail | {what not to build or claim yet} |

## Strategic Bet

{From 3d — the contrarian thesis. What market trend is this product betting on?}

## Evidence

{From 3e — real numbers, not claims}

**Traction:**
- {metric}: {value} ({time period})

**Measured Impact:**
- {outcome}: {evidence}

{If pre-traction: "Pre-traction — tracking: {list of metrics to watch}"}

## Known Product Gaps

{From 3f — honest about what's broken}

| Gap | Impact | Status |
|-----|--------|--------|
| {gap description} | {who it affects and how} | {open / in-progress / planned} |

## Usage

This file enables product-aware reviews:

- **`$pre-mortem`** — Automatically loads product context when this file exists. Default `--quick` mode includes the context inline; deeper modes add a dedicated `product` perspective alongside plan-review judges.
- **`$validate`** — Automatically loads developer-experience context when this file exists. Default `--quick` mode includes the context inline; deeper modes add a dedicated `developer-experience` perspective alongside code-review judges.
- **`$council --preset=product`** — Run product review on demand.
- **`$council --preset=developer-experience`** — Run DX review on demand.

Explicit `--preset` overrides from the user skip auto-include (user intent takes precedence).
```

Set `last_reviewed` to today's date (YYYY-MM-DD format).

### Step 5: Report

Tell the user:

1. **What was created:** `PRODUCT.md` at `{path}`
2. **What it unlocks:**
   - `$pre-mortem` will now load product context by default, including in `--quick` mode; deeper modes add a dedicated product perspective
   - `$validate` will now load developer-experience context by default, including in `--quick` mode; deeper modes add a dedicated DX perspective
   - `$council --preset=product` and `$council --preset=developer-experience` are available on demand
3. **Next steps:** Suggest running `$pre-mortem` on their next plan to see product perspectives in action

## Examples

### Creating Product Doc for New Project

**User says:** `$product`

**What happens:**
1. Agent checks for existing PRODUCT.md, finds none
2. Agent reads README.md and package.json to extract project context
3. Agent asks user about mission, suggesting "CLI tool for automated dependency updates"
4. Agent interviews for 2 personas: DevOps Engineer and Backend Developer
5. Agent asks about value props, user provides: "Zero-config automation, Safe updates, Time savings"
6. Agent asks about competitors, gathers honest where-they-win and where-we-win for each
7. Agent asks for strategic bet: "We bet that dependency security will become a compliance requirement, not a best practice"
8. Agent auto-pulls GitHub stats (142 stars, 2.3K clones/14d) and asks about measured impact
9. Agent pushes for known gaps: user admits "onboarding is confusing" and "no Windows support"
10. Agent runs the product-sense pass: defines the 10-star first experience, PMF wedge, anti-personas, retention loop, moat, and adoption friction
11. Agent scans .agents/ — finds 12 planning rules and 45 learnings, includes as validated principles
12. Agent writes PRODUCT.md with PMF Wedge, 10-Star Experience, Product Strategy, Evidence, Competitive Positioning, Known Gaps, and Strategic Bet sections

**Result:** PRODUCT.md created with evidence-backed content, unlocking product-aware council perspectives in future validations.

### Updating Existing Product Doc

**User says:** `$product`

**What happens:**
1. Agent finds existing PRODUCT.md from 3 months ago
2. Agent prompts: "PRODUCT.md exists. What would you like to do?"
3. User selects "Update — keep existing content as defaults"
4. Agent reads current file, extracts mission and personas as suggestions
5. Agent asks about mission, user keeps existing one
6. Agent asks about personas, user adds new "Security Engineer" persona
7. Agent updates PRODUCT.md with new persona, updates `last_reviewed` date

**Result:** PRODUCT.md refreshed with additional persona, ready for next validation cycle.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No context to pre-populate suggestions | Missing README or project metadata files | Continue with blank suggestions. Ask user to describe project in own words. Extract mission from conversation. |
| User unclear on personas vs users | Confusion about persona definition | Explain: "Personas are specific user archetypes with goals and pain points. Think of one real person who would use this." Provide example. |
| Competitive landscape feels forced | Genuinely novel product or niche tool | Accept "No direct competitors" as valid. Focus on alternative approaches (manual processes, scripts) rather than products. Still ask for strategic bet. |
| PRODUCT.md feels generic | Insufficient user input or rushed interview | Ask follow-up questions. Request specific examples. Challenge vague statements like "makes things easier" — easier how? Measured how? |
| 10-star experience is vague | User describes features instead of an experience | Walk through the first 30-60 minutes minute-by-minute. Ask what the user sees, trusts, shares, repeats, or would miss tomorrow. |
| PMF wedge is too broad | User lists every possible customer | Ask who would be very disappointed if the product disappeared and who should be ignored until that segment loves it. |
| User resists Known Gaps section | Discomfort admitting weaknesses | Explain: "This is an internal doc, not marketing. Honest gaps prevent the team from building on false assumptions. Every product has them." Push for at least 2. |
| No usage data available | Pre-launch or private project | Write "Pre-traction" with a list of metrics to track once launched. The section's presence reminds future updates to fill it in. |
| `gh api` fails or no GitHub remote | Private repo, no auth, or non-GitHub host | Skip auto-gather gracefully. Ask user to provide metrics manually. |
| No .agents/ directory for principles | Project doesn't use AgentOps | Skip the validated principles section entirely. Include user-stated design principles instead. |

## Reference Documents

- [references/product.feature](references/product.feature) — Executable spec: context gather, interview-driven PRODUCT.md, product-aware council unlock, quick-mode inline (soc-qk4b)
