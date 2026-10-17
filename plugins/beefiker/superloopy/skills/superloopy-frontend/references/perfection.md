# Measured Quality Gate (Perfection)

"Looks good" is subjective; this gate makes selected UI claims measurable. It has two layers: a **partial color/spacing token lint** (Superloopy-native, dependency-free) and a **real-browser Lighthouse protocol** (run via `npx`, so nothing is added to Superloopy's dependency-free `package.json`). Use either layer only when its claim and risk are in scope. Both produce run-scoped evidence under `.superloopy/evidence/frontend/`, but neither substitutes for usability, renderer, or native-shell proof.

The token-lint layer accepts `DESIGN.md` only when that file is the project's established design source or a scoped mapping/receipt synchronized with the real owner. If the project uses another authoritative source and no mapping is required, validate that source with its repository-native checks instead of creating `DESIGN.md` merely to run this helper. A narrow nonvisual change does not select either layer unless an existing gate, changed claim, regression signal, or risk makes it relevant.

Create `EVIDENCE_ROOT` with the portable helper from `references/web.md`. The returned path already ends in the generated `YYYYMMDDTHHMMSSZ-<slug>` run ID; do not separately synthesize or set `RUN_ID`. Reuse that exact evidence root for the run. POSIX shells use:

```sh
set -u
EVIDENCE_ROOT="$(node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-quality)" || exit $?
[ -n "$EVIDENCE_ROOT" ] || exit 2
```

PowerShell uses:

```powershell
$EVIDENCE_ROOT = node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" create frontend-quality
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($EVIDENCE_ROOT)) { exit 2 }
```

## Layer 1 — Partial color/spacing token lint (runnable, no deps)

Run the compatibility filename `ds-compliance.mjs` directly when changed color/spacing tokens or their drift are in scope:

```sh
node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md dist/assets/app.css > "${EVIDENCE_ROOT}/token-lint.txt" 2>&1
VALIDATION_STATUS=$?
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify "$EVIDENCE_ROOT" token-lint.txt
VERIFY_STATUS=$?
[ "$VALIDATION_STATUS" -eq 0 ] || exit "$VALIDATION_STATUS"
[ "$VERIFY_STATUS" -eq 0 ] || exit "$VERIFY_STATUS"
```

PowerShell uses the same inputs with native stream capture:

```powershell
node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md dist/assets/app.css *> "$EVIDENCE_ROOT/token-lint.txt"
$ValidationStatus = $LASTEXITCODE
node "${FRONTEND_SKILL_DIR}/scripts/evidence-root.mjs" verify $EVIDENCE_ROOT token-lint.txt
$VerifyStatus = $LASTEXITCODE
if ($ValidationStatus -ne 0) { exit $ValidationStatus }
if ($VerifyStatus -ne 0) { exit $VerifyStatus }
```

Inside an active loop, first run `superloopy loop guide --json`, then capture the active criterion with `superloopy loop prove --artifact "${EVIDENCE_ROOT}/token-lint.txt" -- node "${FRONTEND_SKILL_DIR}/scripts/ds-compliance.mjs" DESIGN.md dist/assets/app.css`. Replace the sample built-file path with the actual production output.

It exits non-zero on undeclared **3-, 4-, 6-, and 8-digit hex** colors or off-scale integer/fractional/negative spacing values in the supported px declarations (absolute 0 and 1px are allowed), with file:line. A pass proves only those bounded checks; it says nothing about CSS color functions, variables, typography, component rules, semantics, accessibility, or overall system adoption.

## Layer 2 — Lighthouse (real browser, surface-selected categories)

Select Lighthouse categories by the deployed surface and changed claim. Performance, accessibility, and best practices are selected when a changed claim, existing project gate, regression signal, or risk makes that browser audit relevant. SEO applies when the audited target itself is crawlable public Web. When the current task target is native or embedded, assess SEO only on a distinct deployed public Web target. HTML/CSS, WebView, canvas, or an embedded browser engine never makes SEO applicable by itself.

- **Choose categories before running.** When the audited target is crawlable public Web, audit `performance,accessibility,best-practices,seo`. Otherwise omit SEO and record `SEO: N/A` with the concrete deployment reason, such as authentication, private access, native-only delivery, or an embedded client with no distinct public Web target. If Lighthouse cannot represent the deployed client, record why and use renderer or target-native proof for that claim.
- **Pin the audit tool to the actual runtime.** Set `LIGHTHOUSE_VERSION` to an exact reviewed semver, not `latest`. The [Lighthouse](https://www.npmjs.com/package/lighthouse) release reviewed on 2026-07-20 is `13.4.0`, which requires Node `>=22.19`; the retained Node 20 compatibility baseline is `12.8.2`. Record the chosen version and runtime reason, run `npx --yes "lighthouse@${LIGHTHOUSE_VERSION}" --version`, and treat a version change as an explicit toolchain change.
- **Measure through a real supported browser, never an unspecified bundled shell or a dev server.** Build for production, select the exact installed browser build and profile from the target-derived browser/OS/input and breakpoint matrix, then audit the served build: `npx --yes "lighthouse@${LIGHTHOUSE_VERSION}" https://staging.example.test/ --output=json --output-path="${EVIDENCE_ROOT}/lighthouse-mobile-run-1.json" --only-categories=performance,accessibility,best-practices`. Replace the sample URL and profile label, increment the run index for every execution, and add `seo` only when applicable. Never overwrite raw runs. (`npx` fetches the pinned tool at runtime; do not add Lighthouse to `package.json`.)
- **Use project budgets and regression truth.** Existing category budgets and the comparable production baseline take precedence. Without a project budget, aim for 100 where the product owns the result and investigate every regression. A score of 90-99 is not an automatic failure: inspect failed audits, attribute owned versus third-party/environment effects, and document accepted limitations. A score below 90 blocks the applicable category unless a concrete third-party or environment limitation is documented and accepted by the responsible owner; a material regression can block at any score.
- **Discipline:** choose representative mobile and/or desktop profiles from the deployed-surface contract; run 3-5 times, retain every indexed raw JSON, compute the median into `lighthouse-summary.json`, and parse each `audits[*].score < 1` programmatically to locate offenders instead of eyeballing. The summary must list its input filenames so the median is reproducible.
- **React Doctor:** when affected React code or risk justifies the scan, pin an exact `REACT_DOCTOR_VERSION` (the [React Doctor](https://www.npmjs.com/package/react-doctor) baseline reviewed on 2026-07-20 is `0.8.1`, requiring Node `^20.19.0 || >=22.13.0`), record it, and default to `npx --yes "react-doctor@${REACT_DOCTOR_VERSION}" --json --no-telemetry --no-supply-chain > "${EVIDENCE_ROOT}/react-doctor.json"`. Its normal CLI mode reports telemetry and enables an external supply-chain scan, so require informed opt-in before omitting either privacy flag; enable supply-chain analysis only when that external dependency-health claim is selected and approved. Triage each finding against the changed, affected, and owned code; only a reproduced issue, configured project gate, or material owned finding blocks completion. Ask before adding any runtime scanner dependency.

## Anti-gaming (reject-on-sight — never weaken UX to win the number)

A metric is only as good as its ungameable-ness. These are failures, not fixes:

- Reporting a CLI/headless-shell score instead of a real-browser one, or measuring the dev server.
- Removing an animation/transition to fix INP; swapping the hero image for a placeholder to fix LCP; disabling JS for a route; `display:none` to dodge an audit.
- Declaring victory after one run, or scoring localhost without re-measuring the deployed build.

Win the score *in the architecture* (bundle splitting, hydration strategy, asset pipeline, off-main-thread work), so the page stays both fast AND fully featured.

## Evidence

When measured-quality claims are selected, record `PERF.md` under `$EVIDENCE_ROOT` summarizing: partial color/spacing token lint result when used; selected Lighthouse categories and applicability reasons; project budget and comparable baseline; exact Lighthouse version, browser version/build and engine, OS, hardware or device profile, viewport/device scale factor, network/CPU profile, build identifier, URL, and run count; median scores per representative profile; owned versus external findings; accepted limitations; the specific audits fixed; and links to every indexed Lighthouse JSON plus `lighthouse-summary.json`. Record Node, React Doctor, or other tool versions when used, link `react-doctor.json`, and state whether telemetry and supply-chain analysis were disabled or explicitly accepted. Close with the Superloopy evidence record pointing at it. A selected performance claim without the artifact is inconclusive, never a pass.
