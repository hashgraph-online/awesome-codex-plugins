# Accessibility: prove the usable path

Review the intended task with keyboard and relevant assistive technology, not
only an automated score. Start with native elements, existing accessible
components and actual names/roles/states. A missing accessibility tool is a
coverage limitation, not permission to invent a screen-reader pass.

## Standards versus conventions

Use the project's specified conformance target. For a web review without one,
WCAG 2.2 A/AA is a useful stated review baseline, not a legal determination or
claim that this checklist establishes conformance. Verify conditions and
exceptions in the [W3C recommendation](https://www.w3.org/TR/WCAG22/).

| Area | Relevant WCAG 2.2 criteria | Inspect |
| --- | --- | --- |
| Controls | 4.1.2, 2.5.3 | Programmatic name, role and current state; visible label agrees |
| Keyboard | 2.1.1, 2.1.2, 2.4.3 | Operability, escape and meaningful focus order |
| Focus | 2.4.7, 2.4.11 | Visible indicator; focused component not fully hidden by author content |
| Forms | 3.3.1, 3.3.2, 3.3.3 | Labels, identified errors and useful correction |
| Status | 4.1.3 | Meaningful updates exposed without unnecessary focus changes |
| Contrast | 1.4.3, 1.4.11 | Required text: 4.5:1, large text: 3:1; qualifying UI/graphics: 3:1 |
| Adaptation | 1.4.4, 1.4.10, 1.4.12 | 200% text resize, 320 CSS px reflow and prescribed text-spacing changes |
| Targets | 2.5.8 | 24 × 24 CSS px or an applicable criterion exception |

These are abbreviated checks, not complete criterion text. Large targets such
as 44 px, one-H1 conventions, particular focus-ring geometry and APG patterns
must not be mislabeled mandatory AA thresholds. AAA criteria and project rules
need separate labels. Reduced-motion support is a product requirement here;
identify the relevant standard separately rather than calling every animation
without a media query an A/AA failure.

## Test the real interaction

1. Start at the flow's entry. Use Tab/Shift+Tab and appropriate native keys to
   reach controls, operate them, recover and finish. Record focus order and
   visible indicators, including sticky headers, dialogs and mobile overlays.
2. Inspect labels, associations, descriptions and current states. Prefer a
   native button or link to rebuilding its semantics with ARIA. Do not add
   redundant roles or hide focusable descendants with `aria-hidden`.
3. Exercise form error, pending, success and permission states with synthetic
   data and non-mutating action seams. Ensure recoverable input survives an
   error. Distinguish visual status from actual accessible announcements.
4. With available assistive technology, check announced names, roles and
   updates. A DOM snapshot or accessibility tree is useful but does not prove
   the screen-reader interaction; say what was actually used.
5. Test reflow, text resize and text-spacing adaptations without losing content
   or actions. Consider exceptions for genuinely two-dimensional content.
6. Test reduced motion and forced colors where applicable. Preserve a static
   status cue. Motion alone must not carry required meaning.

In a review, report the barrier with source and observed interaction. When a
fix is authorized, preserve brand and choose the smallest native/system-level
solution. A visual reference with invisible focus or inadequate contrast is a
conflict to flag, not a pattern to reproduce. Recheck the repaired path in the
same state and viewport; list anything untested.
