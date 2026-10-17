# Result-Change And Construct Audit

Use this reference when a revision materially changes a result's magnitude, direction, ranking, class membership, mechanism, or claim strength.

## Preserve The Comparison

Record the old and new:

- source data version and checksum;
- code commit or script version;
- equation, construct, denominator, weighting, threshold, and preprocessing;
- units, system boundary, reference state, and sign convention;
- sample inclusion/exclusion and missing-data handling;
- output table, figure, and manuscript claim.

Do not overwrite the prior output until the cause is understood and the comparison is recoverable.

## Attribute The Change

Separate contributions from:

1. new or corrected source data;
2. code or parameter changes;
3. unit, sign, coordinate, ordering, or join corrections;
4. changed assumptions, thresholds, or sensitivity choices;
5. changed construct, denominator, boundary, or definition;
6. stochastic variation or model retraining;
7. plotting, rounding, or presentation only.

Use controlled reruns where possible so one factor changes at a time.

## Plausibility Checks

Compare old and new results against:

- dimensional consistency and order of magnitude;
- mass, energy, momentum, or species conservation;
- limiting cases and expected monotonicity;
- accepted correlations, theory, benchmark data, or prior observations;
- uncertainty, repeatability, and sensitivity ranges;
- neighboring records or conditions in the same dataset.

Allow physically or mathematically legitimate zero and negative values. Do not impose generic positivity checks without understanding the quantity and sign convention.

## Reporting

Explain whether the change is a scientific result, a corrected error, a revised definition, or a presentation change. Do not describe two values as a trend when the underlying construct changed.

Bind headline values in the abstract, text, tables, captions, and conclusions to generated machine-readable outputs or a claim manifest when feasible. Add regression tests for values that must remain synchronized.

If the root cause remains unresolved, keep the result provisional and state the next diagnostic rather than selecting the more convenient version.
