# Review Inclusive Impact Workflow

Review whether an experiment design or result accounts for important user
differences.

## When to Use

- A product change may affect user groups differently.
- A test result is positive overall but could hide subgroup harm.
- The team is designing segmentation dimensions before launch.
- Accessibility, device, bandwidth, privacy, or representation concerns exist.

## Prerequisites

- Product change description.
- Experiment population and variants.
- Available user dimensions.
- Metrics and guardrails.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Identify Plausible Impact Differences

**Goal**: Choose dimensions from product risk, not convenience.

- [ ] List how the change affects content, navigation, performance, data use, or access.
- [ ] Name user groups that may experience those effects differently.
- [ ] Remove dimensions with no clear relevance.

### Step 2: Check Data And Ethics

**Goal**: Use dimensions responsibly.

- [ ] Confirm data availability and trust.
- [ ] Check governance for sensitive attributes.
- [ ] Note missing dimensions as limitations.

### Step 3: Check Balance And Representation

**Goal**: Know what the experiment can support.

- [ ] Compare test/control composition for relevant dimensions.
- [ ] Note segments too small for confident interpretation.
- [ ] Avoid safety claims for unrepresented groups.

### Step 4: Interpret Segment Impact

**Goal**: Find uneven benefit or harm.

- [ ] Compare primary metric by segment.
- [ ] Compare guardrails by segment.
- [ ] Check accessibility or qualitative concerns outside metrics.

### Step 5: Recommend Action

**Goal**: Tie subgroup evidence to launch decision.

- [ ] Ship if benefits are broad and guardrails are clean.
- [ ] Ship with mitigation if risk is bounded and fixable.
- [ ] Do not ship if meaningful subgroup harm is unresolved.
- [ ] Investigate when representation or data is insufficient.

## Exit Criteria

The review is complete when the launch recommendation states which user groups
were considered, which were not verifiable, and whether any subgroup concern
changes the decision.
