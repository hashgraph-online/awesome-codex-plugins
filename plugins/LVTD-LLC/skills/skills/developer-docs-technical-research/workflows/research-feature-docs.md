# Research Feature Docs Workflow

Research a product feature before planning or writing developer documentation.

## When To Use

- Feature facts are spread across code, tickets, specs, prototypes, and conversations.
- Implementation details need user-facing meaning.
- Defaults, limits, prerequisites, permissions, errors, risks, or examples are unclear.
- A writer needs traceable research notes before planning, drafting, or review.

## Prerequisites

- Feature name, product area, ticket, spec, code pointer, prototype, API, UI, or existing docs.
- Access to SMEs, test environment, issue tracker, or product artifacts when available.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Frame The Research Brief

**Goal**: Define what the research must answer.

- [ ] State audience, feature, release context, and documentation decision.
- [ ] Identify what could go wrong if the docs are wrong or incomplete.
- [ ] List the facts that must be verified before drafting or publishing.

### Step 2: Inventory Sources

**Goal**: Build a source-of-truth map before asking questions.

- [ ] Collect code, schemas, tests, specs, tickets, designs, existing docs, and release artifacts.
- [ ] Identify SMEs for behavior, product goals, QA coverage, support issues, and field usage.
- [ ] Mark each source as authoritative, supporting, stale, incomplete, or unknown.

### Step 3: Try Or Trace The Product

**Goal**: Verify what can be observed directly.

- [ ] Run the UI, CLI, API, SDK, workflow, prototype, or test path when feasible.
- [ ] Record prerequisites, labels, defaults, outputs, events, errors, and recovery paths.
- [ ] Try common mistakes and note whether the product prevents, explains, or exposes them.

### Step 4: Interview Targeted Sources

**Goal**: Fill meaning, constraints, and user consequences.

- [ ] Ask engineers about behavior, limits, edge cases, implementation constraints, and defects.
- [ ] Ask PMs about user goals, launch scope, tradeoffs, and audience.
- [ ] Ask QA, support, field, or customers about likely failures and real usage language.
- [ ] Convert verbal answers into written notes, ticket comments, or review requests.

### Step 5: Resolve Consequences

**Goal**: Decide what belongs in documentation and what belongs elsewhere.

- [ ] Separate verified facts, assumptions, contradictions, and unsupported paths.
- [ ] Identify user-facing consequences for security, performance, billing, data, permissions, and availability.
- [ ] File product or UX defects when a confusing behavior should be fixed instead of documented around.
- [ ] Assign owner and due date to every open question that blocks docs.

### Step 6: Produce Research Notes

**Goal**: Make planning and drafting safe to start.

- [ ] Summarize the reader problem and doc action.
- [ ] List verified facts with sources.
- [ ] List unresolved questions, contradictions, and review needs.
- [ ] Recommend next step: plan, draft, defer, file issue, or request technical review.

## Quick Checklist

```text
[ ] Research brief states doc decision and risk
[ ] Source map identifies authoritative owners or artifacts
[ ] Hands-on or trace validation completed where feasible
[ ] SMEs answered targeted user-consequence questions
[ ] Open questions have owners and due dates
[ ] Research notes separate fact, inference, and recommendation
```

## Exit Criteria

Research is complete when:

- [ ] The writer can explain what the reader needs to know and why.
- [ ] Critical facts have traceable sources.
- [ ] Publication-blocking questions are visible and owned.
- [ ] The next docs action is clear.
