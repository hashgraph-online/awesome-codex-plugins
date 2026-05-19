# Styling Patterns

Demand-loaded. Read this file when working in a React project that uses Tailwind, CSS-in-JS (MUI, Chakra, Mantine, Emotion, styled-components), or CSS Modules. Skip if styling is plain CSS only.

---

## Approach Selection

Be consistent within the project. The trade-offs:

| Approach | Pros | Cons |
|----------|------|------|
| CSS Modules | Scoped, no runtime | Verbose class names |
| Tailwind CSS | Rapid development | Learning curve, verbose markup |
| CSS-in-JS | Dynamic styles | Runtime overhead, SSR complexity |

**Principles:**

- Be consistent within the project — don't mix approaches per-component without a reason.
- Avoid inline `style={{...}}` in production code; use CSS Modules / Tailwind / CSS-in-JS.
- Co-locate styles with the component when possible.

---

## Conditional class names

Use a `cn()` / `clsx()` helper for conditional classes — never template literals.

```tsx
// Good
<div className={cn("flex items-center", disabled && "opacity-50")} />

// Bad — template literal
<div className={`flex items-center ${disabled ? "opacity-50" : ""}`} />
```

Template literals leave dangling whitespace when the condition is falsy and silently break when a variable is `undefined`. The helper handles both.

---

## Mixing component libraries (Tailwind + MUI / Chakra / etc.)

When a project mixes Tailwind utilities with a CSS-in-JS component library (MUI, Chakra, Mantine), declare an explicit CSS layer order in your global stylesheet so library styles can't override Tailwind utilities (or vice versa) at unpredictable specificity:

```css
@layer theme, base, mui, components, utilities;
```

Inject the library's styles into the corresponding layer (e.g. MUI via `AppRouterCacheProvider` with a layer assignment). Without this, the two systems fight non-deterministically — what works in dev breaks in prod after a CSS-order change.

---

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| Inline `style={{...}}` in production code | CSS Modules, Tailwind, or CSS-in-JS |
| Template literal class names | `cn()` / `clsx()` helper |
| Tailwind utilities + MUI/Chakra without explicit `@layer` order | Declare layer order in global stylesheet |
