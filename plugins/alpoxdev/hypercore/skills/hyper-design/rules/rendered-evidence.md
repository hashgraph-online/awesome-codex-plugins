# Rendered Evidence

Read this rule only when browser capability exists or a user supplies a rendered-evidence JSON handoff.

## Capability gate

- Do not install Playwright, Axe, a browser, or dependencies to obtain rendered evidence.
- Without a valid handoff, report `static_only` or `unavailable`; do not claim visual hierarchy, actual contrast, keyboard, accessibility, or behavior passed.
- Validate a handoff with `scripts/collect-rendered-evidence.sh --input <capture.json>` before citing it.

## Evidence minimum

Every rendered observation needs a surface/URL, viewport width and height, state, locator, capture time, and at least one observed fact: bounding rectangle, overflow, computed style primitive, focus-visible observation, or motion-preference observation.

Use project breakpoints when known; otherwise inspect 375, 768, and 1280 widths. Inspect only states the actual surface exposes. A screenshot may support hierarchy, spacing, or asset-fit discussion, but not semantic, keyboard, WCAG, or end-to-end behavior claims.

## Coverage list

Claims about a whole surface need every surface, not a sample of them. A capture plan names each page, route, tab, modal, and scroll position that owns a changed component, plus every sibling surface that shares one of those components, before the collect step runs.

A capture belongs to the list only if its locator and state name the surface it shows. A coverage list is a checklist, not a summary: each entry carries its own verdict, and the word "most" is not an entry. Missing entries are not covered. The pass/fail rule is complete coverage with every entry passing, so one missing or failing entry keeps the review open.

When the change touches a shared component, siblings are in the list even when nothing in them was edited. A sibling that reads the same value is verified again the same way.

## Freshness and hygiene

A capture whose `capturedAt` is earlier than the newest modification time of its source files is `stale` and proves nothing. A stale result names the capture and both times, so a new capture fixes it rather than a code change. A capture at or after that time is not stale on this rule.

Capture hygiene is a field check on each capture:

- **fileSignature.** When a capture carries a file name and a `fileSignature` value, the signature states the image format; it must agree with the file extension. A `.png` file with a JPEG signature is invalid, and so is any other combination.
- **frameKind.** A capture of a page is `frameKind: page`. A capture of a window is `frameKind: window` and is not page evidence.

`collect-rendered-evidence.sh` validates `sourceMtime`, `fileSignature`, and `frameKind` and reports a stale or invalid capture. The dimensions recorded in a capture are checked against its declared viewport; a mismatch is a finding, not a correction.

```json
{
  "viewport": { "width": 375, "height": 800 },
  "state": "default",
  "capturedAt": "2026-09-03T12:00:00Z",
  "sourceMtime": "2026-09-02T09:30:00Z",
  "frameKind": "page",
  "file": "settings-375.png",
  "fileSignature": "png",
  "dimensions": { "width": 375, "height": 800 },
  "observations": [
    { "locator": "main", "rect": { "x": 0, "y": 0, "width": 375, "height": 720 } }
  ]
}
```

`sourceMtime` takes one ISO date-time or an array of them; the newest entry decides staleness. `fileSignature` is `png` or `jpeg` (`jpg` is accepted for a `.jpg` or `.jpeg` file).

## Finding boundary

A rendered finding records the viewport, state, locator, captured values, and the exact claim it supports. Static findings remain static unless an observed rendered fact independently confirms the claim.

## Measurement contract

When a handoff carries measurement fields (contrast pairs, font sizes, rect pairs, overflow), `collect-rendered-evidence.sh` computes contrast below 4.5, text-on-text overlap above 4px, and horizontal overflow above 2px as findings with locators. See `references/rendered-measurements.md` for the definitions and `references/browser-evidence-schema.md` for the fields.

## Chart geometry checks

For a chart artifact (`references/chart-artifact.md`), three geometry checks are measured on rendered output:

1. The largest bar's rendered height is within **1px** of `value / axisMax * plotHeight`.
2. The legend swatch's computed color equals the series color it names.
3. The first and last axis labels are inside the plot box, not clipped at its edges.

Without rendered measurements these three checks are `unverified`, not a pass.

Without measurement fields the status is `not_run` — never a pass. A failing measurement never passes as rendered evidence.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The idea of a per-surface coverage list, a capture older than its source being stale, and a page-only frame check | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |
| The capability gate, the minimum evidence fields, and the `static_only` / `unavailable` reporting rule | this package's own contract, stated in the sections above |
| PNG file signature `\x89PNG\r\n\x1a\n` | <https://www.w3.org/TR/png-3/> (§5.2 PNG file signature) |
| JPEG start-of-image marker `\xFF\xD8\xFF` | the JPEG specification's SOI marker, recorded here as a constant; no page was fetched and the collector matches only these leading bytes |
| The measurement contract thresholds | `references/rendered-measurements.md`, this package |

### Evidence grade

The coverage-list shape, the staleness comparison, and the `page` frame requirement are this package's contract, re-authored from an unlicensed source. The two file signatures are normative format constants; the collector matches only their leading bytes and claims nothing about the rest of the file.
