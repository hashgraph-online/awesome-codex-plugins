# Web route

Use this route for browser-hosted DOM, installed Web, custom-rendered Web, and embedded browser clients. Preserve the shared UX contract and the project's existing stack. Design quality, functional truth, accessibility, performance, crawlability, and native-shell integration are separate claims with separate proof.

Real-browser visual evidence is required for changed visual claims, not as a substitute for behavioral or accessibility evidence. A narrow nonvisual change may complete without a new design system or screenshot set when its own regression evidence is sufficient.

## Delivery classes and proof ownership

Classify the deployed surface before selecting a Web checklist. Public versus private deployment, DOM versus custom rendering, installed capabilities, and shell ownership matter more than a framework label.

### Product/application DOM Web

This includes authenticated, private, internal, administrative, editor, and public application surfaces. Preserve the existing product design system, workflow, information architecture, and density unless the task explicitly changes them. Run the production build, affected journey, adjacent regression, and supported-browser floor. Add operating-state, accessibility-tree, adaptation, and performance checks when affected, claimed, or selected by risk. SEO applies when the current Web target is public and crawlable and that claim or risk is selected; authentication, privacy, and application UI do not imply crawlability.

### Marketing/editorial Web

For a campaign, publication, landing page, or explicit new visual direction, load `references/anti-slop.md`. Ground brand, editorial hierarchy, composition, imagery, and copy in real content and the approved visual direction. Prove affected forms, navigation, consent, localization, accessibility, performance, and product handoff claims as behavior rather than decoration.

### PWA and browser extension

For a PWA, map service worker registration, installability, cache policy, offline/stale behavior, update activation, data migration, permission recovery, and standalone/browser display modes. Always run the build, launch, affected journey, and adjacent regression floor; prove the mapped capabilities when affected, claimed, or selected by risk. For a browser extension, separate extension-page, browser chrome, background/service-worker, content script, host-page, storage, and permission ownership. Run the same minimum floor in a supported browser, then add install/update/removal, cross-browser, storage, and least-privilege proof when those claims or risks are in scope.

### Canvas/custom-rendered Web

Load `references/renderer.md`. Separately prove semantics, accessibility, text and input behavior, focus/selection/IME, scaling, and performance through the renderer that owns them. Treat crawlability as a capability to separately prove for a deployed public surface. A canvas screenshot is insufficient evidence for behavior, semantics, text input, or crawlability.

### Embedded client Web

Load the applicable `references/desktop.md` or `references/mobile.md`, then `references/hybrid.md`. Browser-side client evidence covers only the client. Require shell proof for native ownership, lifecycle, permissions, accessibility, menus, windowing, and packaging on the actual target; client proof cannot substitute for shell proof.

When the current target is native or embedded, evaluate SEO only for a distinct deployed public Web target; do not score the shell or embedded client as though it were that site. HTML/CSS, WebView, canvas, or an embedded browser engine never makes SEO applicable by itself.

## Reference loading

Load the smallest applicable set and state it in one sentence:

- **Marketing, editorial, campaign, or explicit new visual direction:** `references/anti-slop.md`.
- **Canvas/custom renderer:** `references/renderer.md`.
- **Embedded client:** applicable desktop or mobile reference plus `references/hybrid.md`.
- **Named brand or mood:** `references/design/_INDEX.md`, then one matching teardown. Extract an unlisted brand only when authorized.
- **Visually important build from intent:** `references/image-first.md`.
- **Creating or extending tokens:** `references/design-system.md`.
- **Adopting an existing platform or organizational system:** `references/system-map.md`; ask before adding a dependency.
- **Any changed temporal claim:** the shared router selects `references/motion-core.md`; add the Web specialization `references/motion.md` only for browser-owned scroll-driven, pointer-physics, or animated-node implementation.
- **Redesigning a living site:** `references/redesign.md`.
- **Measured browser quality:** `references/perfection.md` when a performance, Lighthouse, or token-compliance claim is affected or selected by risk.

Authenticated, private, and internal product work does not automatically load a marketing aesthetic. Existing design-system and product conventions remain authoritative.

## Proportional design contract

Inspect the existing design system, tokens, components, and representative current surface before changing visuals. The project's current design source of truth remains authoritative; `DESIGN.md` is a scoped mapping/receipt only when the repository has no equivalent or when every changed value links back to and stays synchronized with that source.

- **Narrow nonvisual change:** record `Design impact: unchanged` and `Visual evidence: not applicable`, with behavioral, accessibility, and regression evidence. `DESIGN.md` and `VISUAL_QA.md` are required only for a changed visual claim, not for copy semantics, focus order, accessible naming, or an equivalent nonvisual fix.
- **Visual delta inside an existing system:** document only the changed tokens, components, responsive invariants, and states. Reuse existing CSS variables and primitives.
- **New or redesigned visual direction:** update the project's authoritative design source before UI code. If `DESIGN.md` is the repository's established source, update it; otherwise use it only as a scoped evidence mapping when needed. Define atmosphere, color, typography, spacing, components, motion, and depth. Every new visual value traces to one authoritative token or an explicitly synchronized platform value.

When a visual direction is in scope, emit a one-line Design Read with the surface kind, audience, existing or named direction, and evidence. Dial guidance is heuristic: user intent wins first, then the existing interface and an approved visual target; accessibility, performance, and platform constraints narrow the remaining choices.

## Baseline and implementation

Reproduce the current journey in the production-equivalent browser, then locate the route, components, state and service owners, existing CSS variables, tests, and adjacent journeys. Preserve working behavior and supported deep links. Map each shared UX contract clause to its acceptance case, implementation file, test, and evidence artifact.

Build operating states from actual ownership: initial/loading/empty/partial/stale/offline/degraded/error/retry/cancel, authentication/session/permission/entitlement changes, duplicate or optimistic submissions, and conflicts where applicable. Do not animate layout properties; respect reduced motion; use the established icon and styling infrastructure before proposing additions.

## Target-derived verification matrix

Derive supported browser engine, browser version range, OS, and input from repository Browserslist/configuration, package and runtime constraints, documented product support, and valid usage analytics. Analytics may prioritize execution but cannot silently remove a contractual or accessibility target.

Derive widths from actual breakpoints, container behavior, minimum and maximum supported windows, embedded bounds, content extremes, zoom, and text scaling. Include keyboard, touch, pointer, assistive technology, IME, locale, direction, color scheme, reduced motion, and contrast modes when supported or material.

390 / 768 / 1280 px remain useful baseline samples for continuity, but they are not universal proof and never replace target-derived breakpoints or browser/OS/input coverage. Record the exact browser build, engine, OS, input, viewport, device scale factor, zoom, locale, and state behind each artifact.

For each served Web implementation or plan, define a **minimum validation floor**: production build, affected journey, adjacent regression, and at least one supported real browser. Add design compliance, visual capture, 390 / 768 / 1280 baseline samples, target-derived additions, Lighthouse, and React Doctor only when the changed claim or risk selects them; React Doctor also requires a React repository.

## Visual-QA evidence gate

For a changed visual claim, or an interaction claim with a visible-state or layout consequence, capture the production build in the target-derived matrix and write `VISUAL_QA.md` under `.superloopy/evidence/frontend/<YYYYMMDDTHHMMSSZ-slug>/`. Record reference, actual target, state, viewport, browser/OS/input, observed difference, source cause, result, and limitation. A purely behavioral interaction with no visible consequence uses behavioral proof instead.

When a visual reference exists, `node "${FRONTEND_SKILL_DIR}/scripts/visual-diff.mjs" path/to/reference.png path/to/actual.png --json` can aim review at hotspots. Pixel similarity is not the verdict: inspect the rendered journey, text and localization, interaction states, focus, reflow, overflow, and reduced-motion behavior. A nonvisual claim uses behavioral or accessibility evidence instead of a decorative screenshot.

Run the applicable `references/anti-slop.md` pre-flight only for its declared scope. Do not weaken UX, hide content, remove necessary feedback, or replace real assets merely to clear a metric.

## Measured quality

Use `references/perfection.md` only when the changed token, performance, accessibility-audit, best-practice, or public SEO claim and its risk justify that layer. The `ds-compliance.mjs` compatibility filename is a partial color/spacing token lint only. Lighthouse measures selected production-browser claims only; it does not prove usability, renderer semantics, native shell behavior, or packaging. Pin and record tool and browser versions as that reference requires.

## Evidence modes and executable commands

`FRONTEND_SKILL_DIR` below is the actual absolute directory of this loaded frontend skill, announced as `FRONTEND_SKILL_DIR` during activation. Packaged helpers live under `${FRONTEND_SKILL_DIR}/scripts/`; project inputs and `.superloopy/evidence/` stay under the target project's current working directory. Never assume the target repository contains a `skills/superloopy-frontend/` checkout.

### Standalone frontend invocation

Run each validation command directly and write its stdout/stderr or a structured report to a non-empty artifact. Use the portable run ID `YYYYMMDDTHHMMSSZ-<slug>`; the UTC timestamp has no colon and the 1-48 character slug uses lowercase ASCII letters or digits joined by single hyphens. Create the root once per logical run with the dependency-free Node helper. The helper rejects path traversal, Windows reserved names, empty evidence, and files outside that root.

POSIX (`sh`, Bash, or zsh):

```sh
set -u
EVIDENCE_ROOT="$(node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-check)" || exit $?
[ -n "$EVIDENCE_ROOT" ] || exit 2
BUILT_FILE=dist/assets/app.css
node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md "$BUILT_FILE" > "${EVIDENCE_ROOT}/token-lint.txt" 2>&1
VALIDATION_STATUS=$?
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify "$EVIDENCE_ROOT" token-lint.txt
VERIFY_STATUS=$?
[ "$VALIDATION_STATUS" -eq 0 ] || exit "$VALIDATION_STATUS"
[ "$VERIFY_STATUS" -eq 0 ] || exit "$VERIFY_STATUS"
```

PowerShell:

```powershell
$EVIDENCE_ROOT = node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-check
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($EVIDENCE_ROOT)) { exit 2 }
$BUILT_FILE = "dist/assets/app.css"
node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md $BUILT_FILE *> "$EVIDENCE_ROOT/token-lint.txt"
$ValidationStatus = $LASTEXITCODE
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify $EVIDENCE_ROOT token-lint.txt
$VerifyStatus = $LASTEXITCODE
if ($ValidationStatus -ne 0) { exit $ValidationStatus }
if ($VerifyStatus -ne 0) { exit $VerifyStatus }
```

Return the final artifact receipt without calling loop-only commands:

```text
SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>
```

### Active Superloopy loop

Ask the loop for the current criterion, start the goal if the guide requests it, create one run root, then capture the validation against that criterion.

POSIX:

```sh
set -u
EVIDENCE_ROOT="$(node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-check)" || exit $?
[ -n "$EVIDENCE_ROOT" ] || exit 2
BUILT_FILE=dist/assets/app.css
superloopy loop guide --json || exit $?
superloopy loop prove --artifact "${EVIDENCE_ROOT}/token-lint.txt" -- node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md "$BUILT_FILE"
VALIDATION_STATUS=$?
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify "$EVIDENCE_ROOT" token-lint.txt
VERIFY_STATUS=$?
[ "$VALIDATION_STATUS" -eq 0 ] || exit "$VALIDATION_STATUS"
[ "$VERIFY_STATUS" -eq 0 ] || exit "$VERIFY_STATUS"
```

PowerShell:

```powershell
$EVIDENCE_ROOT = node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-check
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($EVIDENCE_ROOT)) { exit 2 }
$BUILT_FILE = "dist/assets/app.css"
superloopy loop guide --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
superloopy loop prove --artifact "$EVIDENCE_ROOT/token-lint.txt" -- node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md $BUILT_FILE
$ValidationStatus = $LASTEXITCODE
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify $EVIDENCE_ROOT token-lint.txt
$VerifyStatus = $LASTEXITCODE
if ($ValidationStatus -ne 0) { exit $ValidationStatus }
if ($VerifyStatus -ne 0) { exit $VerifyStatus }
```

To attach an existing non-empty artifact instead, copy the actual IDs and target from `loop guide --json`:

```sh
superloopy loop evidence --goal-id G001 --criterion-id C001 --status pass --artifact "${EVIDENCE_ROOT}/VISUAL_QA.md" --notes "verified changed visual claims" --json
```

`loop prove` requires an active goal. `loop evidence` requires both goal and criterion IDs. Do not use either command for a standalone frontend invocation with no loop plan.

## Completion checklist

- The baseline, affected journey, adjacent regression surface, and contract-to-code/test traceability are recorded.
- Delivery class and proof owners are named.
- Product/application Web preserves its established workflow and system; marketing/editorial work passes the applicable anti-slop review.
- PWA, extension, renderer, and embedded-shell claims have owner-specific proof when in scope.
- The surface renders correctly in a real browser from a production build across the target-derived browser/OS/input/breakpoint matrix.
- Functional, operating-state, accessibility, editable-text/IME, localization, motion, and performance claims have matching evidence.
- SEO is proven when the current target is crawlable public Web, or for a distinct public Web deployment when the current target is native/embedded; otherwise it is recorded as not applicable with a reason.
- A narrow nonvisual change records design and visual non-applicability; a changed visual claim or visibly consequential interaction has `VISUAL_QA.md`.
- Tool, browser, OS, build, state, and limitation versions are recorded.
- The final response includes `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.
