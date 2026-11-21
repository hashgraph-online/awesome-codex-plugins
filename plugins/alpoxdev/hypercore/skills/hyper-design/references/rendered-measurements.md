# Rendered Measurements

Read whenever a rendered-evidence handoff is reviewed or a claim depends on what the browser drew. A static source review never measures contrast, type size, spacing rhythm, overlap, or overflow; those are only numeric when a browser capability produces them.

## 1. What a renderer must produce

A browser capability that claims rendered measurements **MUST** produce numbers, not adjectives. Each capture records the viewport width and height, the surface state, and per-observation values at every checked width. The default checked widths are 375, 768, and 1280 CSS px, with the 320 px reflow check every layout owes; `rules/craft-floor.md` §4 owns the set, and project breakpoints override it when known.

- Computed foreground and painted background color pairs as `#rgb` or `#rrggbb` hex, foreground first. The background is the color actually painted under the text, including any scrim.
- Computed font size per text role (`display`, `heading`, `body`, `caption`, `control`) in CSS px, measured from the layout rather than read from the stylesheet.
- Vertical gap between each heading and its first content block, in CSS px.
- Element rectangles for overlap checks: the text box (`textRect`) and the container box (`rect`), each with `x`, `y`, `width`, and `height`.
- Horizontal overflow per checked width, in CSS px past the viewport edge, with a stress string (a long unbroken token) present so the measurement exercises wrapping.
- The exact `stressString` value used, so another renderer can repeat the same measurement.

A measurement is only a number with a locator and a viewport. A screenshot supports spacing and asset-fit discussion; it is never proof of contrast, type size, overlap, or overflow.

## 2. Thresholds the collector applies

`scripts/collect-rendered-evidence.sh` computes three finding types from these numbers. Each finding carries the locator, viewport, state, measured value, threshold, and whether it failed.

- **Contrast.** The WCAG 2.x ratio `(L1 + 0.05) / (L2 + 0.05)` over linearized relative luminance, computed in jq with the same `0.03928` linearization threshold as the contrast-check awk command. Below 4.5 the pair fails for normal text. The unrounded ratio decides; the stored `ratio` is the rounded display value.
- **Overlap.** The smaller of the shared horizontal and vertical extents of two distinct observations' `textRect` values, within one capture and width. Above 4 CSS px of text-on-text overlap the finding fails.
- **Overflow.** A numeric `overflowX` above 2 CSS px at a checked width fails, and the finding records that width.

## 3. When measurements do not exist

When no browser capability exists, or a handoff carries none of these fields, the measurement status is `not_run` with a reason. It is never a pass. A handoff with measurements that meet every threshold reports them and still passes; a handoff with a failing measurement never passes as rendered evidence.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Relative luminance, the `0.03928` linearization threshold, the contrast ratio, and the 4.5:1 threshold for normal text | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (definitions of relative luminance and contrast ratio) |
| The idea of treating a rendered measurement set as a linter over numeric findings (contrast on the painted background, computed type sizes, overlap, overflow) | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |
| The 4px overlap and 2px overflow finding thresholds, and the `not_run` rule for missing measurements | this package's own choice, stated in §2 and §3 above |

### Evidence grade

The contrast formula is normative WCAG 2.2; the worked values (`#999999` on `#ffffff` = 2.85, `#000000` on `#ffffff` = 21.00) are reproducible from the reference table in `contrast-check.md`. The overlap and overflow thresholds are this package's contract, not a WCAG requirement.
