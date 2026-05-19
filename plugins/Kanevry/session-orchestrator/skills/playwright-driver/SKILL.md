---
name: playwright-driver
user-invocable: false
tags: [test, driver, web, playwright]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when executing web tests via the canonical `playwright` npm package
  (Microsoft, Apache-2.0). Dispatched by `skills/test-runner/` to execute
  web tests against a target, captures token-frugal AX-tree snapshots +
  screenshots + console output under `.orchestrator/metrics/test-runs/<run-id>/`,
  and exits with deterministic JSON output the orchestrator can parse.
---

# Playwright Driver Skill

## Soul

Before anything else, read and internalize `soul.md` in this skill directory. It defines WHO you are — a thin executor, not an orchestrator. Every action in this session should reflect that identity.

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If GATE_CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion. If GATE_OPEN, continue.

<HARD-GATE>
This driver wraps `playwright` (Apache-2.0, Microsoft). It does NOT use `@playwright/mcp` for browser drive — MCP is ~4× more expensive in tokens per test (Microsoft's own benchmark: ~114K tokens MCP vs ~27K CLI). The R5 grep-canary in `scripts/lib/validate/check-playwright-mcp-canary.mjs` enforces this: any reference to `@playwright/mcp` or `playwright-mcp` under `skills/playwright-driver/**` or `scripts/lib/test-runner/**` fails validate-plugin.
</HARD-GATE>

## Package Note — PRD Correction (Read This First)

**The PRD originally referenced `@playwright/cli` — that wording is WRONG. Do not use it.**

| Package | Version (2026-05-14) | Status |
|---|---|---|
| `playwright` | 1.60.0 | **Canonical — use this** |
| `@playwright/test` | 1.60.0 | Test framework (same release train) |
| `@playwright/cli` | 0.1.13 | Unrelated, unstable — DO NOT USE |
| `@playwright/mcp` | 0.0.75 | MCP adapter — R5 hard-gate blocks this |

Verified via `npm view playwright version` → `1.60.0` (2026-05-14 probe). The binary the orchestrator dispatches is named `playwright` (not `playwright-cli`). Use `playwright@^1.60.0` for compatible-minor updates or pin to `playwright@1.60.0` for reproducibility.

## Install

```bash
npm i -g playwright@1.60.0
playwright install chromium    # download browser binaries
```

For project-local install (preferred in CI):

```bash
npm install --save-dev playwright@1.60.0
npx playwright install chromium
```

## Canonical Usage

The orchestrator (`skills/test-runner/`) dispatches this driver via Bash. Session naming follows the artifact-paths contract:

```bash
RUN_ID="${pid}-${ms_timestamp}"      # from scripts/lib/test-runner/artifact-paths.mjs:makeRunId()
RUN_DIR=".orchestrator/metrics/test-runs/${RUN_ID}"

# Output paths via env vars (Playwright canonical):
#   PLAYWRIGHT_HTML_OUTPUT_DIR=${RUN_DIR}/report
#   PLAYWRIGHT_JSON_OUTPUT_FILE=${RUN_DIR}/results.json
#   PLAYWRIGHT_HTML_OPEN=never
PLAYWRIGHT_HTML_OUTPUT_DIR="${RUN_DIR}/report" \
PLAYWRIGHT_JSON_OUTPUT_FILE="${RUN_DIR}/results.json" \
PLAYWRIGHT_HTML_OPEN=never \
playwright test \
  --output "${RUN_DIR}/test-results" \
  --reporter html,json \
  --trace on \
  --project chromium
```

> Canonical: see https://playwright.dev/docs/test-reporters — reporter names are comma-separated; paths flow via env vars. See `scripts/lib/playwright-driver/runner.mjs` for the canonical invocation.

The orchestrator provides `RUN_ID` and `RUN_DIR` via environment variables. The driver reads these, executes Playwright, and exits. Nothing else.

## Artifact Layout

All artifacts land under `${RUN_DIR}/`. Structure:

```
.orchestrator/metrics/test-runs/<run-id>/
  results.json          # Playwright JSON reporter output — orchestrator parses this
  report/
    index.html          # HTML report (served via `playwright show-report ${RUN_DIR}/report`)
  test-results/
    <test-name>/
      trace.zip         # Playwright trace bundle (open via `playwright show-trace`)
  screenshots/          # pre-created by runner.mjs; content written by test fixtures
    <test-name>-<step>.png   # per-step screenshots (written by test fixture via page.screenshot())
  ax-snapshots/         # pre-created by runner.mjs; content written by test fixtures
    <test-name>.yaml    # Playwright AX-tree dump via page.accessibility.snapshot() (written by test fixture, NOT by driver)
    axe-<route-slug>-<timestamp>.json  # axe-core JSON output (written by test fixture using @axe-core/playwright, NOT by driver)
  console.log           # NDJSON console output (written by test fixture via page.on('console', ...), NOT by driver)
```

**Division of responsibility:**
- **runner.mjs (driver):** spawns `playwright test`, sets reporter env vars (`PLAYWRIGHT_HTML_OUTPUT_DIR`, `PLAYWRIGHT_JSON_OUTPUT_FILE`, `PLAYWRIGHT_HTML_OPEN`), pre-creates `ax-snapshots/` and `screenshots/` directories before spawn so test fixtures can write into them without racing, captures the process exit code, and routes reporter output to `results.json` / `report/`.
- **Test fixtures (in target repo):** navigate pages, emit AX-tree snapshots, run axe-core scans, capture screenshots, and append console NDJSON — all using the `RUN_DIR` env var provided by the driver.

**Token discipline:** NEVER inline AX-tree dumps into the coordinator context — they balloon to 50–200K tokens. Always write to disk under `${RUN_DIR}/ax-snapshots/`. The `ux-evaluator` agent reads from disk, not from prompt context.

## Token-Frugal AX Snapshot Pattern

Tests that need AX-tree data write it in the fixture, not via the driver:

```typescript
// playwright.config.ts fixture pattern
test.afterEach(async ({ page }, testInfo) => {
  const snapshot = await page.accessibility.snapshot();
  const snapshotPath = path.join(
    process.env.RUN_DIR ?? '.orchestrator/metrics/test-runs/default',
    'ax-snapshots',
    `${testInfo.title.replace(/\s+/g, '-')}.yaml`
  );
  await fs.writeFile(snapshotPath, yaml.stringify(snapshot));
});
```

The driver itself never reads or forwards AX snapshots. It only controls invocation.

## Console Capture Pattern

To capture console output as NDJSON:

```typescript
// in test or fixture
page.on('console', (msg) => {
  const entry = JSON.stringify({
    ts: Date.now(),
    type: msg.type(),
    text: msg.text(),
    location: msg.location(),
  });
  fs.appendFileSync(path.join(process.env.RUN_DIR, 'console.log'), entry + '\n');
});
```

## Headed vs Headless

Default: headless (CI-friendly). Operator override via profile:

```bash
playwright test --headed    # local debugging
playwright test --debug     # opens Playwright Inspector
playwright show-trace "${RUN_DIR}/test-results/<test>/trace.zip"
playwright show-report "${RUN_DIR}/report"
```

The test-runner profile registry (`.orchestrator/policy/test-profiles.json`) controls headed/headless and browser selection — the driver stays simple and reads these from environment variables set by the orchestrator.

## Composability Contract

### Invocation Shape

```bash
# Output paths via env vars (Playwright canonical):
#   PLAYWRIGHT_HTML_OUTPUT_DIR=${RUN_DIR}/report
#   PLAYWRIGHT_JSON_OUTPUT_FILE=${RUN_DIR}/results.json
#   PLAYWRIGHT_HTML_OPEN=never
bash -c "PLAYWRIGHT_HTML_OUTPUT_DIR=${RUN_DIR}/report \
  PLAYWRIGHT_JSON_OUTPUT_FILE=${RUN_DIR}/results.json \
  PLAYWRIGHT_HTML_OPEN=never \
  playwright test \
  --output ${RUN_DIR}/test-results \
  --reporter html,json \
  --trace on \
  --project ${PROFILE_PROJECT:-chromium}"
```

> Canonical: see https://playwright.dev/docs/test-reporters — reporter names are comma-separated; paths flow via env vars. See `scripts/lib/playwright-driver/runner.mjs` for the canonical invocation.

### Exit Codes

| Code | Meaning | Orchestrator Action |
|---|---|---|
| 0 | All tests passed | Record pass, continue |
| 1 | At least one test failed | Failures become findings (non-fatal) |
| 2 | Framework error (network, browser-install) | Surface as driver error, halt run |

### Outputs the Orchestrator MUST Parse

- `${RUN_DIR}/results.json` — Playwright JSON reporter format (`testRun.{expected,unexpected,skipped,status}`)
- `${RUN_DIR}/test-results/**/trace.zip` — trace bundles, one per test
- `${RUN_DIR}/screenshots/**/*.png` — per-step screenshots
- `${RUN_DIR}/console.log` — captured console as NDJSON
- `${RUN_DIR}/ax-snapshots/*.yaml` — Playwright AX-tree dumps via `page.accessibility.snapshot()` (written by test fixtures)
- `${RUN_DIR}/ax-snapshots/axe-*.json` — axe-core violation reports from `@axe-core/playwright` (written by test fixtures; consumed by `ux-evaluator` Check 2)

## Version Pin + Upper-Bound Advisory

Pinned: `playwright@1.60.0` (verified 2026-05-14). The 1.x line is the long-term stable track — Playwright has not announced a v2. Upper-bound advisory: re-validate this skill when upstream crosses 1.65; check for behavioral shifts in JSON reporter format and trace bundle schema before re-pinning.

## Playwright Subcommands Reference

| Subcommand | Purpose |
|---|---|
| `playwright test` | Run test suite |
| `playwright codegen <url>` | Record tests interactively |
| `playwright install` | Download browser binaries |
| `playwright show-report <dir>` | Serve HTML report locally |
| `playwright show-trace <zip>` | Open trace viewer |
| `playwright screenshot <url>` | Single-shot screenshot |
| `playwright open <url>` | Open browser with inspector |

## Anti-Patterns

- **DO NOT** import `@playwright/mcp` for browser drive — 4× token cost. R5 grep-canary blocks this at validate-plugin time.
- **DO NOT** inline AX-tree dumps into agent prompt context — always write to disk under `${RUN_DIR}/ax-snapshots/`.
- **DO NOT** invoke `npx playwright` per-test in a loop — install once, dispatch the local binary.
- **DO NOT** mix Playwright runs with different session IDs — use the orchestrator's `RUN_ID` everywhere.
- **DO NOT** use `@playwright/cli@0.1.13` — that is an unrelated, low-version package. Use `playwright@1.60.0`.
- **DO NOT** write artifacts outside `${RUN_DIR}` — single source of truth for the orchestrator.

## Sub-File Reference

| File | Purpose |
|---|---|
| `soul.md` | Driver identity: thin wrapper, not orchestrator |
