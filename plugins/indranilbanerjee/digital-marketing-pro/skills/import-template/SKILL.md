---
name: import-template
description: "Import deliverable templates. Use when: adding proposal formats, report structures, or brief templates."
---

# /digital-marketing-pro:import-template

## Purpose

Import deliverable templates that define the output format for plugin commands. Templates specify section structure, content requirements, and formatting rules for proposals, reports, briefs, presentations, and other marketing deliverables.

When a command like `/digital-marketing-pro:performance-report` runs, it checks for a custom template first. If one exists, the output follows the template format instead of the default.

## Input Required

The user provides:

- **Template content**: Pasted template structure, section headings, or format specifications
- **Template name**: What this template is for (e.g., "proposal", "performance-report", "content-brief", "campaign-plan")
- **Description** (optional): When to use this template

If the user doesn't provide a name, infer it from the content structure.

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for existing guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.

2. **Analyze the template structure**:
   - Identify section headings and hierarchy
   - Note content requirements per section (length, data points, format)
   - Identify placeholder markers for dynamic content
   - Detect format preferences (bullet vs. narrative, data-heavy vs. summary)

3. **Structure into a reusable template**:
   - Preserve all section headings and ordering
   - Add content guidance comments (what goes in each section)
   - Mark which sections are required vs. optional
   - Include format notes (max length, style requirements)
   - Add placeholder syntax: `{{variable_name}}` for dynamic content

4. **Map to commands** — Identify which plugin commands should use this template:
   - Template named "performance-report" → `/digital-marketing-pro:performance-report`
   - Template named "proposal" → campaign plan outputs
   - Template named "content-brief" → `/digital-marketing-pro:content-brief`
   - Custom templates can be referenced by any module

5. **Check for existing templates** — If a template with this name already exists:
   - Show the current template
   - Ask: replace (overwrite) or keep both (rename new one)

6. **Save the template**:
   - Save using `guidelines-manager.py --brand {slug} --action save-template --name {name}`
   - Or write directly to `~/.claude-marketing/brands/{slug}/templates/{name}.md`
   - Update the template manifest with name and description

7. **Confirm and explain usage**:
   - Show which commands will use this template
   - Explain that the template applies to this brand only
   - Note: agency-wide templates can be duplicated across brands

## Output

- Confirmation with template name and section count
- Preview of the structured template
- List of commands that will use this template
- Suggestion: "Next time you run `/digital-marketing-pro:{matching-command}`, the output will follow this template format."

## Examples

**User**: "Our monthly performance reports should have these sections: Executive Summary (3 bullet max), Channel Performance (table with MTD vs target), Campaign Highlights (top 3 campaigns), Issues & Risks, Recommendations, Next Month Plan"

**Result**: Saves to `~/.claude-marketing/brands/{slug}/templates/performance-report.md`:
```markdown
# Monthly Performance Report Template

## Executive Summary
<!-- Max 3 bullet points summarizing overall performance -->
- {{headline_metric_1}}
- {{headline_metric_2}}
- {{headline_metric_3}}

## Channel Performance
<!-- Table format: Channel | MTD Actual | Target | Variance | Status -->
| Channel | MTD Actual | Target | Variance | Status |
|---------|-----------|--------|----------|--------|
| {{channel_rows}} |

## Campaign Highlights
<!-- Top 3 performing campaigns with key metrics -->
### 1. {{top_campaign_1}}
- Objective: {{objective}}
- Results: {{key_metrics}}
- Insight: {{learning}}

### 2. {{top_campaign_2}}
### 3. {{top_campaign_3}}

## Issues & Risks
<!-- Current issues affecting performance and upcoming risks -->
- {{issues_list}}

## Recommendations
<!-- Actionable recommendations based on data -->
- {{recommendations_list}}

## Next Month Plan
<!-- Planned activities, launches, and focus areas -->
- {{next_month_plan}}
```

**User**: "Our proposals always follow this format: Cover page with client name and date, Situation Analysis, Objectives, Strategy, Tactical Plan by Channel, Budget Breakdown, Timeline, Team, Terms"

**Result**: Saves to `~/.claude-marketing/brands/{slug}/templates/proposal.md`:
```markdown
# Client Proposal Template

## Cover
- Client: {{client_name}}
- Date: {{date}}
- Prepared by: {{agency_name}}

## 1. Situation Analysis
<!-- Current state, market context, challenges, opportunities -->
<!-- Length: 1-2 pages -->

## 2. Objectives
<!-- SMART goals aligned to client business KPIs -->
<!-- Format: numbered list with metrics -->

## 3. Strategy
<!-- Strategic approach, positioning, target audiences -->
<!-- Include: audience segments, messaging angle, competitive positioning -->

## 4. Tactical Plan by Channel
<!-- Detailed activities per channel -->
<!-- Format: subsection per channel with activities, frequency, content types -->

## 5. Budget Breakdown
<!-- Table format: Channel | Monthly | Quarterly | Annual | % of Total -->

## 6. Timeline
<!-- Gantt-style phases or month-by-month milestones -->
<!-- Mark: setup, launch, optimization, reporting checkpoints -->

## 7. Team
<!-- Team members, roles, contact information, availability -->

## 8. Terms
<!-- Payment terms, contract duration, deliverables, SLAs -->
```

## Reference Files

- `skills/context-engine/guidelines-framework.md` — How templates integrate with the guideline system
- `scripts/guidelines-manager.py` — CLI for template CRUD operations (--action list-templates, save-template, get-template)
