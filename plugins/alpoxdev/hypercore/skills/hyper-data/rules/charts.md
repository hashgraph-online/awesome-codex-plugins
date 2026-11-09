# Charts

Read this rule only when the user asked for a chart. A chart is never a default; the number or a short table answers most questions and decoration dilutes the answer. When a chart is requested, this rule decides its type, its time handling, and what to check before delivery.

## 1. When to Chart

- Chart when the user asked for one. Default to no chart: the number and a five-row table answer most questions.
- A trend over time, a distribution, a comparison across many categories, or a relationship between variables is a shape prose cannot carry. In those cases a chart may accompany the answer, and the text still states the finding.
- One chart answers one question. A chart with three panels answers two questions badly.

## 2. Type Follows the Question

| Question shape | Chart |
|---|---|
| How did this change over time | Line, datetime x-axis |
| Which categories are biggest | Horizontal bar, sorted by value |
| How is this distributed | Histogram with a tuned bin count, or a box plot per group |
| Is X related to Y | Scatter; add a trend line only when it aids the eye |
| What is the composition of a whole | Stacked or 100% bar; pie only for four or fewer slices |
| Many series over time | Small multiples, not one spaghetti chart |

- Sort categorical bars by value, never alphabetically.
- The title states the finding ("Seoul overtook Busan in March"), not the dataset name. Axis labels carry units.
- A chart forced into a wrong type misleads faster than prose that stays numeric.

## 3. Time Zone and Partial Buckets

- Cut daily, weekly, and monthly buckets in the reader's time zone, not in the execution machine's zone and not silently in UTC. Name that zone in the axis label or the caption. Resolve an unknown zone before bucketing.
- Mark an unfinished bucket (today, this week, this month) as partial on its own bar with a lighter fill or a hatch and a label. A partial bucket shown as a normal bar reads as a drop in the data.
- When the cutoff sits mid-day (a daily bucket that starts at the reader's midnight), state that the day boundary is local.

## 4. Quality and Rendering

- Size for the medium: standalone plots read well around `figsize=(10, 6)` at default dpi; documents want `dpi=150` or more at export. Call `tight_layout()` (or `constrained_layout=True`) before saving; clipped labels are the most common chart defect.
- The default color cycle is fine. Avoid rainbow palettes, 3D bars, and decoration that carries no meaning.
- Few series: label lines directly, or keep the legend inside empty plot space. Many series: gray the context and color only the series that answers the question.
- With matplotlib, save a standalone PNG beside the report with `plt.savefig(path, dpi=150, bbox_inches="tight")`. HTML output is another output shape; this skill's chart is the rendered file itself.

## 5. CJK Fonts

Matplotlib's default font renders CJK as empty boxes (tofu). Set the fallback before plotting whenever any label or title contains CJK:

```python
import platform
import matplotlib
cjk = {"Darwin": "AppleGothic", "Windows": "Malgun Gothic"}.get(platform.system(), "Noto Sans CJK KR")
matplotlib.rcParams["font.family"] = [cjk, "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False   # keeps the minus sign rendering
```

Probe the font and the engine before plotting; never auto-install fonts or libraries.

## 6. Cross-Check and Inspection

- Cross-check one figure: recompute a headline number from a second source (another table, the system's own total, or a raw count). Name that source beside the chart, state whether it agrees, and quantify any difference. When no second source is available, disclose that the cross-check is unverified; never invent agreement.
- Inspect the rendered file before delivery. Open the image the script actually wrote and check four things: labels readable and unclipped, no tofu or mojibake, nothing overlapping, and the chart shows the finding the title claims. A failed check means fix and re-render, not ship with a caveat. A chart nobody inspected is not evidence.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Charting only when asked or when the answer is a shape prose cannot carry, and the type table | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| Bucketing in the reader's time zone and marking partial buckets on the bar itself | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| Cross-checking one figure from a second source and disclosing it as unverified when unavailable | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| The CJK fallback and `axes.unicode_minus = False` | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| Inspecting the rendered chart before delivery | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - the type table, the CJK fallback lines, and the inspection checklist are re-authored mechanism rows from a public repository at a pinned commit that carries no license. The port keeps the matplotlib route only; the browser-artifact route is a different output shape and is not named here.
