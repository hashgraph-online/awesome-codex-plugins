# DCG Troubleshooting

## Quick Diagnostics

```bash
dcg doctor    # First step for any issue
```

---

## Common Issues

### 1. Commands Not Being Blocked

**Symptom:** Destructive commands run without DCG intercepting.

**Diagnose:**
```bash
$ dcg doctor
Hook Registration:
  ✗ Claude Code hook NOT registered
```

**Fix:**
```bash
# Re-register hook
dcg install

# Verify
dcg doctor
```

**Other causes:**
- `DCG_BYPASS=1` is set → unset it
- Command uses absolute path `/usr/bin/git` → DCG normalizes these, check config
- Running in a context where hooks don't apply

### 2. False Positives (Safe Command Blocked)

**Symptom:** `rm -rf ./node_modules` blocked when it shouldn't be.

**Diagnose:**
```bash
$ dcg explain "rm -rf ./node_modules"
BLOCKED by core.filesystem:rm-rf-dangerous

Evaluation trace:
  ...
  Step 6. Normalization: rm -rf /home/user/project/node_modules
  Step 7. Pack evaluation: MATCH (non-temp path)
```

**Fix options:**

1. **Project allowlist** (recommended):
```toml
# .dcg.toml
[overrides]
allow_patterns = ["rm -rf ./node_modules"]
```

2. **One-time allow:**
```bash
# Human runs this
dcg allow-once ab12
```

3. **Permanent allowlist:**
```bash
dcg allowlist add core.filesystem:rm-rf-dangerous \
    --path "$PWD/node_modules" \
    -r "Package cleanup"
```

### 3. Hook Timeout / Slow Performance

**Symptom:** Commands hang for 200ms before running.

**Diagnose:**
```bash
$ time dcg test "git status"
real    0m0.250s  # Should be <5ms
```

**Possible causes:**
- Complex heredoc scanning taking too long
- Config file parsing issues
- Disk I/O problems

**Fix:**
```bash
# Check heredoc settings
grep -i heredoc ~/.config/dcg/config.toml

# Reduce heredoc limits if needed
# In config.toml:
[heredoc]
max_size_bytes = 524288  # 512KB instead of 1MB
max_lines = 5000         # Reduce from 10000
```

**Note:** DCG is fail-open. If it exceeds 200ms deadline, command runs with warning.

### 4. Allow-Once Code Not Working

**Symptom:** `dcg allow-once ab12` says "Invalid code" or exception doesn't apply.

**Causes:**
1. **Code expired** (24h limit)
2. **Different directory** — codes are bound to exact directory
3. **Command changed** — even whitespace matters

**Diagnose:**
```bash
$ dcg allow-once ab12
Error: Exception not found or expired

Details:
  - Code 'ab12' was valid for: git reset --hard HEAD
  - In directory: /home/user/other-project
  - Current directory: /home/user/this-project
```

**Fix:** Re-run the blocked command to get a fresh code for current context.

### 5. Pack Not Loading

**Symptom:** Database commands not blocked despite enabling pack.

**Diagnose:**
```bash
$ dcg packs
Currently enabled: core.git, core.filesystem
# database.postgresql not showing

$ echo $DCG_PACKS
# Empty or missing postgresql
```

**Fix:**
```bash
# Environment variable
export DCG_PACKS="database.postgresql"

# Or in .dcg.toml
[packs]
enabled = ["database.postgresql"]
```

**Verify:**
```bash
$ dcg explain "DROP DATABASE test"
BLOCKED by database.postgresql:drop-database
```

### 6. Heredoc/Inline Script Not Scanned

**Symptom:** Destructive command in heredoc runs without block.

```bash
# This should be caught
bash -c "rm -rf /important"
```

**Diagnose:**
```bash
$ dcg explain 'bash -c "rm -rf /important"'
ALLOWED

Evaluation trace:
  Step 3. Heredoc detection: triggered (bash -c)
  Step 3a. Tier 1: Pattern match ✓
  Step 3b. Tier 2: Content extraction ✓
  Step 3c. Tier 3: AST parsing... SKIPPED (budget exceeded)
```

**Cause:** Heredoc budget exceeded, fell back to allow.

**Fix:**
```toml
# .dcg.toml - increase heredoc budget
[heredoc]
tier2_budget_ms = 500   # Default 200
tier3_budget_ms = 10000 # Default 5000
```

### 7. Config Not Being Applied

**Symptom:** `.dcg.toml` settings ignored.

**Diagnose:**
```bash
$ dcg doctor
Configuration:
  ✓ User config: ~/.config/dcg/config.toml
  ✗ Project config: .dcg.toml (parse error line 15)
```

**Common config errors:**
```toml
# BAD: Wrong TOML syntax
[packs]
enabled = "postgresql"  # Should be array

# GOOD:
[packs]
enabled = ["database.postgresql"]

# BAD: Invalid pack name
enabled = ["postgres"]  # Should be "database.postgresql"

# GOOD:
enabled = ["database.postgresql"]
```

**Verify config:**
```bash
# TOML syntax check
cat .dcg.toml | python3 -c "import sys,tomli;tomli.loads(sys.stdin.read())"
```

### 8. Agent Bypassing DCG

**Symptom:** Agent uses workarounds like:
- Breaking command across lines
- Using aliases
- Calling absolute paths

**DCG handles these:** Command normalization strips sudo, env, aliases, and absolute paths.

**If still bypassed:**
1. Check DCG version is current: `dcg update`
2. Report bypass pattern to DCG maintainers
3. Add custom block pattern:
```toml
[overrides]
block_patterns = ["the-bypass-pattern"]
```

---

## Hook Protocol Issues

### Claude Code Hook Not Receiving Input

**Check hook is registered:**
```bash
cat ~/.config/claude-code/settings.json | jq '.hooks'
```

**Expected:**
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "dcg hook"}]
  }]
}
```

### Hook Returns Wrong Format

**DCG hook protocol:**

**Input (stdin):**
```json
{"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}}
```

**Deny output (stdout):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: ...",
    "allowOnceCode": "ab12"
  }
}
```

**Allow:** Exit 0 with no output.

---

## Getting Help

1. **Check version:** `dcg --version`
2. **Run diagnostics:** `dcg doctor`
3. **Explain specific command:** `dcg explain "the-command"`
4. **Check logs:** `~/.config/dcg/dcg.log` (if verbose enabled)

**Report issues:** Include output of `dcg doctor` and `dcg explain "command"`.
