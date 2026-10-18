# Dependency Selection

Adding a UI dependency is an architecture decision with a maintenance tail. This is a method, not a recommendation list: which library is right depends on the product, its stack, and its constraints, and changes over time. Work the steps in order.

## 1. Name the job before any library

State the concrete role in one sentence — "toast notifications with stacking and swipe-dismiss", "date range picker with keyboard entry". A job statement that names a library ("we need Sonner") is a conclusion pretending to be a requirement. If the job cannot be stated, the need is not understood yet.

## 2. Check what the project already has

Inspect `package.json`, the lockfile, existing components, and the design system *first*:

- An existing component, token, or primitive that covers the job (even partially) beats any new dependency.
- A library already installed that can cover the job with its existing API beats a second one. Two libraries solving the same job is a defect: doubled bundle, doubled upgrade surface, two interaction languages.
- The framework's own primitives (dialog, popover, details, popover attribute) cover more than expected; the SKILL.md contract — native HTML and CSS with a working fallback, existing stack only — outranks any list of "best" libraries.

Hand-rolling remains legitimate for genuinely small jobs; a dependency for a 30-line component trades audit work for upgrade work with no capability gain.

## 3. One recommendation, with the reasoning shown

When a new dependency is genuinely needed, evaluate candidates and recommend **one**, with the reasons stated against the product's needs — not a menu. Product-fit criteria, in rough order:

- **Coverage of the stated job** (not adjacent features); behavior matches the interaction design already chosen.
- **Platform support** the project's policy requires (browsers, frameworks, versions; SSR/RSC where relevant).
- **Accessibility**: documented keyboard, focus and screen-reader behavior is part of the feature, not a nice-to-have.
- **Maintenance**: release cadence, open-issue responsiveness, governance (who maintains it, how dependently), deprecation signals.
- **Cost**: bundle size, rendering cost, and — for component libraries — styling-system fit with the project's tokens.
- **License** compatibility with the product's distribution.

Record the evaluated alternatives and why the winner won, briefly. Flag but do not churn existing dependencies: discovering the project's picker is unmaintained is a finding to report, not a same-task migration, unless the task is the migration.

## 4. Install only with authorization, adopt only with verification

Installing dependencies needs the user's approval (SKILL.md authority rules). After adoption, verify the dependency through the rendered result — the states the job named, keyboard behavior, and its interactions with the project's CSS — per `verification-and-recovery`. A dependency that renders in isolation but fights the design system fails the job.

## Reading a "which library" request

When asked "should we use X?", answer in terms of the job, the project's installed set, and the criteria above — never from general reputation alone. "X is popular" is not evidence the dependency fits this product; "X covers the stated job, is already a transitive dependency, and adds no new styling system" is.
