# Refresh Existing Docs Workflow

Refresh stale or evolving developer documentation without creating brittle patches.

## When To Use

- Product behavior, terminology, deployment type, permissions, or audience has changed.
- User feedback, support trends, or analytics show confusion in existing docs.
- A topic has accumulated patch additions across releases.
- A small change may affect related topics, examples, screenshots, links, or warnings.
- A major maintenance update needs planning before editing.

## Prerequisites

- Existing doc or doc set.
- Change description, feedback, support issue, product update, terminology change, or stale-content list.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Identify The Trigger

**Goal**: Know why the doc needs maintenance.

- [ ] Classify the trigger: product evolution, user feedback, audience change, terminology change, style change, tooling change, error, or atrophy.
- [ ] Identify affected users and the task or decision at risk.
- [ ] Note release timing or urgency.

### Step 2: Assess Scope

**Goal**: Decide whether to patch, restructure, or plan a larger refresh.

- [ ] Check whether the current topic still has a clear audience, learning objective, starting point, and destination.
- [ ] Decide whether the change is local, multi-topic, or structural.
- [ ] Identify whether new use cases, scenarios, prerequisites, or permissions changed the reader path.
- [ ] Choose patch, restructure, split, merge, or doc-plan follow-up.

### Step 3: Audit Dependencies

**Goal**: Find related content before editing one page.

- [ ] Search for changed terms, setting names, screenshots, examples, warnings, and links.
- [ ] Check related setup, reference, troubleshooting, release, and migration docs.
- [ ] Ask related docs owners about affected content when needed.
- [ ] Record update actions for each dependent page.

### Step 4: Plan And Apply Updates

**Goal**: Make the refresh stable for users.

- [ ] Update the main content path first.
- [ ] Remove obsolete patches, duplicate explanations, and stale links.
- [ ] Add or update prerequisites, examples, screenshots, warnings, and related links.
- [ ] For large refreshes, use a draft branch, sandbox, or staged rollout when available.

### Step 5: Review And Maintain

**Goal**: Prevent the same drift from recurring.

- [ ] Route technical, product, editorial, and support review by risk.
- [ ] Add owner, source of truth, last-reviewed date, and future trigger where the repo supports metadata.
- [ ] Add release-note, redirect, or announcement work if users need to notice the change.

## Exit Criteria

- [ ] The refreshed docs match the current product, audience, and user goal.
- [ ] Related docs and links have been audited.
- [ ] Ownership and future maintenance triggers are recorded.
