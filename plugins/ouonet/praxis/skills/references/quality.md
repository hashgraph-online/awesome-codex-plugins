# Quality and doc-coverage

The quality bar is **declared, then verified**. `convention` (set at `design`/`onboard`) captures the stack's best practices and project conventions; `tdd`/`review` verify code against them; `review`/`ship` verify docs cover the code.

## `convention` standard

Source: tech-spec `stack`/`convention`. Read from code, never invented. Minimum:

- lint / format / typecheck tools (or "none declared")
- error-handling pattern
- test pattern
- security baseline (input validation, secrets, authz)
- naming / file structure

New: state the stack's idiomatic practices. Existing: read from code.

## Code checks (`tdd` refactor gate, `review`)

1. **Mechanical**: Declared lint/format/typecheck must be green. None declared → `review` flags FIX, not BLOCK.
2. **Convention**: Code matches the declared `convention`.
3. **Design**: Coupling, cohesion, abstraction — is the structure sound and idiomatic for the stack? Lint/typecheck can't catch this; you must.

State what you ran, assessed, and changed — or why not.

## Doc-coverage checks (`review`, `ship` gate)

1. `contract` covers the **full** public surface — not only the "must-not-break" stability set.
2. Env vars / config / error modes are documented.
3. README commands runnable: run build/test/lint; for destructive ones, verify entry points — don't blind-run.
4. tech-spec `contract`/`convention` match the code.

## Severity

- lint/format/typecheck red (declared) → BLOCK; undeclared → FIX.
- README command inaccurate / unrunnable → BLOCK (user-visible wrong info).
- `contract` incomplete / env-errors undocumented → FIX.
- Code off `convention` / non-idiomatic → FIX (BLOCK if severe).
