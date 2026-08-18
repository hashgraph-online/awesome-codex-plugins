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

Use:

```bash
node skills/dev-image-to-code/scripts/screenshot-page.mjs \
  --url http://127.0.0.1:5173/ \
  --out UI_RECON/<screen>/screenshots/actual.png \
  --width 1440 \
  --height 900

node skills/dev-image-to-code/scripts/visual-diff.mjs \
  --expected UI_RECON/<screen>/screenshots/source.png \
  --actual UI_RECON/<screen>/screenshots/actual.png \
  --out UI_RECON/<screen>/visual-diff.json \
  --diff UI_RECON/<screen>/screenshots/diff.png

node skills/dev-image-to-code/scripts/interaction-smoke.mjs \
  --url http://127.0.0.1:5173/ \
  --spec UI_RECON/<screen>/interaction-smoke.json \
  --width 1440 \
  --height 900 \
  --out UI_RECON/<screen>/interaction-smoke-report.json
```

Paths may differ when the skill is installed globally; adjust script paths to
the installed skill location.

## Interaction Smoke Test

For every visible semantic control listed in `UI_RECON.md`, verify at least the
minimal visible behavior in a real renderer:

- Inputs/selects/comboboxes can receive focus and keep their visible value.
- Buttons are focusable/clickable and do not throw errors.
- Tabs can change active state, or inactive panels are explicitly documented as
  unknown when only one state was provided.
- Accordions/collapse rows expose `aria-expanded` and toggle known content.
- Disabled controls are not clickable/focusable when that state is visible.

Record this as an `Interaction Smoke Test` section in `VISUAL_REPORT.md`. If a
control is intentionally no-op because hidden behavior is unknown, record the
question or gap instead of marking interaction fidelity complete.

## VISUAL_REPORT.md Template

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
