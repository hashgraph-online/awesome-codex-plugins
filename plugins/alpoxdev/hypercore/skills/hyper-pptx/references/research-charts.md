# Research: Charts

How the chart parts of this package were chosen, and which OOXML rules the ECMA-376 schema actually enforces. A chart that PowerPoint tolerates but the schema rejects is a chart that a strict reader drops, so the schema is the gate here.

## 1. Chart Types And When To Use Them

Ten types are implemented. The list is short on purpose: each entry answers one shape of argument, and a deck that needs an eleventh usually needs two slides.

| Type | The argument it makes | Failure mode it prevents |
|---|---|---|
| `column` | comparing a few categories | — |
| `bar` | comparing categories with long names | rotated labels when vertical |
| `stacked` | composition over a few periods | — |
| `stackedBar` | composition across long-named categories | — |
| `line` | change over time | bars imply discrete periods |
| `area` | change over time with volume | a line understates the total |
| `scatter` | relationship between two measures | a line implies a shared time axis |
| `pie` | one moment's composition, three to five slices | — |
| `doughnut` | the same, with room in the centre for a total | — |
| `combo` | two units on one page | a rate line flattened against a volume scale |

## 2. The Combo Problem

A combo exists because a deck often means "volume went up but the rate went down". Two series with different units on one axis is a lie: the rate line sits on the baseline and reads as zero.

OOXML represents a combo as two chart groups inside one `chartSpace`, sharing a category axis and each holding its own value axis. The plot area holds `barChart` and `lineChart` in sequence; the axis list holds one `catAx` and two `valAx`.

The second value axis must not draw gridlines, or the reader sees two sets of horizontal rules that disagree. It is positioned right, crosses at the category axis's maximum, and is left visible so the reader can see the scale the line uses.

The bar half and the line half both need their axis ids as the **last children** of their group. PowerPoint tolerates their absence; the ECMA schema does not. A strict reader drops the whole chart when they are missing.

## 3. Schema Rules That Bit

| Rule | What happened |
|---|---|
| `c:legendPos` accepts `b`, `t`, `l`, `r`, `tr` only | `val="bottom"` validates in PowerPoint's lenient parser and fails the schema; hide a legend by omitting the element, not by a "none" value |
| `c:barChart` ends with `<c:axId>` pairs | Seven groups were missing them; the schema reported the chart as invalid |
| `a:tcPr` is a sequence with borders before the fill | `lnB` after `solidFill` in a table cell fails the whole slide part |
| `c:ser` children are ordered | `spPr`, `marker`, `dLbls`, `xVal`, `yVal`, `smooth` in that order |

The lesson is that "PowerPoint opens it" is not a gate. The gate is `xmllint --schema` against the ECMA-376 XSD, and the package is checked with it before delivery.

## 4. Cached Values And The Workbook

Every chart series carries `numCache` with a format code and the points, so a reader shows the picture without opening the workbook. But a chart with no embedded worksheet shows an empty "Edit Data" dialog, which makes the deck look broken to the person who wants to change a number.

This package writes a minimal spreadsheet per chart into `ppt/embeddings/`, linked from the chart's relationships, with the categories in column A and each series in its own column. If a reader edits the data, the edit lands somewhere real.

## 5. Labels And Scatter

A scatter needs an x value per point. The spec carries one number per point plus a category label, so the label is the x when every label parses as a number, and the point's position is the x when it does not. Using the value for both axes draws a diagonal, which is never what the author meant — this was a real defect found by viewing the render, not by reading the schema.

Chart text at 8 points is invisible in a projected room. Axis and data labels are set at 12 points in the package and 15 to 16 CSS pixels in the preview, so the two agree.

## 6. What Was Not Implemented

- Trendlines, error bars, and secondary pie-of-pie: each needs its own dialog and is rare enough that a deck can be built without it.
- 3D variants: they cost readability for decoration.
- Axis breaks and log scales: a deck that needs a log axis needs a different chart.

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| Chart parts, chart groups, and cached values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| The ECMA-376 DrawingML chart schema (`c:legendPos`, `c:barChart`, `c:ser` order) | <https://www.ecma-international.org/publications-and-standards/standards/ecma-376/> |
| Combo charts as two groups over shared axes | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| Chart XML produced by a mature library | <https://github.com/gitbrent/PptxGenJS> |
| Grey-first emphasis and one accent per chart | <https://github.com/mpuig/agent-slides> |

### Evidence grade

`LOCAL` — the schema findings were produced by validating this package's own output with `xmllint` against the ECMA-376 XSD on 2026-11-14; each listed violation was reproduced and then fixed. The combo secondary-axis requirement is specification-based: PowerPoint itself was not available to confirm what it does with a single axis.
