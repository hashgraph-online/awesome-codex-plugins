---
name: eval-suite
description: "Batch evaluate multiple content pieces. Use when: scoring a content library, campaign assets, or deliverable set."
---

# /digital-marketing-pro:eval-suite

## Purpose

Batch evaluation across multiple content pieces to produce a portfolio-level quality assessment. Evaluate an entire content library, all assets in a campaign, or a set of deliverables in one run. Instead of evaluating content one piece at a time, this command processes everything together and delivers a holistic view of content quality.

The output includes content rankings, per-dimension analysis, overall quality distribution, common issues across the set, and a prioritized revision list. This is the command to use before a campaign launch (to catch weak assets before they go live), during a content audit (to assess library health), or after a production sprint (to quality-check all deliverables at once). Every evaluation is logged to the quality tracker for longitudinal trend analysis.

## Input Required

The user must provide (or will be prompted for):

- **Content sources**: One or more of the following:
  - A list of file paths (e.g., "evaluate these 5 files: email-v1.txt, email-v2.txt, landing-page.html, ad-copy-fb.txt, ad-copy-google.txt")
  - A directory path (e.g., "evaluate everything in /campaign-q1-assets/") — all text-based files in the directory will be included
  - Multiple inline content blocks with labels (e.g., "Evaluate these: [Label: Homepage Hero] content... [Label: Email Subject] content...")
- **Content type**: Optional — applied globally (e.g., "these are all email subject lines") or specified per item. If omitted, the evaluator will infer type from content characteristics
- **Evidence file**: Optional — shared context document (brief, strategy doc, audience research) applied across all evaluations for more relevant scoring
- **Evaluation depth**: Optional — `quick` (default, faster per-item evaluation) or `full` (comprehensive evaluation with detailed per-dimension commentary per item). Quick is recommended for sets larger than 10 items; full for critical campaign assets
- **Auto-reject threshold**: Optional — composite score below which content is flagged as needing mandatory revision (default: 60)
- **Comparison baseline**: Optional — a previous eval-suite run ID to compare against, showing improvement or regression per piece

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files (voice-and-tone, messaging, channel styles). Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Enumerate all content items**: Resolve the provided sources into a flat list of content items. For directory paths, scan for text-based files (.txt, .md, .html, .csv rows). For inline content, parse labels and content blocks. Assign a label to each item (filename, provided label, or auto-generated index). Report the total item count to the user before proceeding and confirm if the set is larger than 25 items (to set expectations on processing time).
3. **Evaluate each content item**: For each item in the set, run `python scripts/eval-runner.py --brand {slug} --action run-quick --text "{content_or_path}" --content-type "{type}"` (or `--action run-full` if the user requested comprehensive depth). Pass `--evidence "{evidence_path}"` if an evidence file was provided. Collect the per-dimension scores (clarity, persuasion, brand alignment, readability, compliance, engagement potential) and composite score for each item.
4. **Log each evaluation**: For every evaluated item, run `python scripts/quality-tracker.py --brand {slug} --action log-eval --content-type "{type}" --data '{"label": "{label}", "scores": {scores_json}, "suite_id": "{suite_run_id}"}'` to persist results for longitudinal tracking. The suite-id groups all items from this batch together.
5. **Aggregate results**: Compute portfolio-level statistics:
   - Average composite score across all items
   - Score distribution — count of items in each grade band (90+: Excellent, 80-89: Strong, 70-79: Good, 60-69: Needs Work, <60: Auto-reject)
   - Per-dimension portfolio averages — identify which quality dimensions are consistently strong or weak across the entire set
   - Standard deviation to assess consistency (high deviation means uneven quality)
6. **Rank all content pieces**: Sort items from highest to lowest composite score. Present the full ranked list with scores, grades, and content type labels.
7. **Identify common issues**: Analyze the per-dimension scores across all items to find patterns — e.g., "7 of 12 items score below 70 on compliance" or "Persuasion scores are consistently 15+ points below clarity scores." These systemic patterns indicate process or template issues rather than individual content problems.
8. **Generate prioritized revision list**: Sort items that need revision by potential impact. Prioritize items that are (a) below the auto-reject threshold, (b) high-visibility content types (landing pages, ads) with below-average scores, or (c) items where a single dimension drags down an otherwise strong composite. For each item on the revision list, specify which dimension(s) to focus on and what kind of improvement is needed.
9. **Compare against baseline** (if provided): If the user provided a previous suite run ID, retrieve both the current and baseline suite scores from the quality tracker using `python scripts/quality-tracker.py --brand {slug} --action get-summary` for each suite period. Then compute per-item and portfolio-level deltas yourself by matching items across the two runs by label/content-type and calculating score differences. Present results as improved, regressed, or unchanged per item and overall.

## Output

A structured portfolio quality assessment containing:

- **Portfolio summary**: Total piece count, average composite score, grade distribution (Excellent/Strong/Good/Needs Work/Auto-reject counts), overall portfolio grade, consistency score (based on standard deviation)
- **Ranked content list**: All items sorted best to worst — each with label, content type, composite score, grade, and a one-line quality summary
- **Top performers**: The 3 highest-scoring items with specific notes on what makes them strong — useful as internal benchmarks or templates
- **Per-dimension portfolio analysis**: Average score per dimension across the full set, identifying the strongest and weakest dimensions with specific observations (e.g., "Brand alignment averages 88 across the set — voice guidelines are being followed well. Compliance averages 62 — disclaimers and regulatory language are frequently missing.")
- **Common issues report**: Systemic patterns found across multiple items — these indicate process-level problems worth fixing at the template or brief stage rather than per-item revision
- **Prioritized revision list**: Items most in need of revision, sorted by impact, with specific guidance on which dimensions to improve and what kind of changes are needed
- **Auto-reject list**: Items scoring below the threshold with specific reasons and mandatory revision flags
- **Baseline comparison** (if applicable): Per-item deltas and portfolio-level improvement/regression metrics
- **Recommendations**: Actionable next steps — which items to revise first, which process improvements would lift the entire portfolio, and whether any content types consistently underperform (suggesting brief or template issues)

## Agents Used

- **quality-assurance** -- Evaluates each content piece across all quality dimensions, maintains scoring consistency across the batch, identifies systemic quality patterns, generates portfolio-level insights, and produces the prioritized revision recommendations
