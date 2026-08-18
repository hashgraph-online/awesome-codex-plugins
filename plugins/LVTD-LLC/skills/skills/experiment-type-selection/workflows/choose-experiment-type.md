# Choose Experiment Type Workflow

Select the experiment type that answers the real product question.

## When to Use

- The team is unsure whether to run superiority, non-inferiority, equivalence,
  A/B/n, or holdback.
- A proposed A/B test does not match the decision being made.
- A mature product change may need safety or equivalence evidence rather than
  large uplift.

## Prerequisites

- Product decision.
- Candidate change.
- Primary metric or business concern.
- Risk tolerance or acceptable margin when relevant.

**Reference**: `references/core/rules.md`

## Workflow Steps

### Step 1: Write The Claim

**Goal**: Identify what the test must prove.

- [ ] Write the sentence: "We can decide X if the test shows Y."
- [ ] Name whether Y means better, not worse, similar, or durable.

### Step 2: Match Claim To Type

**Goal**: Choose the simplest valid design.

- [ ] Better -> superiority.
- [ ] Not meaningfully worse -> non-inferiority.
- [ ] Practically similar -> equivalence.
- [ ] Multiple alternatives -> A/B/n if traffic supports it.
- [ ] Delayed or cumulative effect -> holdback.

### Step 3: Define Required Margins

**Goal**: Prevent ambiguous interpretation.

- [ ] For non-inferiority, define unacceptable regression.
- [ ] For equivalence, define the equivalence band.
- [ ] For superiority, define meaningful lift.

### Step 4: Check Practical Feasibility

**Goal**: Avoid selecting a design that cannot be run well.

- [ ] Check traffic and duration.
- [ ] Check instrumentation.
- [ ] Check variant interpretability.
- [ ] Check whether long-term measurement is needed.

### Step 5: Document Rejected Types

**Goal**: Make tradeoffs explicit.

- [ ] List one or two plausible alternatives.
- [ ] Explain why each would answer the wrong question or cost too much.

## Exit Criteria

The recommendation is complete when the chosen test type, margins, variants,
and rejected alternatives are explicit enough for stakeholders to challenge.
