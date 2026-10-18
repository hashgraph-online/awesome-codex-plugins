# Bullet Intent Scoring (COSMO framework)

Load this when **auditing bullet quality for conversion** or **rewriting bullets**.
This is the optimization layer that sits on top of the hard compliance caps in
`01-policy-rules.md` § 3 — compliance keeps a listing live; intent coverage makes it
convert. A bullet set can be 100% policy-compliant and still be a feature dump
that answers no shopper question.

## Why this exists

Amazon's ranking and its shopping assistant (Rufus) increasingly retrieve and
summarize listings by **shopper intent and context** (the COSMO model), not just
keyword match. Bullets that read as intent answers — *who it's for, what job it
does, where/when it fits, why to trust it* — surface better and convert better
than bullets that list specs with no connective tissue. The goal of a bullet is
to answer a question a shopper is actually asking, then back it with evidence.

## The four intent dimensions

Every strong bullet set covers all four across its 5 bullets. A single bullet can
hit more than one. Use these as a coverage checklist, not a template.

| Dimension | Answers | Signal vocabulary (anchors, not a whitelist) |
|---|---|---|
| **Audience / need fit** | Who is this for? What problem or preference does it solve? | "ideal for", "designed for", "for sensitive skin", "if you", "anyone who", "helps reduce", "relief from", "prevent", "support" |
| **Function / use case** | What job does it do? In what activity, event, or flow? | "use for", "use as", "clean / cook / store / carry / travel", "for camping / office / workout", "daily use", "on the go" |
| **Context / compatibility** | Where, when, or what does it work with? | "compatible with", "fits", "works with", "replacement for", "dishwasher safe", "indoor / outdoor", "waterproof", material/surface words |
| **Decision evidence** | Why trust it? What's the proof or differentiator? | specs and numbers, "includes / comes with", "set of", "certified / lab tested / BPA-free", "unlike", "patented", dimensions, counts, materials |

Any bullet that contains a **number** (size, count, dimension, %) automatically
carries some decision evidence — but a number alone is not a substitute for the
other three dimensions.

## Per-bullet scoring rubric (1–5)

Start each bullet at **5** and deduct. Floor at 1, cap at 5.

| Condition | Deduct |
|---|---|
| Empty bullet | set to 1 |
| Too short (< 50 chars) — no room to make a point | −2 |
| Short (50–99 chars) — thin; ideal is 100+ for substance | −1 |
| Too long (> 255 chars — also the hard policy cap) | −1 |
| Vague marketing phrase ("premium quality", "high quality", "best in class", "world class", "industry leading", "revolutionary", "amazing", "incredible") | −1 |
| Excessive ALL CAPS (> ~30% of the bullet, or 3+ caps words) | −1 |
| Reads like a comma-separated feature list, not an intent answer (4+ short fragments, most ≤4 words) | −1 |
| Addresses **no** clear shopper intent (none of the four dimensions) | −1 |
| Carries intent but **no concrete decision evidence** (no spec/number/included-item/certification/material) | −1 |

These length thresholds (50 / 100 / 255) are **substance heuristics for scoring**.
They do not override the hard policy rules in `01-policy-rules.md` § 3 (**10–255
characters**, at least 3 bullets, capital start, sentence fragment with no end
punctuation, header:description shape, numbers one–nine spelled out, unique content
per bullet). Compliance gates first; intent score optimizes within.

The 255-character ceiling makes intent coverage *harder*, not optional — there is
less room, so every clause has to earn its place. Cutting vague marketing
("premium quality", "best in class") is usually where the budget comes from.

## Coverage rule (set-level)

After scoring the 5 bullets individually, check the **set**: do the five together
cover all four dimensions? Flag any dimension missing across the entire set —
that's a gap even if every individual bullet scored well. Most thin listings miss
**audience/need** (they describe the product but never name who it's for) or
**decision evidence** (claims with nothing behind them).

## Tier labels (set average)

| Avg score | Tier | Action |
|---|---|---|
| ≥ 4.0 | Good | Minor improvements possible |
| 3.0–3.9 | Fair | Several improvements needed |
| 2.0–2.9 | Weak | Major rewrite recommended |
| < 2.0 | Critical | Bullets need a complete overhaul |

## How to apply

**In an audit** — Report a bullet-intent assessment: the set tier, which
dimensions are covered vs. missing, and the 1–2 weakest bullets with the specific
deduction reason. Keep it to the signal — don't print a five-row score table
unless the user asks. This is the conversion half of the review; the compliance
half (suppression, prohibited content) comes from `01-policy-rules.md`.

**In an edit** — When rewriting bullets, make each one answer at least one
dimension and ensure the set covers all four. Lead with the shopper outcome, then
attach the evidence. Replace vague marketing with concrete attributes.

## Worked example

**Weak (score 2):**
`PREMIUM QUALITY MATERIAL, durable, long lasting, great value, buy now`
*Deductions: vague marketing (−1), excessive caps (−1), feature-list fragments
(−1), no decision evidence (−1). Addresses no clear intent.*

**Strong (score 5):**
`Built for daily commuters: the 18L water-resistant 600D polyester pack holds a
15.6" laptop plus a change of clothes, with a luggage pass-through that slides
over a roller handle so it rides hands-free through the airport`
*Covers audience/need (commuters), function (carry laptop + clothes), context
(fits a 15.6" laptop, pairs with a roller bag, water-resistant), and decision
evidence (18L, 600D polyester, dimensions). One sentence, one shopper, real proof.*

## Notes

- These are **universal** optimization heuristics — they apply across categories.
  Category-specific bullet *patterns* live in the `amazon_atlas` knowledge base
  (per-category style guides, `doc_type: style_guide`); query that for
  category-specific phrasing conventions, then apply this intent rubric on top.
- The vocabulary lists above are anchors to help you recognize intent signals.
  Judge in context — a bullet can answer "who it's for" without using any of the
  literal phrases. Don't reward keyword stuffing of these phrases; reward genuine
  intent answers.
