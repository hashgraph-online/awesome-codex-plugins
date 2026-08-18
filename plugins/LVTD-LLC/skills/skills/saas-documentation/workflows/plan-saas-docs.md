# Plan SaaS Docs Workflow

Plan customer-facing documentation and release readiness for a SaaS or managed-service change.

## When To Use

- A hosted product, admin console, managed service, or cloud feature is changing.
- Customers may need to act, understand responsibility boundaries, or handle new limits.
- Public docs, release notes, support docs, and internal enablement need alignment.
- A change affects many customers through rollout, migration, entitlement, plan, or region.

## Prerequisites

- Feature or release description, affected customer segment, launch timing, and source owner.
- Access to PM, engineering, support, operations, QA, or release artifacts when available.

**Reference**: `../references/core/knowledge.md`

## Workflow Steps

### Step 1: Identify Customer Impact

**Goal**: Make the docs about what changes for users.

- [ ] State who is affected by plan, role, region, rollout, feature flag, integration, or tenant state.
- [ ] Identify customer action required before, during, or after release.
- [ ] Identify security, billing, availability, data, permission, browser, or UI impact.

### Step 2: Define Responsibilities

**Goal**: Prevent confusion about what the provider and customer each own.

- [ ] List provider-managed behavior, operations, rollouts, and support commitments.
- [ ] List customer-controlled configuration, data, users, integrations, and validation.
- [ ] Mark shared responsibilities and unsupported paths.

### Step 3: Choose The Doc Set

**Goal**: Match each audience to the right artifact.

- [ ] Choose public tasks, concepts, reference updates, troubleshooting, and release notes.
- [ ] Choose internal support, operations, enablement, incident, or escalation docs.
- [ ] Identify docs that need screenshots, examples, API/schema updates, or status-page links.

### Step 4: Plan Release Readiness

**Goal**: Make docs ship with service readiness.

- [ ] Assign owners and reviewers for public and internal docs.
- [ ] Verify UI labels, API behavior, browser support, defaults, limits, and permissions near release.
- [ ] Add release notes with customer impact and action.
- [ ] Confirm support and operations know where to find internal procedures.

### Step 5: Define Maintenance Triggers

**Goal**: Keep SaaS docs from drifting after release.

- [ ] Add review triggers for UI changes, service behavior, support issues, incidents, and rollout changes.
- [ ] Mark screenshots, labels, examples, settings, and runbooks that need dependency audits.
- [ ] Record owner and source of truth for recurring updates.

## Quick Checklist

```text
[ ] Customer impact and action are explicit
[ ] Provider/customer responsibility boundary is documented
[ ] Public and internal docs are both considered
[ ] Release notes explain impact, timing, and action
[ ] Support and operations readiness is covered
[ ] Maintenance triggers and owners are recorded
```

## Exit Criteria

- [ ] The doc set matches customer and internal audience needs.
- [ ] The release can be supported without relying on private tribal knowledge.
- [ ] Open service, support, or ownership questions are assigned.
