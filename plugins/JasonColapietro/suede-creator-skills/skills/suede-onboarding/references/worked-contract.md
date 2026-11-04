# Suede AI Onboarding Skills: Worked Contract

This is a synthetic application scenario, not a client result or a required output filename. Adapt the values to the supplied evidence. The skill's existing output format and authority boundaries apply.

## Input

A project-management app has high signup completion but low project creation. Supplied event data identifies first shared project as a candidate activation event; its retention correlation has not been established.

## Expected output

Return the prescribed onboarding design headings: Activation Goal, Flow, Checklist Items when applicable, Empty State Copy, Email Triggers, Metrics Plan, and at most three Test Hypotheses. Label the activation-retention link unverified and define the cohort comparison needed to test it.

## Missing input and recovery

If event counts exclude users who abandoned setup, report the denominator gap before calculating activation. If live access fails, audit the supplied screens and state which interactions remain unchecked. Do not remove consent or authentication controls to reduce apparent friction.

## Validation

Walk a new account through each step, including back, dismiss, validation failure, and returning-user cases. Verify that the first value action is reachable without a forced invite and that event names/denominators match the metrics plan.

## Detailed scope and routing

Suede AI activation path from signup conversion to first value: audits account creation, registration, and trial start (field friction, progressive profiling, passkeys and social sign-in, NIST-aligned password rules, verification, mobile), then designs first-run sequencing, empty states, setup checklists, activation milestones, time to value, and retention-linked measurement. Returns a ranked signup audit or an onboarding flow spec with metrics and up to 3 test hypotheses. Use when visitors start but don't finish signup, or users sign up but never reach first value. NOT FOR: lead-capture and non-account forms (use suede-site-alchemy), lifecycle email sequences (use suede-emails), upgrade prompts and paywalls (use suede-paywalls), cancel flows (use suede-churn-prevention), or deploying auth changes without review.
