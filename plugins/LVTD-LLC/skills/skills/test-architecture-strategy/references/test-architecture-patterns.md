# Test Architecture Patterns

## Test Desiderata Audit

Score the suite against these qualities:

- Isolated: order-independent.
- Deterministic: same result when nothing changed.
- Fast: quick enough for the intended feedback loop.
- Readable: failure intent is clear.
- Behavioral: sensitive to user or domain behavior.
- Structure-agnostic: tolerant of harmless refactors.
- Automated: no human steps.
- Specific: failure points to a likely cause.
- Predictive: green gives production confidence.

Use the weakest qualities to guide the first change.

## Suite Shape

| Layer | Purpose | Keep Small By |
| --- | --- | --- |
| Unit/core | Detailed behavior and edge cases | Removing framework/database dependencies |
| Integration | Boundary correctness | Testing only meaningful seams |
| Functional/end-to-end | Critical user journeys | One journey per major workflow |
| Smoke/deploy | Environment readiness | Checking the smallest production-like path |
| Monitoring | Production confidence | Alerting on real user-impacting failures |

## Migration From Slow Integration Suites

1. Measure runtime and flake sources.
2. Find a high-churn area with many similar integration tests.
3. Extract the business rule into a dependency-light unit.
4. Move detailed cases to fast tests.
5. Keep one integration test proving framework/database wiring.
6. Compare runtime and confidence before repeating.

## Architecture Options

| Symptom | Architectural Response |
| --- | --- |
| Database involved in every test | Functional core or service layer for pure rules |
| External service mocked everywhere | Port/adapter boundary with contract tests |
| Tests break on UI/template refactors | Raise assertion level or use semantic selectors |
| Too many request-path branch tests | Move branching logic into forms/helpers/services |
| Hard-to-test side effects | Inject boundary clients and keep shell thin |

## Runtime Red Lines

Define red lines before pain becomes normal:

- Local pre-commit or inner-loop command target.
- Full local suite target.
- CI required check target.
- Flake tolerance.

The exact numbers depend on the team, but the rule should trigger a visible architecture or suite-design conversation.

## Deletion Criteria

Delete or demote a slow/brittle test only when:

- The behavior is covered at a better layer.
- At least one integration or end-to-end path still proves wiring when needed.
- The replacement fails if the important behavior breaks.
- Runtime, readability, or flake rate improves measurably.
