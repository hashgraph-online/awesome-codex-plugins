---
name: verify-claims
description: "Verify marketing claims. Use when: cross-checking statistics, awards, certifications, or performance claims with sources."
argument-hint: "[content-path]"
---

# /digital-marketing-pro:verify-claims

## Purpose

Cross-check marketing claims against user-provided evidence data. Extracts all verifiable claims from content — statistics, percentages, rankings, awards, certifications, named citations, performance metrics, customer counts, and time-bound assertions — then matches each against an evidence file and classifies it as verified, partially verified, unverified, or contradicted. This command is the dedicated deep-dive for claim integrity, while /digital-marketing-pro:eval-content includes claim verification as one dimension of its broader quality assessment.

Marketing content that cites specific numbers, awards, or results without verified backing is a brand risk. Contradicted claims erode trust if caught by customers, journalists, or regulators. This command ensures every factual assertion in your content is backed by real data, clearly sourced, and defensible under scrutiny.

## Input Required

The user must provide (or will be prompted for):

- **Content with claims**: The text to verify — provided inline, as a pasted block, or as a file path. Any marketing content that makes factual assertions: landing pages, case studies, press releases, ad copy, pitch decks, investor materials, product pages, or client reports
- **Evidence file** (optional but strongly recommended): A JSON file containing source data to verify against. Format: `[{"claim": "descriptive claim text", "source": "data source name or URL", "date": "YYYY-MM-DD when verified", "verified": true/false, "value": "the verified number or fact"}]`. Can be exported from GA4, CRM, sales data, certification bodies, or assembled manually. If not provided, the command operates in extraction-only mode and guides the user on creating an evidence file
- **Specific claim to check** (optional): A single claim to focus on instead of scanning the full content — useful for quick spot-checks on a particular statistic or assertion

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply compliance rules for target markets (`skills/context-engine/compliance-rules.md`) — some industries and regions have stricter requirements for substantiating claims (financial services, healthcare, EU consumer protection). Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load messaging restrictions that may define approved claims and prohibited assertions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Extract claims from content**: Execute `scripts/claim-verifier.py --action extract-claims --text "{content}"` to identify all verifiable assertions. The extractor categorizes claims by type:
   - **Statistical claims**: Percentages, ratios, growth numbers, market size figures ("73% increase in conversions," "4.8x ROAS")
   - **Ranking claims**: Position assertions, comparative statements ("market leader," "#1 rated," "fastest-growing")
   - **Award and certification claims**: Named awards, industry certifications, compliance badges ("ISO 27001 certified," "G2 Leader")
   - **Named citation claims**: Attributed quotes, source references, study citations ("according to Gartner," "Forrester reports")
   - **Performance claims**: Customer counts, time-bound results, SLA promises ("10,000+ customers," "results in 30 days")
   - **Temporal claims**: Date-specific assertions, recency claims ("as of 2026," "latest data shows")
3. **Verify claims against evidence**: If an evidence file is provided, execute `scripts/claim-verifier.py --action verify --text "{content}" --evidence {evidence_file}`. For each extracted claim, the verifier:
   - Attempts to match the claim to an evidence entry by semantic similarity and claim type
   - Classifies the match result: **Verified** (claim matches evidence within acceptable tolerance), **Partially verified** (claim is directionally correct but specific numbers differ, or the source date is stale), **Unverified** (no matching evidence entry found), or **Contradicted** (evidence directly conflicts with the claim)
   - Assigns a confidence score (0-100) to each verification based on match quality, source recency, and specificity alignment
4. **Handle missing evidence file**: If no evidence file is provided, skip the verification step. Instead, present all extracted claims with their types and flag each as "unverified — no evidence provided." Guide the user on creating an evidence file:
   - Explain the JSON format with examples for each claim type
   - Suggest data sources: GA4 for performance metrics, CRM for customer counts, certification bodies for awards, published reports for industry statistics
   - Offer to generate a template evidence file pre-populated with the extracted claims (values left blank for the user to fill)
5. **Detail contradictions**: For each contradicted claim, present a side-by-side comparison: the claim text as written in the content, the evidence data that conflicts, the specific discrepancy (e.g., "content says 73% increase, evidence shows 61% increase"), and the potential impact of publishing the incorrect claim (reputational, regulatory, competitive).
6. **Recommend corrections**: For unverified and contradicted claims, provide specific recommendations:
   - **Contradicted claims**: Suggest corrected text using the evidence value, with hedging language options if exact figures are sensitive ("approximately," "over X," "nearly Y")
   - **Unverified claims**: Suggest adding source attribution, softening absolute statements to qualified ones, or removing the claim until evidence is available
   - **Stale evidence**: Flag claims where the evidence date is more than 12 months old and recommend refreshing the data
7. **Generate verification summary**: Produce an overall verification score (percentage of claims verified or partially verified), a risk assessment based on the number and severity of contradicted and unverified claims, and a compliance note if the brand operates in a regulated industry where unsubstantiated claims carry legal risk.

## Output

A structured verification report containing:

- **Verification score**: Percentage of claims that are verified or partially verified — the headline metric for content claim integrity
- **Claims inventory**: Total claims extracted, broken down by type (statistical, ranking, award, citation, performance, temporal) — showing the scope of factual assertions in the content
- **Per-claim verification results**: For each claim:
  - The claim text as it appears in the content, with location
  - Claim type classification
  - Verification status: Verified, Partially verified, Unverified, or Contradicted
  - Evidence match: The specific evidence entry it was checked against (if any), with source and date
  - Confidence score (0-100) for the verification
  - Issue details: For partially verified or contradicted claims, the specific discrepancy
  - Recommended action: Keep as-is, update with correct value, add source attribution, soften language, or remove
- **Contradiction details**: Side-by-side comparison for each contradicted claim — content text vs. evidence data, with the specific discrepancy highlighted and corrected text suggestion
- **Unverified claims list**: All claims with no matching evidence, grouped by risk level (high-risk: specific numbers and absolute statements; moderate-risk: comparative claims and rankings; low-risk: general qualitative assertions)
- **Stale evidence warnings**: Claims where the supporting evidence is older than 12 months, with a recommendation to refresh the data
- **Corrected text suggestions**: For each claim needing correction, the original text and one or more replacement options — an exact-value version using the evidence data and a hedged version with qualifier language
- **Evidence file template**: If no evidence file was provided, a pre-populated JSON template with all extracted claims ready for the user to fill in verified values and sources
- **Compliance notes**: If the brand operates in a regulated industry (financial services, healthcare, legal, insurance), specific regulatory requirements for claim substantiation with references to relevant rules (FTC Act, EU Consumer Rights Directive, ASA CAP Code, industry-specific regulations)

## Agents Used

- **quality-assurance** — Claim extraction from content using pattern matching and NLP heuristics, claim-to-evidence matching with semantic similarity and type alignment, verification status classification with confidence scoring, contradiction detection with discrepancy quantification, correction text generation with hedging options, and compliance-aware risk assessment for regulated industries
