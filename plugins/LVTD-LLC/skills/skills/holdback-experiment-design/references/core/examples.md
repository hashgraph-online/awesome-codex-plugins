# Holdback Experiment Design Examples

## Degradation Holdback

**Situation**: A new ranking algorithm improves short-term engagement, but the
team worries it may reduce content diversity and retention over time.

**Holdback type**: Degradation holdback.

**Metrics**:
- Retention.
- Content diversity.
- Engagement quality.
- Complaints or hides.

**Exit**: End when long-term guardrails remain stable for the agreed window.

## Long-Term Cumulative Holdback

**Situation**: A personalized homepage may teach users to return more often,
but the effect could compound over several weeks.

**Holdback type**: Long-term cumulative holdback.

**Metrics**:
- Return visits.
- Weekly active users.
- Content starts.
- Revenue guardrails.

**Exit**: End after the cumulative effect is estimated with enough confidence
or the cost of withholding becomes too high.

## Bad Holdback Plan

```markdown
Keep 10% of users out of the feature indefinitely so we can always compare.
```

**Problems**:
- No specific long-term question.
- No duration or review cadence.
- No cost assessment.
- No exit criteria.

## Better Holdback Plan

```markdown
Hold back 2% of eligible users for 8 weeks to estimate whether the recommendation
feature changes weekly active use and return visits over time. Review metrics
weekly and end early if revenue or retention guardrails breach the agreed
threshold.
```

**Why it works**:
- Names question, population, duration, cadence, and guardrails.
