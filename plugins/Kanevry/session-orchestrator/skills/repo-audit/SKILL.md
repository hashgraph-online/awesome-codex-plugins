---
name: repo-audit
description: Use this skill when the user wants to audit a repository for baseline compliance, check code quality, security posture, CI/CD setup, testing, documentation, and ecosystem configuration. Runs 9 checklist categories and emits a Markdown report plus JSON sidecar at .orchestrator/metrics/repo-audit-<timestamp>.json. <example>Context: User is in a project repo and wants a baseline compliance check. user: "/repo-audit" assistant: "Running repo-audit across 9 categories — Configuration, Code Quality, Git Hygiene, CI/CD, Testing, Security, Documentation, Clank Integration (optional), and MCP Configuration. Will produce a Markdown checklist report and JSON sidecar." <commentary>The user wants a compliance check; this skill is appropriate because it runs all 9 categories with pass/fail/warn/skipped statuses and writes structured output.</commentary></example>
model: inherit
color: cyan
---

# Repo Audit Skill

Perform a comprehensive audit of the host repository against the ecosystem baseline. Emits a structured Markdown checklist report and a JSON sidecar for trend tracking.

## Purpose

Answer the question: "Does this repo match the ecosystem baseline?" — a compliance-focused, checkable question with a fixed 9-category checklist. Distinct from `/discovery` (broad quality probes) and `/harness-audit` (plugin installation health).

## Phase 1: Read Session Config

Read the project's `## Session Config` section in `CLAUDE.md` (or `AGENTS.md` for Codex CLI). Store resolved values as `$CONFIG`.

**Command resolution follows `skills/quality-gates/SKILL.md` priority order:**
1. `.orchestrator/policy/quality-gates.json` — canonical policy file (if present).
2. Session Config `test-command` / `typecheck-command` / `lint-command` — fallback.
3. Hardcoded defaults: `npm test`, `npm run typecheck`, `npm run lint`.

If any command is set to the literal string `skip`, skip that check entirely and mark it `skipped`.

## Phase 2: Clank Detection

Check for Clank integration markers:
```bash
ls .clank/ 2>/dev/null || ls clank.config.* 2>/dev/null || ls clank.config.json 2>/dev/null
```

Set `$CLANK_DETECTED=true` if any marker exists, `false` otherwise.

Also check Session Config for `ecosystem: baseline` — if set, treat Clank checks as required rather than optional.

## Phase 3: Run 9 Audit Categories

Run all checks in parallel where possible. For each check use the status symbols:
- `✓` — passes
- `✗` — fails (action required)
- `⚠` — warning (review recommended)
- `skipped` — intentionally skipped

### Category 1: Configuration

| Check | Method |
|---|---|
| `CLAUDE.md` exists (50-100 lines, lean) | `wc -l CLAUDE.md` |
| `.claude/rules/` has path-scoped rules | `ls .claude/rules/*.md 2>/dev/null` |
| `.claude/settings.json` exists | `ls .claude/settings.json` |
| `.mcp.json` exists with servers | `ls .mcp.json` |
| `.gitignore` covers `.env*`, `node_modules`, build artifacts | `grep -E '\.env\*|node_modules' .gitignore` |

### Category 2: Code Quality

Commands resolved from Session Config per Phase 1.

| Check | Method |
|---|---|
| ESLint v9 flat config (`eslint.config.mjs`) | `ls eslint.config.mjs 2>/dev/null` |
| Prettier config (`.prettierrc` or `prettier.config.*`) | `ls .prettierrc* prettier.config.* 2>/dev/null` |
| TypeScript strict mode (`"strict": true` in tsconfig.json) | `grep '"strict": true' tsconfig.json` |
| 0 TypeScript errors | Run `{typecheck-command} 2>&1` — pass if exit code 0 |
| No `console.log` in production code (excluding tests) | `grep -r 'console\.log' --include='*.ts' --include='*.mts' --exclude-dir=tests --exclude-dir=node_modules . 2>/dev/null | grep -v '\.test\.'` |
| Lint passes | Run `{lint-command} 2>&1` — pass if exit code 0 |

### Category 3: Git Hygiene

| Check | Method |
|---|---|
| Husky + lint-staged configured | `ls .husky/ 2>/dev/null && grep 'lint-staged' package.json` |
| commitlint (Conventional Commits) | `ls commitlint.config.* 2>/dev/null || grep 'commitlint' package.json` |
| Gitleaks pre-commit or CI | `ls .gitleaks.toml 2>/dev/null || grep 'gitleaks' .husky/pre-commit 2>/dev/null` |
| No secrets in git history | `git log --all -p 2>/dev/null | grep -i 'password\|secret\|api_key\|token' | head -1` — warn if any found |

### Category 4: CI/CD

| Check | Method |
|---|---|
| CI config exists (`.gitlab-ci.yml` or `.github/workflows/`) | `ls .gitlab-ci.yml 2>/dev/null \|\| ls .github/workflows/*.yml 2>/dev/null` |
| Stages include validate → security → test → deploy | Read CI config, check for these stage names |
| Typecheck in CI | `grep -E 'tsgo|typecheck' .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null` |
| Tests in CI | `grep -E 'vitest|npm test|pnpm test' .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null` |
| Dependency audit in CI | `grep -E 'audit|pnpm audit' .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null` |

### Category 5: Testing

| Check | Method |
|---|---|
| Vitest configured (`vitest.config.ts` or `vitest.config.mjs`) | `ls vitest.config.* 2>/dev/null` |
| Test coverage configured | `grep 'coverage' vitest.config.* 2>/dev/null` |
| E2E tests (Playwright) for frontend repos | `ls playwright.config.* 2>/dev/null` — only required if `next.config.*` or `nuxt.config.*` exists |
| Test scripts in `package.json` | `grep '"test"' package.json 2>/dev/null` |
| Tests pass | Run `{test-command} 2>&1` — pass if exit code 0 |

### Category 6: Security

| Check | Method |
|---|---|
| Auth-at-boundary pattern (`requireAuth`) | `grep -r 'requireAuth' --include='*.ts' src/ 2>/dev/null \|\| echo "N/A (no src/)"` |
| Zod validation on inputs | `grep -r 'z\.object\|z\.string\|z\.parse\|safeParse' --include='*.ts' src/ 2>/dev/null \|\| echo "N/A"` |
| No hardcoded secrets (scan for API key patterns) | `grep -r 'sk-\|api_key\s*=\s*"' --include='*.ts' --include='*.mts' --exclude-dir=node_modules . 2>/dev/null` — warn if found |
| `.env*` files not tracked | `git ls-files | grep '\.env'` — fail if any `.env` (not `.env.example`) tracked |
| `.env.example` documents all secrets | `ls .env.example 2>/dev/null` |

Note: RLS, rate limiting, and CORS checks are `⚠ review` items — they require human judgment and cannot be fully automated. Flag them as `⚠ manual-review-recommended`.

### Category 7: Documentation

| Check | Method |
|---|---|
| `README.md` exists | `ls README.md 2>/dev/null` |
| `.env.example` exists with documented vars | `ls .env.example 2>/dev/null` |
| Architecture documented in `CLAUDE.md` | `grep -i 'architecture\|structure\|stack' CLAUDE.md 2>/dev/null` |

### Category 8: Clank Integration (Optional)

**If `$CLANK_DETECTED=false` AND `ecosystem: baseline` is NOT set in Session Config:**

```
### 8. Clank Integration
Status: skipped — Clank not detected (.clank/ and clank.config.* absent; ecosystem: baseline not set)
```

Do not mark any Clank check as `✗`. Absence of Clank is not a failure outside the baseline ecosystem.

**If `$CLANK_DETECTED=true` OR `ecosystem: baseline` is set:**

| Check | Method |
|---|---|
| `GET /health` endpoint exists (for services) | `grep -r '/health' --include='*.ts' src/ 2>/dev/null` |
| CI pipeline sends webhooks to Event Bus | `grep -E 'webhook\|event.bus\|clank' .gitlab-ci.yml .github/workflows/*.yml 2>/dev/null` |
| Sentry configured (for user-facing apps) | `grep -r 'Sentry' --include='*.ts' --include='*.mts' --exclude-dir=node_modules . 2>/dev/null` |
| Conventional Commits enforced (commitlint) | `ls commitlint.config.* 2>/dev/null || grep 'commitlint' package.json 2>/dev/null` |

### Category 9: MCP Configuration

**Scope:** Audits only the repo-local `.mcp.json` file — does NOT cover the user-machine MCPJungle gateway or globally-imported MCP servers.

| Check | Method |
|---|---|
| `.mcp.json` exists | `ls .mcp.json 2>/dev/null` |
| MCP servers match project type | Read `.mcp.json`, verify server list is appropriate (e.g., `shadcn` only for frontend repos, no stale servers) |
| No stale or unused MCP entries | Cross-reference `.mcp.json` servers against project stack markers |
| MCP server health probe (optional — requires `mcporter`) | For each server declared in repo-local `.mcp.json`: if `command -v mcporter` is present, run `mcporter list --json` and read the per-server `status` field — `ok` → ✓ pass; `auth` → ⚠ warn (remediation: `mcporter auth <server>`); `offline`/`error` → ✗ fail. If `mcporter` is absent → mark this check `skipped` with note "enable with `npm install -g mcporter`". `mcporter` is never a hard dependency; the repo audit proceeds without it. |

## Phase 4: Emit Report

### 4.1 Markdown Report (stdout)

Emit a structured report in this format:

```markdown
# Repo Audit Report — <repo-name>
Generated: <ISO timestamp>
Session Config commands: test=`<test-command>` typecheck=`<typecheck-command>` lint=`<lint-command>`

## Summary
| Category | Pass | Fail | Warn | Skipped |
|---|---|---|---|---|
| 1. Configuration | N | N | N | N |
| 2. Code Quality | N | N | N | N |
| 3. Git Hygiene | N | N | N | N |
| 4. CI/CD | N | N | N | N |
| 5. Testing | N | N | N | N |
| 6. Security | N | N | N | N |
| 7. Documentation | N | N | N | N |
| 8. Clank Integration | N | N | N | N |
| 9. MCP Configuration | N | N | N | N |
| **Total** | N | N | N | N |

**Overall:** ✓ PASS / ✗ FAIL / ⚠ WARN

## Detailed Results

### 1. Configuration
- ✓ CLAUDE.md exists (72 lines — within 50-100 range)
- ✗ `.claude/settings.json` missing — create with permissions and hooks
- ⚠ `.mcp.json` missing — add MCP servers appropriate for your stack
...

### 2. Code Quality
...

### 8. Clank Integration
skipped — Clank not detected (.clank/ and clank.config.* absent; ecosystem: baseline not set in Session Config)

### 9. MCP Configuration
- ✓ `.mcp.json` exists
- ✓ Servers match project type
- ⚠ MCP server health probe: `github` → ok; `shadcn` → auth (run `mcporter auth shadcn`)

## Critical Findings
<List only ✗ items — actionable, with fix guidance>

## Action Items
<Numbered list of recommended fixes, ordered by priority>
```

### 4.2 JSON Sidecar

Write to `.orchestrator/metrics/repo-audit-<unix-timestamp>.json`:

```json
{
  "schema_version": 1,
  "generated_at": "<ISO timestamp>",
  "repo": "<basename of cwd>",
  "commands": {
    "test": "<resolved test-command>",
    "typecheck": "<resolved typecheck-command>",
    "lint": "<resolved lint-command>"
  },
  "clank_detected": false,
  "ecosystem_baseline": false,
  "categories": {
    "configuration": { "pass": 4, "fail": 1, "warn": 0, "skipped": 0, "checks": [] },
    "code_quality": { "pass": 3, "fail": 1, "warn": 1, "skipped": 0, "checks": [] },
    "git_hygiene": { "pass": 2, "fail": 1, "warn": 0, "skipped": 0, "checks": [] },
    "ci_cd": { "pass": 0, "fail": 5, "warn": 0, "skipped": 0, "checks": [] },
    "testing": { "pass": 4, "fail": 0, "warn": 0, "skipped": 1, "checks": [] },
    "security": { "pass": 3, "fail": 1, "warn": 2, "skipped": 0, "checks": [] },
    "documentation": { "pass": 2, "fail": 0, "warn": 1, "skipped": 0, "checks": [] },
    "clank_integration": { "pass": 0, "fail": 0, "warn": 0, "skipped": 4, "checks": [] },
    "mcp_configuration": { "pass": 1, "fail": 0, "warn": 2, "skipped": 0, "checks": [] }
  },
  "summary": {
    "total_pass": 0,
    "total_fail": 0,
    "total_warn": 0,
    "total_skipped": 0,
    "overall": "pass|fail|warn"
  }
}
```

Each `checks` array entry:
```json
{ "id": "config.claude-md-exists", "status": "pass|fail|warn|skipped", "detail": "human-readable result" }
```

MCP server health entries additionally include an optional `remediation` field (representative examples):
```json
{ "id": "mcp.server-health-github", "status": "pass", "detail": "mcporter: status=ok", "remediation": null }
{ "id": "mcp.server-health-shadcn", "status": "warn", "detail": "mcporter: status=auth", "remediation": "mcporter auth shadcn" }
{ "id": "mcp.server-health-probe", "status": "skipped", "detail": "mcporter not installed — enable with npm install -g mcporter", "remediation": "npm install -g mcporter" }
```

Create `.orchestrator/metrics/` if it does not exist:
```bash
mkdir -p .orchestrator/metrics
```

Write using `node -e` or direct file write — do not require any external dependency.

## Overall Status Logic

- `✗ FAIL` — any check has status `fail`
- `⚠ WARN` — no fails, but at least one `warn`
- `✓ PASS` — all checks are `pass` or `skipped`

## Success Criteria

- All 9 categories checked with pass/fail/warn/skipped status
- Clank section correctly detected and marked `skipped` when absent
- Commands resolved from Session Config (not hardcoded `pnpm`)
- JSON sidecar written to `.orchestrator/metrics/repo-audit-<timestamp>.json`
- No false positives — verify findings before reporting
- Critical security findings flagged prominently in "Critical Findings" section
