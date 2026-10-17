# A/B Test Design Brief Examples

Examples of strong and weak experiment brief elements.

## Weak Hypothesis

```text
We will test the new homepage recommendation module to see if users like it.
```

**Problems**:
- No evidence or reason for the change.
- No audience definition.
- No measurable outcome.
- "Like it" is not operationalized.

## Stronger Hypothesis

```text
Because users have difficulty resuming recently watched content, we believe a
personalized recommendation module will increase video plays for eligible
returning users. We will call the test successful if video plays per exposed
user increases without reducing weekly active users, return visits, purchases,
or rentals.
```

**Why it works**:
- Ties the change to observed friction.
- Names the audience and expected behavior.
- Separates success and guardrail metrics.

## Variant Anti-Example

```text
Variant D moves the CTA, changes button color, adds a second action, and adds a
new price symbol.
```

**Problem**: A result for this variant cannot identify which change caused the
metric movement.

## Variant Example

```text
Variant B changes only CTA placement while copy, color, price display, and
surrounding content remain constant.
```

**Why it works**: The result can be interpreted as evidence about placement.

## Proxy Metric Example

```text
Ideal metric: recommendation CTR from module impression to content play.
Available proxy: total video plays per exposed user.
Rationale: video play events are reliable, queryable at user level, and close
enough to expected behavior for this first test.
Risk: total plays may include behavior unrelated to the recommendation module.
```
