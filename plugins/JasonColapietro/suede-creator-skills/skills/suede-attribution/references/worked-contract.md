# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

CRM has 100 unique purchases in October. Google claims 70 conversions and Meta claims 60 in overlapping windows. No user-level overlap or incrementality experiment is available.

## Expected output

Return a reconciliation table with each source, model, window and unique-count definition. Anchor the total to the 100 deduplicated CRM purchases; show 130 platform claims as overlapping claims, not 130 purchases. Name unknown overlap and propose matched-window exports or a bounded incrementality design before reallocating budget.

## Failure case

A hosted-booking URL exposes an already identified email as the visitor ID. Do not decorate the URL with it or merge profiles from it. Return the anonymity-guard failure and a source-level fix path; retain the failed case for regression checks.

## Validation

Check identity, currency and windows before comparing totals. For stitching, test anonymous-to-known join, a duplicate webhook, an identified visitor and a missing metadata field; no path may silently merge unrelated people.

## Coverage and routing

Suede AI marketing attribution: which channels actually drive conversions and revenue, how to choose and read attribution models, reconcile conflicting numbers across ad platforms, GA4, and the CRM, design incrementality, MMM, and geo-holdout reads, add self-reported attribution for dark social and AI answers, and instrument first-party attribution yourself (closing the identify gap, stitching bookings or checkouts on third-party domains to their source). Use when someone asks which channel drives revenue, what their real CAC is, why dashboards disagree, or how to track a conversion they do not host. NOT FOR: event tracking plans, GA4 or GTM setup, and UTM hygiene (use suede-analytics), ad-platform pixels and campaign decisions (use suede-ads), or pipeline-stage and CRM revenue operations (use suede-revops).
