# Web and SaaS

The web has no system design to fall back on, so the token layer is the design system. Put every colour, font, radius, spacing, and shadow decision in one place, and have components use only those tokens.

## Tokens

- **CSS custom properties** on `:root`, named by role (`--surface`, `--surface-raised`, `--ink`, `--muted`, `--accent`, `--accent-hover`, `--accent-subtle`, `--divider`, `--category-1…n`, `--success`, `--warning`, `--danger`)
- **`oklch()`** for the palette. Equal lightness steps look even, and tinting a neutral is a small chroma value at the accent's hue (`oklch(97% 0.008 <accent hue>)`).
- **`color-mix(in oklch, var(--category-2) 14%, var(--surface))`** for tinted chips and icon tiles, with no extra tokens
- **Tailwind v4**: declare the tokens in `@theme` (`--color-ink`, `--font-display`, `--radius-lg`) so utilities like `bg-ink` and `font-display` come from them. **Tailwind v3**: `theme.extend` in `tailwind.config`.
- **Component libraries** (shadcn/ui, HeroUI, MUI, Chakra): set their theme variables to the tokens instead of overriding components one by one. shadcn/ui reads `--background`, `--foreground`, `--primary`, and the others from CSS.

## Dark Mode

- Redefine the same role tokens under `@media (prefers-color-scheme: dark)`, and under a `[data-theme="dark"]` attribute if the app has a toggle. Components never branch on the theme.
- Build elevation from lightness steps (for example 14% → 18% → 22% oklch lightness), not shadows. Keep the steps about twice the light-mode gap between surfaces.
- Point `--accent` and `--accent-hover` at lighter steps of the accent ramp than in light mode
- Set `color-scheme: light dark` so form controls and scrollbars follow

## Type

- **Self-host fonts or use the framework's loader** (`next/font`, Fontsource). Use `font-display: swap` and preload only the display weight used above the fold.
- **Variable fonts** keep weights and widths in one file. Use `font-variation-settings` or `font-stretch` for width axes.
- **System font stack** (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`) is a valid choice for Restrained products
- `font-variant-numeric: tabular-nums` for prices, tables, and timers
- `text-wrap: balance` on headlines, `text-wrap: pretty` on short paragraphs
- Fluid display sizes with `clamp()`, body in `rem` so browser zoom works
- Body line length `max-width: 65ch` or similar

## Surfaces and Depth

- `backdrop-filter: blur()` only on sticky headers, floating bars, and overlays above scrolling content. Give it a translucent background fallback where it is unsupported.
- One `--shadow` token (two at most), built from low-opacity, tinted shadows rather than `rgb(0 0 0 / .25)`
- Radii from `--radius-sm/md/lg/full`. For nested corners, set the inner radius to `calc(var(--radius-lg) - var(--pad))`.

## Layout

- Spacing tokens on a 4px base. Use `gap` on flex and grid containers rather than child margins.
- Content width caps (`max-width`) on marketing pages, with generous section spacing (64–128px on desktop)
- Check at phone width first: 16px side gutters, no horizontal scroll

## Icons and Imagery

- One icon library (Lucide, Phosphor, Heroicons) at one stroke width
- Product imagery as real rendered components or high-resolution screenshots, with `srcset` or the framework's image component
- Store marketing visuals as the product, not as stock photography

## Marketing Pages

Landing and pricing pages are showcase screens. They use the full direction: oversized headline, the signature visual, and one primary CTA style repeated down the page. The app behind the login uses the same tokens at a lower volume.
