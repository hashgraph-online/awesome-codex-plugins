# Edit Developer Doc Workflow

Run a structured edit or review of developer documentation.

## When To Use

- Preparing a doc for release.
- Reviewing a draft for accuracy, completeness, structure, clarity, and brevity.
- Integrating reviewer feedback.

## Prerequisites

- Draft or existing documentation.
- Audience, doc goal, source material, or release context when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Set Review Scope

**Goal**: Choose the right depth of review.

- [ ] Identify doc type, audience, and goal.
- [ ] Identify source of truth for technical claims.
- [ ] Identify high-risk areas: security, data loss, billing, production changes, migrations.
- [ ] Decide whether to return findings, edited text, or both.

### Step 2: Check Technical Accuracy

**Goal**: Find errors that break reader success.

- [ ] Verify commands, code, API details, UI labels, outputs, and links where feasible.
- [ ] Mark unverified technical claims.
- [ ] Confirm warnings for risky operations.
- [ ] Route unknown facts to technical owners.

### Step 3: Check Completeness And Structure

**Goal**: Make sure the reader can finish the task.

- [ ] Check prerequisites, versions, permissions, and environment.
- [ ] Check step order and missing transitions.
- [ ] Check expected results, troubleshooting, and next steps.
- [ ] Confirm headings and title match the reader goal.

### Step 4: Improve Clarity And Brevity

**Goal**: Remove friction without changing meaning.

- [ ] Cut duplication and irrelevant background.
- [ ] Replace vague terms with concrete product terms.
- [ ] Split long steps or paragraphs.
- [ ] Remove idioms, slang, biased wording, and unnecessary reassurance.

### Step 5: Integrate Or Request Feedback

**Goal**: Make review actionable.

- [ ] Group findings by reader risk.
- [ ] Ask reviewers specific questions.
- [ ] Resolve conflicting feedback by user need and source of truth.
- [ ] Keep unresolved assumptions visible.

## Exit Criteria

- [ ] High-risk technical claims are verified or explicitly marked.
- [ ] The doc supports its stated reader goal.
- [ ] Findings or edits are concrete enough to apply.
