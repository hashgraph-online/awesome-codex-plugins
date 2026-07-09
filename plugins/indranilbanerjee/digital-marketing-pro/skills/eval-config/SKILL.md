---
name: eval-config
description: "Configure content eval settings. Use when: adjusting score thresholds, dimension weights, or auto-reject rules."
---

# /digital-marketing-pro:eval-config

## Purpose

Configure the evaluation system for a brand. Set minimum quality thresholds per dimension, adjust scoring weights based on industry priorities and content strategy, configure auto-reject thresholds that prevent substandard content from passing evaluation, and define content-type-specific quality standards that apply different bars to different formats.

The eval config determines how strictly content is scored and what the quality bar looks like for the brand. A healthcare company may weight hallucination risk and claim verification heavily while relaxing readability thresholds for technical audiences. A consumer brand may prioritize brand voice and readability while accepting lighter claim verification for awareness content. An agency managing multiple brands can set different configs per brand. This command makes those trade-offs explicit and adjustable rather than buried in defaults.

## Input Required

The user must provide (or will be prompted for):

- **Configuration action**: What to do — `view` (show current settings via `get-config`), `set-threshold` (change a minimum score for a dimension; add `--content-type` to scope the override to one content type), `set-weights` (change dimension weight distribution; add `--content-type` for a per-type override), `set-auto-reject` (change the composite score below which content automatically fails), `recommend` (analysis only — get industry-appropriate settings suggestions), or `reset` (restore all settings to defaults). There is no separate `set-content-type` action — content-type overrides are applied by passing `--content-type` to `set-threshold` / `set-weights`.
- **Dimension name** (for set-threshold): The dimension to configure — `content_quality`, `brand_voice`, `hallucination_risk`, `claim_verification`, `output_structure`, `readability`, or `composite`
- **Threshold value** (for set-threshold): The minimum acceptable score (0-100) for the specified dimension. Content scoring below this threshold on any dimension is flagged as a failure on that dimension
- **Weights** (for set-weights): A JSON object mapping dimension names to their weights — e.g., `{"content_quality": 0.25, "brand_voice": 0.20, "hallucination_risk": 0.20, "claim_verification": 0.15, "output_structure": 0.10, "readability": 0.10}`. Weights must sum to approximately 1.0 (tolerance of +/- 0.02 for rounding)
- **Auto-reject score** (for set-auto-reject): The composite score below which content automatically fails regardless of individual dimension scores — typically 40-60 depending on brand standards
- **Content type** (for set-content-type): The content type to configure overrides for, plus the overrides themselves — custom thresholds or weights that apply only to that content type

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply industry context for recommendation generation — different industries have different quality priorities. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, note any quality requirements defined in guidelines that should inform threshold recommendations. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Get current configuration**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action get-config` to retrieve all current settings — global thresholds, dimension weights, auto-reject threshold, and any content-type-specific overrides. Identify which settings are custom (set by the user) and which are defaults.
3. **Present current settings**: Display all configuration in a clear, readable format:
   - **Global thresholds**: Each dimension's minimum score with its current value and whether it is custom or default
   - **Dimension weights**: Each dimension's weight in the composite score calculation, shown as both decimal and percentage, with a visual indicator of relative importance
   - **Auto-reject threshold**: The composite score floor with its current value
   - **Content-type overrides**: Any content types with custom settings, showing how they differ from the global config
   - **Effective scoring example**: Show what a hypothetical evaluation would look like under the current config — e.g., "With these weights, a piece scoring 90 on content quality but 50 on hallucination risk would get a composite of X"
4. **Process configuration changes**: Based on the requested action:
   - **set-threshold**: Validate the threshold value is between 0 and 100. Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action set-threshold --dimension {dimension} --threshold {value}` (add `--content-type {type}` to scope it to one content type). Show before/after comparison with the impact on scoring strictness
   - **set-weights**: Validate all weights are between 0 and 1 and sum to approximately 1.0. If they do not sum correctly, show the discrepancy and offer to normalize. Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action set-weights --weights '{weights_json}'`. Show before/after comparison with an example of how the same content would score differently under old vs. new weights
   - **set-auto-reject**: Validate the score is between 0 and 100. Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action set-auto-reject --threshold {score}`. Show the impact — how many of the brand's recent evaluations would have been auto-rejected under the new threshold vs. the old one
   - **content-type override** (no standalone action): apply a per-type threshold or weight by adding `--content-type {content_type}` to `set-threshold` or `set-weights` — e.g. `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action set-threshold --dimension hallucination_risk --threshold 80 --content-type ad_copy`. Show how this content type's effective config now differs from the global config
   - **recommend**: Analyze the brand's industry, audience, content strategy, and compliance requirements to suggest appropriate settings. Reference `skills/context-engine/eval-framework-guide.md` for industry-specific recommendations. Present suggestions with rationale — e.g., "Healthcare brands should weight hallucination risk at 0.25+ because unverified health claims carry regulatory risk"
   - **reset**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-config-manager.py" --brand {slug} --action reset`. Show what changes from the current custom config back to defaults and confirm before executing
5. **Validate configuration integrity**: After any change, verify the configuration is internally consistent:
   - Weights sum to approximately 1.0
   - No threshold is set higher than 100 or lower than 0
   - Auto-reject threshold is lower than the average of dimension thresholds (otherwise almost everything would auto-reject)
   - Content-type overrides do not create impossible scoring scenarios
   - If any validation fails, explain the issue and suggest a correction
6. **Show before/after comparison**: For every configuration change, display a clear side-by-side of old settings vs. new settings, with a concrete example showing how the scoring behavior changes — "Under the old config, [example content] scored 72 (C). Under the new config, it would score 68 (D+) because hallucination risk is now weighted more heavily."
7. **Recommend related adjustments**: If the user changes one setting, suggest related changes that may make sense — e.g., if they raise the hallucination threshold, suggest also raising the claim verification threshold since the two dimensions are related. These are suggestions only, not automatic changes.

## Output

A structured configuration report containing:

- **Current config display**: All thresholds, weights, auto-reject threshold, and content-type overrides in a clear table format — with custom vs. default labels and the last-modified date for each custom setting
- **Before/after comparison** (if a change was made): Side-by-side table showing old and new values, with the specific changes highlighted. Includes a scoring impact example showing how the same content would score differently
- **Historical impact analysis** (if change was made): How many of the brand's recent evaluations (last 30 days) would have had a different outcome (pass/fail/review) under the new config — quantifying the practical impact of the change
- **Industry recommendation** (if requested or relevant): Suggested settings for the brand's industry with rationale for each recommendation, referencing specific quality risks and priorities. Includes a comparison of current settings vs. recommended settings
- **Configuration validation**: Confirmation that the config is internally consistent — weights sum correctly, thresholds are within valid ranges, no conflicting rules. If any issues are detected, they are flagged with suggested corrections
- **Effective scoring reference**: A quick-reference table showing the effective config for each content type — global settings plus any content-type overrides — so the user can see at a glance what quality bar applies where
- **Next steps**: Suggestions for what to do after configuration — run /digital-marketing-pro:eval-content on a sample piece to see the new config in action, run /digital-marketing-pro:quality-report to see how historical evaluations map to the new standards, or configure additional content-type overrides

## Agents Used

- **quality-assurance** — Eval configuration retrieval and modification via eval-config-manager.py, configuration validation (weight normalization, threshold range checks, consistency verification), before/after impact analysis against historical evaluation data, industry-appropriate setting recommendations referencing eval-framework-guide.md, and content-type-specific override management
