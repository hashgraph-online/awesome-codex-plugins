# Holdback Experiment Design Rules

Rules for creating useful and responsible holdbacks.

## Core Rules

### 1. Require A Long-Term Question

Do not create a holdback just because it seems rigorous. State the delayed or
cumulative effect that short-term testing cannot answer.

### 2. Use The Smallest Useful Holdback

Keep enough users for measurement, but minimize withholding cost.

Consider:
- Metric variance.
- Expected effect size.
- Business criticality.
- User impact of not receiving the feature.

### 3. Define Duration Before Launch

Set the expected holdback duration and review cadence before the rollout.

### 4. Monitor Guardrails Continuously

Do not wait until the end if guardrails show meaningful harm or if the holdback
itself creates a problem.

### 5. Document The Cost Of Withholding

Name who does not receive the feature and what they lose. If the feature
improves safety, accessibility, compliance, or core user value, be especially
careful.

### 6. Define Exit Criteria

End or revise the holdback when:

- The long-term question is answered.
- The cost of withholding exceeds the learning value.
- Guardrails require escalation.
- Data quality cannot support the comparison.

## Common Mistakes

| Mistake | Consequence | Better Approach |
|---------|-------------|-----------------|
| No explicit question | Holdback becomes inertia | State delayed/cumulative claim |
| Too large a holdback | Unnecessary user/business cost | Use smallest useful group |
| No end date | Permanent exclusion risk | Set duration and reviews |
| No guardrail monitoring | Delayed harm persists | Monitor during holdback |
