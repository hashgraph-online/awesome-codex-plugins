---
name: design-tokens
description: Use when the user asks for design tokens, translate these tokens, export tokens, make a Compose color scheme from a Figma palette, audit tokens, or share a single token source across web and native. Generates, audits, and translates W3C DTCG tokens to Tailwind v4 @theme, Compose Material3 ColorScheme and Typography, SwiftUI Color/Font extensions, and WinUI ResourceDictionary. SKIP when no token work is involved.
---

# design-tokens — single source, every platform

Goal: one DTCG-format JSON, four platform outputs. No drift.

## Step 1 — Source format: W3C DTCG

Every token bundle this skill produces or consumes is in W3C Design Tokens Community Group format. Keys:
- `$value` — the literal value
- `$type` — `color | dimension | fontFamily | fontWeight | duration | shadow | typography`
- `$description` — human-readable rationale (kept in the token; not a comment)

Example:

```json
{
  "color": {
    "brand": {
      "primary": { "$value": "#3b1c0f", "$type": "color", "$description": "Hero accent — used like a weapon" },
      "primary-hover": { "$value": "{color.brand.primary}", "$type": "color" }
    }
  },
  "spacing": {
    "xs": { "$value": "4px", "$type": "dimension" },
    "sm": { "$value": "8px", "$type": "dimension" }
  },
  "type": {
    "display": {
      "$value": { "fontFamily": "PP Editorial New", "fontSize": "72px", "fontWeight": 400, "lineHeight": 1.05 },
      "$type": "typography"
    }
  }
}
```

## Step 2 — Platform translation matrix

| Platform | Output target |
|---|---|
| Web (Tailwind v4) | `@theme { --color-brand-primary: ...; }` block |
| Web (CSS) | `:root { --color-brand-primary: ...; }` |
| Apple (SwiftUI) | `extension Color { static let brandPrimary = ... }` + `Color` asset catalog JSON |
| Android (Compose) | `ColorScheme(primary = Color(0xFF...), ...)` + `Typography` |
| Windows (WinUI 3) | `<ResourceDictionary>` with `<Color>`, `<SolidColorBrush>`, `<x:Double>` |

Use `../../scripts/token_export.py` for the translation — never hand-translate. Tokens drift fast.

## Step 3 — When you should NOT generate tokens

Three cases where token work is wrong:
1. The user wants ONE platform — let that platform skill use its native idiom directly. Tokens are for reuse.
2. The brief is "Awwwards-tier landing page" — tokens flatten the bespoke choices that make it distinctive.
3. The team has no system to maintain. Tokens without governance become stale faster than they help.

State this explicitly if the user asks to "tokenize everything." Push back once.

## Step 4 — Auditing existing tokens

When asked to audit a token set:

1. **Coverage check** — does it cover the 5 layers? color (semantic + raw), spacing, typography, motion, elevation/material.
2. **Semantic vs raw discipline** — are there "primary-button-bg" tokens (semantic) AND "blue-500" tokens (raw)? Both layers, no shortcuts.
3. **Reference resolution** — semantic tokens must reference raw, never the inverse.
4. **Dark mode parity** — every semantic color has a dark variant.
5. **Platform-specific bans** — flag any token that won't survive translation (e.g. CSS `box-shadow` for native, where elevation is tonal).

## Step 5 — Anti-slop ban list (token-specific)

- Hex colors with no semantic name (`#3b82f6` exposed as a token name)
- 100+ raw colors with no semantic layer
- Spacing scales that aren't 4-based on Windows/Android, 8-based on Apple, fluid on web
- One token bundle declared "the source of truth" but only generated for web (the most common failure)
- Tailwind classes baked into tokens (defeats translation)
- Skipping `$type` (some tools won't validate without it)

## Step 6 — Reference token bundles

Shipped in `../../assets/tokens/`:
- `fluent-2.json` — Microsoft Fluent 2 reference
- `material3-expressive.json` — M3E reference (M3E adds wave/morph tokens vs M3)
- `apple-system.json` — iOS/macOS semantic system colors
- `awwwards-editorial.json` — bespoke "editorial Swiss" example
- `awwwards-brutalist.json` — bespoke "tactile brutalist" example
