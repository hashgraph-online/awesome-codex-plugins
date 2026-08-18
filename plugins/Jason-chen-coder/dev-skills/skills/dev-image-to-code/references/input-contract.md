# Input Contract

Use this contract before analyzing or implementing a UI image.

## Required Inputs

- `ui_image`: a screenshot, exported design image, app screen, or mockup.
- `design_size`: the original design canvas size when known, such as `1440x900`
  or `375x812`.

If the user supplies only an image, ask:

```text
Please provide the design size for this UI image, for example 1440x900 or
375x812. If you do not have it, I can use the image pixel size as the fallback.
```

If the user says they do not have a design size, use the image pixel dimensions
as the design size and record:

```markdown
- Design size: <width>x<height>
- Design size source: inferred-from-image-pixels
```

If the user gives a design size, record:

```markdown
- Design size: <width>x<height>
- Design size source: user-provided
```

## Stop-And-Ask Rule

Ask the user whenever a material detail cannot be confirmed from one of these:

- The UI image.
- Image metadata.
- Existing project code and design system.
- User-provided notes.

Do not continue implementation with unresolved material `GUESS` items.

## What Counts As Material Uncertainty

- Text is unreadable, cropped, or OCR is uncertain.
- Icon meaning is unclear.
- A visual block could be multiple component types.
- A state is unclear: selected, disabled, error, hover, loading, active.
- The screen's target platform or framework is unclear and cannot be inferred
  from the project.
- The user wants responsive behavior but only one breakpoint is provided.
- A chart, map, table, or data visualization needs real data semantics.
- A static screenshot implies hidden interactions or workflow rules.
- The image shows brand assets, fonts, or icons that are not available locally.

## How To Ask

Ask short, concrete questions. Prefer one to three questions at a time.

Good:

```text
I need two confirmations before coding:
1. Is the right-side block a real table or a static summary list?
2. Should this screen only target 1440x900, or should I also adapt it for mobile?
```

Bad:

```text
Please clarify the design.
```

## Fallback Rules

- If the image dimensions are used as the design size, treat exact pixel matching
  as less certain and note the fallback in `UI_RECON.md`.
- If the target stack is not specified but the current directory is an app, infer
  the stack from the repo. If multiple plausible apps exist, ask.
- If the current directory is not an app and no stack is specified, default to a
  standalone HTML/CSS/JS implementation.
- If the user asks for exact fidelity but key assets are missing, ask for the
  assets or document which parts must be approximated.

## Intake Checklist

```markdown
## Input
- UI image:
- Design size:
- Design size source: user-provided / inferred-from-image-pixels
- Target project or output:
- Target platform:
- Known constraints:

## Open Questions
- [ ] ...
```
