# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

In one month, 1,000 subscriptions were active at period start, 40 cancelled voluntarily and 20 were lost after failed payments. Counts are unique subscriptions and exclude new signups.

## Expected output

Report 6% gross subscriber churn for that defined cohort, with voluntary 4% and involuntary 2%. Propose separate cancel-flow and dunning interventions, each with owner, entry/exit criteria, measurement window and a customer-protection guardrail. Preserve immediate cancellation access and avoid treating a save-offer click as a saved customer.

## Failure case

Failed-payment events include repeated retries on the same subscription. Deduplicate to final subscription outcome before reporting churn; if the export lacks stable IDs, return counts as events and request the needed cohort data.

## Validation

Recalculate from opening-cohort denominators, test cancellation completion after declining every offer, and verify recovery from actual settled payment/subscription state. Report jurisdiction-specific requirements with current sources.

## Coverage and routing

Suede AI retention discipline for voluntary and involuntary churn: transparent cancel flows that meet current cancellation law, pause and downgrade paths, reason-matched save offers, failed payment recovery with smart retries and dunning, health scores and proactive signals, and win-back design. Use when diagnosing subscriber loss or designing a bounded retention intervention. NOT FOR: writing the lifecycle emails themselves (use suede-emails), pricing architecture (use suede-pricing), paywall design (use suede-paywalls), or event instrumentation (use suede-analytics).
