---
name: sop-library
description: "Manage agency SOPs. Use when: creating, assigning, versioning, or auditing standard operating procedures."
---

# /digital-marketing-pro:sop-library

## Purpose

Manage the agency's Standard Operating Procedure library. Create SOPs from templates, assign them to specific brands, track compliance against recent executions, and maintain version control. SOPs define mandatory steps for common marketing operations — ensuring consistency, quality, and accountability across all client engagements regardless of which team member is executing the work.

## Input Required

The user must provide (or will be prompted for):

- **Action**: One of: `create`, `list`, `assign`, `check-compliance`, `update`, or `view`
- **SOP category**: The operational area — content-production, paid-media, reporting, crm, seo, social-media, email-marketing, client-management, onboarding, or general
- **Brand slug** (for assign/check-compliance): Which brand to assign the SOP to or check compliance against — must match a configured brand in `~/.claude-marketing/brands/`
- **SOP name** (for create/update/view): A descriptive name for the procedure (e.g., "Blog Post Publishing Checklist", "Monthly Reporting Workflow", "Paid Search Campaign Launch Protocol")
- **SOP content** (for create/update): The procedure steps, checklists, responsible roles, approval requirements, and quality gates — or indicate "from template" to use the category default template
- **Version notes** (for update): What changed and why — recorded in the version history log for audit trail and team communication
- **Priority level** (for create): One of:
  - Critical: Must follow for every execution — compliance failures trigger alerts to management
  - Standard: Recommended for consistency across team members
  - Advisory: Best practice guidance, not mandatory — for reference and training
- **Brand-specific overrides** (for assign): Any steps that should be modified, skipped, or added for this specific brand's requirements, industry regulations, or client preferences
- **Compliance date range** (for check-compliance): How far back to look when checking executions against the SOP — defaults to last 30 days

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Check SOP storage**: Read the SOP library at `~/.claude-marketing/sops/`. Each SOP is stored as a JSON file with metadata (name, category, version, priority, created date, last updated, author, assigned brands, steps array, checklists, and version history)
3. **For CREATE action**: Generate a new SOP from the specified category template. Include:
   - Objective statement and scope definition
   - Prerequisites and required platform access
   - Numbered procedure steps with responsible roles and time estimates per step
   - Quality checkpoints at key gates with pass/fail criteria
   - Approval requirements with escalation paths
   - Completion criteria and rollback procedure if applicable
   - Save to `~/.claude-marketing/sops/{category}/{sop-slug}.json` with version 1.0
4. **For LIST action**: Enumerate all SOPs in the library organized by category. Show name, version, priority level, last updated date, number of steps, total estimated duration, and assignment count (how many brands use this SOP). Highlight any unassigned SOPs and any with compliance rates below 80%
5. **For ASSIGN action**: Link the specified SOP to a brand by creating a reference at `~/.claude-marketing/brands/{slug}/sops/{sop-slug}.json` containing the SOP reference, assignment date, assigner, and any brand-specific overrides or additions to the standard steps
6. **For CHECK-COMPLIANCE action**: Compare the brand's recent executions (from `python "${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py" --brand {slug} --action get-history`) against the assigned SOP requirements. For each SOP step, determine pass/fail/not-applicable/skipped based on execution evidence. Calculate overall compliance percentage and identify patterns in recurring failures
7. **For UPDATE action**: Load the existing SOP, create a versioned backup (append version number to filename in `~/.claude-marketing/sops/_archive/`), apply the updates, increment version number, record change notes with author in the version history array, and flag all affected brands for re-review
8. **For VIEW action**: Display the full SOP with all steps, checklists, metadata, assigned brands list, complete version history, and aggregate compliance status summary across all assigned brands
9. **Validate SOP completeness**: For create and update actions, verify the SOP has all required sections — objective, scope, at least 5 procedure steps, responsible roles for each step, at least one approval gate, completion criteria, and estimated total duration. Flag any gaps before saving
10. **Check for conflicts**: When assigning or updating, verify the SOP does not conflict with existing assigned SOPs for the same brand and category — flag overlapping steps, contradictory requirements, or redundant procedures
11. **Generate compliance trends**: For check-compliance, compare current compliance rate against previous checks to identify improving or declining adherence patterns — flag brands with declining compliance for management attention
12. **Report results**: Present the action outcome with confirmation, any warnings (unassigned SOPs, compliance failures, conflicts detected, incomplete sections), and suggested next steps

## Output

Action-specific output:

- **For CREATE**: Complete SOP document with all sections (objective, scope, prerequisites, numbered steps with roles and time estimates, quality gates, approval requirements, completion criteria, rollback procedure), saved confirmation with file path and version number, estimated total execution time, and prompt to assign to brands
- **For LIST**: Categorized SOP library table — name, category, version, priority, step count, estimated duration, last updated, assigned brand count, and aggregate compliance rate where checked. Summary totals per category and overall library statistics
- **For ASSIGN**: Assignment confirmation with brand name, SOP name, effective date, any brand-specific overrides applied, total steps including overrides, and reminder to run compliance check after next execution cycle
- **For CHECK-COMPLIANCE**: Compliance report with per-step pass/fail/skip status, overall compliance percentage, specific failure details with execution evidence and remediation guidance, trend vs prior check (improving/stable/declining), pattern analysis for recurring failures, and prioritized corrective actions
- **For UPDATE**: Updated SOP with diff summary (what changed with before/after), new version number, version history entry with author and notes, list of affected brands flagged for re-review, and recommendation to re-run compliance checks
- **For VIEW**: Full SOP display with all steps and metadata, assigned brands list with per-brand compliance status, complete version history with change notes, aggregate compliance metrics, and last compliance check date per brand

## Agents Used

- **agency-operations** — SOP creation from category templates, compliance tracking logic, version control and archival management, assignment workflows, conflict detection, trend analysis, and library organization
- **memory-manager** — SOP file storage and retrieval, version history persistence, brand-SOP linkage management, archive maintenance, and compliance data archival
