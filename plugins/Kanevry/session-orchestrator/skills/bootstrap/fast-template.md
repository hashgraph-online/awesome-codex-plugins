# Bootstrap Fast Template

> Scaffold instructions for the Fast tier.
> Called from `skills/bootstrap/SKILL.md` Phase 3 when `CONFIRMED_TIER = fast`.

## What Fast Tier Creates

| File | Purpose |
|------|---------|
| `CLAUDE.md` (or `AGENTS.md` on Codex) | Project instruction file with `## Session Config` |
| `.gitignore` | Platform-appropriate minimal ignore rules |
| `README.md` | One-line stub with project name and description |
| `.orchestrator/bootstrap.lock` | Gate marker — committed to git |

Intentionally absent: `package.json`, frameworks, tests, CI config. The feature that follows brings its own stack.

## Step 1: Ensure Git Repo is Initialized

```bash
cd "$REPO_ROOT"
if [[ ! -d ".git" ]]; then
  git init
  echo "Git repo initialized."
fi
```

## Step 2: Generate CLAUDE.md (or AGENTS.md)

**If `PATH_TYPE = public`:**

Defer entirely to `skills/bootstrap/public-fallback.md` — "Public Path — Fast Tier" section. That file is the single source of truth for Public-path CLAUDE.md generation (claude init path for Claude Code; `_minimal` template synthesis for Codex/Cursor; Session Config injection). Do not duplicate its logic here.

**`claude init` overwrite guard:** `public-fallback.md` Fast Tier runs `claude init` only when
`CLAUDE.md` does not already exist (`[[ ! -f "$REPO_ROOT/CLAUDE.md" ]]`). This prevents
overwriting project-specific customisations on re-runs (issue #108).

After `public-fallback.md` completes CLAUDE.md generation, continue to Step 2b to verify the Session Config block.

**If `PATH_TYPE = private`:**

Use the baseline scripts at `$BASELINE_PATH` as directed by the baseline's own documentation. Proceed with baseline-driven CLAUDE.md generation, then continue to Step 2b.

**Step 2b: Verify Session Config block.** After writing or updating CLAUDE.md, check for the sentinel string `## Session Config`:

```bash
if grep -q "^## Session Config" CLAUDE.md; then
  echo "Session Config block confirmed."
else
  # Sentinel absent — claude init did NOT populate the file (or wrote minimal content).
  # Fall back to plugin-template generation: append canonical Harte-Regeln block
  # BEFORE the Session Config block (pattern: the templates/_shared/... cp steps
  # in Step 3a below).
  if ! grep -q "^## Harte Regeln" CLAUDE.md 2>/dev/null; then
    cat "$PLUGIN_ROOT/templates/_shared/harte-regeln.md" >> CLAUDE.md
  fi
  # Fall back to plugin-template generation: append canonical Session Config block
  # (issue #182: 7 mandatory fields enforced by scripts/lib/config-schema.mjs).
  cat >> CLAUDE.md <<'EOF'

## Session Config

project-name: <PROJECT_NAME>
vcs: <VCS>
persistence: true
enforcement: warn   # strict | warn | off
waves: 5
agents-per-wave: 6
test-command: <detect per package-manager>
typecheck-command: <detect>
lint-command: <detect>
recent-commits: 20
stale-branch-days: 7
skill-evolution:
  autonomy: off            # off | advisory | autonomous-gated — opt-in self-evolution (default off)
EOF
fi
```

If `## Session Config` is present, confirm the 7 mandatory fields (per issue #182, enforced by `scripts/lib/config-schema.mjs`) plus `project-name` and `vcs` are present. Mandatory: `test-command`, `typecheck-command`, `lint-command`, `agents-per-wave`, `waves`, `persistence`, `enforcement`. If any are missing, append them.

**Config file selection by platform:**
- Claude Code → `CLAUDE.md`
- Codex CLI → `AGENTS.md`
- Cursor IDE → `CLAUDE.md`

**Step 2c: CLAUDE.md budget lint.** After Step 2b confirms/repairs the Session Config block, run the raw-file-property lint against the freshly written instruction file:

```bash
node "$PLUGIN_ROOT/scripts/lib/claude-md-budget-lint.mjs" --repo-root "$REPO_ROOT" --require-provenance --mode warn --json
```

`--mode warn` is deliberate at Anlage-time — the lint informs, the operator decides; it never blocks the scaffold. Interpret the JSON `violations[]`:
- `max-lines` — the instruction file is already over the lean-root ceiling (150 lines default). Recommend trimming to pointers per the lean-root convention (delegate detail to `README.md` / `.orchestrator/steering/` / `.claude/rules/*.md` — see this plugin's own `CLAUDE.md` for a worked example of the pointer pattern — note it predates the lint and currently exceeds the 150-line ceiling itself).
- `max-line-chars` — a single line exceeds the char ceiling (400 default); surface the line number for a quick manual wrap.
- `provenance-header` — line 1 lacks a `<!-- source: ...` attribution. On the `claude init` path (Public Fast Tier, Claude Code) this is a WARN only, never a hard failure — `claude init` output is not plugin-authored and has no reason to carry the plugin's provenance convention.

Report any violations to the user as part of the bootstrap summary; do not block or retry on them.

## Step 3: Generate .gitignore

Detect the platform from existing files in the repo root (best-effort, repo may be empty):

```bash
# Detection order — first match wins
if ls *.py pyproject.toml setup.py 2>/dev/null | head -1 | grep -q .; then STACK="python"
elif ls *.ts *.js package.json 2>/dev/null | head -1 | grep -q .; then STACK="node"
else STACK="generic"; fi
```

Write `.gitignore` with the appropriate content:

**Generic (no stack detected):**
```gitignore
# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log

# Environment
.env
.env.local
.env.*.local

# Session Orchestrator state (platform-specific, not committed)
.claude/
.codex/
.cursor/
```

**Node/TypeScript (append to generic):**
```gitignore
# Node
node_modules/
dist/
build/
.next/
coverage/
*.tsbuildinfo
```

**Python (append to generic):**
```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

Note: `.orchestrator/` is NOT gitignored — `bootstrap.lock` must be committed. Only the platform state dirs (`.claude/`, `.codex/`, `.cursor/`) are excluded.

## Step 3a: Install Parallel-Sessions Rule

Write the vendored rule from `$PLUGIN_ROOT/templates/_shared/rules/parallel-sessions.md` to `$REPO_ROOT/.claude/rules/parallel-sessions.md`.

Idempotency:
- Missing → create
- Exists and byte-identical → skip silently
- Exists and differs → overwrite (vendored is canonical)

Shell:
```bash
mkdir -p "$REPO_ROOT/.claude/rules"
cp "$PLUGIN_ROOT/templates/_shared/rules/parallel-sessions.md" "$REPO_ROOT/.claude/rules/parallel-sessions.md"
cp "$PLUGIN_ROOT/templates/_shared/loop.md" "$REPO_ROOT/.claude/loop.md"
```

Why: PSA-003 destructive-command safeguards require every consumer repo to carry the rule. See issue #155. The `loop.md` vendor gives bare `/loop` a repo-aware maintenance prompt (issue #633 Hebel 3).

## Step 4: Generate README.md

```markdown
# <REPO_NAME>

<One-sentence description — same as used in CLAUDE.md.>
```

Keep it minimal. One heading, one sentence. The feature that follows will expand it.

## Step 5: Create .orchestrator Directory and bootstrap.lock

```bash
mkdir -p "$REPO_ROOT/.orchestrator"
```

Write `.orchestrator/bootstrap.lock` **atomically** (mktemp + mv prevents a corrupt lock if the
process is interrupted mid-write):

```bash
_LOCK_TMP=$(mktemp "$REPO_ROOT/.orchestrator/bootstrap.lock.XXXXXX")
cat > "$_LOCK_TMP" << LOCK
# .orchestrator/bootstrap.lock
version: 1
tier: fast
archetype: null
timestamp: <current ISO 8601 UTC — e.g., 2026-04-16T09:30:00Z>
source: <claude-init | plugin-template>
plugin-version: <session-orchestrator plugin version — read from $PLUGIN_ROOT/package.json .version field>
bootstrapped-at: <current ISO 8601 UTC — same value as timestamp; distinct field for age-validation probe>
LOCK
mv "$_LOCK_TMP" "$REPO_ROOT/.orchestrator/bootstrap.lock"
```

Set `source`:
- `claude-init` if CLAUDE.md contained `## Session Config` before Step 2b's sentinel check (i.e., `claude init` populated it)
- `plugin-template` if the sentinel was absent and the fallback path wrote the block

## Step 6: Initial Git Commit

Stage all created files and commit:

```bash
cd "$REPO_ROOT"
BOOTSTRAP_FILES=(CLAUDE.md AGENTS.md .gitignore README.md .orchestrator/bootstrap.lock .claude/rules/parallel-sessions.md)
# Add only the files bootstrap created — no sweeping -u/-A to avoid catching pre-existing files
for _f in "${BOOTSTRAP_FILES[@]}"; do
  [[ -e "$_f" ]] && git add -- "$_f"
done
git commit -m "chore: bootstrap (fast)"
```

The commit message is fixed — do not vary it. It is the artifact that documents bootstrap provenance in `git log`.

## Step 7: Report Created Files

After the commit succeeds, output a concise summary:

```
Bootstrap (fast) complete. Created:
  CLAUDE.md (or AGENTS.md)              — Session Config with project-name, vcs
  .gitignore                            — <stack>-appropriate minimal rules
  README.md                             — one-line stub
  .claude/rules/parallel-sessions.md   — vendored PSA rule (issue #155)
  .orchestrator/bootstrap.lock          — version: 1, tier: fast
Committed: "chore: bootstrap (fast)"
```

Then return control to `SKILL.md` Phase 5.
