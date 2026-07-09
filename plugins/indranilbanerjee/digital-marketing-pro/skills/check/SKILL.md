---
name: check
description: "Run the unified pre-publish quality gate on marketing content — hallucination detection, claim verification, brand voice scoring, structure validation. Use before publishing any marketing copy."
user-invocable: true
triggers:
  - check this content before publishing
  - run the eval suite on this draft
  - validate this marketing copy
  - pre-publish quality gate
  - hallucination check
  - dm check
  - eval my content
  - is this safe to publish
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:check — Unified Pre-Publish Quality Gate

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
| **C2PA provenance** (compliance) | `embed-c2pa.py` (presence check) | When the brand's `target_markets` include an EU/EEA jurisdiction AND an accompanying asset is AI-generated: verifies a C2PA provenance manifest is present and valid. Missing or invalid manifest → **CRITICAL / BLOCKED** (EU AI Act Article 50, applies from 2 Aug 2026) |

Plus content quality and readability scoring (always run).

## Subcommands and modes

### Default (run-quick)

```
/digital-marketing-pro:check <file-path-or-content>
```

Runs the **quick eval**: hallucination detection + content quality + readability. Fast (~2 seconds), zero external dependencies. Use this for routine checks.

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

Validates the content matches the structural requirements of the named schema. Available schemas: `blog_post`, `email`, `ad_copy`, `social_post`, `landing_page`, `press_release`, `content_brief`, `campaign_plan`. Use `--schema list` to see all schemas with their requirements.

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

## EU AI Act Article 50 — C2PA provenance gate

The check gains a compliance dimension for AI-generated assets in EU-targeted campaigns. It fires when **both** conditions hold:

1. The active (or `--brand`) profile's `target_markets` include any EU/EEA jurisdiction, **and**
2. An accompanying asset is declared AI-generated — either the file metadata says so, or the `--evidence` JSON declares `ai_generated: true` for it.

When both hold, the gate runs a C2PA manifest presence check on the asset via `embed-c2pa.py` (presence/verify mode — it does not modify the asset). A **missing or invalid C2PA provenance manifest is a CRITICAL issue → decision = BLOCKED.** Article 50 applies from **2 Aug 2026** (penalty up to EUR 15M or 3% of global turnover). To embed a compliant manifest, run `/digital-marketing-pro:c2pa-metadata`.

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
5. **Parse the JSON output.** Extract composite score, grade, dimension scores, alerts, auto-reject decision.
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

All scripts use stdlib only (except brand-voice-scorer which optionally uses nltk). No external API calls, no internet required.

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
3. Parse JSON output. Composite: 58.4, grade: D+, auto_rejected: true
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
User: /digital-marketing-pro:check "Our amazing product boosts conversion by 347% — visit example.com today!"

Skill:
1. Detect inline content (not a file path)
2. Write content to a temp file
3. Run quick eval
4. Report:
   CRITICAL: 2
     - Placeholder URL "example.com" — replace with real URL before publishing
     - Unattributed statistic "347%" — fabricated stat or missing citation
   Decision: BLOCKED
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
- `docs/architecture.md` Section 11 — eval framework architecture
