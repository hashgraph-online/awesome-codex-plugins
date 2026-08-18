# Developer Docs Technical Research Knowledge

Technical research turns uncertain product behavior into evidence that a writer can use safely.

Source basis: *The Product Is Docs*, Chapter 13, "Research for Technical Writers," Chapter 16, "Technical Verification," Chapter 19, "Working with Engineers," and Chapter 22, "Working with Product Management."

## Key Concepts

### Research Brief

**Definition**: A short statement of what the docs must prove or explain.

The brief keeps research from becoming general product exploration. It names the audience, feature, doc decision, risk, and deadline.

### Source-Of-Truth Map

**Definition**: A record of which artifact or person owns each important fact.

Good source maps separate durable sources such as code, schemas, specs, tests, tickets, analytics, and release plans from temporary answers given in conversation.

### Hands-On Validation

**Definition**: Directly trying the product path, API call, UI, CLI, test environment, or prototype to observe behavior.

Hands-on validation catches missing prerequisites, mismatched UI labels, unclear errors, and unsupported edge cases that interviews often miss.

### SME Interview

**Definition**: A targeted conversation with a subject matter expert to clarify meaning, consequences, constraints, or unresolved facts.

Engineers often know behavior and implementation tradeoffs. PMs know user goals and launch decisions. QA, support, field, and customers reveal failure modes and real usage.

### Doc-Ready Uncertainty

**Definition**: An unresolved question that is visible, owned, and bounded enough that planning can continue.

Uncertainty becomes dangerous when it is hidden inside draft text. Track owner, due date, decision needed, and fallback.

## Source Types

| Source | Best For | Risk |
|--------|----------|------|
| Code, schema, generated reference | Actual behavior and names | May omit user purpose or edge-case meaning |
| Specs and design docs | Intended behavior and rationale | May be stale or aspirational |
| Product UI, CLI, API, prototype | Observed user path | May require access or may not represent final release |
| Engineers | Constraints, implementation, limits, defects | May focus on internals over user consequences |
| Product management | user goals, tradeoffs, scope, release timing | May not know exact behavior |
| QA | tested behavior, known risks, reproducible failures | May focus on test cases rather than docs path |
| Support and field teams | recurring confusion and customer language | May reflect old behavior or isolated accounts |
| Existing docs | continuity, terminology, migration impact | May already be wrong |

## Core Rules

1. **Start with the documentation decision** - Know what the research must enable.
2. **Map sources before asking questions** - Avoid treating the loudest source as the authoritative one.
3. **Verify hands-on when feasible** - Observed behavior is essential for procedures, examples, screenshots, UI labels, and errors.
4. **Ask for consequences** - For every implementation detail, ask what the reader can do, decide, risk, or misunderstand.
5. **Separate fact from interpretation** - Record what is verified, what is inferred, and what is recommended.
6. **Use the right SME for the question** - Engineers, PMs, QA, support, and field teams answer different kinds of questions.
7. **Keep written notes** - Verbal answers should become traceable research notes, ticket comments, or review requests.
8. **Name owners for open questions** - Unowned questions become draft risk.
9. **Escalate contradictions early** - Conflicting answers are product or communication signals, not just writing problems.
10. **File product defects for avoidable confusion** - Do not normalize bad UX by documenting around it without flagging it.
11. **Protect release timing** - Mark what must be resolved before publication and what can be handled in follow-up.
12. **Avoid copying source prose** - Transform research into reader-centered documentation.

## Question Bank

| Area | Ask |
|------|-----|
| User goal | What task, decision, or problem does this feature support? |
| Audience | Who is expected to use it, and who should not? |
| Prerequisites | What account, role, version, plan, environment, or setup is required? |
| Behavior | What happens by default, at limits, and when inputs are invalid? |
| Permissions | Who can configure, run, view, delete, or recover it? |
| Risks | Can this affect security, billing, data integrity, performance, or availability? |
| Observability | What output, log, event, UI state, or API response proves success or failure? |
| Change impact | What existing docs, examples, screenshots, or release notes are affected? |
| Support | What do users already misunderstand or ask about? |
| Ownership | Which artifact or person is authoritative after release? |

## Evidence Ledger Pattern

```text
Fact: Workspace admins can replay failed notification deliveries for 7 days
Source: Admin API handler + PM launch ticket + QA replay test
Observed: Replay succeeds in staging for failed delivery ID 1842
User consequence: Docs need permission prerequisite and retention warning
Open question: Final UI label for replay button
Owner: Notifications PM, due before release candidate
Docs action: Add to admin how-to and support runbook
```

## Common Misconceptions

- **Myth**: A feature spec is enough research.
  **Reality**: Specs often explain intended implementation; docs need verified user paths and consequences.
- **Myth**: Technical research means asking an engineer how it works.
  **Reality**: Accurate docs often require code, product, PM, QA, support, and hands-on evidence.
- **Myth**: A confusing behavior should always be documented.
  **Reality**: If confusion is avoidable, file a product issue and document only the supported path.
- **Myth**: Unresolved questions can stay in private notes.
  **Reality**: Publication risk needs named owners and visible follow-up.

## Red Flags

- The draft contains claims with no source owner.
- SMEs disagree and the disagreement is not tracked.
- The writer cannot perform or trace the documented path.
- Errors, limits, permissions, or billing effects are unknown.
- The docs describe implementation details that have no reader consequence.
- A workaround exists only because the product path is unclear.
- Research notes do not identify what is verified versus assumed.

## Output Patterns

### Research Brief

```text
Question: Can customers safely rotate webhook secrets without downtime?
Audience: Backend engineer maintaining production webhooks
Decision needed: How-to guide, release note, or API reference update?
Risk: Incorrect sequence could break event delivery
Sources to check: API schema, settings UI, engineer, QA test, support tickets
```

### Open Question

```text
Question: Does rotation invalidate old signatures immediately or after grace period?
Why it matters: Affects warning, procedure order, and rollback guidance
Current evidence: Spec says immediate, engineer says 24-hour grace period
Owner: Webhooks tech lead
Due: Before docs technical review
```
