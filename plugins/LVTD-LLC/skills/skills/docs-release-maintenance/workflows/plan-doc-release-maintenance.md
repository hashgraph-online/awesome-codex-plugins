# Plan Doc Release Maintenance Workflow

Plan documentation release, maintenance, deprecation, or deletion work.

## When To Use

- Preparing docs for a code or product release.
- Defining ownership and freshness checks.
- Setting up maintenance automation.
- Deprecating or deleting stale docs.

## Prerequisites

- Code/product change, release notes, issue, doc set, or stale-content list.
- Owners or source-of-truth candidates when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Analyze User Impact

**Goal**: Understand who needs the docs and when.

- [ ] Identify what changed or what content is stale.
- [ ] Identify affected users and required actions.
- [ ] Identify release date, support window, or deprecation deadline.
- [ ] List docs that need create, update, deprecate, or delete actions.

### Step 2: Build Publishing Checklist

**Goal**: Make release readiness explicit.

- [ ] Assign doc owner and final approver.
- [ ] Identify peer and technical reviewers.
- [ ] Define tests for links, samples, screenshots, generated refs, and facts.
- [ ] Confirm publish location and timing.
- [ ] Plan announcement or release notes.

### Step 3: Plan Maintenance

**Goal**: Keep docs accurate after launch.

- [ ] Assign owner or source-of-truth metadata.
- [ ] Define update triggers.
- [ ] Recommend freshness checks, link checks, linters, or generated refs.
- [ ] Note automation risks or manual handoffs.

### Step 4: Handle Deprecation Or Deletion

**Goal**: Retire content without harming users.

- [ ] Decide whether users need advance notice.
- [ ] Provide alternatives or migration guide.
- [ ] Add deprecation notice or release note when needed.
- [ ] Plan redirects, search updates, and link cleanup.
- [ ] Define deletion timing and owner approval.

### Step 5: Report Risks And Next Actions

**Goal**: Give the team an executable plan.

- [ ] List blockers and unverified facts.
- [ ] Prioritize by user impact and release timing.
- [ ] Return a checklist with owners and due dates when known.

## Exit Criteria

- [ ] Release, maintenance, or deprecation work has owner, review, and timing.
- [ ] User impact and required action are explicit.
- [ ] Removed or stale content has a safe path for users.
