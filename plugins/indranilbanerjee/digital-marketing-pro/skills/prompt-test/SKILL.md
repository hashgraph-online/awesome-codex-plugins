---
name: prompt-test
description: "A/B test content variations. Use when: comparing quality scores across prompt approaches, headline styles, or content versions."
---

# /digital-marketing-pro:prompt-test

## Purpose

A/B test content output variations by comparing quality scores across different prompt approaches, headline styles, CTA phrasing, or complete content strategy variations. Create named tests, log variants with their evaluation scores, and determine which approach produces the best quality results.

This command brings experimental rigor to content creation. Instead of guessing which headline style, subject line approach, or content structure works best, you run a structured test: define the experiment, log each variant with its quality scores, and get a statistically grounded recommendation on which approach to adopt. Useful for testing subject line styles (curiosity vs. benefit-driven), headline approaches (question vs. statement vs. how-to), CTA phrasing (urgency vs. value vs. social proof), tone variations (formal vs. conversational), or complete content strategy A/B comparisons.

## Input Required

The user must provide (or will be prompted for):

- **Action**: What to do — `create` (set up a new test), `log` (add a variant to an existing test), `results` (get comparison and winner), or `list` (show all tests)
- **Test name**: A descriptive name for the experiment (e.g., "Q1 email subject line style", "homepage headline approach") — required for `create`, `log`, and `results`
- **Variant label**: Identifier for this variant (e.g., "A", "B", "C", "control", "curiosity-driven", "benefit-led") — required for `log`
- **Content for the variant**: The actual content to evaluate — text inline, file path, or pasted content block — required for `log`
- **Variant description**: Brief explanation of the approach or strategy this variant represents (e.g., "Uses curiosity gap with no product mention", "Leads with quantified benefit") — required for `log`
- **Content type**: The type of content being tested (email subject line, headline, ad copy, CTA, full article, etc.) — optional, applied during evaluation for dimension weighting
- **Evidence file**: Supporting data or research that informs the test hypothesis — optional, passed to evaluation for context

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files (voice-and-tone rules, messaging hierarchy, channel style guides). Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **For `create` action**: Set up a new test by running `python scripts/prompt-ab-tester.py --brand {slug} --action create-test --test-name "{name}"`. This initializes the test record with metadata (creation date, brand, content type) and prepares it for variant logging. Confirm the test was created and remind the user to log variants with `/digital-marketing-pro:prompt-test` using the `log` action.
3. **For `log` action**: First evaluate the variant content for quality by running `python scripts/eval-runner.py --brand {slug} --action run-quick --text "{content_or_path}" --content-type "{type}"` (pass `--evidence "{evidence_path}"` if provided). This produces per-dimension scores (clarity, persuasion, brand alignment, readability, compliance, etc.) and a composite score. Then log the variant with its scores by running `python scripts/prompt-ab-tester.py --brand {slug} --action log-variant --test-name "{name}" --variant-label "{label}" --variant-description "{description}" --scores "{scores_json}"`. Present the individual variant scores to the user immediately so they can see how this variant performed before logging additional variants.
4. **For `results` action**: Pull the full comparison by running `python scripts/prompt-ab-tester.py --brand {slug} --action get-results --test-name "{name}"`. Analyze the results:
   - Identify the winning variant by highest composite score
   - Calculate the margin of victory (percentage difference between winner and runner-up)
   - Assess statistical significance — if variants are within 5% of each other, flag as "too close to call" and recommend additional testing or tiebreaker criteria
   - Break down per-dimension performance to show where each variant excels or falls short (e.g., Variant A wins on persuasion but Variant B wins on clarity)
   - Identify the specific strengths of the winning approach that can be applied to future content
   - Flag any variants that fell below the auto-reject threshold (composite < 60) as unsuitable
5. **For `list` action**: Run `python scripts/prompt-ab-tester.py --brand {slug} --action list-tests` to show all tests for this brand, their status (in-progress, completed), variant count, and creation date.
6. **Present results with clear recommendation**: Summarize findings in a decision-ready format — state the winner, explain why it won, quantify the advantage, note any caveats, and provide a specific recommendation on which approach to adopt going forward. If the winning approach reveals a pattern (e.g., benefit-driven headlines consistently outperform curiosity-based ones for this brand), note that as a reusable insight.

## Output

A structured test report containing:

- **Test summary**: Test name, content type, number of variants, date range
- **Per-variant scorecard**: Each variant's label, description, composite score, and per-dimension breakdown (clarity, persuasion, brand alignment, readability, compliance, engagement potential)
- **Winner declaration**: Which variant won, by what margin, and whether the margin is statistically meaningful
- **Dimension analysis**: Which variant leads on each individual dimension — reveals trade-offs (e.g., "Variant B is more persuasive but Variant A has better brand alignment")
- **Confidence level**: High confidence (>15% margin), moderate confidence (5-15% margin), or low confidence (<5% margin, recommend further testing)
- **Specific recommendation**: Clear statement on which approach to adopt and why, with guidance on how to apply the winning approach to future content
- **Reusable insight**: Any pattern or principle that emerged from this test that can inform the broader content strategy
- **Auto-reject flags**: Any variants that scored below the quality threshold with specific reasons

## Agents Used

- **quality-assurance** -- Evaluates each variant's content quality across multiple dimensions, provides scoring consistency, identifies quality issues, and ensures evaluation criteria align with brand standards
- **content-creator** -- Generates additional variant content if the user requests AI-produced alternatives to test against their own versions, applies brand voice to generated variants
