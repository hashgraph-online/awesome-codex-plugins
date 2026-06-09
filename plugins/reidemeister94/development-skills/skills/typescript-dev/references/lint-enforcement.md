# Lint Enforcement (JS/TS)

Reference for any JS/TS skill running Phase 3 verify verification. Linting is a blocking gate — same severity as a failing test — wherever a linter is configured. When no linter is configured, the gate is skipped with a recorded warning.

## When to Read This

Read this file at the start of Phase 3 verify in any JS/TS development skill (`frontend-dev`, `typescript-dev`). It defines:

- How to detect which linter(s) the project uses
- How to invoke them (with the detected package manager — see [package-manager.md](package-manager.md))
- How lint failures interact with the Phase 3 verify gate
- What to record in `## Verification Results`

## Detection Algorithm — Union, Not Priority

Detection is a union, not a priority ladder. Multiple linter configs are common in real projects (e.g., biome for fast format-lint + eslint for type-aware rules + oxlint as a fast pre-pass) and they are complementary, not alternatives. Picking only one would silently skip the others.

### Step 1 — `scripts.lint` short-circuit

If `package.json` defines a `scripts.lint` entry, that single command IS the project's lint definition. Run it and stop:

```
<PM> run lint
```

Substitute the detected package manager (see [package-manager.md](package-manager.md)). The project author's script may chain multiple tools, scope to changed files, set `--max-warnings=N`, etc. — respect their explicit definition.

### Step 2 — Union of standalone linter configs

If no `scripts.lint` is defined, scan for standalone linter configs and run **every** one detected. All must pass:

| Config files | Command |
|---|---|
| `biome.json` or `biome.jsonc` | `<PM> exec biome check` |
| `eslint.config.*` (flat config) OR `.eslintrc.*` OR `eslintConfig` field in `package.json` | `<PM> exec eslint .` |
| `.oxlintrc.json` | `<PM> exec oxlint` |

Run them in any order. Aggregate the results — if any one fails, Phase 3 verify fails.

### Step 3 — No detection signal

If neither `scripts.lint` nor any standalone linter config is found:

- Record `Lint: skipped (no \`scripts.lint\`, no linter config detected)` in `## Verification Results`.
- Do NOT block Phase 3 verify. The project hasn't opted into linting; that's a project decision, not a skill override.

## Behavior

| Situation | Action |
|---|---|
| Lint command exits 0 | Record pass, continue Phase 3 verify. |
| Lint command exits non-zero | **Phase 3 verify FAILS.** Same handling as a failing test: read errors, fix, re-run verification. Iterate until lint passes. |
| Multiple linters configured | Run all of them. Each must pass independently. |
| `scripts.lint` is defined but the script is a no-op (e.g., `echo skip`) | Trust the project author. The skill respects explicit project intent — if the user has chosen to neuter their own lint script, that's their decision. |
| Linter config present but the binary isn't installed | Treat as a project-setup error: record the failure in verification output and surface it to the user. Don't auto-install. |

## No `--fix` Auto-Remediation

The skill does NOT run `eslint --fix` / `biome check --apply` / equivalent. Lint output is treated as diagnostics; agents read errors and fix them intentionally. Auto-fix can mask design issues that lint surfaces (unused imports often signal dead code paths; type-narrowing rules often flag missing null checks).

If the project's own `scripts.lint` includes `--fix`, that's the project's choice — respect it.

## Verification Output Convention

Append one entry per linter run to the `## Verification Results` block in the plan file:

### When `scripts.lint` short-circuits

```markdown
- **Lint:** project script (`<PM> run lint`) — PASSED
```

or on failure:

```markdown
- **Lint:** project script (`<PM> run lint`) — FAILED (12 errors)
  - First 3:
    - `src/auth.ts:42:7` no-unused-vars
    - `src/auth.ts:58:3` prefer-const
    - `src/api/login.ts:14:1` import/order
```

### When the union runs

One entry per detected linter:

```markdown
- **Lint:** biome via `biome.json` — PASSED
- **Lint:** eslint via `eslint.config.js` — FAILED (4 errors)
  - First 3: ...
- **Lint:** oxlint via `.oxlintrc.json` — PASSED
```

### When skipped

```markdown
- **Lint:** skipped (no `scripts.lint`, no linter config detected)
```

## Note for Legacy Projects

If a project has thousands of pre-existing lint errors and full enforcement would halt all work, the right answer lives in the project's own `scripts.lint`:

- Scope to changed files: `eslint $(git diff --name-only main...HEAD | grep -E '\\.(ts|tsx|js|jsx)$')`
- Tune severity: `eslint . --max-warnings=100`
- Disable specific rules pending cleanup

These are project decisions. The skill enforces what the project has configured — it does not silently lower the bar.
