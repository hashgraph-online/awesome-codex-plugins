---
name: eighty-twenty-market-selection
description: Find hyper-responsive buyers and disqualify weak markets using 80/20 Sales and Marketing. Use when choosing a target segment, validating demand, screening prospects, finding urgent buyer problems, or deciding whether a market is worth sales and marketing effort.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: 80/20 Market Selection
  category: Marketing
  tags: eighty-twenty,sales,marketing,segmentation,qualification
---

# 80/20 Market Selection

Use this skill to identify the small slice of a market most likely to respond,
buy, and produce disproportionate value. It is based on 80/20 Sales and
Marketing by Perry Marshall.

## Source Traceability

Primary source: 80/20 Sales and Marketing, chapters 2, 3, 20, and 21.

- Chapter 2 introduces response-triggered market testing.
- Chapter 3 applies 80/20 to common sales frustrations.
- Chapter 20 covers polarized, highly responsive markets.
- Chapter 21 covers fast market research using buyer language and unanswered
  questions.

## Workflow

### 1. Define The Market Choice

Capture:

- Product or offer.
- Candidate segment.
- Buyer role.
- Urgent problem.
- Current alternative.
- Proposed proof of responsiveness.

If the segment is broad, split it into narrower groups before judging it.

### 2. Find Responsiveness Signals

Look for proof that buyers already move:

- Search queries for the problem.
- Social posts, forums, reviews, or communities using emotional buyer language.
- Paid offers, competitors, agencies, consultants, or tools already serving the
  need.
- Budget, compliance pressure, deadlines, risk, or loss tied to inaction.
- Strong positive or negative reactions, not mild approval.

Do not confuse a logical problem with a responsive market. The question is
whether buyers act.

### 3. Disqualify Weak Segments

Reject or downgrade segments when:

- They lack money or authority.
- The pain is not urgent.
- They do not believe the offer category.
- They cannot say yes without many blockers.
- The solution does not fit their current plans.
- Buyer language is vague or borrowed from the seller.

### 4. Pick The Testing Move

Choose the smallest action that reveals responsiveness:

- Landing page or offer smoke test.
- Direct outreach to a narrow list.
- Paid search or paid social micro-test.
- Community/listening sprint.
- Interview batch with problem-language capture.
- Waitlist, application, or hand-raise mechanism.

## Output Format

```markdown
# Market Selection Recommendation

## Candidate Segment
- Segment:
- Buyer:
- Urgent problem:
- Current alternative:

## Responsiveness Evidence
| Signal | Evidence | Strength |
|--------|----------|----------|

## Disqualification Check
| Factor | Pass/Concern/Fail | Notes |
|--------|-------------------|-------|
| Money | | |
| Urgency | | |
| Belief | | |
| Authority | | |
| Fit | | |

## Recommended Test
- Test:
- Success signal:
- Kill signal:
- Next segment if this fails:
```

## Quality Bar

- Do not recommend a broad market without narrowing it.
- Do not treat polite interest as buyer responsiveness.
- Use buyer language, not seller language.
- Include explicit disqualifiers before recommending a test.
- Prefer observable action over stated preference.
