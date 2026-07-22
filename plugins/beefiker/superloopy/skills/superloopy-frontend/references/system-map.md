# Official Design-System Contract Map

Use this reference only when the work has an **actual platform contract**: the repository already depends on a system, the UI runs inside a host that requires one, the user explicitly requests adoption, or an organization or public-service policy names it. Visual resemblance is not a contract. “Microsoft-like,” “GitHub-like,” or “Material-inspired” without one of those signals stays on the brand/mood route.

This map does not replace the project's authoritative design source or make a migration, redesign, anti-slop pass, SEO audit, or visual artifact automatically applicable. A narrow nonvisual change may retain the current system and use behavioral, accessibility, and regression proof. SEO remains limited to the current crawlable public Web target or a distinct deployed public Web target in scope.

## Decision sequence

1. Inspect `package.json`, lockfiles, imports, component directories, the current rendered surface, and the repository's authoritative design source (`DESIGN.md` only when the repository establishes it). Preserve the existing stack and its working accessibility behavior.
2. Identify the contract owner: existing dependency, embedded host, explicit user choice, or documented policy. Record that evidence in the authoritative source or existing project receipt. If a separate `DESIGN.md` is useful, it must be a scoped mapping that links back to and stays synchronized with that owner, never a competing source.
3. Verify the current official documentation, maintenance status, framework/version support, license, and migration guidance. Package recommendations drift.
4. If the required package is missing, explain the impact and get **explicit approval before installing** it. Never run an install command merely because a brief resembles a brand. After approval, re-check the package's current official setup and the repository's package manager: when implementation was requested, execute the one verified package-manager command; when the user requested advice only, present that one command without running it.
5. Keep **one primary appearance owner per surface**. Migration shells and low-level utilities may coexist behind explicit boundaries, but two competing component systems must not style the same subtree.
6. After any approved install or migration step, verify lockfile/package resolution, imports/build integration, and the affected labels, semantics, keyboard behavior, focus, contrast, and application states in the target-derived browser/OS/input and breakpoint matrix, expanding only for changed claims or risk. An official system provides primitives; it does not make the application accessible automatically.

When an unknown owner, policy, migration boundary, or package choice would materially change the result, ask the minimum necessary questions and batch independent unknowns. Otherwise disclose the uncertainty and constrain the claim.

## Contract map

| Verified contract | Maintained official route | Notes |
| --- | --- | --- |
| Microsoft product surface or existing Fluent app | `@fluentui/react-components` or `@fluentui/web-components` | Choose the implementation matching the existing framework. |
| Existing Material Web application | `@material/web` + Material 3 tokens | The official repository currently says **maintenance mode pending new maintainers**. Do not select it for new work without re-checking status and alternatives: https://github.com/material-components/material-web |
| Framework-specific Material application | The maintained official implementation for that framework | Verify the framework route instead of assuming `@material/web` is the universal answer. |
| IBM product or existing Carbon app | `@carbon/react` + `@carbon/styles` | Preserve Carbon tokens and data-density patterns already in use. |
| Shopify admin/app surface | Polaris web components (`polaris.js`) | Follow the current surface-specific guidance: https://shopify.dev/docs/api/polaris/ |
| Atlassian product or existing Atlaskit app | `@atlaskit/*` + `@atlaskit/tokens` | Install only the components the surface needs. |
| GitHub product surface in an existing Primer React app | `@primer/react` | Use the official product UI components and preserve the app's current package/version. |
| GitHub product surface using Primer CSS | `@primer/css` | Keep the CSS route when the project does not use Primer React. |
| GitHub marketing or brand surface | `@primer/react-brand` | Use the brand package only for supported marketing work. “GitHub-like” styling alone is not enough to adopt Primer. |
| GOV.UK service governed by GOV.UK guidance | `govuk-frontend` | Confirm the service standard and required supported versions. |
| US federal surface governed by USWDS guidance | `uswds` | Confirm agency policy and project requirements. |

## Foundations are not platform contracts

Bootstrap, Radix Themes, shadcn/ui, and Tailwind are possible foundations, not automatic answers to a visual adjective. Keep the repository’s current foundation unless the user approves a migration. In particular, shadcn/ui can use Tailwind and Radix/Base primitives internally; that is compatible layering, not multiple competing appearance owners.

| Need after stack inspection | Candidate |
| --- | --- |
| Existing Bootstrap product or explicitly speed-first approved build | Bootstrap 5.3 |
| Accessible React primitives with an owned theme | `@radix-ui/themes` or project-selected primitives |
| Source-owned React components in an existing compatible stack | shadcn/ui |
| Utilities in a project already using or explicitly adopting them | Tailwind |

## Aesthetic directions

Glassmorphism, bento grids, brutalism, editorial layouts, dark-tech terminals, aurora gradients, and kinetic typography have no official component package. Implement them with the existing styling layer and label borrowed inspiration honestly.

Apple Liquid Glass is an Apple-platform material. A web build using `backdrop-filter`, layered borders, and highlights is a labeled approximation. Start with a readable solid fill, enhance only when transparency support is available, and honor `prefers-reduced-transparency` where the browser implements it; that experimental query cannot be the only fallback.

## Approved implementation versus advice-only commands

The examples below are candidates, not authorization. Re-check current official setup instructions and the repository package manager first. After explicit approval, an implementation request executes exactly the verified matching command and then performs the integration checks from step 6; an advice-only request presents exactly that command and does not execute it. Do not dump alternatives after the route is known.

```bash
npm install @fluentui/react-components
npm install @carbon/react @carbon/styles
npm install @atlaskit/tokens
npm install @primer/react
npm install @primer/css
npm install @primer/react-brand
npm install govuk-frontend
npm install uswds
npm install bootstrap
npm install @radix-ui/themes
npx shadcn@latest init
```

These are dependencies of the user’s project, never Superloopy itself. Do not add one without approval, and do not replace an existing equivalent merely to match this table.

## Primary documentation

- Fluent: https://fluent2.microsoft.design/
- Material: https://m3.material.io/develop/web
- Carbon: https://carbondesignsystem.com/
- Polaris: https://shopify.dev/docs/api/polaris/
- Atlassian: https://atlassian.design/
- Primer product React: https://primer.style/product/getting-started/react/
- Primer brand React: https://primer.style/brand/getting-started/esm/
- GOV.UK: https://design-system.service.gov.uk/
- USWDS: https://designsystem.digital.gov/
- Radix Themes: https://www.radix-ui.com/themes/docs
- shadcn/ui: https://ui.shadcn.com/docs
- Apple materials: https://developer.apple.com/design/human-interface-guidelines/materials

Selected contract-map ideas were adapted under MIT from Taste Skill; see `references/upstream-notice.md`.
