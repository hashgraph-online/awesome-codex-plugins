# Decide Platform Strategy Workflow

Choose a practical build, buy, hybrid, or manual experimentation platform path.

## When to Use

- A team wants to start A/B testing.
- Leaders are debating build versus buy.
- Existing feature flags are being stretched into experimentation.
- Experiment volume is outgrowing manual analysis.

## Prerequisites

- Product surfaces to test.
- Expected experiment volume.
- Current feature flag, analytics, and data stack.
- Team capacity and ownership constraints.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Define Experimentation Demand

**Goal**: Size the platform to real use.

- [ ] Estimate experiments per quarter.
- [ ] Identify participating teams.
- [ ] Name product surfaces and clients.
- [ ] Name decision-makers and analysts.

### Step 2: Inventory Current Capabilities

**Goal**: Avoid buying or building what already exists.

- [ ] Feature delivery or flags.
- [ ] Eligibility and targeting.
- [ ] Stable assignment.
- [ ] Exposure logging.
- [ ] Event data and metric computation.
- [ ] Dashboards or reporting.

### Step 3: Identify Gaps

**Goal**: Separate blockers from maturity improvements.

- [ ] Mark each capability as must-have now, later, or unnecessary.
- [ ] Identify data-trust risks.
- [ ] Identify governance risks.

### Step 4: Compare Options

**Goal**: Make the tradeoff explicit.

- [ ] Score build, buy, hybrid, and manual against speed, fit, cost, risk, and ownership.
- [ ] Document integration constraints.
- [ ] Document maintenance owner.

### Step 5: Recommend A Roadmap

**Goal**: Start useful and evolve deliberately.

- [ ] Define the first valid experiment setup.
- [ ] Define the next two maturity milestones.
- [ ] Define triggers for investing more.

## Exit Criteria

The strategy is complete when the team knows what to use for the next
experiment, what not to build yet, and what conditions justify expanding the
platform.
