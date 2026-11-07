# Package Workflow

Use this rule file to turn a rough product request into a create or update flow for the full layered planning package.

## 1. Choose the mode first

- `create`: no existing package folder matches the initiative, or the user explicitly wants a new planning package.
- `update`: an existing package already exists and the request refines scope, requirements, specs, flows, wireframes, metrics, risks, launch details, or review helpers.

Prefer `update` when the user is iterating on an established initiative.

## 2. Gather the minimum working brief

Before writing, identify or infer:

- product or feature name
- problem to solve
- target users or operators
- desired outcome or business goal
- primary use case
- known constraints or deadlines
- likely platforms or surfaces
- known unknowns

If the request is sparse, infer only low-risk basics and keep the rest as explicit assumptions or open questions.

## 3. Decide whether research is required

Run live research when requirements depend on:

- current market or competitor claims
- recent product, user, legal, platform, or technical facts
- specific metrics, benchmarks, prices, policies, or APIs the user did not provide
- safety, compliance, or financial claims

Research rules:

- Use distinct queries from different angles.
- Prefer official, primary, or otherwise authoritative sources.
- Stop when the evidence is sufficient to support package decisions.
- Record queries, links, retrieval dates, and evidence gaps in `sources.md`.

Skip external research when the user provided enough context and the package can safely mark remaining unknowns.

## 4. Draft in dependency order

Use this order for new packages:

1. `sources.md` working context, provided constraints, and research notes
2. `prd.md` product decision record and requirement IDs
3. `feature-spec.md` functional behavior derived from PRD requirements
4. `user-flow.md` user paths derived from user-facing feature behavior
5. `wireframe.md` low-fidelity screen structure derived from user-flow steps and states
6. `diagram.md`, `diagram.data.json`, and rendered `diagram.svg` as the planning map wrapper
7. `preview.html` local browser preview

This order keeps the PRD as the source of product truth and downstream docs as derived review artifacts. Do not draft the feature spec, user flow, or wireframe as independent documents disconnected from the PRD.

## 5. Apply the layered handoff contract

Use this traceability chain:

| Source artifact | Must hand off | Downstream artifact |
|---|---|---|
| `prd.md` | Requirement IDs, goals, scope, non-goals, metrics, risks, open questions | `feature-spec.md` |
| `feature-spec.md` | Feature requirement IDs, triggers, states, permissions, errors, acceptance criteria | `user-flow.md` |
| `user-flow.md` | Actors, entry points, decision points, happy/alternate/error paths, screen-state needs | `wireframe.md` |
| `wireframe.md` | Screen IDs, layout blocks, state variants, unresolved design/product questions | `diagram.md` and `preview.html` |

When a downstream artifact reveals a missing decision, update the upstream artifact or add an explicit open question there. Do not hide the gap only in the downstream file.

## 6. Update instead of rewrite

When updating:

- read all existing package files first
- preserve decisions that still hold
- patch only affected sections
- append a dated change-history row to `prd.md`
- update downstream docs when PRD changes affect behavior, flows, or screens
- add new evidence to `sources.md` instead of deleting earlier evidence unless it is clearly obsolete
- rebuild `diagram.svg` and `preview.html` after package content, diagram data, or source-log changes

## 7. Keep artifacts aligned

After drafting or updating, check cross-document consistency:

- every must-have PRD requirement appears in `feature-spec.md`
- every feature-spec behavior has a user-flow path or explicit non-user-facing note
- every user-facing flow has a wireframe screen or screen-state entry
- the diagram has a central initiative node and branches for PRD, feature spec, user flow, wireframe, and open questions
- `preview.html` reflects the latest package files and rendered diagram
- every research-backed non-obvious claim has a source entry
- every unresolved ambiguity is visible in open questions or assumptions

## Sources

> No external sources; content checked 2026-09-21.

This file states this package's own create/update workflow and layered handoff contract. It cites no external URL and asserts no external fact, so no external source is recorded.
