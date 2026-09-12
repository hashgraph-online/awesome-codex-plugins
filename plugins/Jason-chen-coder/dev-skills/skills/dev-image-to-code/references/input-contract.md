# Input Contract

Use this reference when dimensions, the target, assets, or business meaning are
unclear. Ordinary reconstruction does not require a separate intake document.

## Establish The Baseline

The `ui_image` is required. Use `design_size` from the user when supplied and
record its source as `user-provided`. Otherwise run `scripts/image-metadata.mjs`
or inspect metadata, use the image pixel dimensions provisionally, and record
`inferred-from-image-pixels`. Do not stop merely to ask whether a size is known.

Image pixels may differ from CSS pixels because of device pixel ratio, cropping,
or resizing. Check the image proportions against the target project and user
notes. Ask when the mismatch changes a material layout decision, especially for
an exact-fidelity request. Do not label a provisional baseline as measured CSS
dimensions.

Infer the stack and component library from the target app. Ask about the target
when multiple plausible apps remain and choosing one would change scope. In an
empty directory, a standalone HTML/CSS/JS page is a reasonable default.

## Decide What Needs Clarification

Use existing source, assets, or notes before asking. Distinguish:

| Missing detail | Response |
|---|---|
| Exact spacing, font weight, or radius | Choose the closest measured/local value and verify visually |
| Unshown mobile layout | Apply conservative responsive constraints; disclose inferred behavior |
| Unknown brand font or key asset | Search supplied/local assets; disclose substitution, ask if exact fidelity depends on it |
| Unreadable business-critical label | Ask or leave that label explicitly unresolved; continue other regions |
| Unknown tab panel, options, or route | Reuse documented content; otherwise report the gap without inventing business data |
| Backend action, permissions, payment, or destructive effect | Resolve the contract and authorization before wiring the action |
| Decorative glyph or ambiguous visual state | Use context and visual evidence; ask only if its meaning changes behavior |

Batch related blocking questions concisely. State the specific decision and
why it matters. A question about one region does not block unrelated layout work.

## Optional Intake Notes

For a complex screen, record this information in existing task notes or a small
`UI_RECON.md`; omit fields that do not help implementation or verification:

```markdown
- Source image:
- Design size and source:
- Target route/platform:
- Required fidelity and viewports:
- Missing assets or business details:
- Provisional decisions:
```
