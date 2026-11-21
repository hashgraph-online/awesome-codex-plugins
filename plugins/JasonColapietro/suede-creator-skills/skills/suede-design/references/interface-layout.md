# Layout: keep the task reachable

Reuse the existing grid, density, spacing tokens and responsive strategy.
Review grouping, reading order and adaptation through real content. A value
that differs from a favored spacing multiplier is not a finding.

## Inspect before proposing structure

Identify the entry point, primary action, supporting facts and completion or
recovery path. Record how the current layout communicates their relationship.
For a whole flow, follow the transitions instead of judging one ideal screen.
For a diff, trace shared containers and direct consumers of changed layout rules.

Check that source order, visible order and keyboard order form a usable
sequence. A CSS reorder is a lead to test, not automatic proof of failure.
Look for controls obscured by sticky content, collisions, text overlap and
unreachable off-screen actions. Confirm actual bounds and scrolling behavior.

Keep intentional borders, cards, rows, asymmetry and compact density when they
help users understand the task. Nested reading cards can express hierarchy;
a borderless row is not inherently better. Diagnose competing emphasis or
ambiguous grouping with evidence before changing the container model.

## Stress representative content

- Use desktop/mobile sizes from the supported product, plus narrow reflow and
  relevant zoom/text-size checks. Record exact dimensions; test around an
  observed breakpoint rather than choosing only popular device presets.
- Include loading, empty, error, success, focus, disabled and permission states
  where applicable. A state that does not exist needs an honest gap note.
- Try long permitted labels, realistic empty/large datasets and translated
  strings. Use clearly synthetic examples without replacing approved copy in
  production. Test supported RTL with logical properties and meaningful order.
- Inspect flex/grid shrink behavior, intrinsic media width, min/max sizing,
  content wrapping and fixed-height text boxes before adding a breakpoint.
- Check that virtual keyboards, safe-area chrome, sticky headers and overlays
  leave the next action reachable. Do not assume `100vh`/`100dvh` by themselves
  prove the mobile keyboard case; reproduce on the relevant runtime.
- Where truncation is intentional, establish a usable route to the full value
  when the task needs it. A hover-only tooltip is insufficient on touch.

## Choose the smallest correction

Prefer an existing container/token adjustment or proper intrinsic sizing over
leaf offsets. Depending on the demonstrated cause, `min-width: 0`, a wrapping
row, `minmax(0, 1fr)`, a sensible minimum height, a supported container query or
an existing breakpoint may be appropriate. These are candidates to test, not
blanket replacements. Preserve unrelated layout intent and density.

For example, if a shared form shell overflows at 390 px because a fixed child
and its padding exceed available width, report that shared sizing cause. Do
not redesign every form or rewrite its offer. Render the correction at matching
width/state and inspect both the narrow case and a representative wide consumer.

Report the concrete lost content/action or grouping error, its scope and the
smallest scoped fix. Suggest a different composition separately only when it
has a plausible task/conversion benefit; no invented uplift claims.
