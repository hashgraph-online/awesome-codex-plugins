# Define Docs Done Workflow

Add documentation checks to definition of done, release readiness, or acceptance criteria.

## When To Use

- User-facing changes ship without docs impact assessment.
- Definition of done says "docs updated" but has no concrete checks.
- Release readiness omits docs, release notes, support enablement, or technical review.
- A team needs a lightweight, repeatable docs gate.

## Prerequisites

- Team definition of done, release checklist, acceptance criteria, or Agile board configuration.
- Typical change types, release cadence, reviewer roles, and documentation ownership.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Classify Change Types

**Goal**: Avoid one-size-fits-all docs gates.

- [ ] List common work types: bug fix, UI change, API change, new feature, migration, deprecation, internal service change, support workflow.
- [ ] Identify which work types require public docs, release notes, code samples, support docs, or internal runbooks.
- [ ] Define what "no docs needed" means and who approves it.

### Step 2: Draft Docs Done Checks

**Goal**: Create concrete, usable criteria.

- [ ] Add docs impact assessed.
- [ ] Add public docs updated or no-docs decision recorded.
- [ ] Add release note when users need awareness or action.
- [ ] Add technical, QA, product, security, legal, or support review based on risk.
- [ ] Add owner and maintenance trigger for lasting content.

### Step 3: Attach Checks To Workflow

**Goal**: Put the criteria where the team will use them.

- [ ] Add checklist fields, story template items, acceptance criteria, release checklist items, or board automation.
- [ ] Link docs tasks to feature work.
- [ ] Define who updates status and who resolves blockers.

### Step 4: Test Against Recent Work

**Goal**: Make sure the checks catch real issues without creating noise.

- [ ] Apply the draft checks to three recent or upcoming stories.
- [ ] Remove criteria that do not affect release readiness.
- [ ] Add missing criteria exposed by support, QA, or review misses.

### Step 5: Inspect After Release

**Goal**: Keep the definition useful.

- [ ] Review support tickets, customer feedback, stale pages, late reviews, and missed release notes.
- [ ] Adjust checks and ownership in retrospective or release review.
- [ ] Preserve examples of good docs-linked stories for future teams.

## Quick Checklist

```text
[ ] Change types classified
[ ] Docs impact assessment defined
[ ] Concrete docs done checks drafted
[ ] Checks added to board, template, or release gate
[ ] Recent work tested against checks
[ ] Retrospective signals planned
```

## Exit Criteria

- [ ] Definition of done makes docs impact visible without requiring docs for irrelevant changes.
- [ ] Review, release notes, support enablement, and maintenance are covered when relevant.
- [ ] The team knows who owns each check.
