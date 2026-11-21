# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

A signup flow fires signup_complete on both a success-page reload and the API callback. The target contract is one event per successful account creation with an opaque account ID and no email payload.

## Expected output

Return a tracking plan with trigger, event owner, deduplication key, required properties, consent condition and destination. Identify both existing firing sites with evidence; propose one authoritative success trigger and a reload-safe deduplication rule. Include a browser/debug readback table for a new signup, reload and failed signup.

## Failure case

Debug access is unavailable. Supply the source-based diagnosis and exact verification steps, mark firing proof pending and avoid claiming that GA4 received or deduplicated an event.

## Validation

Observe one successful signup event, zero additional events on reload and zero on failure. Inspect the actual outbound payload for forbidden email fields and confirm consent behavior before publishing container changes.

## Coverage and routing

Suede AI measurement discipline: tracking plans, event and key-event instrumentation in GA4 and GTM, consent mode v2, UTM hygiene, AI assistant and organic search channel grouping, and readback proof of what actually fires. Use when setting up, auditing, or repairing analytics across web, product, paid, and lifecycle surfaces. NOT FOR: experiment design or significance (use suede-ab-testing), campaign optimization (use suede-ads), attribution models, model comparison, or cross-tool reconciliation (use suede-attribution), or revenue-process architecture (use suede-revops).
