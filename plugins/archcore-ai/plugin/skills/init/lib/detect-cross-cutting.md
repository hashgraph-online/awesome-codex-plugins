# Cross-Cutting Pattern Detection

## What it detects

A **cross-cutting convention** is a recurring, per-module practice the codebase applies the same way across many units of work — worth codifying as a rule so future code follows it. The canonical shapes are a **logging shape** (how each module emits diagnostic output), a **per-handler guard** (an auth/validation/wrap applied at the boundary of each request, job, command, or device handler), and a **mandated shared indirection** (a local module everyone imports instead of going to a third-party dependency directly). The underlying property is language- and domain-agnostic: it holds for web handlers, ML pipeline stages, embedded ISRs, game systems, data/IaC modules, and in-house frameworks alike — only the primitive that expresses it changes. Used in `medium` and `large` modes (whole-repo); small repos rarely have a stable enough convention to codify.

## How to find it (any codebase)

Scan at most 200 source files; skip if nothing meets a threshold. From 2–3 representative source files, first identify **this stack's three primitives**, then apply the **unchanged recurrence thresholds** below:

1. **Logging primitive** — find how a module emits diagnostics (`console.*` / `logger.*` / `print` / `fmt.Println` / `slog.*` / a framework logger / a custom `debugLog`). Signal: a per-module label such as `[<Module>]` appears inside the emit call in **≥ 3 distinct files**, AND the labels are per-module (different files, different labels) — not one shared string.
2. **Per-handler guard mechanism** — find how the stack wraps a handler at definition time: decorator, attribute, annotation, plug, layer, before-filter, or middleware chain. Signal: **one identical guard recurs at ≥ 3 handler definitions**, excluding framework built-ins (the router/route macro itself).
3. **Local shared-module import idiom** — find the stack's import form for a repo-local module (relative path, repo package name, internal package). Signal: **the same local symbol is imported in ≥ 5 files** AND an obvious direct third-party alternative exists that some files could have used instead but don't.

Recurrence below a threshold = no signal. Keep the conservative "surface nothing over a false rule" bar — false positives are worse than missed patterns. Do NOT read a Python data-script's `print("[Stage 1]...")` progress output as a log-prefix convention; do NOT promote infrastructure `app.use(...)` (CORS, body-parser, compression) into a security-guard MUST-rule; do NOT mandate a coincidental shared utility import that has no third-party alternative. If multiple signals fire, keep at most **two**, priority **guard > log-prefix > shared-import** (auth matters most; shared-import is weakest). Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

| Primitive | Example emit / wrap / import forms | Example candidate rule |
| --- | --- | --- |
| Log prefix | `console.(log\|info\|warn\|error)`, `logger.(info\|warn\|error\|debug\|trace)`, `log.(info\|warn\|error\|debug)`, `debugLog(`, Python `print(`, Go `fmt.Println` / `log.Println` / `slog.(Info\|Warn\|Error\|Debug)` — each carrying a `[A-Z][A-Za-z0-9 _-]+` label | Prefix logs with `[<ModuleName>]` matching the module of origin (filter by module in debug sessions). |
| Per-handler guard | TS/JS `withX(handler)`, `handler.use(X)`; Python `@authenticated` / `@login_required` / `@require_auth` / `@jwt_required`; Java `@PreAuthorize` / `@Secured` / `@RolesAllowed`; Go `middleware.Chain(X, Y, Z)` with a recurring ID; Elixir `plug :require_auth` | All handlers MUST be wrapped with `<guardName>`. Do not expose a handler without this guard. |
| Shared import | TS/JS `import { logger } from '../lib/logger'`, `import { db } from '@/db'`; Python `from app.logger import logger`; Go internal-package import with a recurring alias — where `winston` / `pino` / `log/slog` is the bypassed direct alternative | Use the shared `<symbol>` from `<path>`; do not import `<underlying-lib>` directly. |

**Deliberately out of scope here:** call-graph analysis; type-level conventions (`ApiResponse<T>`); file-structure conventions (every module has a `types.ts`); error-handling shapes — all false-positive easily without more data.

## Output

**In `/archcore:init` (Tier-2):** each surviving candidate is surfaced as a `rule` **stub** in init's single preview (the one-line description + the paths it governs). On `confirm`, init composes and creates it as a `rule` — concern-slug filename, `status='draft'` (heuristic-derived; the user confirms before it becomes canon) — under `_shared/rule-contract.md` in Phase E. It does NOT use the y/n prompt below or route to `/archcore:decide`. Allow 0–2 candidates. In large mode, scan **repo-wide** — cross-cutting patterns are inherently global, not limited to the selected domains.

**Standalone (outside init):** show each candidate to the user:

> Detected cross-cutting pattern: <one-line description of the rule>. Seen in: <path-1>, <path-2>, <path-3> (+ N more).
>
> Codify as a rule? (y/n)

On `y`, direct user to `/archcore:decide` (passes a draft rule as context). Do NOT auto-invoke — the user should confirm the exact phrasing through the standard flow. On `n` or no trigger, skip silently.
