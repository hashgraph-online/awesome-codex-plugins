# Quickstart Troubleshooting

## Optional Hooks Aren't Running

**Symptom:** You opted into AgentOps hooks, but they do not fire on session start or tool use.

**Checks:**
```bash
# Verify hooks are installed
ao hooks test

# Check repo hook source exists and is valid
cat hooks/codex-hooks.json | jq . 2>/dev/null

# Check installed native hooks
cat ~/.codex/hooks.json | jq '.hooks' 2>/dev/null

# Verify the plugin is enabled
rg '^\[plugins\."agentops@agentops-marketplace"\]$|^enabled = true$' ~/.codex/config.toml
```

**Fixes:**
- Reinstall the native Codex plugin with hooks: `curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash -s -- --with-hooks`
- Check that `hooks/codex-hooks.json` is not malformed JSON
- Restart Codex after hook changes

## Skills Not Showing Up

**Symptom:** `$quickstart`, `$vibe`, or other skills don't trigger.

**Checks:**
```bash
# Check SKILL.md exists with valid frontmatter
head -5 ~/.codex/plugins/cache/agentops-marketplace/agentops/local/skills-codex/quickstart/SKILL.md

# List installed skills
find ~/.codex/plugins/cache/agentops-marketplace/agentops/local/skills-codex -maxdepth 1 -mindepth 1 -type d | sort
```

**Fixes:**
- Reinstall: `curl -fsSL https://raw.githubusercontent.com/boshu2/agentops/main/scripts/install-codex.sh | bash`
- If duplicates persist, archive stale raw mirrors:
  ```bash
  mv ~/.agents/skills ~/.agents/skills.backup.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
  mv ~/.codex/skills ~/.codex/skills.backup.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
  ```

## CLI Not Found (ao, bd, gt)

**Symptom:** `command not found: ao` (or `bd`, `gt`).

**Installation:**
```bash
# ao (AgentOps CLI) — requires Homebrew tap first
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops
brew install agentops
ao init              # Create .agents/ dirs + .gitignore
ao init --hooks      # Optional: install runtime hooks

# bd (Beads issue tracking)
brew install boshu2/agentops/beads
bd init --prefix <your-prefix>

# gt (Gas Town workspace manager)
brew install boshu2/agentops/gastown
```

**Verify PATH:**
```bash
which ao bd gt 2>/dev/null
echo $PATH | tr ':' '\n' | grep -E 'homebrew|bin'
```

## Permission Denied

**Symptom:** Cannot create `.agents/` directory or write files.

**Checks:**
```bash
# Check directory permissions
ls -la . | head -3

# Check if .agents exists and is writable
ls -la .agents/ 2>/dev/null

# Try creating
mkdir -p .agents && echo "OK" || echo "PERMISSION DENIED"
```

**Fixes:**
- Check directory ownership: `ls -la .`
- Fix permissions: `chmod u+w .` (if you own the directory)
- If in a shared/mounted directory, work in a local clone instead

## Non-Git Directory

**Symptom:** Quickstart warns about missing git repo.

**Options:**

1. **Initialize git** (recommended):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
   Then re-run `$quickstart` for the full experience.

2. **Continue in manual mode:**
   Quickstart will skip git-dependent features (recent changes, vibe on diffs) and use file-browsing equivalents instead. You can still use `$research`, `$plan`, and other non-git skills.

## Language Detection Failed

**Symptom:** Quickstart says "I couldn't auto-detect a language."

**Why:** Quickstart couldn't find any recognized project files in its **shallow scan** (it avoids walking entire repos). In monorepos, the primary module might be deeper than the scan depth.

**Fix:**
- Run quickstart from your repo root (recommended), or `cd` into the primary module directory (e.g., `cli/`, `src/`).
- If detection still fails, tell quickstart your primary language when prompted and continue manually.

## Session Knowledge Not Persisting

**Symptom:** Each session starts fresh, no prior knowledge loaded.

**Checks:**
```bash
# Is ao CLI available?
which ao

# Is .agents/ directory present?
ls .agents/

# Check flywheel health
ao metrics flywheel status
```

**Fixes:**
- Install ao: `brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops && brew install agentops && ao init`
- Hookless default: run `$validation` or `ao flywheel close-loop` explicitly at closeout.
- Optional hooks: `ao init --hooks` or `install-codex.sh --with-hooks`, then verify `hooks/session-start.sh`.
