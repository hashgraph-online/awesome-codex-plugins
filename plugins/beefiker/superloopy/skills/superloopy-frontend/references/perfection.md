# Measured Quality Gate (Perfection)

"Looks good" is subjective; this gate makes UI quality an objective pass/fail the loop can enforce. It has two layers: a **runnable design-system check** (loopy-native, dependency-free) and a **real-browser Lighthouse protocol** (run via `npx`, so nothing is added to loopy's dependency-free `package.json`). Both produce an evidence artifact under `.superloopy/evidence/frontend/`.

## Layer 1 — Design System Compliance (runnable, no deps)

The "measurable taste" gate: output must conform to its own DESIGN.md tokens. Run it and record the result as proof:

```
superloopy loop prove -- node skills/superloopy-frontend/scripts/ds-compliance.mjs DESIGN.md <built CSS/TSX files…>
```

It exits non-zero on any **undeclared hex color** or **off-scale spacing** (px not on the base unit; 0 and 1px allowed), with file:line. "Lighthouse 100 but 14 undeclared hex codes and 8 magic spacing values = NOT DONE." This is the part loopy can hard-gate by itself.

## Layer 2 — Lighthouse (real browser, high floor)

Make performance/accessibility/best-practices/SEO a number the agent iterates against, not a vibe.

- **Measure through a real browser, never the CLI headless-shell or a dev server.** Build for production first, then audit the served build: `npx --yes lighthouse <url> --output=json --output-path=.superloopy/evidence/frontend/lighthouse.json --only-categories=performance,accessibility,best-practices,seo`. (`npx` fetches at runtime; do not add lighthouse to `package.json`.)
- **Floor is high.** Aim 100 in every category; treat <90 as broken and 90-99 as work remaining. A 100 forces real fixes: semantic HTML, contrast, focus order, ARIA, sized media (CLS), LCP, SEO meta.
- **Discipline:** mobile preset primary (CPU throttle / slow network) + desktop secondary; run 3-5 times and take the median; parse the JSON `audits[*].score < 1` programmatically to locate offenders instead of eyeballing.
- **React:** for React projects, run `npx react-doctor@latest --json` (static render-perf scan) first and treat perf findings as blockers; optionally inject react-scan/lite to assert zero unnecessary renders.

## Anti-gaming (reject-on-sight — never weaken UX to win the number)

A metric is only as good as its ungameable-ness. These are failures, not fixes:

- Reporting a CLI/headless-shell score instead of a real-browser one, or measuring the dev server.
- Removing an animation/transition to fix INP; swapping the hero image for a placeholder to fix LCP; disabling JS for a route; `display:none` to dodge an audit.
- Declaring victory after one run, or scoring localhost without re-measuring the deployed build.

Win the score *in the architecture* (bundle splitting, hydration strategy, asset pipeline, off-main-thread work), so the page stays both fast AND fully featured.

## Evidence

Record a `PERF.md` under the evidence root summarizing: ds-compliance result, Lighthouse median scores per category (mobile + desktop), the specific audits fixed, and links to `lighthouse.json`. Close with the Superloopy evidence record pointing at it. A perf claim without the artifact is inconclusive, never a pass.
