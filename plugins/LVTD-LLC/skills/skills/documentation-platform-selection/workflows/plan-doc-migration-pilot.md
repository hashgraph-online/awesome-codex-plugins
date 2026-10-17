# Plan Doc Migration Pilot Workflow

Plan a documentation platform pilot or migration without losing URLs, metadata, workflow, or reader paths.

## When To Use

- A team needs proof before committing to a platform migration.
- A migration is likely but scope, risk, ownership, or rollback is unclear.
- Existing content has redirects, metadata, generated refs, reusable content, media, or search behavior to preserve.
- The team needs to validate writer workflow and reader experience with real content.

## Prerequisites

- Candidate platform or shortlist.
- Content inventory, representative content set, current URL patterns, author workflow, and known constraints when available.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Select Representative Content

**Goal**: Pilot with content that exposes real platform risk.

- [ ] Include at least one concept, how-to, reference, release note, and media-heavy or generated page when relevant.
- [ ] Include content with existing URLs, redirects, metadata, links, and ownership.
- [ ] Include content that represents hard cases, not only polished easy pages.

### Step 2: Define Success Measures

**Goal**: Know what the pilot must prove.

- [ ] Define reader measures: findability, search, navigation, accessibility, mobile, feedback, and stable URLs.
- [ ] Define author measures: edit, review, preview, publish, rollback, link check, and ownership workflow.
- [ ] Define migration measures: content fidelity, metadata preservation, redirects, assets, and search behavior.
- [ ] Define support measures: who can fix build, theme, search, auth, and deploy failures.

### Step 3: Run Migration Trial

**Goal**: Test content, workflow, and support burden together.

- [ ] Migrate pilot content with metadata, assets, links, and redirects.
- [ ] Run the authoring and review workflow end to end.
- [ ] Validate search, navigation, accessibility, URL behavior, and analytics setup.
- [ ] Record manual cleanup, conversion loss, broken links, and customization work.

### Step 4: Decide Rollout Shape

**Goal**: Turn pilot evidence into a practical migration plan.

- [ ] Decide whether to proceed, pause for process fixes, change tools, or reject.
- [ ] Define migration phases, content freeze rules, redirect mapping, and rollback plan.
- [ ] Assign owners for platform, content cleanup, redirects, search, build, and communications.
- [ ] Plan writer training and reviewer onboarding.

### Step 5: Preserve Decision Record

**Goal**: Leave a useful artifact for future maintainers.

- [ ] Record chosen platform, rejected options, accepted tradeoffs, and unresolved risks.
- [ ] Store requirement matrix, pilot results, redirect strategy, support ownership, and review triggers.
- [ ] Link related IA, release, and maintenance plans.

## Common Mistakes

| Mistake | Why It Hurts | Do Instead |
|---------|--------------|------------|
| Piloting with easy content only | Hides migration and workflow risk | Use representative hard cases |
| Treating visual parity as success | Ignores URLs, search, metadata, and author workflow | Define reader, author, migration, and support measures |
| Migrating before cleanup decisions | Carries stale content into a new system | Inventory and label keep, remove, merge, split, move, review |
| No rollback or exit plan | Locks the team into a weak pilot | Define stop conditions and rollback |

## Exit Criteria

- [ ] Pilot evidence supports a clear proceed, pause, change, or reject decision.
- [ ] Migration risks are known and owned.
- [ ] URL, metadata, search, author workflow, and support plans are explicit.
