# Research Feature Docs Workflow

Research a product feature before planning or writing developer documentation.

## When To Use

- Source material explains implementation but not user consequences.
- A feature has unclear defaults, limits, permissions, risks, or workflows.
- SMEs disagree or important facts are spread across code, tickets, specs, and conversations.
- The writer needs enough evidence to write accurate, useful docs.

## Prerequisites

- Feature, product area, ticket, spec, code, prototype, or existing docs.
- Access to SMEs, issue tracker, product surface, or source-of-truth material when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Scan The Territory

**Goal**: Build enough context to ask good questions.

- [ ] Read available specs, tickets, design notes, release notes, and related docs.
- [ ] Identify the audience, business case, and user problem.
- [ ] List terms, standards, dependencies, and domain assumptions that need accuracy.

### Step 2: Try Or Trace The Product

**Goal**: Verify what can be checked directly.

- [ ] Use the feature, prototype, CLI, API, UI, or test environment when feasible.
- [ ] Record prerequisites, defaults, UI labels, outputs, and errors as observed.
- [ ] Try likely mistakes and note whether the product prevents, explains, or exposes them.

### Step 3: Interview The Right Sources

**Goal**: Get meaning and consequences, not just implementation.

- [ ] Ask the responsible developer about behavior, limits, edge cases, and implementation consequences.
- [ ] Ask product management about user goals, tradeoffs, release timing, and target scenarios.
- [ ] Ask QA, support, field, or customers about likely failures and real usage.
- [ ] Use each source's effective communication mode, but preserve written notes.

### Step 4: Resolve Documentation Questions

**Goal**: Convert research into doc-ready facts.

- [ ] Identify defaults, limits, permissions, performance, security, data integrity, and support risks.
- [ ] Decide which implementation details have user-facing consequences.
- [ ] File product defects for awkward flows that should not become documentation burden.
- [ ] Mark unresolved questions with owner and due date.

### Step 5: Produce Research Notes

**Goal**: Give planning and drafting a reliable source.

- [ ] Summarize what the reader needs to know and why.
- [ ] List verified facts and source of truth.
- [ ] List assumptions, contradictions, and review needs.
- [ ] Recommend content type, scenario, or documentation decision follow-up.

## Exit Criteria

- [ ] User goal, feature behavior, risks, and source-of-truth owners are documented.
- [ ] Hands-on or cross-source verification happened where feasible.
- [ ] Open questions are assigned instead of hidden in the draft.
