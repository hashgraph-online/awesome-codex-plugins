# PRD Sections Reference

Use this reference when drafting or updating `prd.md`.

Evidence basis: the section set below is grounded in a repository-local research report, `../../../.hyper/research/002-prd-package-layered-artifacts.md`, which reviewed 12 PRD sources and compared them with feature-spec, user-flow, and wireframe sources. That report is a local artifact outside this skill package and is not shipped with it, so the section set and the source notes below are written to stand alone without it.

## Contents

- Stable section set
- Section prompts
- Overview and status
- Problem and objective
- Users and use cases
- Scope and non-goals
- Requirements
- Metrics and success criteria
- Assumptions, constraints, risks, dependencies
- Open questions
- Related downstream artifacts
- Optional: Alternatives or options considered
- Optional: Release criteria
- Change history

## Stable section set

This section set is the strongest common denominator across the researched PRD guides:

- Overview and status
- Problem and objective
- Users and use cases
- Scope and non-goals
- Requirements with stable IDs
- Metrics and success criteria
- Assumptions, constraints, risks, and dependencies
- Open questions
- Related downstream artifacts: `feature-spec.md`, `user-flow.md`, `wireframe.md`, `diagram.md`, `sources.md`
- Change history

Optional sections when justified:

- Alternatives or options considered
- Release criteria
- Review or meeting goals
- Launch/readiness plan

Evidence basis:

- Atlassian emphasizes high-level context, assumptions, user stories, questions, and explicit out-of-scope boundaries. Source: [Atlassian PRD guide](https://www.atlassian.com/agile/requirements)
- Atlassian's product requirements template tracks objective, success metrics, assumptions, user stories, and open questions. Source: [Atlassian product requirements template](https://www.atlassian.com/software/confluence/templates/product-requirements)
- ProductPlan frames a PRD around release-complete capabilities, use cases, constraints, and dependencies. Source: [ProductPlan PRD glossary](https://www.productplan.com/glossary/product-requirements-document)
- Aha! emphasizes enough context to guide good solutions without over-prescribing implementation. Source: [Aha! PRD template guide](https://www.aha.io/roadmapping/guide/templates/create/prd)
- Productboard and Miro emphasize outcomes, success measures, out-of-scope decisions, constraints, dependencies, risks, and stakeholders. Sources: [Productboard PRD glossary](https://www.productboard.com/glossary/product-requirements-document/), [Miro PRD template](https://miro.com/templates/prd/)
- Pendo adds goals, success metrics, out-of-scope items, open questions, and product usage measurement. Source: [Pendo PRD template](https://www.pendo.io/de-de/product-led/artifacts/product-requirements-document-prd-template/)

## Section prompts

### Overview and status

- What is this initiative called?
- Who owns it?
- What is the current status?
- What is the target milestone or release window?

### Problem and objective

- What user or business problem exists today?
- Why now?
- What outcome should change if this work succeeds?

### Users and use cases

- Who is affected?
- What core jobs or scenarios matter most?
- What evidence supports these use cases?

### Scope and non-goals

- What will this work include?
- What will it intentionally not include?
- What follow-up work is deferred?

### Requirements

- What product behavior must exist?
- Which requirement ID should downstream artifacts use?
- What acceptance criteria define done at the product level?
- What linked designs, user stories, or tickets clarify the requirement?

### Metrics and success criteria

- How will success be measured?
- What leading indicators and outcome metrics matter?
- Are there guardrail metrics that could get worse even if the main metric improves?

### Assumptions, constraints, risks, dependencies

- What must be true for the plan to work?
- What could block delivery or reduce impact?
- Which teams, systems, or decisions does this depend on?

### Open questions

- What is unresolved?
- Which question blocks feature-spec, user-flow, or wireframe detail?
- What research, decision, or validation still needs to happen?

### Related downstream artifacts

- Does `feature-spec.md` cover every must-have PRD requirement?
- Does `user-flow.md` cover every user-facing feature behavior?
- Does `wireframe.md` cover every user-facing flow screen/state?
- Are `diagram.md`, `diagram.svg`, and `preview.html` current?

### Optional: Alternatives or options considered

- What meaningful options were considered?
- Why was the chosen direction preferred?

### Optional: Release criteria

- What conditions must be true before launch?
- What readiness, reliability, or rollout gates still need to be met?

### Change history

- What changed?
- When did it change?
- Why did it change?

## Sources

> External links checked 2026-09-21.

The section set above is repository-authored; the PRD guides below are the external sources the inline notes cite.

| Inline claim | Source |
|---|---|
| High-level context, assumptions, user stories, questions, and explicit out-of-scope boundaries | [Atlassian PRD guide](https://www.atlassian.com/agile/requirements) |
| Objective, success metrics, assumptions, user stories, and open questions in the product requirements template | [Atlassian product requirements template](https://www.atlassian.com/software/confluence/templates/product-requirements) |
| PRDs framed around release-complete capabilities, use cases, constraints, and dependencies | [ProductPlan PRD glossary](https://www.productplan.com/glossary/product-requirements-document) |
| Enough context to guide good solutions without over-prescribing implementation | [Aha! PRD template guide](https://www.aha.io/roadmapping/guide/templates/create/prd) |
| Outcomes, success measures, out-of-scope decisions, constraints, dependencies, risks, and stakeholders | [Productboard PRD glossary](https://www.productboard.com/glossary/product-requirements-document/), [Miro PRD template](https://miro.com/templates/prd/) |
| Goals, success metrics, out-of-scope items, open questions, and product usage measurement | [Pendo PRD template](https://www.pendo.io/de-de/product-led/artifacts/product-requirements-document-prd-template/) |

Every link above resolved on 2026-09-21. The inline summaries paraphrase each guide's emphasis as recorded in the original survey; they were not re-read line by line on that date, and the guides may have changed since.
