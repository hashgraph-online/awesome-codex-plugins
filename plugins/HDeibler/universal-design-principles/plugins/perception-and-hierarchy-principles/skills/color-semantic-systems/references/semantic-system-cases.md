# Semantic color systems: case reference

A reference complementing `color-semantic-systems` with case patterns from real design systems.

## Material Design's status colors

Material 3 defines:

- **Primary** — brand emphasis.
- **Error** — destructive / failure state.
- **Surface** / **Background** / **Outline** — chrome neutrals.
- **Tertiary** — optional accent for variety.

Each defined as a tonal palette (13 stops) with documented mappings for light, dark, and high-contrast modes. The system is overkill for many products but useful as a reference for what a fully-thought-through semantic system looks like.

## Tailwind's color naming

Tailwind ships ~22 colors (gray, zinc, neutral, stone, red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose) each with 11 stops (50–950). The wide adoption has made these names common vocabulary.

Tailwind itself is *not* opinionated about which color is "destructive" or "success" — that's left to the project. Most projects map:

- `red-500` → destructive
- `green-500` → success
- `amber-500` → warning
- `blue-500` (or brand color) → primary

## shadcn/ui's semantic tokens

Built on Tailwind, shadcn defines semantic CSS variables:

- `--background` / `--foreground`
- `--card` / `--card-foreground`
- `--primary` / `--primary-foreground`
- `--secondary` / `--secondary-foreground`
- `--destructive` / `--destructive-foreground`
- `--muted` / `--muted-foreground`
- `--accent` / `--accent-foreground`
- `--border` / `--ring`

Each pair is designed to satisfy WCAG contrast. The semantic naming separates *role* from *value* — components reference `--primary`, and the project assigns the actual hex.

## Bootstrap's contextual colors

Bootstrap (since v3) uses semantic naming: `primary`, `secondary`, `success`, `info`, `warning`, `danger`, `light`, `dark`. Each is assigned a fixed value in the framework (overridable in custom builds).

## Atlassian's color system

Atlassian's design system documents both raw color tokens (e.g., `Blue 500`) and semantic role tokens (e.g., `Default Background`, `Information Icon`). Components reference role tokens; raw tokens are reserved for design exploration.

## Common semantic mismatch failures

- **Brand red as also destructive red.** If your brand is red and your destructive color is also red, every CTA looks like a delete button.
- **Color reused across roles.** "Pending" and "Info" both rendered in the same blue. Users can't distinguish.
- **Saturation creep.** Originally muted status colors get tweaked brighter for "more visibility," eventually all colors are at full saturation and none stand out.

## Heuristics for semantic-system review

1. **List every color in the system; for each, name its role(s).** A color with multiple roles (the same red as both brand and destructive) creates conflicts.
2. **Check status colors are perceptually distinguishable.** Run a colorblind simulation; verify each status remains distinct.
3. **Check the contrast pairs.** Foreground/background combinations specified by the system should clear AA.
4. **Audit cross-product.** Is the same status color used the same way across surfaces? Drift creates inconsistency.

## Resources

- **Material Design 3** — m3.material.io.
- **Tailwind CSS** color reference — tailwindcss.com/docs/colors.
- **shadcn/ui theming** — ui.shadcn.com.
- **Atlassian Design System** color docs.
- **Adobe Spectrum** color spec.
