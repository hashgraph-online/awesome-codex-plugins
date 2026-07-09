# Implementation Paths

Choose the implementation path after image analysis and clarification.

## Decision Tree

| Context | Default path | Notes |
|---|---|---|
| Existing project with matching components | Reuse local components | Inspect imports and nearby screens first |
| Existing project, no matching components | Add scoped components | Keep styling local and token-based |
| Empty directory or standalone request | HTML/CSS/JS | Keep it runnable without a build step when possible |
| React/Vue/Next app | Use existing routes/components | Preserve state, i18n, styling, and test patterns |
| Flutter app | Use existing widgets/theme | Verify with targeted widget or golden-like checks where available |
| Mobile image | Fixed design width plus responsive constraints | Keep touch targets usable |
| Multiple images/states | Shared components plus state map | Do not duplicate per-screen markup |
| SaaS/admin UI | Semantic table/form/card components | Prioritize density, alignment, repeat actions |
| Chart/map/canvas/3D UI | Ask for data and interaction semantics | Static approximation must be explicit |

## Existing Project Rules

Before editing:

- Read project instructions and design context.
- Identify the target file or route.
- Search for similar local screens/components.
- Use the existing component library before native HTML or third-party widgets.
- Use existing theme variables, rem rules, breakpoints, and icon libraries.
- Keep copy in the existing i18n system if the project uses one.

Do not introduce a new UI library, icon set, CSS framework, chart library, or
state manager just to match one screenshot unless the user approves it.

## Standalone Web Rules

When no project is present:

- Create the smallest runnable artifact.
- Use semantic HTML and scoped CSS.
- Use CSS custom properties for design tokens.
- Use fixed design-size preview styles first, then optional responsive behavior.
- Avoid external network assets unless the user supplied them or approved them.

## Responsive Rules

The provided design size proves one breakpoint only.

- If the user asks for exact reconstruction, match the design size first.
- If the user asks for responsive behavior, ask which breakpoints matter unless
  the project already defines them.
- If no breakpoints are provided, make conservative responsive constraints:
  fluid containers, no overlap, readable text, usable touch targets.
- Do not claim mobile fidelity from a desktop-only image.

## Data And Interaction Rules

Static UI images do not prove business logic.

- Use mock data only when implementing a static prototype or when the project has
  established fixtures.
- Implement visible control semantics when the control type is clear from the
  screenshot or local project context.
- Ask before wiring destructive actions, navigation destinations, hidden tab
  panels, dropdown option lists, filters, sorting, pagination, chart data, map
  layers, uploads, payments, or auth.
- Preserve visible states from the image. Hidden states require user or project
  evidence.

## Minimum Semantic Controls

Even for a standalone web simulation, use real controls for clear UI elements:

| Visible element | Standalone HTML baseline | Existing app baseline |
|---|---|---|
| Primary/secondary action | `<button>` | Project button component |
| Text/numeric/search input | `<input>` | Project input/form component |
| Dropdown/select | `<select>` or ARIA combobox | Project select component |
| Tabs/segmented control | `<button role="tab">` inside `role="tablist"` plus panels | Project tabs component |
| Checkbox/radio/switch | Native control with label | Project form component |
| Expand/collapse row | `<button aria-expanded>` plus region | Project accordion/disclosure |
| Data grid/table | `<table>` where tabular | Project table/grid component |

When hidden options or panels are unknown, use the visible value/state and a
documented placeholder/no-op for the hidden behavior, then ask the user before
inventing real content.

## Implementation Quality Checklist

- The screen renders at the design size without scrollbars unless the image
  implies scroll.
- Text does not overflow or overlap.
- Clear controls are semantic and keyboard focusable.
- Visible interactions have no console errors when smoke-tested.
- Dynamic labels cannot resize fixed-format UI unexpectedly.
- Icons and buttons have stable dimensions.
- Colors and spacing are tokenized or aligned to the project style system.
- The code is scoped to the requested screen.
- Verification commands are fresh and recorded.
