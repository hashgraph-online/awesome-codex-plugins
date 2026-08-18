---
name: b2b-timing-engine
description: Design recurring B2B buyer-presence systems that keep a company remembered until pain becomes urgent, using time-based visibility cadence instead of unreliable intent signals or linear funnel assumptions. Use when buyers know the company but deals stall, follow-up is inconsistent, the team waits for triggers, expands markets too early, or wants a 4-6 week account visibility rhythm.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: B2B Timing Engine
  category: Marketing
  tags: b2b-sales,sales,timing,follow-up,pipeline
---

# B2B Timing Engine

Use this skill when the company is known and understood but is not present when
buyers become ready. The goal is to engineer repeated visibility across the real
target market so buyers remember the company when pain spikes.

## Source Traceability

Primary source: Unf*ck Your Sales by Jakob Greenfeld, especially the "Timing",
"Diagnostics", "The Trigger Fallacy", "The Annoyance Fallacy", "The Shiny New
Market Fallacy", "The Funnel Fallacy", "The 95-5 Law", and "Engineering
Timing" sections.

## Diagnostic Signals

Timing is likely the constraint when:

- Buyers know what the company does but engage only sporadically.
- Outreach is based on replies, opens, or supposed intent triggers instead of a
  reliable presence cadence.
- The team worries about annoying the market before the market reliably
  remembers the company.
- The team wants to chase a new segment before fully covering the proven one.
- CRM attribution overstates one touch while ignoring months of buyer memory
  building.

## Timing Check

Audit the target account list:

- Has every viable buyer seen or heard from the company in the last 4-6 weeks?
- Is last touch tracked by buyer or account?
- Are touches distributed across useful channels?
- Is the current segment saturated before considering a new market?

If coverage is missing or inconsistent, timing is the likely constraint.

## Workflow

### 1. Set The Visibility Window

Use a 30-45 day window as the default. Every viable buyer should receive or see
at least one relevant touch inside that window.

### 2. Build The Timing Ledger

Track:

- Account.
- Buyer.
- Last touch date.
- Channel.
- Message or asset.
- Next planned touch.

Track last exposure, not only last reply.

### 3. Rotate Touch Types

Use a mix of channels that create low-friction familiarity:

- Short outbound notes.
- Useful follow-up with proof or perspective.
- Manual DMs.
- Calls where appropriate.
- Retargeting or account-based ads.
- Founder or company content the buyer is likely to see.

### 4. Stay With The Proven Market

Do not expand into a new segment because the current one feels boring. Expand
only after the current viable market has sustained coverage and a clear reason
to believe the constraint is no longer timing.

## Output Format

```markdown
# B2B Timing Engine

## Market Coverage
- Segment:
- Accounts:
- Buyers:
- Current 30-45 day coverage:

## Timing Ledger Fields
| Field | Definition |
|-------|------------|
| Account | |
| Buyer | |
| Last touch | |
| Channel | |
| Next touch | |

## Cadence Plan
| Buyer Segment | Touch Type | Frequency | Purpose | Owner |
|---------------|------------|-----------|---------|-------|

## Risks
- Intent-signal traps:
- Over-contact risks:
- Market expansion risks:
```

## Quality Bar

- Do not build the plan around third-party intent data unless there is strong
  evidence it predicts buying readiness.
- Do not treat one ignored email as proof that the market is annoyed.
- Do not optimize linear funnel attribution for long, nonlinear B2B decisions.
- Do not expand markets before the proven market has repeated coverage.
- Make presence systematic, measurable, and boring enough to compound.
