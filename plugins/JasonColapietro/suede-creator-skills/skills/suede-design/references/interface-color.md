# Color: roles, contrast and consistency

Use the project's color notation, semantic tokens and theme mechanism. A
consistent hex palette is not worse than OKLCH, and black/white is not a defect.
Do not apply Suede marketing colors to another UI or infer original brand
tokens from approximate screenshot samples.

## Trace the semantic role

Map each inspected value from primitive → semantic token → component → state.
Check themes and variants. A separator token reused for body text can silently
break when borders change; report the role mismatch and confirmed consumers.
Do not create unused ramps or migrate the whole palette to correct one pair.

State meaning must remain understandable without color alone. Validate actual
text/icon/shape cues for error, selection, success, disabled and permission
states. A hue shared by brand and destructive actions is not automatically a
violation; test whether the action's treatment communicates its consequence.

## Measure the pair that appears

Start with declared values for source analysis, then inspect computed and
composited foreground/background for a rendered claim. Account for opacity,
ancestor backgrounds, images, gradients, blending, hover/focus states and theme.
A token pair calculation is not proof of a translucent label over an image.

Report the pair, state, method, measured ratio and applicable threshold. Apply
WCAG criteria and exceptions from `interface-accessibility.md`; do not apply a
body-text threshold to every decorative or disabled element. Never invent a
contrast measurement or treat a sampled JPEG value as an original design token.

For gradients/images, inspect the portions behind the actual text and necessary
controls. If the available evidence cannot establish the pair across relevant
content, state what remains unverified instead of reporting a single average.

## Correct the shared cause when authorized

Prefer the existing semantic action or text pair. If a shared semantic value
changes, inspect confirmed consumers in both revisions. An unchanged component
can carry a regression caused by the token diff. Correct the semantic pair,
not one leaf's literal color, unless the component's role is itself wrong.

Check light/dark, hover/focus, disabled and any relevant status variants after a
fix. A one-state contrast pass does not establish the full component. Preserve
brand hue and established emphasis where an accessible value within the system
solves the issue; flag a conflicting reference and use the smallest approved
accessible solution.

For a new palette within a design brief, choose only roles the product uses.
Measure generated values and supported color-gamut behavior; notation or a
theoretical ramp does not guarantee usable pairs. Use existing project tooling,
not a newly fetched color library solely to perform the review.
