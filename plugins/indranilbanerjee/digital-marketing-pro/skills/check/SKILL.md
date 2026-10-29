---
name: check
description: "Run the scored pre-publish gate via eval-runner.py: claims, brand voice, compliance, AI tells. \"check this before we publish\""
user-invocable: true
argument-hint: "<file-or-content> [--full|--compliance] [--brand <slug>] [--evidence <path>] [--schema <name>]"
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:check — Unified Pre-Publish Quality Gate

> **Script location.** If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the scripts are in this plugin's `scripts/` folder, next to `skills/`. Run them with Python 3.10 or newer: `python`, or `python3` where `python` is not found (macOS, many Linux systems).

This skill is the canonical pre-publish gate for marketing content. It wraps the evaluation suite (`scripts/eval-runner.py`) and produces a single pass/fail decision with actionable issues.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List the brand's workspace at `~/.claude-marketing/brands/{slug}/` (or `$CLAUDE_PLUGIN_DATA/digital-marketing-pro/brands/{slug}/` when that env var is set) before opening files. On re-invocation mid-session, skip files already in context.

Use this skill **before publishing any marketing content** — blog posts, ad copy, emails, social posts, landing pages, press releases, or any branded copy.

## Why this skill exists

An earlier version shipped a global PreToolUse hook that auto-ran a hallucination + brand-compliance check on every Write/Edit operation in every project. That hook was removed because it fired globally across all plugins and projects (Slack writes, GitHub PRs, code edits — all of it), causing friction in non-marketing work.

`/digital-marketing-pro:check` replaces that automatic gate with an **explicit user-invoked gate**. The work is the same; the trigger is intentional.

## What the check evaluates

The check delegates to `scripts/eval-runner.py` (the master eval orchestrator) which calls four sibling scripts:

| Dimension | Script | What it checks |
|---|---|---|
| **Hallucination** | `hallucination-detector.py` | Unattributed statistics, placeholder URLs (example.com / your-site.com), unsupported superlatives ("best", "#1", "leading"), fabricated citations |
| **Claims** | `claim-verifier.py` (when `--evidence` provided) | Cross-checks specific claims against a user-provided evidence file |
| **Brand voice** | `brand-voice-scorer.py` (when `--brand` provided) | Scores content against the active brand's voice profile (formality, energy, humor, authority, prefer/avoid words) |
| **Structure** | `output-validator.py` (when `--schema` provided) | Validates content matches expected schema (blog_post, email, ad_copy, social_post, landing_page, press_release, content_brief, campaign_plan) |
| **C2PA provenance** (compliance) | `embed-c2pa.py` (presence check) | When the brand's `target_markets` include an EU/EEA jurisdiction AND an accompanying asset is AI-generated: verifies a C2PA provenance manifest is present and valid. Missing or invalid manifest → **CRITICAL / BLOCKED** (EU AI Act Article 50, in force since 2 August 2026) |

Plus content quality and readability scoring (always run).

## Subcommands and modes

### Default (run-quick)

```
/digital-marketing-pro:check <file-path-or-content>
```

Runs the **quick eval**: hallucination detection + content quality + readability. Fast (a few seconds). Content quality and readability need `textstat` (`python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" --install lite`); without it they are skipped, the result says `"partial": true` with `missing_dimensions`, and the grade is "incomplete" (one dimension) or at most B. Use this for routine checks.

### Full eval (run-full)

```
/digital-marketing-pro:check <file-path-or-content> --full
```

Runs all 6 dimensions: hallucination + claims (if evidence provided) + brand voice (if brand provided) + structure (if schema provided) + content quality + readability. Use before publishing anything client-facing or external.

### Compliance-focused (run-compliance)

```
/digital-marketing-pro:check <file-path-or-content> --compliance --brand <slug> [--evidence <path>] [--schema <name>]
```

Runs hallucination + claims + brand voice + structure. Best for regulated industries (healthcare, financial services, alcohol, cannabis, gambling) where claim substantiation and brand-voice fidelity matter most.

### With evidence file

```
/digital-marketing-pro:check <file-path> --evidence <evidence-file.json>
```

When the content makes specific claims you want to substantiate, provide a JSON evidence file:

```json
{
  "evidence": [
    {
      "claim": "50% increase in conversions",
      "source": "GA4 Q4 report",
      "date": "2025-12-31",
      "verified": true
    },
    {
      "claim": "Trusted by Fortune 500 companies",
      "source": "Customer roster (internal)",
      "date": "2026-04-01",
      "verified": true
    }
  ]
}
```

The check will extract every claim from the content and flag any that don't match an evidence entry.

### With schema validation

```
/digital-marketing-pro:check <file-path> --schema blog_post
```

Validates the content matches the structural requirements of the named schema. Available schemas: `blog_post`, `email`, `ad_copy`, `social_post`, `landing_page`, `press_release`, `content_brief`, `campaign_plan`. `--schema list` prints all schemas with their requirements; an unknown name stops with exit 2 and the valid list.

### With brand voice check

```
/digital-marketing-pro:check <file-path> --brand acme
```

Scores the content against the brand voice profile at `~/.claude-marketing/brands/acme/profile.json`. Reports per-dimension breakdown (formality, energy, humor, authority) plus deviation from prefer/avoid word lists.

## Output format

The check returns a unified report:

```
DM CHECK REPORT — <file or content snippet>
=============================================

Composite Score: 73.4 / 100  (Grade: B-)
Auto-Reject: NO

Dimensions:
  Hallucination ............ 96/100  PASS  (weight 0.40)
  Content Quality .......... 78/100  PASS  (weight 0.35)
  Readability .............. 65/100  PASS  (weight 0.25)

Issues Found:
  CRITICAL: None
  WARNING (2):
    - Line 14: Unattributed statistic "76% of buyers prefer..."
      Suggestion: cite source or rephrase as observation
    - Line 22: Superlative "best in class" without substantiation
      Suggestion: replace with measurable claim or proof point

Decision: PASS — safe to publish but address WARNINGs first
```

If any CRITICAL issue is found, decision = **BLOCKED** and the user is asked to fix before publishing.

### Decision rules

eval-runner.py returns the decision itself, in `decision`, with every flagged item in `issues` (dimension, severity, value, reason):

- **PASS** — no CRITICAL or WARNING issue, no dimension below its minimum, every dimension that applies ran, and the composite is at or above the brand's `auto_reject_threshold` (default 40). Exit 0.
- **WARN** — no CRITICAL issue, but at least one high or medium issue, a dimension below its minimum (`dimension_alerts`), or a dimension that failed to run (`partial`). Exit 0; the user should address it before publishing.
- **BLOCKED** — at least one CRITICAL issue (for example a placeholder URL in a call to action, or a fabricated statistic in a headline), or the composite below the auto-reject threshold. Exit 3; the content cannot publish until fixed. A missing or invalid C2PA manifest on an AI-generated asset for an EU-targeted brand (the gate below) is also CRITICAL.

The brand's thresholds, minimums and weights come from `/digital-marketing-pro:eval-config` and apply to every run. No script checks for a regulated industry's required disclaimer: review that by hand against the brand's guidelines.

## AI-tell scans (advisory section, never scored)

Alongside the eval-runner scorers, run both tell scans and report them as a single ADVISORY section of the check output:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/ai-tell-scan.py"          --file <input>   # Tier 1: surface
python "${CLAUDE_PLUGIN_ROOT}/scripts/structural-tell-scan.py"  --file <input>   # Tier 2: structure
```

- **Tier 1 (surface)** — LLM-favored vocabulary, significance markers, soft-adverb clusters, connective and participial openers, em-dash density, ungrounded one-liners. Report the overall LOW/MODERATE/HIGH rating and the flagged sentences with their suggested fix. Significance markers are reported with `"fix": "Delete this sentence; do not reword it."` — pass that through verbatim, because rewording is the wrong remedy.
- **Tier 2 (structure)** — the overall OK/NOTE/ATTENTION band plus each NOTE/ATTENTION finding with its spans (moralizing, section symmetry, parallel headings, specificity, stance, paragraph evenness, entity development). For `entity_development`, always carry through that the fix is to develop an existing specific, never to delete specifics.

**This whole section NEVER affects the PASS/WARN/BLOCKED decision.** Both scripts keep their thresholds inside themselves, deliberately outside the eval config, because these are editorial judgment calls for a human editor, not publish gates — and because a detector proxy has a real false-positive rate on genuinely human writing. (The one place a tell scan does gate is the content-engine's `humanize_passed`, and only on the two tells precise enough to gate on: `significance_marker` and `soft_adverb_cluster`. `llm_favored_word` was dropped from that set on 2026-08-15 after it was measured firing **only** on prose published before ChatGPT existed and never on model prose. That gate is a density floor — measured, it fails no published human writing and catches no unedited model prose — so never report a pass as evidence that a piece reads human.) Both scans measure visible text only; neither can see, and neither has any relationship to, any statistical watermark.

## EU AI Act Article 50 — C2PA provenance gate

The check gains a compliance dimension for AI-generated assets in EU-targeted campaigns. It fires when **both** conditions hold:

1. The active (or `--brand`) profile's `target_markets` include any EU/EEA jurisdiction, **and**
2. An accompanying asset is declared AI-generated — either the file metadata says so, or the `--evidence` JSON declares `ai_generated: true` for it.

When both hold, the gate checks the asset read-only with `python "${CLAUDE_PLUGIN_ROOT}/scripts/embed-c2pa.py" --verify <asset>`: exit 0 = manifest present and valid (a self-signed dev signer is reported as `untrusted_signer`, not failed), 6 = no manifest, 7 = manifest fails validation, 2 = c2pa-python not installed (report the dimension as SKIPPED with the printed install command; never PASS it). A **missing or invalid C2PA provenance manifest (exit 6 or 7) is a CRITICAL issue → decision = BLOCKED.** Article 50 applies from **2 Aug 2026** (penalty up to EUR 15M or 3% of global turnover). To embed a compliant manifest, run `/digital-marketing-pro:c2pa-metadata`.

If `embed-c2pa.py` is not present in the script inventory or the asset cannot be resolved, surface the dimension as SKIPPED with a warning (never silently PASS an EU AI-asset check).

## How the skill operates

The skill follows this flow:

1. **Resolve the input.** If the user passed a file path, read it. If they passed inline content, use it.
2. **Resolve options.** If `--brand` not specified, attempt to load from active brand at `~/.claude-marketing/brands/_active-brand.json`. If `--schema` not specified, infer from content type if obvious (blog markdown → `blog_post`, etc.) or skip structure check.
3. **Build the eval-runner command.** Choose action: `run-quick` (default), `run-full` (with `--full`), `run-compliance` (with `--compliance`).
4. **Execute via Bash.**
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-runner.py" --action run-quick --file <input> [--brand <slug>] [--evidence <path>] [--schema <name>]
   ```
5. **Parse the JSON output.** Read `decision` (PASS / WARN / BLOCKED; exit 3 means BLOCKED), `issues`, composite score, grade, dimension scores, `dimension_alerts`, `auto_rejected`, and `partial` with `missing_dimensions`. Never upgrade the decision the script returned.
6. **Format for the user.** Present the human-readable report shown above. Lead with the decision (PASS / WARN / BLOCKED).
7. **If BLOCKED, refuse to recommend publishing.** Always require the user to address CRITICAL issues before they proceed.

## Scripts called

- `scripts/eval-runner.py` — master orchestrator
- `scripts/hallucination-detector.py` — invoked by eval-runner
- `scripts/claim-verifier.py` — invoked by eval-runner if `--evidence` provided
- `scripts/brand-voice-scorer.py` — invoked by eval-runner if `--brand` provided
- `scripts/output-validator.py` — invoked by eval-runner if `--schema` provided
- `scripts/content-scorer.py` — invoked by eval-runner
- `scripts/readability-analyzer.py` — invoked by eval-runner
- `scripts/embed-c2pa.py` — presence/verify check for the EU AI Act Article 50 C2PA gate (only when an EU-targeted brand has an AI-generated asset)

No external API calls, no internet required. hallucination-detector, claim-verifier and output-validator are stdlib only; content-scorer and readability-analyzer need `textstat`, and brand-voice-scorer needs `nltk` (both installed by `setup.py --install lite`). A dimension whose package is missing is skipped and named in `missing_dimensions`, never scored as a pass.

## Examples

### Example 1: Quick check on a draft

```
User: /digital-marketing-pro:check drafts/q2-launch-blog.md

Skill:
1. Read drafts/q2-launch-blog.md
2. Run python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-runner.py" --action run-quick --file drafts/q2-launch-blog.md
3. Parse JSON output:
   composite_score: 81.2, grade: B+, auto_rejected: false
   hallucination: 92/100 pass, content_quality: 76/100 pass, readability: 84/100 pass
   alerts: 1 warning ("unattributed stat in line 14")
4. Format report:

DM CHECK REPORT — drafts/q2-launch-blog.md
============================================
Composite Score: 81.2 / 100  (Grade: B+)
Decision: PASS

Dimensions:
  Hallucination ......... 92/100  pass
  Content Quality ....... 76/100  pass
  Readability ........... 84/100  pass

Issues Found:
  WARNING (1):
    - Line 14: Unattributed statistic "76% of marketers say..."
      Suggestion: cite source or rephrase as observation

Decision: PASS — safe to publish; recommend addressing the WARNING first.
```

### Example 2: Full eval with brand + evidence + schema

```
User: /digital-marketing-pro:check drafts/healthcare-ad.md --full --brand healthfirst --evidence facts/q2-claims.json --schema ad_copy

Skill:
1. Read drafts/healthcare-ad.md
2. Run python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-runner.py" --action run-full --file drafts/healthcare-ad.md --brand healthfirst --evidence facts/q2-claims.json --schema ad_copy
3. Parse JSON output. Composite: 58.4, grade: C-, auto_rejected: true (the brand's auto-reject line is 60), decision: BLOCKED
4. Format report with CRITICAL issues highlighted
5. Decision: BLOCKED. Two unattributed health claims need substantiation before this can publish.
```

### Example 3: Compliance check on regulated content

```
User: /digital-marketing-pro:check drafts/financial-services-landing.md --compliance --brand finadvisor --evidence facts/finra-disclosures.json

Skill:
1. Read content
2. Run python "${CLAUDE_PLUGIN_ROOT}/scripts/eval-runner.py" --action run-compliance --file drafts/financial-services-landing.md --brand finadvisor --evidence facts/finra-disclosures.json
3. Output prioritises hallucination + claim verification + brand voice + structure
4. Returns decision with FINRA-relevant issues highlighted
```

### Example 4: Quick check on inline content

```
User: /digital-marketing-pro:check "Our product boosts conversion by 347%. Buy now at https://example.com/offer"

Skill:
1. Detect inline content (not a file path)
2. Run the quick eval with --text
3. eval-runner exits 3: "decision": "BLOCKED", one critical item in "issues"
4. Report:
   CRITICAL (1):
     - Placeholder URL "https://example.com/offer" in a call to action — replace it with the real URL before publishing
   Decision: BLOCKED
   Also ask for the source of "347%": the detector does not flag every statistic, so read the draft as well.
```

## When to use which mode

| Scenario | Recommended mode |
|---|---|
| Routine content check during drafting | `/digital-marketing-pro:check <file>` (quick) |
| Before publishing any external content | `/digital-marketing-pro:check <file> --full --brand <slug>` |
| Regulated industry content (healthcare / financial / alcohol / cannabis / gambling) | `/digital-marketing-pro:check <file> --compliance --brand <slug> --evidence <facts>` |
| Client-facing deliverable (Growth Plan, Yearly Planner, monthly report) | `/digital-marketing-pro:check <file> --full --brand <slug>` |
| Ad copy specifically | `/digital-marketing-pro:check <file> --schema ad_copy --brand <slug>` |
| Email specifically | `/digital-marketing-pro:check <file> --schema email --brand <slug>` |
| Blog post specifically | `/digital-marketing-pro:check <file> --schema blog_post --brand <slug>` |

## Behaviour rules

1. **Never report PASS if there are CRITICAL issues.** Always BLOCKED.
2. **Always report the composite score and grade.** Even if PASS, surface room for improvement.
3. **Always include actionable suggestions.** Each issue must be paired with a fix recommendation.
4. **Resolve the active brand if not specified.** Check `~/.claude-marketing/brands/_active-brand.json`. If no active brand, run without `--brand` (skip brand voice dimension).
5. **Never modify the content.** This skill only reports — the user (or the agent that produced the content) makes the fix.
6. **Surface skipped dimensions explicitly.** If the user did not provide `--evidence` or `--schema`, note that the corresponding dimensions were skipped.

## Related skills + commands

- `/digital-marketing-pro:engagement growth-plan` — produces Part 8 deliverable; should be checked with `/digital-marketing-pro:check --full --schema content_brief` before client delivery
- `/digital-marketing-pro:content-engine` — produces marketing content; recommended workflow is `/digital-marketing-pro:content-engine` → review → `/digital-marketing-pro:check` → publish
- `/digital-marketing-pro:eval-content` — legacy alias that routes to this skill

## Related references

- `scripts/eval-runner.py` — the master orchestrator this skill wraps
- `skills/context-engine/eval-framework-guide.md` — full eval framework documentation
- `skills/context-engine/eval-rubrics.md` — per-dimension scoring rubrics
- `docs/architecture.md` Section 16 (Evaluation Layer) — eval framework architecture
