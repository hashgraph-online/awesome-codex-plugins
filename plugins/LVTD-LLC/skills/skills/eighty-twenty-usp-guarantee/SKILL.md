---
name: eighty-twenty-usp-guarantee
description: Create 80/20-style unique selling propositions, guarantees, and result-based offers. Use when positioning an offer, strengthening a value proposition, raising prices, creating a guarantee, or making a sales promise more specific and credible.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: 80/20 USP Guarantee
  category: Marketing
  tags: eighty-twenty,positioning,offers,guarantees,sales
---

# 80/20 USP Guarantee

Use this skill to turn vague positioning into a specific promise for a specific
buyer under specific conditions. It is based on 80/20 Sales and Marketing by
Perry Marshall.

## Source Traceability

Primary source: 80/20 Sales and Marketing, chapters 8 and 13.

- Chapter 8 covers business and personal unique selling propositions.
- Chapter 13 covers result-based selling, power guarantees, and premium offers.

## Workflow

### 1. Clarify The Buyer And Result

Capture:

- Buyer type.
- Current state.
- Desired result.
- Time horizon.
- Constraints.
- Proof the seller can credibly claim.

The USP should not try to persuade everyone. It should make the right buyer feel
seen and the wrong buyer opt out.

### 2. Separate Procedure From Result

List what the seller does, then translate it into what the buyer gets.

Ask:

- What outcome does the buyer actually pay for?
- What risk does the buyer want removed?
- What result could be guaranteed under clear conditions?
- What buyer commitments are required for the result?

### 3. Build The Power USP

Use this structure:

- If you are [qualified buyer].
- And you commit [requirements].
- Then you will achieve [specific result].
- Or else [seller penalty, refund, extra work, or other meaningful remedy].

Keep the penalty real enough to signal confidence, but bounded enough to be
operationally safe.

### 4. Stress Test The Guarantee

Check:

- Is the buyer qualified tightly enough?
- Are buyer responsibilities explicit?
- Is the result measurable?
- Is the remedy meaningful?
- Could fulfillment actually support this promise?

## Output Format

```markdown
# USP And Guarantee

## Buyer And Result
- Qualified buyer:
- Desired result:
- Time horizon:
- Required buyer commitments:

## Procedure To Result Translation
| Seller Activity | Buyer Result | Proof |
|-----------------|--------------|-------|

## Power USP Draft
[If buyer + commitment, then result, or remedy.]

## Risk Controls
- Qualification rule:
- Buyer responsibilities:
- Exclusions:
- Operational constraint:
```

## Quality Bar

- Do not write a USP that applies to everyone.
- Do not guarantee a result without buyer commitments.
- Do not confuse deliverables with outcomes.
- Make the remedy specific.
- Flag operational risk before recommending a bold guarantee.
