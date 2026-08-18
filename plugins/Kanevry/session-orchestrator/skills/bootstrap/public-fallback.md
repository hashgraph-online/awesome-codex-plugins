# Bootstrap Public Fallback

> Support file for `skills/bootstrap/SKILL.md`.
> Defines the Private vs. Public path decision and the Public path scaffold logic for all tiers.

## Step 1: Detect PATH_TYPE (Silent — No User Interaction)

Read `plan-baseline-path` from Session Config in `CLAUDE.md` (or `AGENTS.md` on Codex):

```bash
BASELINE_PATH=$(grep -m1 "^plan-baseline-path:" "$REPO_ROOT/CLAUDE.md" 2>/dev/null | awk '{print $2}')
# Expand leading ~ to $HOME so paths like ~/Projects/projects-baseline work correctly
BASELINE_PATH="${BASELINE_PATH/#\~/$HOME}"
```

Decision logic (evaluated in order — first match wins):

| Condition | PATH_TYPE |
|-----------|-----------|
| `plan-baseline-path` key is absent in Session Config | `public` |
| `plan-baseline-path` key is present but value is empty | `public` |
| Key is present, value is non-empty, AND `test -d "$BASELINE_PATH"` succeeds | `private` |
| Key is present, value is non-empty, BUT path does not exist on disk | `public` |

Set `PATH_TYPE = private | public`. Do not report this detection to the user — it is silent.

> **Note on rules-fetch (Phase 3.5 of SKILL.md):** The optional rules-fetch step runs regardless of `PATH_TYPE`. Both private (with `plan-baseline-path` set) and public (without it) repos can opt into the fetch by setting `baseline-ref` in Session Config. The fetch is independent of how the initial scaffold was generated.

---

## Private Path

When `PATH_TYPE = private`, the baseline templates are used directly. No new logic is needed here — the existing tier-template flow (`fast-template.md`, `standard-template.md`, `deep-template.md`) already calls `$BASELINE_PATH` scripts for CLAUDE.md generation and archetype file sourcing. Continue with the calling template file's steps unchanged.

---

## Public Path

When `PATH_TYPE = public`, no `projects-baseline` is available. Use the plugin-bundled templates and platform-appropriate CLAUDE.md generation described below.

### Detect Platform

Read the current platform using the patterns from `skills/_shared/platform-tools.md`:

```bash
if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
  PLATFORM="claude"
elif [[ -n "${CODEX_PLUGIN_ROOT:-}" ]]; then
  PLATFORM="codex"
elif [[ -n "${CURSOR_RULES_DIR:-}" ]]; then
  PLATFORM="cursor"
else
  # Fallback: inspect running process name or default to claude
  PLATFORM="claude"
fi
```

---

### Public Path — Fast Tier

#### If `PLATFORM = claude`

Run `claude init` to generate `CLAUDE.md`, **but only if `CLAUDE.md` does not already exist**.
Skipping when the file is present prevents `claude init` from overwriting project-specific
customisations on bootstrap re-runs or Upgrade Flow passes (issue #108):

```bash
cd "$REPO_ROOT"
if [[ ! -f "$REPO_ROOT/CLAUDE.md" ]]; then
  claude init 2>/dev/null
fi
CLAUDE_INIT_STATUS=$?
```

If `claude init` exits 0 and produces a non-empty `CLAUDE.md`, it is the base. Proceed to inject the Harte Regeln block, then the Session Config block.

**Inject `## Harte Regeln` section** — append the canonical hard-rules content BEFORE the Session Config block, if the section is absent:

```bash
if ! grep -q "^## Harte Regeln" "$REPO_ROOT/CLAUDE.md" 2>/dev/null; then
  cat "$PLUGIN_ROOT/templates/_shared/harte-regeln.md" >> "$REPO_ROOT/CLAUDE.md"
fi
```

**Inject `## Session Config` section** — append after the last line of the generated CLAUDE.md if the section is absent:

```markdown
## Session Config

project-name: <REPO_NAME>
vcs: <detect: "gitlab" | "github" | "none" — see VCS detection below>
persistence: true
enforcement: warn   # strict | warn | off
waves: 5
agents-per-wave: 6
test-command: <detect per package-manager — e.g., "npm test">
typecheck-command: <detect — e.g., "npm run typecheck">
lint-command: <detect — e.g., "npm run lint">
recent-commits: 20
stale-branch-days: 7
```

Note: `plan-baseline-path` is intentionally omitted on the Public path. The 7 mandatory fields enforced by the Session Config validator (`scripts/lib/config-schema.mjs`, issue #182) are: `test-command`, `typecheck-command`, `lint-command`, `agents-per-wave`, `waves`, `persistence`, `enforcement`.

If `claude init` fails (non-zero exit or empty output), fall through to the Codex/Cursor path below.

#### If `PLATFORM = codex` or `PLATFORM = cursor`

Use the minimal template to synthesize `CLAUDE.md` (for Claude Code/Cursor) or `AGENTS.md` (for Codex):

1. Read `templates/_minimal/CLAUDE.md.tmpl` from the plugin root.
2. Substitute the following placeholders using repo context:

   | Placeholder | Source |
   |-------------|--------|
   | `{{PROJECT_TITLE}}` | `$REPO_NAME` (from `basename $(git rev-parse --show-toplevel)`) |
   | `{{PROJECT_DESCRIPTION}}` | One-sentence description derived from the user's first prompt — be concrete, not generic |
   | `{{STACK_LANGUAGE}}` | Detected from `ls` output: `*.py` / `pyproject.toml` → Python, `*.ts` / `*.js` / `package.json` → TypeScript, else "TBD" |
   | `{{STACK_PACKAGE_MANAGER}}` | `pnpm` for Node, `uv` for Python, else "TBD" |
   | `{{STACK_TEST_RUNNER}}` | `vitest` for Node, `pytest` for Python, else "TBD" |
   | `{{STACK_LINTER}}` | `eslint` for Node, `ruff` for Python, else "TBD" |
   | `{{CMD_DEV}}` | Infer from stack: `pnpm dev` / `uv run python src/main.py` / "TBD" |
   | `{{CMD_TEST}}` | `pnpm test` / `uv run pytest` / "TBD" |
   | `{{CMD_BUILD}}` | `pnpm build` / "N/A" / "TBD" |
   | `{{CMD_LINT}}` | `pnpm lint` / `uv run ruff check .` / "TBD" |
   | `{{CONVENTIONS}}` | Pull 3–5 lines from `git log -n 5 --oneline` if available, else "Follow existing project conventions." |
   | `{{HARD_RULES_TABLE}}` | Verbatim content of `templates/_shared/harte-regeln.md` (rules list, minus the provenance comment line) |
   | `{{VCS}}` | See VCS detection below |
   | `{{PROJECT_NAME}}` | `$REPO_NAME` |
   | `{{PLAN_BASELINE_PATH}}` | Omit this entire line (remove the `plan-baseline-path: ...` line from output) |
   | `{{TEST_COMMAND}}` | Same as `{{CMD_TEST}}` |
   | `{{TYPECHECK_COMMAND}}` | `pnpm build` for TS, `false` otherwise |
   | `{{LINT_COMMAND}}` | Same as `{{CMD_LINT}}` |

3. Write the substituted output to:
   - `CLAUDE.md` for Claude Code and Cursor
   - `AGENTS.md` for Codex CLI

**VCS detection:**

```bash
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if echo "$REMOTE_URL" | grep -q "gitlab"; then VCS="gitlab"
elif echo "$REMOTE_URL" | grep -q "github"; then VCS="github"
else VCS="none"; fi
```

Also substitute README and gitignore from `_minimal` templates:

- Copy `templates/_minimal/README.md.tmpl` → `README.md`, substituting:
  - `{{PROJECT_TITLE}}` → `$REPO_NAME`
  - `{{PROJECT_DESCRIPTION}}` → one-sentence description from user prompt
  - `{{USAGE_INSTRUCTIONS}}` → "TBD — add usage instructions here."
  - `{{DEVELOPMENT_INSTRUCTIONS}}` → "TBD — add development instructions here."
  - `{{LICENSE}}` → "MIT" (default) — user may change
- Copy `templates/_minimal/gitignore.tmpl` → `.gitignore` as-is (no placeholders to substitute)

---

### Public Path — Standard Tier

1. **Resolve archetype** from `CONFIRMED_ARCHETYPE` (set by `intensity-heuristic.md` or user selection in Phase 2 of SKILL.md):

   | Archetype | Template Directory |
   |-----------|-------------------|
   | `static-html` | `templates/static-html/` |
   | `node-minimal` | `templates/node-minimal/` |
   | `nextjs-minimal` | `templates/nextjs-minimal/` |
   | `python-uv` | `templates/python-uv/` |

   If `CONFIRMED_ARCHETYPE` is `null` or unset, default to `node-minimal`.

2. **Copy all files** from the template directory to `$REPO_ROOT`:

   Use `cp -rP` (no-dereference) so that symlinks inside the template directory are copied **as
   symlinks** rather than followed. This prevents a maliciously crafted or accidentally
   misconfigured template from writing files outside `$REPO_ROOT` via absolute-target symlinks
   (issue #108 — CWE-22 symlink traversal):

   ```bash
   PLUGIN_ROOT="$(dirname "$(dirname "$(dirname "$0")")")"  # resolve plugin root
   TMPL_DIR="$PLUGIN_ROOT/templates/$CONFIRMED_ARCHETYPE"
   # -P: copy symlinks as symlinks (no-dereference) — prevents symlink-traversal outside $REPO_ROOT
   cp -rP "$TMPL_DIR/." "$REPO_ROOT/"
   ```

   Preserve directory structure. Do not overwrite files that already exist (from Fast tier steps) unless explicitly noted.

3. **Substitute placeholders** in all copied files. For each file under `$REPO_ROOT` that was just copied, apply substitutions for every placeholder used across archetype templates:

   | Placeholder | Source / Default |
   |-------------|-----------------|
   | `{{PROJECT_NAME}}` | `$REPO_NAME` (slugified: lowercase, hyphens for spaces) |
   | `{{PROJECT_TITLE}}` | `$REPO_NAME` (title-cased: first letter of each word capitalised) |
   | `{{PROJECT_DESCRIPTION}}` | One-sentence description from user prompt |
   | `{{DESCRIPTION}}` | Same as `{{PROJECT_DESCRIPTION}}` (alias used in some templates) |
   | `{{VCS}}` | `gitlab` / `github` / `none` (from VCS detection above) |
   | `{{LICENSE}}` | `MIT` (default — user may change after bootstrap) |
   | `{{USAGE_INSTRUCTIONS}}` | `TBD — add usage instructions here.` |
   | `{{DEVELOPMENT_INSTRUCTIONS}}` | `TBD — add development instructions here.` |
   | `{{STACK_LANGUAGE}}` | `Python` for python-uv, `TypeScript` for node/nextjs, `HTML/CSS/JS` for static-html |
   | `{{STACK_PACKAGE_MANAGER}}` | `uv` for python-uv, `pnpm` for node/nextjs, `none` for static-html |
   | `{{STACK_TEST_RUNNER}}` | `pytest` for python-uv, `vitest` for node/nextjs, `none` for static-html |
   | `{{STACK_LINTER}}` | `ruff` for python-uv, `eslint` for node/nextjs, `none` for static-html |
   | `{{CMD_DEV}}` | `uv run python src/main.py` for python-uv, `pnpm dev` for nextjs, `pnpm build` for node-minimal, `open index.html` for static-html |
   | `{{CMD_TEST}}` | `uv run pytest` for python-uv, `pnpm test` for node/nextjs, `(none)` for static-html |
   | `{{CMD_BUILD}}` | `(N/A)` for python-uv, `pnpm build` for node/nextjs, `(none)` for static-html |
   | `{{CMD_LINT}}` | `uv run ruff check .` for python-uv, `pnpm lint` for node/nextjs, `(none)` for static-html |
   | `{{CONVENTIONS}}` | Pull 3–5 lines from `git log -n 5 --oneline` if available, else `Follow existing project conventions.` |
   | `{{TEST_COMMAND}}` | Same value as `{{CMD_TEST}}` |
   | `{{TYPECHECK_COMMAND}}` | `pnpm build` for TS archetypes (node/nextjs), `false` for python-uv and static-html |
   | `{{LINT_COMMAND}}` | Same value as `{{CMD_LINT}}` |
   | `{{PLAN_BASELINE_PATH}}` | Remove the line entirely (Public path — no baseline) |

   Derive `PROJECT_TITLE` from `REPO_NAME` by title-casing (replace hyphens/underscores with spaces, capitalise each word):

   ```bash
   PROJECT_SLUG=$(echo "$REPO_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
   PROJECT_TITLE=$(echo "$REPO_NAME" | tr '-_' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2)); print}')
   ```

   Set archetype-specific values before substitution:

   ```bash
   case "$CONFIRMED_ARCHETYPE" in
     python-uv)
       STACK_LANGUAGE="Python"; STACK_PKG="uv"; STACK_TEST="pytest"; STACK_LINT="ruff"
       CMD_DEV="uv run python src/main.py"; CMD_TEST="uv run pytest"
       CMD_BUILD="N/A"; CMD_LINT="uv run ruff check ."
       TYPECHECK_CMD="false"
       ;;
     nextjs-minimal)
       STACK_LANGUAGE="TypeScript"; STACK_PKG="pnpm"; STACK_TEST="vitest"; STACK_LINT="eslint"
       CMD_DEV="pnpm dev"; CMD_TEST="pnpm test"
       CMD_BUILD="pnpm build"; CMD_LINT="pnpm lint"
       TYPECHECK_CMD="pnpm build"
       ;;
     node-minimal)
       STACK_LANGUAGE="TypeScript"; STACK_PKG="pnpm"; STACK_TEST="vitest"; STACK_LINT="eslint"
       CMD_DEV="pnpm build"; CMD_TEST="pnpm test"
       CMD_BUILD="pnpm build"; CMD_LINT="pnpm lint"
       TYPECHECK_CMD="pnpm build"
       ;;
     static-html)
       STACK_LANGUAGE="HTML/CSS/JS"; STACK_PKG="none"; STACK_TEST="none"; STACK_LINT="none"
       CMD_DEV="open index.html"; CMD_TEST=""; CMD_BUILD=""; CMD_LINT=""
       TYPECHECK_CMD="false"
       ;;
   esac

   CONVENTIONS=$(git -C "$REPO_ROOT" log -n 5 --oneline 2>/dev/null | head -5 || echo "Follow existing project conventions.")
   ```

   Apply all substitutions:

   ```bash
   find "$REPO_ROOT" -type f \
     ! -path "*/.git/*" \
     ! -path "*/.orchestrator/*" \
     ! -name "*.lock" | while IFS= read -r file; do
     python3 - "$file" \
       "$PROJECT_SLUG" "$PROJECT_TITLE" "$PROJECT_DESCRIPTION" "$VCS" \
       "$STACK_LANGUAGE" "$STACK_PKG" "$STACK_TEST" "$STACK_LINT" \
       "$CMD_DEV" "$CMD_TEST" "$CMD_BUILD" "$CMD_LINT" \
       "$CONVENTIONS" "$TYPECHECK_CMD" <<'PYEOF'
import sys

(path, project_slug, project_title, description, vcs,
 stack_lang, stack_pkg, stack_test, stack_lint,
 cmd_dev, cmd_test, cmd_build, cmd_lint,
 conventions, typecheck_cmd) = sys.argv[1:16]

with open(path, 'r', encoding='utf-8', errors='replace') as fh:
    content = fh.read()

content = content.replace('{{PROJECT_NAME}}', project_slug)
content = content.replace('{{PROJECT_TITLE}}', project_title)
content = content.replace('{{PROJECT_DESCRIPTION}}', description)
content = content.replace('{{DESCRIPTION}}', description)
content = content.replace('{{VCS}}', vcs)
content = content.replace('{{LICENSE}}', 'MIT')
content = content.replace('{{USAGE_INSTRUCTIONS}}', 'TBD — add usage instructions here.')
content = content.replace('{{DEVELOPMENT_INSTRUCTIONS}}', 'TBD — add development instructions here.')
content = content.replace('{{STACK_LANGUAGE}}', stack_lang)
content = content.replace('{{STACK_PACKAGE_MANAGER}}', stack_pkg)
content = content.replace('{{STACK_TEST_RUNNER}}', stack_test)
content = content.replace('{{STACK_LINTER}}', stack_lint)
content = content.replace('{{CMD_DEV}}', cmd_dev)
content = content.replace('{{CMD_TEST}}', cmd_test)
content = content.replace('{{CMD_BUILD}}', cmd_build)
content = content.replace('{{CMD_LINT}}', cmd_lint)
content = content.replace('{{CONVENTIONS}}', conventions)
content = content.replace('{{TEST_COMMAND}}', cmd_test)
content = content.replace('{{TYPECHECK_COMMAND}}', typecheck_cmd)
content = content.replace('{{LINT_COMMAND}}', cmd_lint)
# Remove lines containing the plan-baseline-path placeholder
content = '\n'.join(
    line for line in content.splitlines()
    if '{{PLAN_BASELINE_PATH}}' not in line
)
# Preserve trailing newline if original had one
if not content.endswith('\n'):
    content += '\n'
with open(path, 'w', encoding='utf-8') as fh:
    fh.write(content)
PYEOF
   done
   ```

4. **python-uv only: rename source directory**

   If `CONFIRMED_ARCHETYPE = python-uv`, the template contains `src/__PROJECT_NAME__/`. Rename it to `src/<project_slug>/`:

   ```bash
   if [[ "$CONFIRMED_ARCHETYPE" == "python-uv" ]] && [[ -d "$REPO_ROOT/src/__PROJECT_NAME__" ]]; then
     mv "$REPO_ROOT/src/__PROJECT_NAME__" "$REPO_ROOT/src/$PROJECT_SLUG"
   fi
   ```

5. **Tier-specific extensions:** After copying and substituting, continue with `standard-template.md` Standard-specific steps (S1–S6 for the matched archetype). Those steps write additional tooling files (`.editorconfig`, expanded README, etc.) and tier-gate correctly — they already know the archetype from `CONFIRMED_ARCHETYPE`.

---

### Public Path — Deep Tier

Follow all Standard tier steps above (including archetype template copy + substitution + python-uv rename), then continue with `deep-template.md` Deep-specific steps (D1–D6 for VCS-conditional CI, CODEOWNERS, CHANGELOG, issue templates, MR/PR template, branch protection).

The deep-template steps already reference `VCS` and `CONFIRMED_ARCHETYPE` — they integrate correctly without modification.

---

## Source Value for bootstrap.lock

After the Public path scaffold completes, set `source` for the lock file:

| Condition | `source` value |
|-----------|---------------|
| `claude init` ran successfully (Claude Code Fast path) | `claude-init` |
| Plugin template copied (any other case) | `plugin-template` |

This value is passed back to SKILL.md Phase 4 for writing `.orchestrator/bootstrap.lock`.
