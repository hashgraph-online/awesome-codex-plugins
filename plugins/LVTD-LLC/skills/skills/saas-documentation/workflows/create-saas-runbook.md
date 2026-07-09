# Create SaaS Runbook Workflow

Create an internal support or operations runbook for a SaaS service workflow.

## When To Use

- Support or operations needs repeatable steps for a customer-impacting issue.
- A SaaS feature needs escalation, mitigation, replay, rollback, or verification guidance.
- Incident response depends on product behavior, tooling, permissions, or customer communication.
- Internal docs are stale or incomplete for a managed-service operation.

## Prerequisites

- Trigger condition, service owner, affected customer or tenant scope, available tools, and access requirements.
- Known risks, support policy, escalation path, or incident process when available.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Define Trigger And Scope

**Goal**: Make clear when the runbook applies.

- [ ] State the alert, ticket, customer symptom, metric, log, or incident condition that starts the workflow.
- [ ] Define affected customer scope, severity, and known exclusions.
- [ ] Identify when to stop and escalate instead of continuing.

### Step 2: Record Access And Safety

**Goal**: Prevent operational mistakes.

- [ ] List required role, tool, environment, tenant identifier, approval, and audit requirement.
- [ ] State customer impact of each destructive, replay, rollback, or mitigation action.
- [ ] Include privacy, security, billing, and data integrity cautions.

### Step 3: Write Operational Steps

**Goal**: Give a repeatable procedure that can be followed during pressure.

- [ ] Start with diagnosis and verification before action.
- [ ] Write one action per step with exact tool, command, UI path, or API where appropriate.
- [ ] Add expected result after each critical step.
- [ ] Include rollback, retry, or escalation branch when the expected result does not happen.

### Step 4: Add Customer Communication

**Goal**: Align internal work with external experience.

- [ ] State what can be communicated to the customer and by whom.
- [ ] Link public docs, status page, incident communication, or support macros.
- [ ] Add post-action confirmation or customer follow-up steps.

### Step 5: Validate And Maintain

**Goal**: Make the runbook trustworthy after creation.

- [ ] Review with service owner, support, operations, and security if relevant.
- [ ] Test in staging or with a safe example when feasible.
- [ ] Add owner, last-reviewed date, and review triggers.
- [ ] Link related public docs and release notes.

## Common Mistakes

| Mistake | Why It Hurts | Do Instead |
|---------|--------------|------------|
| Writing a runbook as background prose | Hard to use during incidents | Use numbered steps with checks and expected results |
| Omitting customer impact | Operators may take unsafe actions | State impact and communication path |
| Depending on one expert | Creates support bottlenecks | Capture source owner, access, and escalation path |
| Forgetting review triggers | Runbook becomes stale after service changes | Add owner and maintenance triggers |

## Exit Criteria

- [ ] Trigger, scope, access, safety, steps, communication, and escalation are clear.
- [ ] The runbook has an owner and review triggers.
- [ ] Public docs or customer communication links are connected where relevant.
