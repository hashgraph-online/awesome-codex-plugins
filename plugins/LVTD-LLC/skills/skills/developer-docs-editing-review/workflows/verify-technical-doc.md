# Verify Technical Doc Workflow

Run technical verification for developer documentation with risky facts or procedures.

## When To Use

- Procedures can affect production, security, billing, data, availability, or migrations.
- Commands, API examples, UI labels, screenshots, outputs, or limits must be accurate.
- A doc needs SME, QA, support, product, or peer review before release.
- Reviews are missing, shallow, conflicting, or not tied to specific risks.

## Prerequisites

- Draft, procedure, sample, release doc, migration guide, or existing documentation.
- Source material, product surface, test environment, or reviewers when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Classify Verification Risk

**Goal**: Decide how much verification the doc needs.

- [ ] Identify technical claims, commands, code, UI labels, outputs, links, defaults, limits, and warnings.
- [ ] Mark high-risk areas: security, privacy, data loss, billing, production changes, migrations, or irreversible operations.
- [ ] Decide whether self-test, SME review, QA testing, or a review meeting is needed.

### Step 2: Prepare The Review

**Goal**: Help reviewers spend time on substance.

- [ ] Self-edit the draft before review.
- [ ] Send the smallest useful review unit.
- [ ] Assign required reviewers individually.
- [ ] Tell each reviewer exactly what to verify.
- [ ] Track request, deadline, and owner in the team's normal tooling when possible.

### Step 3: Verify Facts And Procedures

**Goal**: Prove the doc works or expose unresolved risk.

- [ ] Run or simulate commands and procedures where feasible.
- [ ] Ask SMEs to verify behavior, constraints, and implementation consequences.
- [ ] Ask QA to test complex, destructive, edge-case-heavy, or hard-to-set-up procedures.
- [ ] Ask support or field teams to check customer-facing failure modes.
- [ ] Record pass, fail, blocked, or not-tested status for each risky item.

### Step 4: Resolve Review Results

**Goal**: Turn verification into doc changes.

- [ ] Apply verified corrections.
- [ ] Resolve contradictions through source of truth, user need, and risk.
- [ ] Request clarification when review comments are vague.
- [ ] Escalate missing required reviews before release if user risk remains high.

### Step 5: Record Residual Risk

**Goal**: Make release readiness explicit.

- [ ] Summarize what was verified and by whom.
- [ ] List what remains unverified and why.
- [ ] Name the owner who accepts any residual risk.
- [ ] Preserve written confirmation for QA-tested or high-risk procedures.

## Exit Criteria

- [ ] High-risk claims are verified, corrected, or explicitly marked as residual risk.
- [ ] Required reviewers and QA tests are complete or escalated.
- [ ] The doc is safe enough to release for its reader and product context.
