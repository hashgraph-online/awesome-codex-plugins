# Bootstrap Standard Template

> Scaffold instructions for the Standard tier.
> Called from `skills/bootstrap/SKILL.md` Phase 3 when `CONFIRMED_TIER = standard`.

Standard tier is a strict superset of Fast tier. Execute all Fast-tier steps first, then the Standard-specific steps below.

## Step 1–7: Execute Fast Tier

Read and execute `skills/bootstrap/fast-template.md` Steps 1–7 in full. Do not skip any step. The Fast commit (`chore: bootstrap (fast)`) is NOT made — Fast steps produce files only; the single commit happens at Standard Step 7 below.

**Exception to fast-template Step 6:** Do not run the git commit in fast-template Step 6. All files (Fast + Standard) are committed together at Standard Step 7 below.

**Exception to fast-template Step 5 (bootstrap.lock):** Do not write `.orchestrator/bootstrap.lock` yet. The lock is written with `tier: standard` at Standard Step 6.

## Archetype Detection

Before executing the stack-specific steps, resolve the final archetype:

```
ARCHETYPE = CONFIRMED_ARCHETYPE  # set by SKILL.md from intensity-heuristic or user selection
```

Valid values: `static-html` | `node-minimal` | `nextjs-minimal` | `python-uv`

If `ARCHETYPE` is `null` or unset at this point, default to `node-minimal`.

The sections below are conditional on `ARCHETYPE`. Execute only the section that matches.

---

## Archetype: `static-html`

No build tooling needed. Create minimal structure for a static HTML project.

### Step S1: No manifest file

Static HTML has no `package.json` or `pyproject.toml`. Skip to Step S2.

### Step S2: No tsconfig

Static HTML has no TypeScript. Skip to Step S3.

### Step S3: No ESLint / Prettier

No linter for plain HTML/CSS/JS projects. Skip to Step S4.

### Step S4: No test framework

No automated test for static HTML. Skip to Step S5.

### Step S5: Expanded README.md

Overwrite the stub README.md created by the Fast step:

```markdown
# <REPO_NAME>

<One-sentence description.>

## Usage

Open `index.html` in a browser or serve with any static file server:

```bash
npx serve .
```

## Development

Edit `index.html`, `style.css`, and `script.js` directly. No build step required.
```

### Step S6: .editorconfig

Write `.editorconfig`:

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.html]
indent_size = 2

[*.css]
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

---

## Archetype: `node-minimal`

Node/TypeScript project without a framework. Creates `package.json`, `tsconfig.json`, ESLint, Prettier, Vitest, and one sanity test.

### Step S1: package.json

Write `package.json`:

```json
{
  "name": "<REPO_NAME>",
  "version": "0.1.0",
  "description": "<One-sentence description from user prompt>",
  "type": "module",
  "scripts": {
    "build": "tsc --noEmit",
    "lint": "eslint .",
    "format": "prettier --write .",
    "test": "vitest run"
  },
  "devDependencies": {
    "@eslint/js": "^9.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0",
    "vitest": "^2.0.0"
  }
}
```

### Step S2: tsconfig.json

Write `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist"
  },
  "include": ["src/**/*", "tests/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

### Step S3: ESLint v9 flat config + Prettier

Write `eslint.config.mjs`:

```js
import js from "@eslint/js";

/** @type {import("eslint").Linter.Config[]} */
export default [
  js.configs.recommended,
  {
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
    },
  },
  {
    ignores: ["dist/", "node_modules/", "coverage/"],
  },
];
```

Write `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### Step S4: Vitest sanity test

Create directory and test file:

```bash
mkdir -p "$REPO_ROOT/tests"
```

Write `tests/sanity.test.ts`:

```ts
import { describe, it, expect } from "vitest";

describe("sanity", () => {
  it("true is true", () => {
    expect(true).toBe(true);
  });
});
```

Also create the source directory so TypeScript is happy:

```bash
mkdir -p "$REPO_ROOT/src"
```

Write `src/index.ts` (minimal entry point):

```ts
// Entry point — replace with your implementation.
export {};
```

### Step S5: Expanded README.md

Overwrite the stub README.md:

```markdown
# <REPO_NAME>

<One-sentence description.>

## Installation

```bash
pnpm install
```

## Usage

```bash
pnpm build
```

## Development

| Command | Description |
|---------|-------------|
| `pnpm build` | Type-check with TypeScript |
| `pnpm lint` | Lint with ESLint |
| `pnpm format` | Format with Prettier |
| `pnpm test` | Run tests with Vitest |
```

### Step S6: .editorconfig

Write `.editorconfig`:

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```

---

## Archetype: `nextjs-minimal`

Bare Next.js setup. Creates `package.json`, `tsconfig.json`, ESLint, Prettier, Vitest, and one sanity test.

### Step S1: package.json

Write `package.json`:

```json
{
  "name": "<REPO_NAME>",
  "version": "0.1.0",
  "description": "<One-sentence description from user prompt>",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "format": "prettier --write .",
    "test": "vitest run"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0",
    "vitest": "^2.0.0"
  }
}
```

### Step S2: tsconfig.json

Write `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Step S3: ESLint v9 flat config + Prettier

Write `eslint.config.mjs`:

```js
import js from "@eslint/js";

/** @type {import("eslint").Linter.Config[]} */
export default [
  js.configs.recommended,
  {
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
    },
  },
  {
    ignores: ["dist/", "node_modules/", ".next/", "coverage/"],
  },
];
```

Write `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### Step S4: Vitest sanity test

Create directory and test file:

```bash
mkdir -p "$REPO_ROOT/tests"
```

Write `tests/sanity.test.ts`:

```ts
import { describe, it, expect } from "vitest";

describe("sanity", () => {
  it("true is true", () => {
    expect(true).toBe(true);
  });
});
```

Create minimal Next.js app entry:

```bash
mkdir -p "$REPO_ROOT/src/app"
```

Write `src/app/page.tsx`:

```tsx
export default function Home() {
  return <main><h1><REPO_NAME></h1></main>;
}
```

Write `src/app/layout.tsx`:

```tsx
export const metadata = { title: "<REPO_NAME>" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

### Step S5: Expanded README.md

Overwrite the stub README.md:

```markdown
# <REPO_NAME>

<One-sentence description.>

## Installation

```bash
pnpm install
```

## Usage

```bash
pnpm dev      # Start development server at http://localhost:3000
pnpm build    # Production build
pnpm start    # Start production server
```

## Development

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start dev server |
| `pnpm lint` | Lint with ESLint |
| `pnpm format` | Format with Prettier |
| `pnpm test` | Run tests with Vitest |
```

### Step S6: .editorconfig

Write `.editorconfig`:

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```

---

## Archetype: `python-uv`

Python project using `uv` as the package manager and `pytest` for testing.

### Step S1: pyproject.toml

Write `pyproject.toml`:

```toml
[project]
name = "<REPO_NAME>"
version = "0.1.0"
description = "<One-sentence description from user prompt>"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "ruff>=0.4",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Step S2: No tsconfig

Python project. Skip.

### Step S3: Ruff (replaces ESLint/Prettier for Python)

Ruff is already configured in `pyproject.toml` above. No separate config file needed. Note: Ruff is the Python-ecosystem equivalent of ESLint + Prettier for this archetype.

### Step S4: pytest sanity test

```bash
mkdir -p "$REPO_ROOT/tests"
touch "$REPO_ROOT/tests/__init__.py"
mkdir -p "$REPO_ROOT/src"
touch "$REPO_ROOT/src/__init__.py"
```

Write `tests/test_sanity.py`:

```python
def test_sanity() -> None:
    assert True
```

### Step S5: Expanded README.md

Overwrite the stub README.md:

```markdown
# <REPO_NAME>

<One-sentence description.>

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python src/main.py
```

## Development

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies |
| `uv run ruff check .` | Lint with Ruff |
| `uv run ruff format .` | Format with Ruff |
| `uv run pytest` | Run tests with pytest |
```

### Step S6: .editorconfig

Write `.editorconfig`:

```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[*.yml]
indent_size = 2

[*.json]
indent_size = 2
```

---

<!-- @include _shared-template.md#parallel-sessions-rule -->
## Step 3a: Install Parallel-Sessions Rule

Canonical implementation in [`_shared-template.md#parallel-sessions-rule`](_shared-template.md).

Write the vendored rule from `$PLUGIN_ROOT/templates/_shared/rules/parallel-sessions.md` to
`$REPO_ROOT/.claude/rules/parallel-sessions.md` (idempotent: missing→create, identical→skip,
differs→overwrite). The shared partial also runs
`cp "$PLUGIN_ROOT/templates/_shared/loop.md" "$REPO_ROOT/.claude/loop.md"` so bare `/loop` gets a
repo-aware maintenance prompt. See shared partial for full shell command. Issues #155, #633.

Note: Runs before S99. If S99 fetches a newer `parallel-sessions.md` from the baseline, the
baseline version wins (acceptable — S99 is canonical).

## Step 3b: Initialize .orchestrator/metrics/ (#185)

Create the metrics directory and an empty learnings file so the `/evolve` skill and discovery probes have a write target from day one:

```bash
mkdir -p "$REPO_ROOT/.orchestrator/metrics"
[[ -f "$REPO_ROOT/.orchestrator/metrics/learnings.jsonl" ]] || \
  : > "$REPO_ROOT/.orchestrator/metrics/learnings.jsonl"
```

**Idempotent.** Re-running bootstrap does not overwrite an existing file.

**Gitignore guidance:** Do NOT add `.orchestrator/metrics/*.jsonl` to `.gitignore`. The files are intentionally visible in version control — they carry project learnings and session history that future contributors benefit from.

<!-- @include _shared-template.md#baseline-fetch -->
## Step S99: (Optional) Fetch Canonical Rules + Agents from Baseline

Canonical implementation in [`_shared-template.md#baseline-fetch`](_shared-template.md).

OPT-IN: only fires when `baseline-ref` is in Session Config, `GITLAB_TOKEN` is set, and
`scripts/lib/fetch-baseline.mjs` exists. Fetches `.claude/rules/*.md` from the baseline GitLab
project (default project 52) and writes `.claude/.baseline-fetch.lock`. Does NOT abort on failure.
The rule manifest includes `owner-persona.md` (alongside `parallel-sessions.md`, `development.md`,
and the rest of the always-on rules). See shared partial for full implementation.

---

<!-- @include _shared-template.md#vault-registration -->
## Step 5.5: Vault-Registration Prompt (Product Repos) (#190)

Canonical implementation in [`_shared-template.md#vault-registration`](_shared-template.md).

Runs `scripts/lib/product-repo-detect.mjs` to detect product-repo signals. When detected and no
`vault:` key exists in Session Config, prompts the user (Y/n) to register a vault entry.
Idempotent via `hasVaultConfig`. See shared partial for full detection script and examples.

---

## Step 6: Write bootstrap.lock (Standard)

Write `.orchestrator/bootstrap.lock` **atomically** (mktemp + mv prevents a corrupt lock if the
process is interrupted mid-write):

```bash
_LOCK_TMP=$(mktemp "$REPO_ROOT/.orchestrator/bootstrap.lock.XXXXXX")
cat > "$_LOCK_TMP" << LOCK
# .orchestrator/bootstrap.lock
version: 1
tier: standard
archetype: <CONFIRMED_ARCHETYPE>
timestamp: <current ISO 8601 UTC — e.g., 2026-04-16T09:30:00Z>
source: <claude-init | plugin-template | projects-baseline>
plugin-version: <session-orchestrator plugin version — read from $PLUGIN_ROOT/package.json .version field>
bootstrapped-at: <current ISO 8601 UTC — same value as timestamp; distinct field for age-validation probe>
LOCK
mv "$_LOCK_TMP" "$REPO_ROOT/.orchestrator/bootstrap.lock"
```

Set `source` using the same logic as fast-template Step 5:
- `projects-baseline` if `PATH_TYPE = private` and baseline scripts were used
- `claude-init` if `claude init` ran successfully
- `plugin-template` otherwise

<!-- @include _shared-template.md#quality-gate-policy -->
## Step 6.5: Quality-Gate Policy File (#183)

Canonical implementation in [`_shared-template.md#quality-gate-policy`](_shared-template.md).

Write `.orchestrator/policy/quality-gates.json` with package-manager-detected defaults (idempotent:
skip if file already exists). Uses `scripts/lib/package-manager.mjs`; falls back to npm defaults.
See shared partial for full shell command. Issue #183.

<!-- @include _shared-template.md#state-md-scaffold -->
## Step 6.6: STATE.md Scaffold (#184)

Canonical implementation in [`_shared-template.md#state-md-scaffold`](_shared-template.md).

Scaffold `.claude/STATE.md` from `skills/bootstrap/STATE.md.template` (idempotent: skip if
already exists). On Codex CLI / Cursor IDE, substitute `.codex/` or `.cursor/` for `.claude/`.
See shared partial for full shell command. Issue #184.

<!-- @include _shared-template.md#agents-scaffold -->
## Step 6.7: .claude/agents/ Scaffold (#189)

Canonical implementation in [`_shared-template.md#agents-scaffold`](_shared-template.md).

Copy 3 opinionated agent templates (`project-discovery`, `project-code-review`,
`project-quality-gate`) into `$REPO_ROOT/.claude/agents/`. Idempotent: skip existing files.
See shared partial for full shell command. Issue #189.

## Step 7: Initial Git Commit

Stage all created files and commit:

```bash
cd "$REPO_ROOT"
BOOTSTRAP_FILES=(
  CLAUDE.md AGENTS.md .gitignore README.md .orchestrator/bootstrap.lock
  .orchestrator/policy/quality-gates.json
  package.json pyproject.toml tsconfig.json eslint.config.mjs .prettierrc
  .editorconfig src/ tests/ .claude/
)
# Add only the files bootstrap created — no sweeping -u/-A to avoid catching pre-existing files
for _f in "${BOOTSTRAP_FILES[@]}"; do
  [[ -e "$_f" ]] && git add -- "$_f"
done
git commit -m "chore: bootstrap (standard)"
```

The commit message is fixed — do not vary it.

## Step 8: Report Created Files

After the commit succeeds, output a concise summary of all files created (Fast + Standard). Include the archetype in the header line:

```
Bootstrap (standard, <archetype>) complete. Created:
  CLAUDE.md (or AGENTS.md)             — Session Config (7 mandatory fields, validated)
  .gitignore                            — stack-appropriate rules
  README.md                             — expanded with Installation, Usage, Dev
  .editorconfig                         — consistent editor settings
  <manifest file>                       — e.g., package.json / pyproject.toml
  <tsconfig.json>                       — if JS/TS archetype
  <eslint.config.mjs + .prettierrc>    — if JS/TS archetype
  <tests/sanity.test.ts or equiv>       — sanity test
  .claude/rules/parallel-sessions.md   — vendored PSA rule (issue #155)
  .claude/STATE.md                      — idle placeholder (issue #184)
  .orchestrator/bootstrap.lock          — version: 1, tier: standard
  .orchestrator/policy/quality-gates.json — test/typecheck/lint commands (issue #183)
Committed: "chore: bootstrap (standard)"
```

Then return control to `SKILL.md` Phase 5.
