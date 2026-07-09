---
name: import-sop
description: "Import agency SOPs. Use when: adding workflow definitions, approval processes, or launch checklists."
---

# /digital-marketing-pro:import-sop

## Purpose

Import and structure agency Standard Operating Procedures (SOPs) that apply across all clients. SOPs define **how work gets done** — approval workflows, content review steps, campaign launch checklists, escalation procedures, and quality gates.

SOPs are stored at the agency level (`~/.claude-marketing/sops/`), not per-brand, so they apply consistently across all clients.

## Input Required

The user provides:

- **SOP content**: Pasted workflow steps, checklist items, or process descriptions
- **SOP name**: What this SOP covers (e.g., "content-approval", "campaign-launch", "crisis-escalation")
- **Description** (optional): Brief summary of when this SOP applies

If the user doesn't provide a name, infer it from the content.

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for existing guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.

2. **Classify the SOP type**:
   - **Content workflow**: Review, approval, and publishing steps for content
   - **Campaign checklist**: Pre-launch, launch, and post-launch verification steps
   - **Escalation procedure**: Who to contact, decision authority, response timelines
   - **Quality assurance**: Testing steps, brand compliance checks, accessibility verification
   - **Client onboarding**: Steps for setting up a new client in the system
   - **Reporting workflow**: Data collection, analysis, presentation, delivery steps

3. **Structure into actionable steps**:
   - Number each step clearly
   - Identify decision points (if/then branches)
   - Mark which steps require human approval vs. automated checks
   - Add role assignments where mentioned (who does what)
   - Include timelines/SLAs where provided
   - Flag any steps the plugin can automate vs. steps requiring human action

4. **Check for existing SOPs** — If an SOP with this name already exists:
   - Show the current SOP content
   - Ask: merge (combine steps), replace (overwrite), or cancel
   - When merging, deduplicate and maintain step order

5. **Save the SOP**:
   - Save using `guidelines-manager.py --action save-sop --name {name} --content "{content}"`
   - Or write directly to `~/.claude-marketing/sops/{name}.md`
   - Update the SOP manifest

6. **Explain integration** — Tell the user how this SOP will be applied:
   - Which commands will reference this SOP
   - Which workflow steps will be added to outputs
   - When human approval gates will be flagged

## Output

- Confirmation with SOP name and step count
- Preview of the structured SOP
- Explanation of which commands/modules will reference this SOP
- Suggestion: "This SOP will apply across all brands. To create brand-specific workflows, use guidelines instead."

## Examples

**User**: "Before publishing any content, it needs to go through: 1. Writer creates draft, 2. Editor reviews for quality, 3. Brand manager checks voice alignment, 4. Legal reviews if it contains claims, 5. Client approves, 6. Publish"

**Result**: Saves to `~/.claude-marketing/sops/content-approval.md`:
```markdown
# Content Approval Workflow

## Scope
Applies to all content before publishing across all brands/clients.

## Steps

1. **Writer creates draft**
   - Role: Content Creator
   - Plugin support: Content Engine generates draft with brand voice applied
   - Output: Draft content document

2. **Editor reviews for quality**
   - Role: Editor
   - Checklist: Grammar, clarity, structure, readability score
   - Plugin support: Content scorer provides readability metrics
   - Gate: Human approval required

3. **Brand manager checks voice alignment**
   - Role: Brand Manager
   - Checklist: Voice consistency, messaging alignment, restriction compliance
   - Plugin support: Brand voice scorer provides alignment score
   - Gate: Human approval required

4. **Legal reviews (conditional)**
   - Trigger: Content contains health claims, financial claims, testimonials, or competitor comparisons
   - Role: Legal Team
   - Gate: Human approval required

5. **Client approves**
   - Role: Client Stakeholder
   - Gate: Human approval required

6. **Publish**
   - Role: Content Creator / Social Media Manager
   - Plugin support: Platform formatting applied automatically
```

**User**: "Our agency has a crisis escalation process: minor issues go to account manager, major issues go to agency director, critical issues go to CEO within 1 hour"

**Result**: Saves to `~/.claude-marketing/sops/crisis-escalation.md`:
```markdown
# Crisis Escalation Procedure

## Severity Levels

### Minor (Severity: Low)
- **Examples**: Negative review, minor social media complaint, factual error in published content
- **Escalate to**: Account Manager
- **Response SLA**: 4 hours
- **Action**: Acknowledge, draft response, resolve

### Major (Severity: Medium)
- **Examples**: Viral negative post, media inquiry, product recall mention, multiple complaints
- **Escalate to**: Agency Director
- **Response SLA**: 1 hour
- **Action**: Pause scheduled content, draft holding statement, convene response team

### Critical (Severity: High)
- **Examples**: Legal threat, data breach, executive controversy, widespread media coverage
- **Escalate to**: CEO
- **Response SLA**: 1 hour
- **Action**: All content paused, crisis team activated, holding statement within 30 minutes
```

## Reference Files

- `skills/context-engine/guidelines-framework.md` — How SOPs integrate with the guideline system
- `scripts/guidelines-manager.py` — CLI for SOP CRUD operations (--action list-sops, save-sop, get-sop)
