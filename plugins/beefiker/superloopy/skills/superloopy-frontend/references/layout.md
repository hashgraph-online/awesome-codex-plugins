# Cross-Platform Spatial Contract

Load this reference only when a material spatial claim changes. It owns task-relative placement, content exposure, size negotiation, scrolling, overflow, reflow, and adaptation across supported UI targets; the selected platform, renderer, and toolkit references own their concrete APIs.

## Activation and proportionality

Add this reference when a new or redesigned surface changes visible regions, when a region is added, removed, reordered, reparented, collapsed, or expanded, or when information hierarchy or disclosure changes spatial presentation. Also select it when scroll/fixed/sticky/overlay ownership, virtualization, breakpoints, window or container behavior, reflow, overflow, content measure, reading order, or focus traversal changes, and for a reproduced clipping, overlap, hidden-action, lost-context, or scroll failure.

Do not add it for a copy, color, accessible-name, data, or behavior-only change whose geometry and traversal stay unchanged. Record `Layout impact: unchanged — <reason>` instead.

A narrow spatial fix stays in the existing receipt with the changed invariant, owner, failure case, adjacent regression, and proof. This remains true when the existing surface is multi-region or virtualized; that architecture alone does not expand the artifact. A new or materially redesigned multi-region, virtualized, or high-consequence surface adds the relevant fields below to the proportional `UX_CONTRACT.md`; it does not require a separate layout artifact.

## Spatial ownership record

Record only the fields selected by the changed claim:

- primary task, primary content, supporting content, and the state in which each region exists;
- each region's exposure mode—`always visible`, `summary`, `on demand`, or `omitted`—and the task condition that selects it;
- disclosure label and controlling affordance when present, the source or summary state, the disclosed or destination state, and the relationship that remains understandable across them. `Always visible` and `omitted` are valid exposure decisions and do not imply a two-state control;
- collapsed and expanded states only when the selected disclosure mechanism uses collapse and expand. A details route, modal, drill-down, staged flow, or contextual reveal records its own source and destination states instead;
- semantic/model order, reading order, visual placement, and focus/traversal order, including intentional differences and how relationships remain understandable;
- layout owner and every scroll owner, plus the region that determines available width, height, and overlay bounds;
- size constraints, intrinsic or platform-derived minimums and maximums, and which regions may shrink, wrap, clip, scroll, or overflow;
- fixed, sticky, floating, modal, inspector, frozen-axis, or overlay responsibilities and the content they must not cover;
- target-derived change points grounded in content and supported bounds rather than copied device widths;
- each disclosure transition and the focus, context, and state it preserves; and
- state, selection, focus, scroll, and context that must survive each adaptation. Preserve semantic task context by default, not an exact object identity or pixel offset when content is hidden, reparented, recycled, or resized; require exact preservation only when the product contract makes it meaningful.

A reusable primitive should have one primary spatial responsibility. A shell or composite may coordinate several responsibilities when each child owner and boundary is explicit.

## Scroll, panes, and two-dimensional work

Multiple scroll regions are valid when each has a named user task and owner. Test entry, exit, wheel or gesture routing, focus visibility, restoration, and the context users need to understand which region moved. Nested scrolling without distinct task ownership is a defect; multiple scrolling is not itself a defect.

Two-dimensional scrolling is valid when the task is inherently spatial, as in a spreadsheet, canvas, timeline, map, or dense comparison surface. Preserve headers, coordinates, selection, zoom anchors, navigation alternatives, and reachable commands instead of forcing a one-column document model.

At narrow bounds, list-detail, inspector, and multi-pane work may stack, collapse, overlay, or navigate to another view. Choose from the actual task and platform convention. Preserve selection, back/return behavior, focus restoration, scroll position, and unsaved state rather than imposing one transformation on every target.

## Adaptation and content stress

Derive the matrix from supported window and container bounds, orientation or posture, system insets, text scaling, zoom, density, input, and actual layout change points. Exercise just below and above affected change points plus relevant minimum, typical, and maximum bounds.

Select applicable content stress cases: empty content, short and long labels, long paragraphs, unbroken strings, dynamic errors, taller scripts, mixed-direction text, and RTL. A visual reference or baseline width never substitutes for these target-derived cases.

## Virtualized collections

A virtualized surface preserves logical collection order, stable item identity, count or range semantics, selection, focus, scroll anchoring, and restoration even when only a subset of items is instantiated. Do not infer that every logical item must exist simultaneously in the renderer or accessibility tree. Select only affected cases from recycling, insertion and removal while scrolled, first/middle/last boundaries, variable item sizes, and offscreen navigation according to the target's semantic model; mark unaffected boundaries `N/A` with a reason instead of broadening a narrow change.

## Evidence

Prove the affected spatial claim on the actual target. For affected disclosure on that actual target, exercise its source or summary state and disclosed or destination state at the affected bounds and inputs. Exercise collapsed and expanded states only when that selected mechanism uses them. Use rendered captures for visible geometry, interaction evidence for scroll, resize, selection, focus, disclosure, and restoration, accessibility evidence for the semantics claimed, and performance evidence only when performance is claimed or risk-selected. Record the exact target, state, content, bounds, input, result, and limitation; a static screenshot cannot prove traversal or scroll ownership.
