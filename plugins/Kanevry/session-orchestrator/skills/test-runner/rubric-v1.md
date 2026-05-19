# UX Rubric v1

> Readable specification of the 4 UX checks applied by the `ux-evaluator` agent.
> Stable spec — v2 will live as a sibling `rubric-v2.md` in this same directory.
> The `findings.jsonl` metadata record carries `rubric_version: "v1"` so consumers
> can distinguish evaluations run against different rubric revisions.

---

## Findings JSON schema (per finding)

Each finding in `findings.jsonl` is a JSON object on its own line (NDJSON). The
first line of the file is a metadata record (`"_meta": true`). All subsequent
lines conform to this schema:

```json
{
  "run_id":           "<string — test-runner run identifier, e.g. '12345-1715688000123'>",
  "rubric_version":   "v1",
  "severity":         "<'critical' | 'high' | 'medium' | 'low'>",
  "check":            "<'onboarding-step-count' | 'axe-violations' | 'console-errors' | 'liquid-glass-conformance'>",
  "fingerprint":      "<16-hex-char string — see Fingerprint formula below>",
  "evidence_path":    "<relative path from run-dir root to the supporting artifact>",
  "suggested_priority": "<'critical' | 'high' | 'medium' | 'low' — same as severity for v1>",
  "scope":            "<short label: 'onboarding' | 'a11y' | 'console' | 'liquid-glass'>",
  "checkId":          "<check identifier used as fingerprint input — see per-check section>",
  "locator":          "<DOM selector, AX path, entry URL, or screen.frame identifier>",
  "title":            "<one-sentence summary of the violation>",
  "description":      "<2–4 sentence explanation including evidence reference and rubric citation>",
  "recommendation":   "<actionable next step specific enough to act on without re-reading the finding>"
}
```

**Invariants:**
- `fingerprint` is unique within a single run (collisions are logged, only first occurrence emitted).
- `evidence_path` must point to an artifact that exists in the run directory at evaluation time.
- `severity` and `suggested_priority` are lowercase in the JSON record (uppercase only in human-readable stdout tables).
- No field may be `null` or absent. Use `""` for fields where the value is genuinely unavailable, and explain in `description`.

**Metadata record (first line of `findings.jsonl`):**

```json
{
  "_meta": true,
  "rubric_version": "v1",
  "run_id": "<run-id>",
  "evaluated_at": "<ISO-8601-UTC timestamp>",
  "checks_applied": 4,
  "findings_count": <integer>,
  "collisions": <integer — normally 0>
}
```

---

## Fingerprint formula

```javascript
fingerprint = sha256(`${scope}\n${checkId}\n${locator}`).slice(0, 16)
```

**Inputs** (joined with `\n` newline separator):

| Input | Description |
|---|---|
| `scope` | Short namespace label — `'onboarding'`, `'a11y'`, `'console'`, `'liquid-glass'` |
| `checkId` | Check-specific identifier — see each check section for the exact value |
| `locator` | Stable DOM selector, AX path, entry URL, or screen.frame string |

**Design rationale for `\n` separator:** Newlines are forbidden in shell argument
boundaries by the `ARG_BOUNDARY_DANGEROUS` pattern (`/[\n\r\0]/`) established in
`scripts/lib/autopilot/mr-draft.mjs`. Using `\n` as the separator means it can never
appear within a locator string that passed validation, so the concatenated input is
collision-free by construction.

**Implementation:** `scripts/lib/test-runner/fingerprint.mjs` exports
`fingerprintFinding({scope, checkId, locator})`. The function uses Node.js
`crypto.createHash('sha256')` (no external dependencies) and returns the first 16
hex characters of the digest (64 bits of collision resistance — sufficient for the
expected finding volume of < 10 000 per run).

**Truncation rule for long locators:** Locators longer than 256 characters are
truncated to their first 256 characters before fingerprinting. This is consistent
with the `ux-evaluator` agent's description field convention. Both the evaluator
and the fingerprint module must apply truncation to guarantee matching fingerprints.

**Stability guarantee:** Given identical `(scope, checkId, locator)` inputs, the
fingerprint is identical across any two evaluation runs, regardless of timestamp,
run-id, or system state. Never include runtime-varying values in fingerprint inputs.

---

## Check 1: onboarding-step-count

**Purpose:** Count distinct onboarding or wizard steps reachable from the flow's
entry point. Flag when the step count exceeds 7.

**Why 7:** The "7 ± 2" rule (Miller, 1956) characterises the capacity of short-term
working memory. Onboarding flows that require users to hold more than 7 steps in
mind reliably correlate with drop-off. A typical mobile app's V3.3 release shipped a
10-step onboarding flow with no E2E coverage; user-completion rate dropped significantly.
This rubric was inspired by that incident and is cited in project PRDs as the canonical
example for onboarding quality gates.

**Severity mapping:**

| Step count | Severity |
|---|---|
| ≤ 7 | No finding |
| 8–9 | HIGH |
| ≥ 10 | CRITICAL |

**What counts as a step:** A distinct page, screen, or wizard panel the user must
navigate through sequentially to complete onboarding. A "confirm" dialog on top of
a step does not count as a separate step. A branch path (e.g., "optional profile
setup") counts only if the user cannot skip it.

**Evidence required:**
- AX-tree snapshot with each step's primary heading text and a screenshot per step
  (both written by test fixtures in the target repo to `<run-dir>/ax-snapshots/` and
  `<run-dir>/screenshots/` — runner.mjs pre-creates these directories but does not
  emit the content).
- The test fixtures must have navigated through the full onboarding sequence and
  captured an AX snapshot at each step transition. If the fixtures did not cover the
  full flow, the evaluator logs a warning and emits no finding (evidence requirement
  is not met).

**Fingerprint inputs:**
- `scope = 'onboarding'`
- `checkId = 'step-count-over-7'`
- `locator = <entry-route-URL-for-web | entry-screen-name-for-macOS>`

**Example finding (HIGH):**

```json
{
  "run_id": "42-1715700000000",
  "rubric_version": "v1",
  "severity": "high",
  "check": "onboarding-step-count",
  "fingerprint": "a3f1c8e72d904b1a",
  "evidence_path": "screenshots/onboarding-step-8.png",
  "suggested_priority": "high",
  "scope": "onboarding",
  "checkId": "step-count-over-7",
  "locator": "/onboarding/start",
  "title": "Onboarding flow has 9 steps (limit: 7)",
  "description": "The onboarding sequence starting at /onboarding/start requires the user to complete 9 distinct steps before reaching the dashboard. Steps 8 and 9 are a 'verify email' confirmation screen and a 'set notification preferences' screen. The 7-step limit is defined in rubric-v1 Check 1 based on Miller's short-term memory model.",
  "recommendation": "Merge 'verify email' into the account-creation step (step 2) or defer 'notification preferences' to a post-onboarding nudge. Target ≤7 steps in the critical path."
}
```

---

## Check 2: axe-violations (critical + serious)

**Purpose:** Read axe-core JSON output captured by the Playwright driver and flag
every accessibility violation tagged `critical` or `serious` by axe-core's impact
rating. Lower severity levels (`moderate`, `minor`) are out of scope for v1 — they
belong in a separate `/discovery` pass or a future `rubric-v2.md` extension.

**Why axe critical/serious only:** WCAG AA conformance requires that critical and
serious violations be eliminated before launch. Moderate and minor violations are
important but rarely block release; including them in v1 would produce too much noise
for the reconcile pipeline's per-finding issue creation to handle economically.

**Severity mapping:**

| axe-core impact | Finding severity |
|---|---|
| `'critical'` | CRITICAL |
| `'serious'` | HIGH |
| `'moderate'` | (not a finding in v1) |
| `'minor'` | (not a finding in v1) |

**Artifact location:** `<run-dir>/ax-snapshots/axe-*.json`
(written by test fixture using `@axe-core/playwright`; runner.mjs pre-creates the
`ax-snapshots/` directory but does NOT write these files — axe-core SOFT-SKIPs
if `@axe-core/playwright` is absent from the target repo)

Each file is a JSON array of axe-core `Result` objects. The evaluator iterates every
result entry in every snapshot file and emits one finding per unique
`(ruleId, nodes[0].target)` pair that is `critical` or `serious`.

**Evidence required:**
- The verbatim axe-core `Result` object embedded in the finding's `description` field
  (JSON-stringified, or as a structured sub-object if the reconcile pipeline supports it).
- The screenshot file from the same route, if present (referenced in `evidence_path`).

**Fingerprint inputs:**
- `scope = 'a11y'`
- `checkId = 'axe-' + ruleId` (e.g., `'axe-color-contrast'`, `'axe-image-alt'`)
- `locator = nodes[0].target` — the CSS selector array joined with ` > ` if it is
  a nested selector, or the first string element if it is already a string

**Example finding (CRITICAL):**

```json
{
  "run_id": "42-1715700000000",
  "rubric_version": "v1",
  "severity": "critical",
  "check": "axe-violations",
  "fingerprint": "b9d2041ef3a77c50",
  "evidence_path": "ax-snapshots/axe-dashboard-2025-05-14T14-00-00.json",
  "suggested_priority": "critical",
  "scope": "a11y",
  "checkId": "axe-button-name",
  "locator": "#submit-btn",
  "title": "axe-core critical: button-name — submit button has no accessible name",
  "description": "axe-core reports a critical violation of the 'button-name' rule on selector '#submit-btn' (dashboard route, snapshot axe-dashboard-2025-05-14T14-00-00.json). The button has no visible text, aria-label, or aria-labelledby. This violates WCAG 2.1 Success Criterion 4.1.2 (Name, Role, Value). Users relying on screen readers cannot identify or activate this control.",
  "recommendation": "Add aria-label='Submit' or visible button text to the '#submit-btn' element. Verify with a screen reader (VoiceOver or NVDA) after fix."
}
```

---

## Check 3: console-errors

**Purpose:** Read the browser or application console output captured by the driver
and flag error-level messages that are visible to end users — uncaught exceptions,
unhandled promise rejections, and network errors surfaced in the UI.

**Why console errors matter:** TypeScript compile checks and lint catch static
errors; axe-core catches accessibility violations; but runtime errors only surface
during actual execution. A JavaScript exception that crashes a component or a 404
that silently removes a UI section degrades user trust and is the class of bug most
likely to slip through until a real user reports it.

**What is an error-level message (flag these):**
- Lines prefixed with `ERROR`, `UNCAUGHT`, `Unhandled`, `TypeError`, `ReferenceError`
- HTTP 4xx or 5xx responses logged to the console (e.g., `Failed to load resource: the server responded with a status of 404`)
- Unhandled Promise rejections (text contains `UnhandledPromiseRejection` or `UnhandledRejection`)

**What is developer-tooling noise (do NOT flag):**
- React or Vue hydration mismatch hints (often informational in dev mode)
- Hot Module Replacement (HMR) status messages
- Browser extension warnings (`[extension]`, `chrome-extension://`)
- `[Violation]` warnings from Chrome about long tasks (performance, not UX-blocking)
- Source map warnings

**Severity mapping:**

| Error class | Severity |
|---|---|
| Uncaught exception / unhandled rejection | HIGH |
| Visible HTTP 4xx/5xx (resource load failure in UI) | MEDIUM |

**Artifact location:** `<run-dir>/console.log` — runner.mjs appends raw Playwright
process stdout/stderr to this file; structured NDJSON `{ts, type, text, location}`
entries are fixture-emitted via `page.on('console', ...)` and are what the evaluator
parses. Each line has the shape:
`{"ts":<epoch-ms>,"type":"error"|"warning"|...,"text":"<message>","location":{...}}`.
The evaluator parses each line as JSON and inspects the `type` and `text` fields.
If the file is absent, skip check 3.

**Fingerprint inputs:**
- `scope = 'console'`
- `checkId = 'error-' + msgClass` where `msgClass` is the normalized error class:
  - `'uncaught-exception'` for TypeError/ReferenceError/UnhandledRejection
  - `'http-4xx'` or `'http-5xx'` for network errors
- `locator = <origin-URL-if-present | file:line-if-stack-frame-available | 'unknown'>`

**Example finding (HIGH):**

```json
{
  "run_id": "42-1715700000000",
  "rubric_version": "v1",
  "severity": "high",
  "check": "console-errors",
  "fingerprint": "c7a140b8fe291d63",
  "evidence_path": "console.log",
  "suggested_priority": "high",
  "scope": "console",
  "checkId": "error-uncaught-exception",
  "locator": "src/components/InvoiceTable.tsx:87",
  "title": "Uncaught TypeError: Cannot read property 'id' of undefined",
  "description": "The browser console captured an uncaught TypeError at InvoiceTable.tsx:87 during the dashboard flow. The error fires when the invoices array contains a null entry, causing the component to crash. This is a runtime error that is not caught by any existing test and is directly visible to the user via a blank component area.",
  "recommendation": "Add a null guard before accessing .id in the map callback at InvoiceTable.tsx:87. Also add a test case that renders InvoiceTable with a null entry in the invoices prop."
}
```

---

## Check 4: liquid-glass-conformance

**Purpose:** For SwiftUI targets where `Package.swift` declares iOS 26+ or macOS
Tahoe (26+), verify that UI surfaces using translucent or blurred backgrounds apply
Apple's Liquid Glass API (`.glassEffect()`) rather than legacy `.background(.thinMaterial)`
or custom `.blur(radius:)` modifiers.

**Why Liquid Glass:** Apple Liquid Glass was introduced at WWDC 2025 and is the
canonical platform baseline for translucent surfaces in SwiftUI 26+. Apps that
continue using legacy material modifiers on iOS 26+ / macOS Tahoe risk visual
inconsistency with system UI, rejection in App Store review for "non-standard
appearance", and future deprecation of the legacy API. PRD §1.2 names this check
as the secondary motivation for the UX rubric alongside accessibility compliance.

**Applicability condition:** This check is only executed when both conditions hold:
1. `Package.swift` exists in the repository root (or nearest ancestor).
2. `Package.swift` declares `.iOS("26")` or higher, OR `.macOS("26")` or higher,
   in its `platforms: [...]` array.

If neither condition is met, skip check 4 and note the skip in the stdout summary.
This is the expected behavior for pure web projects and Swift projects targeting
earlier OS versions.

**What to flag:** Screens or frames where the AX-tree dump or screenshot metadata
indicates a translucent/blurred background that uses:
- `.background(.thinMaterial)` or `.background(.ultraThinMaterial)` etc.
- `.background(Material.*)` (any Material enum case)
- A `.blur(radius:)` modifier applied to a container as a background effect

**What is compliant (do NOT flag):**
- `.glassEffect()` — correct Liquid Glass API
- `.glassEffect(.regular)` / `.glassEffect(.prominent)` — parametrised Liquid Glass
- Solid color backgrounds (no blur) — these are not Liquid Glass candidates
- Explicitly documented exceptions in `docs/apple-hig-exceptions.md`

**Severity mapping:**

| Condition | Severity |
|---|---|
| Non-compliant surface, no documented exception | MEDIUM |
| Non-compliant surface, documented exception in `docs/apple-hig-exceptions.md` | LOW |

**Evidence required:**
- Peekaboo screenshot of the non-compliant surface (referenced in `evidence_path`).
- The AX-path or frame identifier (referenced in `locator`).

> **Note (v1):** peekaboo-driver may emit `ax-snapshots/glass-modifiers-*.json` artifacts carrying `schema_version: v1, status: stub` for forward compatibility. The v1 rubric does NOT read these — Check 4 operates from screenshots + AX dump annotations only. Future ux-evaluator versions may consume the JSON to classify frames directly.

**Fingerprint inputs:**
- `scope = 'liquid-glass'`
- `checkId = 'missing-glassEffect'`
- `locator = <screen-name>.<frame-id>` (e.g., `'DashboardScreen.headerBlurFrame'`)

**Example finding (MEDIUM):**

```json
{
  "run_id": "42-1715700000000",
  "rubric_version": "v1",
  "severity": "medium",
  "check": "liquid-glass-conformance",
  "fingerprint": "d4e9f2a63c518b07",
  "evidence_path": "screenshots/DashboardScreen-headerBlurFrame.png",
  "suggested_priority": "medium",
  "scope": "liquid-glass",
  "checkId": "missing-glassEffect",
  "locator": "DashboardScreen.headerBlurFrame",
  "title": "Legacy .background(.thinMaterial) on DashboardScreen header — should use .glassEffect()",
  "description": "The DashboardScreen header frame (DashboardScreen.headerBlurFrame) uses .background(.thinMaterial) for its translucent background. The project targets macOS 26+, where .glassEffect() is the canonical Liquid Glass API (WWDC25). Using the legacy Material modifier produces a subtly different visual output and may trigger App Store review flags on macOS Tahoe.",
  "recommendation": "Replace .background(.thinMaterial) with .glassEffect() on the header container in DashboardScreen.swift. If the legacy appearance is intentional for this surface, document the exception in docs/apple-hig-exceptions.md to suppress this finding."
}
```

---

## Out-of-scope (v1)

The following concern areas are deliberately excluded from v1. They may be addressed
in a future `rubric-v2.md` or a separate evaluation skill.

- **Visual-diff / pixel regression.** Pixel-level before/after comparison requires
  a baseline screenshot corpus and a diff algorithm. This is a separate driver
  capability not yet available in test-runner v1.

- **Performance metrics (LCP, FCP, CLS, INP).** Core Web Vitals and layout shift
  metrics require instrumentation beyond the Playwright AX + screenshot capture
  available in test-runner v1. These belong in a dedicated performance rubric.

- **Cross-platform Windows / Linux targets.** The liquid-glass check is macOS/iOS
  specific. Windows and Linux desktop targets are out of scope for all 4 checks
  in v1. Web targets are in scope for checks 1, 2, and 3.

- **Mobile (iOS / Android) native targets.** Playwright does not cover native mobile;
  XCUITest or Appium integration is deferred to a future driver.

- **Stagehand v3 / Browserbase cloud probes.** Cloud-based headless browser pools
  introduce network latency and session management complexity. v1 is scoped to
  local Playwright runs only.

- **Automated recommendation generation via LLM.** The `recommendation` field is
  written by the `ux-evaluator` agent (an LLM). LLM-generated recommendations are
  advisory — they are not automatically filed as code changes. A human or a
  `code-implementer` agent must review and apply them.
