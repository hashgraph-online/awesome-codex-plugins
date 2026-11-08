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
      "observations": [
        {
          "locator": "button[type=submit]",
          "rect": { "x": 16, "y": 600, "width": 343, "height": 44 },
          "overflowX": false,
          "focusVisible": true,
          "computed": { "fontSize": "16px", "color": "rgb(0, 0, 0)" }
        }
      ]
    }
  ]
}
```

`state` is one of `default`, `hover`, `focus`, `active`, `disabled`, `loading`, `empty`, or `error`. `computed` contains only string primitive values. `screenshot` is optional metadata and never proof of accessibility or behavior.

## Sources

> Claims checked 2026-09-21. No external source was used in this file.

The handoff schema is this package's own JSON contract, enforced by its collector and fixtures. The example values are illustrative, not data taken from an external service.
