# Create Experiment Quality Roadmap Workflow

Create a roadmap for verifying experiments before launch and monitoring them
while they run.

## When to Use

- Experiments are misconfigured or produce untrusted results.
- The platform lacks prelaunch verification.
- Teams need canaries, A/A tests, leakage checks, or monitoring dashboards.
- Leadership wants to invest in experimentation quality.

## Prerequisites

- Current experiment setup and QA process.
- Known failure modes or recent incident examples.
- Assignment, exposure, metric, and dashboard ownership.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Inventory Quality Failures

**Goal**: Focus on real risks.

- [ ] List recent misconfigurations, invalid tests, or delayed issue detection.
- [ ] Classify failures as setup, targeting, assignment, exposure, metrics,
  treatment, leakage, interference, or analysis.
- [ ] Identify which failures are repeated.

### Step 2: Define The Gold Standard

**Goal**: Make a correct experiment observable.

- [ ] Define required configuration fields.
- [ ] Define control/treatment validation.
- [ ] Define exposure and metric logging requirements.
- [ ] Define user-experience checks.

### Step 3: Add Verification Tools

**Goal**: Catch errors before users are broadly affected.

- [ ] Add prelaunch checklist or QA app for treatment spot checks.
- [ ] Add canary launch checks for early assignment, exposure, and metrics.
- [ ] Add active dashboards and alerts for running experiments.

### Step 4: Validate Platform Health

**Goal**: Ensure infrastructure itself is trustworthy.

- [ ] Plan periodic A/A tests.
- [ ] Track assignment balance and false alert rates.
- [ ] Review instrumentation and metric pipeline reliability.

### Step 5: Operationalize The Roadmap

**Goal**: Make verification part of normal experimentation.

- [ ] Add verification steps to the playbook.
- [ ] Assign owners for alerts and escalations.
- [ ] Track experimentation quality metrics over time.

## Quick Checklist

```text
[ ] Known failure modes inventoried
[ ] Gold standard requirements defined
[ ] Prelaunch verification added
[ ] Canary and active monitoring planned
[ ] A/A health checks planned
[ ] Owners and escalation rules assigned
```

## Exit Criteria

The roadmap is ready when recurring experiment-quality failures have named
checks, owners, metrics, and escalation paths before they can invalidate another
experiment unnoticed.
