# Interview Documentation Sources Workflow

Prepare and run SME conversations that produce doc-ready evidence.

## When To Use

- A writer needs facts from engineers, PMs, QA, support, field, or customers.
- Prior interviews produced vague answers or implementation-only explanations.
- The team needs a written record of answers and owners.
- Multiple SMEs disagree about behavior or scope.

## Prerequisites

- Research brief or doc question.
- Candidate source list and any relevant specs, tickets, code, product paths, or draft sections.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Choose The Right Source

**Goal**: Match the question to the source most likely to know.

- [ ] Use engineers for behavior, constraints, edge cases, implementation consequences, and source owners.
- [ ] Use PMs for user goals, launch scope, tradeoffs, audience, and roadmap limits.
- [ ] Use QA for tested behavior, reproducible failures, and verification paths.
- [ ] Use support or field teams for common questions, customer terms, and failure patterns.

### Step 2: Prepare Specific Questions

**Goal**: Avoid spending interview time on background discovery.

- [ ] Share the research brief and relevant artifacts in advance when practical.
- [ ] Convert broad questions into behavior, consequence, and source-owner questions.
- [ ] Mark which answers must be precise before docs can ship.

### Step 3: Ask For Meaning And Evidence

**Goal**: Move from explanation to doc-ready facts.

- [ ] Ask what the reader is trying to do and what decision the feature changes.
- [ ] Ask what is default, required, limited, unsupported, risky, or surprising.
- [ ] Ask how to verify success or failure.
- [ ] Ask which artifact should be treated as authoritative after release.

### Step 4: Capture And Confirm

**Goal**: Preserve the answer in a durable form.

- [ ] Record concise notes with speaker, date, context, and affected doc section.
- [ ] Repeat back the user-facing conclusion and ask the SME to correct it.
- [ ] Link notes to tickets, pull requests, docs tasks, or review comments.
- [ ] Mark assumptions and follow-up questions separately from verified facts.

### Step 5: Close The Loop

**Goal**: Turn conversation into docs action.

- [ ] Add source owners and due dates for unresolved questions.
- [ ] Request technical review for high-risk claims.
- [ ] File product defects for confusing or unsupported paths.
- [ ] Share the resulting notes or draft section with the right reviewers.

## Common Mistakes

| Mistake | Why It Hurts | Do Instead |
|---------|--------------|------------|
| Asking "how does it work?" only | Produces implementation detail without reader value | Ask what the reader can do, decide, risk, or misunderstand |
| Treating chat as the final source | Answers disappear or become stale | Capture a written note and authoritative source |
| Interviewing one role for every question | Important context is missed | Match source to question type |
| Hiding uncertainty in draft prose | Reviewers miss publication risk | Track open questions explicitly |

## Exit Criteria

- [ ] Answers are captured with source, context, and follow-up.
- [ ] User-facing consequences are clearer than before the interview.
- [ ] Open questions have owners and next actions.
