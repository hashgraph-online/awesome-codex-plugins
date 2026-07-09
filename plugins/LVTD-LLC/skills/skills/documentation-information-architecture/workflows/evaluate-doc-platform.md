# Evaluate Doc Platform Workflow

Evaluate documentation tools or delivery platforms from user, author, maintenance, and migration requirements.

## When To Use

- Choosing a documentation platform or authoring tool.
- Planning a docs migration.
- Deciding whether a tool change will solve findability, reuse, versioning, feedback, or publishing problems.
- Comparing wiki, static site, docs-as-code, CMS, DITA, API-doc, or custom platform options.

## Prerequisites

- Current docs pain points, desired reader experience, authoring workflow, or platform options.
- Existing content inventory or migration constraints when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Define Outcomes

**Goal**: Start from experience and requirements.

- [ ] State the reader experience the platform must support.
- [ ] State the authoring, review, publishing, and maintenance experience writers need.
- [ ] Identify business constraints: budget, staffing, localization, compliance, support, and release cadence.

### Step 2: Separate Tool Problems From Process Problems

**Goal**: Avoid migrating for the wrong reason.

- [ ] Identify whether pain comes from IA, ownership, review, stale content, metadata, tooling, or platform support.
- [ ] List process fixes that should happen before or alongside platform work.
- [ ] Decide whether the tool change is necessary, helpful, premature, or unrelated.

### Step 3: Build Requirement Categories

**Goal**: Make comparison defensible.

- [ ] Define reader usability requirements: search, navigation, accessibility, responsive layout, feedback, offline/PDF needs.
- [ ] Define content requirements: reuse, versioning, localization, media, metadata, API generation, structured authoring.
- [ ] Define integration requirements: source control, issue tracking, product links, analytics, authentication, build and deploy.
- [ ] Define maintenance requirements: redirects, link checks, owners, review workflow, freshness checks, branch strategy.
- [ ] Define migration and portability requirements.

### Step 4: Compare Options

**Goal**: Evaluate tradeoffs without feature excitement.

- [ ] Score each option against requirements.
- [ ] Identify training, customization, support, and maintenance burden.
- [ ] Identify lock-in and export risk.
- [ ] Identify what content redesign or cleanup the migration would force.

### Step 5: Recommend A Path

**Goal**: Produce an actionable decision.

- [ ] Recommend tool, no-change, pilot, or process-first path.
- [ ] List assumptions and unknowns.
- [ ] Define pilot content, success measures, owner, timeline, and rollback or exit plan.

## Exit Criteria

- [ ] Recommendation is based on prioritized requirements.
- [ ] Process problems are not disguised as tooling problems.
- [ ] Migration, maintenance, support, and portability risks are explicit.
