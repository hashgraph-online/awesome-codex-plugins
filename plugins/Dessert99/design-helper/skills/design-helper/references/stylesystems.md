# Style systems

## Detect first

Never guess. Run these three at the project root; the result forks five ways.

    ls tailwind.config.* 2>/dev/null
    grep -rlm1 '@tailwind\|@import "tailwindcss"\|^\s*:root' --include='*.css' --include='*.scss' \
      --exclude-dir={node_modules,.next,dist,build} . | head
    grep -o 'styled-components\|@emotion/[a-z]*\|"sass"' package.json | sort -u

**Quote the `--include` globs.** zsh expands them first and dies with
`no matches found`. If the frontend lives in a subfolder (`frontend/`, `apps/web/`),
run them there — the root finds nothing.

## Draw in the system, or on a blank slate

- **Changing something that exists** → use exactly what detection found. Arbitrary
  values make "does this fit ours?" unanswerable and the comparison worthless.
- **New project, or hunting a different direction** → don't bind to existing values.
  They are today's answer, not the right one. Open it with the coordinate sweep in
  `references/sweeping.md` — on a new project from the middle of the scale, and when
  hunting a direction with today's value in the centre cell.
- **Unsure → ask in one line.** "우리 것 안에서 볼까, 백지에서 볼까"

**Always state what it was drawn with** — "프로젝트 유틸리티" · "프로젝트 CSS 변수" ·
"임의값 탐색안". The screen alone can't tell them apart, and it changes how the user
reads every specimen.

## The five forks

### Utility — Tailwind

The sheet lives in `$WS`, outside the project, so the project's `content` scan never
sees it. The fix is a flag or an entry file **in `$WS`** — never a second config in
the project. `tailwind.config.sheet.ts`, a copy with `content` extended, anything of
the kind: that is the file that gets left behind, and it is not needed.

Build into `$WS/sheet.css`, `<link>` that from the sheet, and keep the build running as
a watcher for the session so classes written into the sheet show on the next poll. Run
from the project root so `npx` finds the project's own Tailwind. Which command depends
on the version:

**v3** — `tailwind.config.*` exists, the CSS says `@tailwind base`. The CLI takes the
sheet's path as a flag, so the project config is used as is:

    npx tailwindcss -c tailwind.config.ts -i src/index.css \
      --content "$WS/sheet.html" -o "$WS/sheet.css" -w >/dev/null 2>&1 &
    echo $! > "$WS/tailwind.pid"

`-i` is the file detection found `@tailwind` in. `--content` replaces the config's list
for this build only, so just the sheet is scanned.

**v4** — no config file, the CSS says `@import "tailwindcss"`. Write an entry file in
`$WS` that pulls the project's stylesheet in by absolute path and points the scanner at
`$WS`:

    V=$(node -p "require('./node_modules/tailwindcss/package.json').version")
    cat > "$WS/sheet.in.css" <<EOF
    @import "$PWD/src/app.css";
    @source "$WS";
    EOF
    npx "@tailwindcss/cli@$V" -i "$WS/sheet.in.css" -o "$WS/sheet.css" -w >/dev/null 2>&1 &
    echo $! > "$WS/tailwind.pid"

`$PWD/src/app.css` is the file detection found the import in. Everything it declares —
`@theme`, `@source`, `@config` — comes along with it.

**Pin the version, because the CLI is usually not installed.** Most v4 projects build
through `@tailwindcss/postcss` and never depend on `@tailwindcss/cli`, so `npx` fetches
it over the network — and unpinned it fetches `latest`, which can differ from what the
project compiles with. Pinning to the project's own `tailwindcss` version makes the
sheet and the app agree.

No network and no cached CLI → **the utility fork is unavailable.** Fall back to reading
the values out of `@theme` and drawing with CSS variables, and say which it was: the
screen can't tell them apart and `프로젝트 유틸리티` would no longer be true.

Blast radius — count the class, then the token behind it:

    grep -rn 'rounded-lg' --include='*.tsx' --include='*.jsx' src/ | wc -l
    grep -n 'borderRadius' tailwind.config.*      # v3: is the value itself being changed?
    grep -n '\-\-radius-lg' src/app.css           # v4: same question, in @theme

Changing a config value moves every use of that class. Adding a new class moves nothing.

### CSS variables — `:root { --* }` · `tokens.css` · `theme.css`

`<link>` the file and draw with `var(--x)`. Refresh alone picks up edits.

Blast radius:

    grep -rn 'var(--radius-md)' --include='*.css' --include='*.tsx' . | wc -l
    grep -rn '\-\-radius-md' tokens.css            # is it derived from another token?

Watch for chained tokens — `--radius-card: var(--radius-md)` means the count above is
only the direct uses.

### SCSS variables — `*.scss` · `_variables.scss`

Read the values and carry them into the specimen file as CSS variables. SCSS variables
are compile-time, so the browser never sees them.

Blast radius: `grep -rn '\$radius-md' --include='*.scss' . | wc -l`. Note that SCSS
also resolves at build time, so a change needs a rebuild before it shows anywhere.

### CSS-in-JS — `styled-components` · `@emotion` · `theme.ts`

Unusable in static HTML. Read the theme object's values and carry them over as CSS
variables for the specimen file.

Blast radius: `grep -rn 'theme.radius.md\|radius\[.md.\]' src/ | wc -l`. Interpolated
access (`theme[key]`) won't grep — say so rather than reporting a count you can't stand
behind.

### Blank slate — nothing found

Write the values directly. No silent-failure check needed, and blast radius is
whatever files the change lands in.

## Feeding the controls

Only for an interactive sheet — `references/controls.md`. Four fields, per fork:

| fork | `scale` | `inSystem` | `token` · `uses` |
|---|---|---|---|
| Utility | the utility names, in scale order | `'all'` | the config key or `@theme` entry, and the class's grep count |
| CSS variables | the token values, in order | the same values | `--radius-md`, and the `var()` grep count |
| SCSS | values read out of `_variables.scss` | the same values | `$radius-md`, and its grep count |
| CSS-in-JS | values read out of the theme object | the same values | the theme path, `null` if access is interpolated |
| Blank slate | the default ladder in `references/sweeping.md` | `[]` | **`null`** |

The chip is the only thing standing between a scrub and a one-off value, so keep `uses`
honest. Where a count can't be stood behind — interpolated access — set `token: null`
and say so in chat rather than printing a number that isn't true.

## Reporting blast radius

While choosing, one line per specimen:

```
토큰 그대로 · --radius-md 고침 (23곳) · 새 토큰
```

Before applying, the real tally: which files, which lines, which tokens, and what else
moves with them. Scope defaults are in `SKILL.md` — `Ending`.
