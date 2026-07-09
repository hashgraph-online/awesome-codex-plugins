---
name: b2b-reach-engineering
description: Build B2B reach systems that make a defined market aware of the company through named accounts, real buyers, controlled delivery channels, and first-touch saturation. Use when the right market may not know the company exists, outbound gets little signal, brand awareness is vague, the target market is too broad, or the team needs a concrete account list and reach plan.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: B2B Reach Engineering
  category: Marketing
  tags: b2b-sales,sales,outbound,reach,account-based-marketing
---

# B2B Reach Engineering

Use this skill when obscurity is the sales constraint. The goal is to turn a
vague market into a reachable list of companies and buyers, then plan deliberate
first-touch coverage before optimizing conversion.

## Source Traceability

Primary source: Unf*ck Your Sales by Jakob Greenfeld, especially the "Reach",
"Diagnostics", "The Rejection Fallacy", "The TAM Fallacy", "The Precision
Fallacy", "The First-Touch Law", and "Engineering Reach" sections.

## Diagnostic Signals

Reach is likely the constraint when:

- The company has a good offer but too few relevant buyers know it exists.
- The team interprets silence as rejection before confirming actual market
  exposure.
- Targeting is either over-narrow and hesitant or too broad and noisy.
- The team talks about a huge TAM but cannot name the specific companies and
  people who must know the company.
- Optimization is focused on subject lines, funnels, or conversion before the
  first pass through the target market is complete.

## Workflow

### 1. Extract Non-Negotiables

Use evidence from closed deals, serious opportunities, and competitor wins.
Identify the minimum criteria that must be true for a deal to be plausible.

Capture:

- Company type, size, geography, system, regulation, or trigger.
- Buyer role or owner of the pain.
- Pain intensity and ability to act.
- Disqualifiers that make a deal unrealistic.

### 2. Build The Reach List

Convert the target market into named accounts:

- List only companies that match the non-negotiables.
- Name the 1-3 humans at each account who feel the pain or can act on it.
- Keep the list concrete enough to contact and measure.
- Treat broad TAM language as a warning sign.

### 3. Choose Controlled Delivery Channels

Prefer channels where delivery can be proven or closely estimated:

- Cold email to named buyers.
- Manual DMs.
- Calls.
- Account-based ads against the list.
- Warm intros when available.

Avoid waiting for broad brand awareness, generic posting, or black-box targeting
when reach coverage is the constraint.

### 4. Saturate Before Optimizing

Do not judge messaging, conversion, or sales quality until every qualified buyer
on the list has had at least one real exposure.

Track:

- Accounts identified.
- Buyers identified.
- First touches delivered.
- Delivery or exposure rate.
- Replies or second-step signals, as secondary metrics.

## Output Format

```markdown
# B2B Reach Plan

## Non-Negotiables
- Must-have account criteria:
- Must-have buyer criteria:
- Disqualifiers:

## Target List Plan
| Segment | Account Criteria | Buyer Roles | Estimated Accounts | Source |
|---------|------------------|-------------|--------------------|--------|

## Channel Plan
| Channel | Why It Controls Delivery | First-Touch Action | Coverage Metric |
|---------|--------------------------|--------------------|-----------------|

## Saturation Target
- Accounts:
- Buyers:
- First-touch deadline:
- Success signal:
```

## Quality Bar

- Do not call silence rejection until exposure has been proven.
- Do not recommend broad awareness plays when named-buyer reach is possible.
- Do not over-segment before the first pass is complete.
- Do not blast unqualified lists and call it reach.
- Make coverage measurable before discussing optimization.
