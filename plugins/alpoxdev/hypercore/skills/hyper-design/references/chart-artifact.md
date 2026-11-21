# Chart Artifact

Read when the deliverable is a numeric chart shipped as a standalone file, typically one HTML file holding bars, lines, or points for a set of values: monthly sales, cohort counts, survey shares. The screen and dashboard rules in this package describe a page inside a product; here the file is the product, and the failures are a CDN script that draws nothing offline, a first paint that waits on JavaScript, and bars whose heights never match their values.

## Contents

- 1. Offline single file
- 2. Proportional geometry
- 3. No-JavaScript first paint
- 4. Provenance note
- 5. Empty and error states

## 1. Offline single file

Inline every dependency in the file: styles in `<style>`, scripts in `<script>` without `src`, fonts as `data:` URIs or system stacks, and images as `data:` URIs. No external stylesheet, script, font, or image request. No request at all is the test: fetched assets are the failure, not a fallback.

Theme colors may use `light-dark()` so one file carries both themes without a separate stylesheet; the two resolved values are what gets checked for contrast.

## 2. Proportional geometry

Bars MUST be sized `value / axisMax * 100%` of the plot height, and axis labels MUST be positioned by percentage against the same box. The offline file MUST inline every script, style, font, and image, and the chart MUST be readable on first paint without JavaScript.

Position axis labels by percentage against the same plot box, so a label for `axisMax` sits at the top and a zero label sits at the baseline. A label placed by pixel guessing drifts the moment the plot height changes.

## 3. No-JavaScript first paint

The bars, labels, and values render as plain markup or inline SVG, so the chart is readable with JavaScript disabled. JavaScript may enhance an already readable chart, with a hover readout or a theme toggle; it never draws the chart for the first time.

## 4. Provenance note

Name the data source, the period, and how the numbers were computed in a note on the chart. Mark a partial period as partial: a half-month bar reads "정산 구간: 1–15일" rather than presenting itself as a full month. A chart that hides where its numbers came from fails delivery gate H1.

## 5. Empty and error states

Design both states in the file, not as an afterthought: the empty state says the period has no data and names the next action ("데이터가 아직 도착하지 않았습니다. 정산 파일 업로드 후 다시 확인해 주세요"), and the error state names the cause and the retry step. A blank plot is never an empty state.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Inline every script, style, font, and image; bars sized `value / axisMax * 100%` in a fixed-height plot with percentage-positioned axis labels; readable first paint without JavaScript; a "how this was computed" note; designed empty and error states | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |

### Evidence grade

The offline rule and the proportional geometry are practitioner rules with no measurements taken; the shape of the file, not a study, is the evidence.
