# Stone vs Opinion — Confidence Tagging

Every fact captured during engagement intake (Part 1) is tagged with one of two confidence levels. This separation is foundational to the engagement methodology.

## The Two Tags

### Stone

**Definition:** What the client knows for certain. A fact independently verifiable or directly observed.

Examples of Stone:
- "Our company was founded in 2018" (verifiable from registration)
- "We have 47 employees as of April 2026" (verifiable from HR records)
- "Our annual revenue last year was INR 12 crore" (verifiable from financials)
- "We sell only in India and Singapore" (verifiable from operations)
- "Our pricing tiers are INR 999, INR 4,999, INR 19,999 per month" (verifiable from product)
- "We use HubSpot CRM and Klaviyo for email" (verifiable from systems)
- "Our biggest customer is [named brand]" (verifiable from contracts)
- "Our average order value is INR 2,400" (verifiable from order data)

Stone facts are treated as ground truth in unbiased research (Parts 2–4) and in all downstream skills.

### Opinion

**Definition:** What the client believes. A claim that may be true but has not been independently validated.

Examples of Opinion:
- "Our customers love us for our quality"
- "We are known as the most affordable option in our category"
- "Our biggest growth opportunity is the South India market"
- "Our main competitor is [named brand]"
- "Our customers research for 2 weeks before buying"
- "Our brand is positioned as premium"
- "Most of our customers come through word of mouth"
- "Our content marketing has been very effective"

Opinion facts are captured but **explicitly tagged as hypotheses**. They are NOT used as ground truth in the unbiased research phase. Instead, they become **research questions** that Parts 2–4 actively try to validate or contradict.

## Why this separation matters

Without Stone vs Opinion separation, client intake contaminates unbiased research. The client tells the agency "we are positioned as premium" — and the unbiased research, instead of independently assessing the brand's actual market position, produces a confirmatory analysis that just restates the client's belief.

By tagging the same intake item as Opinion, the unbiased research phase is forced to answer: *Is the brand actually positioned as premium in the market? What evidence supports or contradicts this?*

The result is genuine market intelligence rather than dressed-up client narrative.

## Capturing Stone vs Opinion in Part 1

The Part 1 intake produces two files:

### `stone-facts.json`

```json
{
  "engagement_id": "acme-2026-q2",
  "captured_at": "2026-05-03T10:00:00Z",
  "facts": [
    {
      "id": "stone-001",
      "category": "company",
      "fact": "Founded in 2018",
      "source": "client statement, validated against MCA records",
      "validation_method": "public-record"
    },
    {
      "id": "stone-002",
      "category": "scale",
      "fact": "47 employees as of April 2026",
      "source": "client HR system",
      "validation_method": "client-document"
    },
    {
      "id": "stone-003",
      "category": "geography",
      "fact": "Sells only in India and Singapore",
      "source": "client statement, confirmed from website footer + product listings",
      "validation_method": "public-source"
    }
  ]
}
```

### `opinion-hypotheses.json`

```json
{
  "engagement_id": "acme-2026-q2",
  "captured_at": "2026-05-03T10:00:00Z",
  "hypotheses": [
    {
      "id": "opinion-001",
      "category": "positioning",
      "hypothesis": "We are positioned as the most affordable option in our category",
      "client_evidence": "client belief, citing customer feedback",
      "research_question": "Is the brand actually positioned as the most affordable in its category? How does pricing compare to top 5 competitors? What do third-party reviews say about price perception?",
      "research_assigned_to": "Part 2 ecosystem scan + Part 4.2 Competitor Positioning"
    },
    {
      "id": "opinion-002",
      "category": "audience",
      "hypothesis": "Our biggest growth opportunity is the South India market",
      "client_evidence": "client intuition, recent enquiry uptick",
      "research_question": "What does the unbiased market sizing say about South India opportunity vs other geographies? What is the competitive density in South India?",
      "research_assigned_to": "Part 4.4 Market Analysis"
    }
  ]
}
```

## How research consumes Stone vs Opinion

### Parts 2–4 (Unbiased Research)

- Read `stone-facts.json` — these are accepted as ground truth
- Read `opinion-hypotheses.json` — these become **research questions to validate**
- Do NOT consult client documents (deck, internal reports, etc.) during this phase
- Use only public sources, third-party data, market reports, competitive intelligence
- Produce findings that either confirm, contradict, or refine each opinion hypothesis

### Part 5 (Client Validation)

Each opinion hypothesis is brought back to the client as a finding:

> "You mentioned during intake that South India is your biggest growth opportunity. The unbiased market analysis suggests West India and Tier-2 Maharashtra cities have larger TAM and lower competitive density. This finding requires your validation before proceeding."

The client then ACCEPTS / REJECTS / EDITS the finding (with rationale).

### Parts 6+ (Operating)

- Stone facts continue to be ground truth across the engagement
- Opinion hypotheses are now either:
  - **Validated** (both client and unbiased research agree) → treated as fact
  - **Corrected** (unbiased research showed something different and client accepted the correction) → treated as fact, flagged as "originally stated as opinion, validated as different"
  - **Maintained against research** (unbiased research disagreed but client insisted) → flagged as "client-asserted, market evidence to the contrary"
  - **Open** (still unresolved) → continues to be a research question

## Stone vs Opinion in skill outputs

When a skill cites a fact, it can include the confidence trail:

> Per Stone (verified from MCA records), the company was founded in 2018.

> Per validated Opinion (originally client belief, confirmed by Part 4.2 Competitor Positioning analysis), the brand is positioned as a value-tier alternative to enterprise incumbents.

> Per client-asserted Opinion (market evidence to the contrary), the South India market is treated as the priority growth geography. The team should monitor whether actual performance validates this assertion within Q1.

This makes the entire engagement intellectually traceable. Anyone reviewing months later can see what was assumed, what was validated, and where assumptions still rest on client belief alone.

## Common pitfalls to avoid

1. **Treating client opinion as fact during research.** This contaminates the unbiased view and produces confirmatory rather than independent analysis.
2. **Refusing to capture client opinions at all.** Opinions are valuable — they reveal what the client believes and what they want to be true. Just tag them clearly.
3. **Re-classifying opinions as Stone after a single confirming data point.** Validation requires meaningful evidence, not a single anecdote.
4. **Letting Stone facts go un-cited.** Even Stone facts need their source documented. "Founded in 2018" without a source is just another opinion.
5. **Forgetting to revisit unresolved opinions.** Opinions that stay "open" after Part 5 should be revisited in Part 12 (continuous improvement) when more data accumulates.

## Related references

- [engagement-flow-methodology.md](engagement-flow-methodology.md) — Part 1 context
- [two-views-model.md](two-views-model.md) — how validated opinions feed v2
- [living-instruction-file-spec.md](living-instruction-file-spec.md) — where validated facts live
