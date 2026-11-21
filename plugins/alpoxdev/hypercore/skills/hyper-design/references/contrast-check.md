# Contrast Check

Read whenever a text, icon, border, or focus color pair is judged, and before writing "passes AA" anywhere. The eye overestimates contrast on gray pairs, so a pair is never asserted to pass without computing it.

## 1. Formula (WCAG 2.x)

1. Convert each channel to 0-1: `c = value / 255`.
2. Linearize: `c / 12.92` when `c <= 0.03928`, otherwise `((c + 0.055) / 1.055) ^ 2.4`.
3. Relative luminance: `L = 0.2126 R + 0.7152 G + 0.0722 B`.
4. Ratio: `(L1 + 0.05) / (L2 + 0.05)`, with `L1` the lighter color. The range is 1 to 21.
5. Compare the unrounded ratio with 4.5 (normal text) and 3.0 (large text, icons, control boundaries, focus indicators). Round only for display: 4.4983 prints as 4.50 and still fails 4.5.

## 2. Command

Paste this function into a POSIX shell (bash, zsh) and call it with two opaque hex colors, text first. It needs only `awk`, and it does not write files.

```bash
contrast() {
  awk -v fg="$1" -v bg="$2" '
    function hexval(h,  i, c, v) { h = tolower(h); v = 0
      for (i = 1; i <= length(h); i++) { c = index("0123456789abcdef", substr(h, i, 1)) - 1
        if (c < 0) return -1; v = v * 16 + c } return v }
    function lum(hex,  r, g, b) { sub(/^#/, "", hex)
      if (length(hex) == 3) hex = substr(hex,1,1) substr(hex,1,1) substr(hex,2,1) substr(hex,2,1) substr(hex,3,1) substr(hex,3,1)
      if (length(hex) != 6) { bad = 1; return 0 }
      r = lin(hexval(substr(hex,1,2))); g = lin(hexval(substr(hex,3,2))); b = lin(hexval(substr(hex,5,2)))
      return 0.2126 * r + 0.7152 * g + 0.0722 * b }
    function lin(v,  c) { if (v < 0) { bad = 1; return 0 } c = v / 255
      return (c <= 0.03928) ? c / 12.92 : ((c + 0.055) / 1.055) ^ 2.4 }
    BEGIN { a = lum(fg); b = lum(bg)
      if (bad) { print "error: colors must be #rgb or #rrggbb" > "/dev/stderr"; exit 2 }
      hi = (a > b) ? a : b; lo = (a > b) ? b : a; ratio = (hi + 0.05) / (lo + 0.05)
      printf "ratio %.2f (%.4f)\n", ratio, ratio
      printf "normal text: %s (needs 4.5)\n", (ratio >= 4.5) ? "PASS" : "FAIL"
      printf "large text and non-text UI: %s (needs 3.0)\n", (ratio >= 3.0) ? "PASS" : "FAIL"
      exit (ratio >= 4.5) ? 0 : 1 }'
}
contrast "#777777" "#ffffff"
# ratio 4.48 (4.4781)
# normal text: FAIL (needs 4.5)
# large text and non-text UI: PASS (needs 3.0)
```

The function returns 0 when the pair passes 4.5, 1 when it does not, and 2 for malformed input (not `#rgb` or `#rrggbb`).

- A color with transparency is first composited over its real background: `channel = alpha * fg + (1 - alpha) * bg` per channel, then the opaque result goes into the command.
- Text over an image or gradient is checked at its worst point: sample the lightest (for light text) or darkest (for dark text) pixels under the text, including any scrim.
- Record the pair, the ratio, and the verdict in the report's gate table.

## 3. Reference Table

Values computed with the formula above; use them as a sanity check, never instead of computing a pair that is not listed.

| Text on background | Ratio | Normal text (4.5) | Large text (3.0) |
|---|---|---|---|
| `#000000` on `#ffffff` | 21.00 | pass | pass |
| `#ffffff` on `#333333` | 12.63 | pass | pass |
| `#ffffff` on `#666666` | 5.74 | pass | pass |
| `#777777` on `#ffffff` | 4.48 | fail | pass |
| `#777777` on `#070707` | 4.50 (4.4983) | fail | pass |
| `#ffffff` on `#888888` | 3.54 | fail | pass |
| `#ffffff` on `#999999` | 2.85 | fail | fail |
| `#555555` on `#000000` | 2.82 | fail | fail |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Relative luminance, the 0.03928 linearization threshold, the contrast ratio, and the 4.5:1 and 3:1 thresholds | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (definitions of relative luminance and contrast ratio) |
| The "never assert a gray pair" rule, the reference table, and the near-threshold example | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-human/SKILL.md`, The Contrast Checker; MIT, Copyright 2026 Miqdad Badjuber). Its Python checker was not copied; the command above is this package's awk implementation. |
| The command reproduces every row of the reference table and rejects malformed input | this package's execution check, 2026-11-07, macOS awk |

### Evidence grade

The formula is normative WCAG 2.2. The command was checked against the eight table rows; alpha compositing is described, not implemented, so composite first.
