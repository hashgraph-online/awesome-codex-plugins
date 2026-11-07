# Validation

Use this checklist before declaring the planning package complete.

## Required checks

- The request really called for a product planning package, PRD, feature spec, user flow, low-fidelity wireframe, diagram, or preview.
- The package folder exists under `.hyper/prd/[slug]/`.
- New packages contain `prd.md`, `feature-spec.md`, `user-flow.md`, `wireframe.md`, `diagram.md`, `diagram.data.json`, `diagram.svg`, `preview.html`, and `sources.md`.
- The PRD includes goals, scope, non-goals, requirements with IDs, metrics, risks/dependencies, open questions, and change history.
- The feature spec covers all must-have PRD requirements with functional behavior, acceptance criteria, states, permissions, errors, analytics, and rollout notes when relevant.
- The user flow covers actors, entry points, happy paths, alternate paths, edge/error states, recovery paths, and exit points.
- The wireframe covers each user-facing flow with screen inventory, low-fidelity layout blocks, components, state variants, annotations, and unresolved design/product questions.
- The diagram includes a central idea node, branches for PRD/spec/flow/wireframe, second-level nodes, open gaps, valid Mermaid/text structure, valid JSON node data, and a rendered SVG.
- The preview HTML opens without external dependencies and includes the diagram plus text artifacts.
- Any research-backed non-obvious claim has a link in `sources.md`.
- `sources.md` contains provided context and either distinct queries or an explicit note that external research was unnecessary.
- When updating, the PRD change history shows what changed and why.
- Unknowns are visible as open questions or assumptions, not silently omitted.
- Complex packages include `flow.json` with current phase state and final validation status.

## Chain traceability checks

- Every must-have PRD requirement maps to at least one feature-spec row or an explicit deferral.
- Every user-facing feature-spec behavior maps to a user-flow step, decision, or explicit non-user-facing note.
- Every user-flow step that needs a screen maps to a wireframe screen/state entry.
- Every wireframe screen has a purpose, related flow step, primary action or state rationale, and open questions when uncertain.
- Downstream artifacts do not introduce new product decisions without reflecting them in `prd.md` or marking them as open questions.

## Cross-artifact checks

- The diagram maps the package at a glance and links to the text artifacts.
- PRD requirements map to feature-spec requirements.
- Feature-spec behaviors map to user-flow paths or explicit non-user-facing notes.
- User-facing flows map to wireframe screens or screen states.
- Preview content is rebuilt after source artifact changes.
- Metrics and analytics events are consistent across PRD and feature spec.
- Risks, dependencies, and open questions are not contradicted across files.

## Quality checks

- The package is concise enough to scan quickly.
- Main decisions live in `prd.md`; detailed behavior lives in `feature-spec.md`; paths live in `user-flow.md`; screen structure lives in `wireframe.md`; evidence accumulation lives in `sources.md`.
- Requirements are written as product behavior or outcomes, not implementation mandates unless that constraint is genuinely required.
- User flows model meaningful decisions and recovery paths, not only happy-path screen order.
- Wireframes are low-fidelity structure, not premature visual polish.

## Forward-test questions

- Could a new teammate understand what problem this initiative solves?
- Could engineering tell what is required, optional, and out of scope?
- Could QA derive test scenarios from acceptance criteria and flow edge cases?
- Could design understand the required screens and states before making visual comps?
- Could someone revisit the package next month and see what changed?
- If evidence shifts, can `sources.md` be refreshed without rewriting the package?

## Sources

> No external sources; content checked 2026-09-21.

This file states this package's own completion checklist and review questions. It cites no external URL and asserts no external fact, so no external source is recorded.
