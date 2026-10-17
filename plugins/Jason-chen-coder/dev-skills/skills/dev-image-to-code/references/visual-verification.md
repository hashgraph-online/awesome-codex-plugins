# Visual Verification

Verification is part of the skill, not a final flourish. Do not claim completion
without rendering the implementation when the target can be rendered locally.

## Browser Verification Flow

1. Start the local app or open the standalone page.
2. Capture a screenshot at the design size.
3. Collect console/runtime errors.
4. Smoke-test implemented controls.
5. Compare the implementation screenshot to the source image.
6. Fix visible drift or document accepted gaps.

Resolve `<skill-dir>` to the absolute installed skill directory. The example
evidence folder is optional; use existing task output paths when available.

```bash
node "<skill-dir>/scripts/screenshot-page.mjs" \
  --url http://127.0.0.1:5173/ \
  --out UI_RECON/<screen>/screenshots/actual.png \
  --width 1440 \
  --height 900

node "<skill-dir>/scripts/visual-diff.mjs" \
  --expected UI_RECON/<screen>/screenshots/source.png \
  --actual UI_RECON/<screen>/screenshots/actual.png \
  --out UI_RECON/<screen>/visual-diff.json \
  --diff UI_RECON/<screen>/screenshots/diff.png

node "<skill-dir>/scripts/interaction-smoke.mjs" \
  --url http://127.0.0.1:5173/ \
  --spec UI_RECON/<screen>/interaction-smoke.json \
  --width 1440 \
  --height 900 \
  --out UI_RECON/<screen>/interaction-smoke-report.json
```

Image diffs are diagnostic evidence, not a universal acceptance threshold.
Match viewport and image dimensions before comparing; inspect font rendering,
anti-aliasing, and dynamic content differences visually.

## Interaction Smoke Test

For the visible semantic controls identified during analysis, verify at least the
minimal visible behavior in a real renderer:

- Inputs/selects/comboboxes can receive focus and keep their visible value.
- Buttons are focusable/clickable and do not throw errors.
- Tabs can change active state, or inactive panels are explicitly documented as
  unknown when only one state was provided.
- Accordions/collapse rows expose `aria-expanded` and toggle known content.
- Disabled controls reject activation; focus behavior follows the native/project
  component's accessibility convention.

Use `expectFocused`, `expectValue`, or `expectAttribute` assertions with the
bundled smoke helper; a successful click alone does not verify a state change.
Inspect its per-check `ok` values and runtime errors, not just process exit status.
Use project/browser assertions when the helper cannot observe the required result.

Record results in task notes or an `Interaction Smoke Test` section in an optional
`VISUAL_REPORT.md`. If a control is intentionally no-op because hidden behavior
is unknown, record the gap instead of marking interaction fidelity complete.

## Optional VISUAL_REPORT.md Template

Use for substantial reconstructions or requested audit trails. Omit irrelevant
sections and numerical scores unless they help comparison across iterations.

```markdown
# <screen-name> Visual Report

## Verification Commands
- `<command>`

## Runtime Result
- App URL:
- Viewport:
- Console errors:
- Build/test result:

## Interaction Smoke Test
| Control | Expected visible behavior | Result | Evidence |
|---|---|---|---|

## Visual Comparison
| Dimension | Score /5 | Evidence | Notes |
|---|---:|---|---|
| Structure fidelity |  | screenshot / diff |  |
| Visual fidelity |  | screenshot / diff |  |
| Text fidelity |  | screenshot / diff |  |
| Component semantics |  | code / screenshot |  |
| Interaction/state fidelity |  | manual/browser check |  |
| Responsive behavior |  | viewport checks |  |
| Project consistency |  | source files |  |
| Maintainability |  | source files |  |

## Known Gaps
- `<gap>`

## User-Accepted Differences
- `<difference>`

## Next Iteration
- `<next step>`
```

## Scoring Guide

Score only what evidence supports.

| Dimension | 5 | 3 | 1 |
|---|---|---|---|
| Structure fidelity | Regions and hierarchy match | Main regions match | Layout differs materially |
| Visual fidelity | Colors, spacing, radius, shadows close | Main style close | Looks like another design |
| Text fidelity | All text exact | Minor unreadable/placeholder text | Important labels wrong |
| Component semantics | Components map to real controls | Some static approximations | Mostly boxes/divs |
| Interaction/state fidelity | Visible states and key interactions work | Visible states only | State semantics unclear |
| Responsive behavior | Requested breakpoints verified | Basic no-overlap scaling | Breaks outside design size |
| Project consistency | Uses local system | Some local patterns | New unrelated style system |
| Maintainability | Small, scoped, readable | Acceptable duplication | Fragile or broad changes |

## Honest Reporting

Record gaps plainly:

- Missing source assets.
- Unknown font or icon set.
- Unknown chart data.
- Unverified interaction.
- Responsive behavior inferred from one image.
- Pixel diff caused by font rendering or unavailable assets.

Do not mark a task complete solely because code was written. The rendered result
is the evidence.
