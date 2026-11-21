# UI behavior: state clarity before polish

Inspect the real component and its state transitions. Surface finish, icons and
motion should support comprehension and successful action. A stationary button,
border-based elevation or shadow-free brand does not need a decorative fix.

## State coverage

List reachable default, hover, focus, active, selected, loading, empty, error,
success, disabled and permission states; mark non-applicable states with a
reason. Exercise the transitions users actually encounter, including retry,
back, cancellation and rapid repeated input where safe. Use synthetic state
seams and non-mutating actions; never submit a live payment, booking or lead.

A real production component is the subject. Do not rebuild a lookalike to claim
that component passed. For state workbenches, stress fixtures or side-by-side
variants, use suede-component-lab if available. Without it, follow the same
local fixture principles and explicitly verify production exclusion.

## Behavior to verify

- Inputs and frequent controls respond promptly and communicate pending work
  truthfully. Disabled states must not appear successful or remain actionable
  through another input method.
- A state change leaves a usable static cue; motion alone is insufficient.
  Reduced-motion users retain the information and action path.
- Hover-only cues have a keyboard/touch equivalent. Test touch behavior rather
  than assuming a desktop hover selector handles it.
- Overlays preserve a usable keyboard path, return focus appropriately, and
  do not obscure their own actions. Test scroll containment in the supported
  browser instead of adding a universal CSS recipe.
- Icons use the project's family, semantics and state conventions. Inspect
  the accessible name and actual alignment; a fixed stroke width or optical
  nudge is not a general rule.
- Surfaces distinguish grouping, selection and elevation clearly within the
  existing design. Check forced-colors behavior where relevant; shadows alone
  may disappear. Do not delete meaningful borders for aesthetic preference.

## Motion and optical choices are contextual

Preserve the local motion language. Press scaling is optional; there is no
mandatory `0.96`, easing curve, duration or stagger. Choose motion only when it
clarifies state, continuity or an authorized expressive moment. Avoid delaying
frequent tasks or animating essential content from permanently hidden defaults.

Inspect reversal, interruption and repeated interaction. Transition the
properties that change instead of `all` where that prevents unintended work.
Measure performance before adding `will-change` or a library. Transform and
opacity often avoid layout work, but that is an optimization clue, not a ban on
all other animated properties. Use the existing runtime; no new dependency is
required by this reference.

Optical alignment, nested radii and shadow strength need rendered inspection in
context. A mathematical recipe can suggest a candidate, but cannot prove a
visual defect. Respect established density, hit areas and reading order.

## Evidence after a fix

Reproduce, make only the authorized change, then recapture matching
viewport/content/state and inspect again. Include keyboard, reduced-motion and
relevant pointer checks. A screenshot proves a captured frame, not a complete
transition. State whether behavior was exercised, inferred from source or
unverified, and keep optional polish separate from task-blocking findings.
