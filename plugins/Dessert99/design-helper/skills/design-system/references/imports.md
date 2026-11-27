# Taking values from public design systems

A public design system can supply candidates, so the user doesn't have to invent every
value. Its values join a ladder as specimens; they are never settled by being imported.

## Sources

| 출처 | Take | Where the values come from |
|---|---|---|
| Tailwind 기본값 | spacing steps, type sizes, radius, shadow, color palette | the `tailwindcss` package: v4 declares its defaults as CSS variables in the package's `theme.css`; v3 in its default theme module |
| Radix Colors | color scales with fixed uses per step | the `@radix-ui/colors` package: one CSS file per scale, light and dark |
| Open Props | nearly every foundation as CSS variables | the `open-props` package's CSS |
| Material 3 | color roles from a seed color, type roles, shape | `@material/material-color-utilities` for color; the official Material 3 specification pages for type and shape |
| shadcn/ui | color role names and values, radius | the theme CSS in the official shadcn/ui repository |

Any other system the user names may be used the same way. A company's brand system
(a product's own design language) is a reference for values only, never a base.

## What is taken

- **Tokens:** values, and how the system splits them into roles (Radix Colors: steps 1
  and 2 for backgrounds, 11 and 12 for text). This is the import.
- **Component looks, not code:** a component's height, padding and radius may be a
  specimen (`shadcn/ui 버튼처럼 높이 36 · 여백 16 · 모서리 6`). No library is installed;
  installing one is an implementation step after the record.
- **Not accessibility.** A system's contrast guarantees hold only inside that system.
  Every pair actually picked is measured (`worker.md`, visible accessibility).

## Units

- **One item:** a single row's candidate (`간격 기본 단위`).
- **One area:** the whole area as one specimen (`색 전체: Radix Colors`).
- **The base:** the system is the starting point and only differences are decided. It
  is recorded in `README.md` as `기반: <system> <version>`.

Mixing sources is allowed. Every candidate is drawn on the board with everything settled
so far, so a mix that doesn't hold together shows on the sheet.

## Getting the values right

Never write a system's values from memory: a wrong value looks plausible and fails
silently.

1. Read them from the published source: the project's installed package when present,
   otherwise the package unpacked into `$WS` (`npm pack <name>@<version>`, then
   `tar -xzf`), or the official file at a fixed release or commit.
2. Note the version or commit; the record's `출처` and `base` carry it.
3. No network and no installed copy: say that the source is unavailable and draw
   without it. Don't substitute remembered values.
4. Convert only the format, and only when the conversion is exact. An `oklch()` color
   outside sRGB changes when written as hex: keep the source format, or say on the
   caption's values line that the hex is the nearest sRGB color.
