# A/B Testing Platform Strategy Rules

Rules for platform scoping and build-vs-buy decisions.

## Core Rules

### 1. Start With The Smallest Useful Capability

Do not wait years for the perfect platform before learning from experiments.
Start with enough targeting, assignment, logging, and analysis to run a valid
test.

### 2. Make Measurement A Platform Requirement

Feature delivery without trustworthy metrics is not an experimentation
platform. Exposure and metric pipelines are core requirements.

### 3. Build When Internal Constraints Dominate

Building is more defensible when:

- Product surfaces are unusual or deeply integrated.
- Internal data definitions are complex.
- Privacy, compliance, or reliability requirements are hard to outsource.
- The organization has a platform team that can own maintenance.

### 4. Buy When Speed And Standardization Matter More

Buying is more defensible when:

- Use cases match common vendor capabilities.
- The team lacks platform capacity.
- Vendor SDKs fit the product stack.
- External reporting and governance are acceptable.

### 5. Use Hybrid Designs Deliberately

Hybrid can work well, but only when ownership boundaries are clear.

Examples:
- Vendor SDK for assignment; internal warehouse for metrics.
- Internal feature flags; external analysis dashboard.

### 6. Expand Scope Only When Demand Is Proven

Triggers for expansion:

- Experiment volume exceeds manual coordination.
- Teams repeat the same analysis work.
- Inconsistent metric definitions cause disputes.
- More teams need self-service.
- Risk requires stronger governance.

## Quick Reference

| Decision Factor | Build Leaning | Buy Leaning |
|-----------------|---------------|-------------|
| Product uniqueness | High | Low |
| Internal data complexity | High | Low |
| Time to first test | Flexible | Urgent |
| Platform team capacity | Strong | Limited |
| Governance needs | Custom | Standard |
| Experiment volume | Growing and strategic | Early or moderate |
