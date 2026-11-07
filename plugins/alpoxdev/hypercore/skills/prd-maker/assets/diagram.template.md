# [Initiative Name] Planning Diagram

> Canonical source for the visual planning map. Keep this in sync with `diagram.data.json`; render `diagram.svg` with `bash scripts/render-planning-map.sh`.

## Package Links

- PRD: `./prd.md`
- Feature spec: `./feature-spec.md`
- User flow: `./user-flow.md`
- Wireframe: `./wireframe.md`
- Sources: `./sources.md`

## Diagram

```mermaid
mindmap
  root(([Initiative Name]))
    PRD
      Problem
      Goals
      Scope
      Metrics
    Feature Spec
      Requirements
      States
      Acceptance Criteria
    User Flow
      Entry Points
      Happy Path
      Edge Cases
    Wireframe
      Screens
      Components
      Empty/Error States
    Open Questions
      Product
      Design
      Technical
```

## Node Inventory

| Node | Type | Linked artifact | Notes |
|------|------|-----------------|-------|
| [Initiative Name] | root | `prd.md` | Central idea |
| PRD | branch | `prd.md` | Product decision record |
| Feature Spec | branch | `feature-spec.md` | Functional behavior |
| User Flow | branch | `user-flow.md` | Journey and states |
| Wireframe | branch | `wireframe.md` | Low-fidelity structure |
| Open Questions | branch | `prd.md` | Unresolved gaps |

## Render Notes

- Renderer used: [none / mermaid-cli / other]
- Rendered file: [none / `diagram.svg`]
- Last checked: YYYY-MM-DD
