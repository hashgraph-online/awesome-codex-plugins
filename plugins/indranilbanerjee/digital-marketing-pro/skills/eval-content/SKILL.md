---
name: eval-content
description: "Evaluate content quality. Use when: scoring drafts, checking hallucinations, or assessing brand voice compliance."
argument-hint: "[content-path]"
---

# /digital-marketing-pro:eval-content

## Purpose

Comprehensive content evaluation using the full eval pipeline. Runs content through six scoring dimensions — content quality, brand voice, hallucination risk, claim verification, output structure, and readability — to produce a composite score with letter grade, flag specific issues with fix suggestions, and compare against brand quality baselines. This is the go-to command before any content goes to publication, client review, or campaign launch.

Every evaluation is logged to the quality tracker so regression detection, trend analysis, and brand-level quality reporting work continuously. If the brand has custom thresholds or dimension weights configured via /digital-marketing-pro:eval-config, those are applied automatically — otherwise industry-standard defaults are used.

## Input Required

The user must provide (or will be prompted for):

- **Content to evaluate**: The text to score — provided inline, as a pasted block, or as a file path. Supports any marketing content format: blog post, email, ad copy, social post, landing page, press release, content brief, campaign plan, or custom
- **Content type** (optional): One of `blog_post`, `email`, `ad_copy`, `social_post`, `landing_page`, `press_release`, `content_brief`, `campaign_plan`, or `custom`. If omitted, the eval runner auto-detects based on content structure and length. Content type determines which built-in schema is used for structure validation and which readability benchmarks apply
- **Evidence file** (optional): A JSON file containing verifiable claims with source data — required for full claim verification scoring. Format: `[{"claim": "...", "source": "...", "date": "...", "verified": true}]`. If not provided, claim verification runs in extraction-only mode and flags all specific claims as "unverified — evidence recommended"
- **Schema** (optional): A custom JSON schema file for structure validation — used when the content type does not match any of the 8 built-in schemas, or when the brand has a custom template that defines required sections, word counts, and formatting rules

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files (especially `messaging.md` for voice scoring and `visual-identity.md` for format standards). Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Load eval configuration**: Execute `scripts/eval-config-manager.py --brand {slug} --action get-config` to retrieve brand-specific thresholds, dimension weights, and auto-reject rules. If no custom config exists, use defaults from `skills/context-engine/eval-framework-guide.md`. Note which settings are custom vs. default in the output.
3. **Run full evaluation**: Execute `scripts/eval-runner.py --brand {slug} --action run-full --text "{content}" --content-type {content_type}` with optional `--evidence {evidence_file}` and `--schema {schema_file}` flags. This runs all six dimensions:
   - **Content quality** (via content-scorer.py): Depth, originality, accuracy, value to reader, strategic alignment
   - **Brand voice** (via brand-voice-scorer.py): Tone match, terminology consistency, personality alignment, guideline compliance
   - **Hallucination risk** (via hallucination-detector.py): Unverified statistics, fabricated citations, false specificity, invented quotes, unsupported superlatives
   - **Claim verification** (via claim-verifier.py): Cross-reference extracted claims against evidence data — verified, partially verified, unverified, or contradicted
   - **Output structure** (via output-validator.py): Required sections present, word count within range, markdown formatting correct, no placeholder text, CTA consistency
   - **Readability** (via readability-analyzer.py): Flesch-Kincaid grade, sentence complexity, jargon density, audience-appropriate language level
4. **Analyze results — classify issues by severity**: Review all dimension scores and individual findings. Classify each issue as:
   - **Critical** (must fix before publication): Hallucination flags with high confidence, contradicted claims with evidence mismatch, auto-reject threshold failures, compliance violations
   - **Moderate** (should fix, significantly impacts quality): Below-threshold dimension scores, missing required sections, brand voice deviations, readability outside target range
   - **Minor** (recommended improvements): Style suggestions, optional section additions, readability fine-tuning, formatting polish
5. **Generate fix recommendations**: For each flagged issue, provide the specific text or section affected, the exact location in the content, the severity level, a concrete fix suggestion with example replacement text, and the expected score improvement if fixed. Reference `skills/context-engine/eval-rubrics.md` for dimension-specific fix guidance.
6. **Compare to baseline**: Execute `scripts/quality-tracker.py --brand {slug} --action get-trends --days 30` to pull the brand's recent quality history. If historical data exists, show how this content's composite score and individual dimension scores compare to the 30-day rolling average — above average, at average, or below average, with the delta. Flag if this content would lower the brand's average.
7. **Log evaluation**: Execute `scripts/quality-tracker.py --brand {slug} --action log-eval --content-type {type} --data '{"composite": {score}, "dimensions": {dimension_scores_json}}'` to persist the evaluation for trend tracking and regression detection. This step is mandatory — every evaluation must be logged.
8. **Present results with recommendation**: Synthesize all findings into a clear pass/fail/review recommendation:
   - **Pass**: Composite score meets threshold, no critical issues, all dimensions above minimums — content is ready for publication
   - **Review**: Composite score is borderline or moderate issues exist — content needs targeted fixes before publication
   - **Fail**: Composite score below auto-reject threshold, critical issues present, or any dimension below its minimum — content requires significant revision

## Output

A structured evaluation report containing:

- **Composite score and letter grade**: Overall score (0-100) with letter grade (A+ through F), plus the pass/fail/review recommendation with clear reasoning
- **Dimension breakdown**: Individual scores for all six dimensions — content quality, brand voice, hallucination risk, claim verification, output structure, readability — each with the score, the threshold, pass/fail status, and a one-line summary of key findings
- **Critical issues list**: Each with the flagged text, location, severity rationale, and a specific fix suggestion with example replacement text
- **Moderate issues list**: Same structure as critical — below-threshold scores, missing sections, voice deviations, readability concerns
- **Minor issues list**: Style and polish recommendations with suggested improvements
- **Fix impact estimate**: For the top 5 highest-impact fixes, the estimated score improvement if each is applied — helping the user prioritize which fixes matter most
- **Baseline comparison**: How this content compares to the brand's 30-day average composite and per-dimension scores — with delta and trend direction (improving, stable, declining)
- **Auto-reject check**: Whether any auto-reject rules were triggered and which specific thresholds were violated
- **Next steps**: If the content failed or needs review, a prioritized fix checklist ordered by impact; if it passed, confirmation that it is publication-ready with any optional polish suggestions

## Agents Used

- **quality-assurance** — Full eval pipeline orchestration, composite scoring with letter grade calculation, issue severity classification (critical/moderate/minor), fix recommendation generation with specific replacement text, baseline comparison against historical brand quality data, auto-reject threshold enforcement, and eval logging for continuous quality tracking
