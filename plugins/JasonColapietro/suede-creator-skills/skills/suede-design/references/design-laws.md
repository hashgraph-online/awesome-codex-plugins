# Design principles and domain checks

Use these checks for the user's task and the product's existing design system.
The filename is retained for compatibility; not every design preference is a
law. Successful task completion, conversion, accessibility and reuse take
priority over decorative novelty.

## Choose the relevant reference

| Domain | Read when | Evidence to collect |
| --- | --- | --- |
| [Accessibility](interface-accessibility.md) | Controls, forms, navigation, focus, permissions or status change | Semantics, keyboard path, relevant assistive-technology behavior and measured pairs |
| [Layout](interface-layout.md) | Structure, density, responsiveness, overflow or localization | Actual bounds, reading order, narrow/zoom states and full action path |
| [Interface writing](interface-writing.md) | Labels, errors, confirmations or state copy | Existing vocabulary, invoked action, approved claims and recovery behavior |
| [Typography](interface-typography.md) | Hierarchy, fonts, wrapping, numbers or text adaptation | Loaded fonts, computed values, real strings and reflow |
| [Color](interface-color.md) | Tokens, themes, state meaning or contrast | Semantic token consumers, composited foreground/background and measured ratios |
| [UI behavior](interface-behavior.md) | Surfaces, icons, motion or interaction polish | State transitions, actual feedback, reduced motion and pointer/keyboard behavior |

For a complete flow, inspect all six and disclose missing coverage. For a
specific concern, load the relevant references; do not turn it into a full
restyle. Read [interface review](interface-review.md) for a read-only audit or
change review, including exact scope and attribution.

## What makes a finding

1. **Standard:** identify the applicable standard and criterion; test its
   conditions and exceptions before claiming a failure.
2. **Project convention:** cite the agreed rule or shared implementation and
   show the inconsistent behavior and impact.
3. **Suggestion:** name the possible improvement and its tradeoff. It is not a
   defect solely because a reviewer prefers it.

No palette, color notation, font pairing, spacing multiplier, border treatment,
optical offset, pressed scale, easing or stagger recipe is universal. Pure
black/white, one font family, compact density, nested cards and no motion can
all be deliberate. Preserve them unless demonstrated harm or an authorized
redesign calls for change.

Prefer existing native controls and local components. When several symptoms
share a token or component, report one root cause, list confirmed consumers and
propose the smallest correction at that source. New tokens or overrides need a
role the existing system cannot express; do not migrate systems during a fix.

For new designs, a clear hierarchy, reusable semantic roles, readable type and
consistent spacing are useful starting points. Optional signature treatments
must serve the product. In Suede marketing work, a user-selected authoritative
visual kit may define the treatment; inspect its original pixels first. A kit
never becomes the default style for unrelated product UI.

## Verification discipline

Use representative desktop/mobile content and loading, empty, error, success,
focus, disabled and permission states where applicable. Do not simulate a
production component by rebuilding its appearance. Use the real component and
synthetic state seams; route reusable workbenches to suede-component-lab.

Observe → make an authorized fix → render again at matching viewport/state →
inspect again. Source checks support source claims; they cannot prove layout,
focus visibility, final composited contrast or interaction behavior. Record
untested states and concrete blockers. Never turn a heuristic score into a
security, accessibility-conformance or conversion-uplift certification.
