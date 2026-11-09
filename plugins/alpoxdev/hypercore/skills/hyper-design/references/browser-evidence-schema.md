# Browser Evidence Handoff Schema

Use this schema only when supplying evidence collected by an already available browser capability. The collector validates the input; it does not open a browser.

```json
{
  "version": 1,
  "surface": "http://localhost:3000/settings",
  "captures": [
    {
      "viewport": { "width": 375, "height": 800 },
      "state": "default",
      "capturedAt": "2026-08-29T12:00:00Z",
      "stressString": "supercalifragilisticexpialidocious",
      "observations": [
        {
          "locator": "button[type=submit]",
          "rect": { "x": 16, "y": 600, "width": 343, "height": 44 },
          "textRect": { "x": 32, "y": 612, "width": 200, "height": 20 },
          "role": "control",
          "fontSizePx": 16,
          "gapAbovePx": 24,
          "overflowX": false,
          "contrastPairs": [
            { "label": "label-on-surface", "foreground": "#000000", "background": "#ffffff" }
          ],
          "focusVisible": true,
          "computed": { "fontSize": "16px", "color": "#000000", "backgroundColor": "#ffffff" }
        }
      ]
    }
  ]
}
```

`state` is one of `default`, `hover`, `focus`, `active`, `disabled`, `loading`, `empty`, or `error`. `computed` contains only string primitive values. `screenshot` is optional metadata and never proof of accessibility or behavior.

## Measurement fields

The fields a measurement-capable renderer produces, consumed by `collect-rendered-evidence.sh`:

- `computed.foreground` (or `color`) and `computed.background` (or `backgroundColor`): the painted text/background pair as `#rgb` or `#rrggbb` hex. The collector computes the WCAG ratio and fails below 4.5.
- `contrastPairs`: extra pairs as `{label, foreground, background}` objects, each measured the same way.
- `fontSizePx` (or `measuredFontSize`): computed font size in CSS px for the observation's role.
- `gapAbovePx`: vertical gap above the element in CSS px.
- `textRect`: the text box rectangle. The collector compares the `textRect` boxes of distinct observations in the same capture and fails overlap above 4px; a text box inside its own container is not an overlap.
- `overflowX`: either `false` (no overflow observed) or a number of CSS px past the viewport edge; numbers above 2 fail at that capture's width.
- `stressString` (on the capture): the unbroken string present while overflow was measured.

Observations without any measurement field report `measurements.status: "not_run"`; that is never a pass. See `rendered-measurements.md` for the full definition and thresholds.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The handoff schema is this package's own JSON contract, enforced by its collector and fixtures. The measurement fields extend this package's contract with re-authored fields (no text or code copied from `dbc-hbin/omp-ulw @ 74df40f`); thresholds follow `rendered-measurements.md`. Example values are illustrative, not data taken from an external service.
