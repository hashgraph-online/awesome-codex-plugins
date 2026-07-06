# DCG Commands Reference

## Command Overview

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `dcg doctor` | Verify installation | Hook not working |
| `dcg explain "cmd"` | Understand why blocked | After any block |
| `dcg test "cmd"` | Dry-run evaluation | Before risky commands |
| `dcg allow-once CODE` | Temporary exception | Human approves |
| `dcg allowlist add` | Permanent exception | Recurring safe ops |
| `dcg allowlist list` | Show exceptions | Audit allowlist |
| `dcg packs` | List available packs | See what's enabled |
| `dcg scan` | Scan repository | Pre-commit checks |
| `dcg update` | Self-update | Get latest rules |

---

## dcg doctor

Verify DCG installation and hook registration.

```bash
$ dcg doctor
DCG Doctor
══════════════════════════════════════════════════

Binary:
  ✓ dcg version 0.8.2 (built 2025-01-15)
  ✓ Located at /usr/local/bin/dcg

Hook Registration:
  ✓ Claude Code hook registered in ~/.config/claude-code/settings.json
  ✓ Hook path: /usr/local/bin/dcg hook

Configuration:
  ✓ User config: ~/.config/dcg/config.toml
  ✓ Project config: .dcg.toml (not found - using defaults)

Packs:
  ✓ Core packs loaded: core.git, core.filesystem
  ✓ Optional packs: 0 enabled

Status: All checks passed
```

**Use when:** Hook doesn't seem to be working, commands aren't being blocked.

---

## dcg explain "command"

Show exactly why a command is blocked/allowed with full evaluation trace.

```bash
$ dcg explain "git reset --hard HEAD"
BLOCKED by core.git:reset-hard

Evaluation trace (7-step pipeline):
  Step 1. Config allow overrides ... no match
  Step 2. Config block overrides ... no match
  Step 3. Heredoc detection ....... not applicable
  Step 4. Quick reject ............ triggered (pattern: "reset")
  Step 5. Context sanitization .... no changes
  Step 6. Normalization ........... "git reset --hard HEAD"
  Step 7. Pack evaluation:
          - Safe patterns ........ no match
          - Destructive patterns . MATCH "reset --hard"

Rule details:
  Pack: core.git
  Rule ID: reset-hard
  Severity: high
  Reason: Discards all uncommitted changes permanently

Suggestion: Use `git stash` to preserve changes before resetting
```

```bash
$ dcg explain "git checkout -b feature"
ALLOWED

Evaluation trace (7-step pipeline):
  Step 4. Quick reject ............ no trigger
  Step 7. Pack evaluation:
          - Safe patterns ........ MATCH "checkout -b" (creating branch)

No block - command is safe.
```

**Use when:** You want to understand WHY something was blocked before deciding next steps.

---

## dcg test "command"

Dry-run evaluation without executing.

```bash
$ dcg test "rm -rf /home/user/project"
WOULD BE BLOCKED

Rule: core.filesystem:rm-rf-dangerous
Reason: Recursive deletion of non-temporary path

$ dcg test "rm -rf ./build"
WOULD BE ALLOWED

Context: Relative path in current directory considered safe
```

**Use when:** Checking before running something you're unsure about.

---

## dcg allow-once CODE

Create temporary exception for a blocked command.

```bash
$ dcg allow-once ab12
Exception created:
  Command: git reset --hard HEAD
  Directory: /home/user/project
  Expires: 2025-01-16T10:30:00Z (24 hours)

Run the command again within 24 hours to execute.
```

**Characteristics:**
- Code is 4 hex characters (cryptographically bound to command + directory)
- Expires after 24 hours
- Single use per command instance
- Stored in `~/.config/dcg/pending_exceptions.jsonl`
- Logged to `~/.config/dcg/audit.log`

**Critical:** The HUMAN runs this command, not the agent. Agent should never execute `dcg allow-once`.

---

## dcg allowlist

Manage permanent exceptions.

```bash
# Add allowlist entry
$ dcg allowlist add core.git:reset-hard -r "CI cleanup requires this"

# Add with scope
$ dcg allowlist add core.filesystem:rm-rf-dangerous \
    --path "/home/user/project/build" \
    -r "Build directory cleanup"

# List entries
$ dcg allowlist list
┌──────────────────────────────────┬────────────────────────────┬─────────────────────────┐
│ Rule ID                          │ Scope                      │ Reason                  │
├──────────────────────────────────┼────────────────────────────┼─────────────────────────┤
│ core.git:reset-hard              │ global                     │ CI cleanup requires     │
│ core.filesystem:rm-rf-dangerous  │ /home/user/project/build   │ Build directory cleanup │
└──────────────────────────────────┴────────────────────────────┴─────────────────────────┘

# Remove entry
$ dcg allowlist remove core.git:reset-hard
```

**Layered allowlists (highest to lowest priority):**
1. `.dcg/allowlist.toml` — Project-level
2. `~/.config/dcg/allowlist.toml` — User-level
3. `/etc/dcg/allowlist.toml` — System-level

---

## dcg packs

List available and enabled rule packs.

```bash
$ dcg packs
Core (always enabled):
  ✓ core.git         - Destructive git commands
  ✓ core.filesystem  - Dangerous file operations

Optional (49 available):
  Database:     postgresql, mysql, mongodb, redis, sqlite
  Containers:   docker, compose, podman
  Kubernetes:   kubectl, helm, kustomize
  Cloud:        aws, azure, gcp
  Storage:      s3, gcs, azure_blob, minio
  ...

Currently enabled: core.git, core.filesystem

$ dcg packs --verbose
# Shows all patterns in each pack
```

---

## dcg scan

Scan repository for destructive commands in scripts and config files.

```bash
# Scan entire repo
$ dcg scan
Scanning 142 files...

FINDINGS:
┌─────────────────────────────────┬──────────┬─────────────────────────────────┐
│ File                            │ Line     │ Issue                           │
├─────────────────────────────────┼──────────┼─────────────────────────────────┤
│ scripts/deploy.sh               │ 45       │ git reset --hard (core.git)     │
│ .github/workflows/ci.yml        │ 23       │ rm -rf / (core.filesystem)      │
│ Makefile                        │ 67       │ DROP DATABASE (database.*)      │
└─────────────────────────────────┴──────────┴─────────────────────────────────┘

Found 3 issues in 3 files.

# Scan only staged files
$ dcg scan --staged

# Scan specific path
$ dcg scan --path scripts/

# Scan with SARIF output (for CI)
$ dcg scan --format sarif > results.sarif
```

**Supported file types:**
| Type | Contexts Scanned |
|------|-----------------|
| Shell scripts (`.sh`) | All executable lines |
| Dockerfile | `RUN` instructions |
| GitHub Actions | `run:` fields |
| GitLab CI | `script:`, `before_script:`, `after_script:` |
| Makefile | Recipe lines |
| Docker Compose | `command:`, `entrypoint:` |

### Install Pre-commit Hook

```bash
$ dcg scan install-pre-commit
Installed pre-commit hook at .git/hooks/pre-commit
Staged files will be scanned before each commit.
```

---

## dcg update

Self-update to latest version.

```bash
$ dcg update
Current version: 0.8.1
Latest version: 0.8.2

Downloading...
Verifying signature...
Installing...

Updated to 0.8.2
```

---

## Output Formats

All commands support `--format`:

```bash
dcg explain "cmd" --format json    # Machine-readable
dcg explain "cmd" --format text    # Human-readable (default)
dcg scan --format sarif            # SARIF for CI integration
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DCG_PACKS` | Enable packs | `"database.postgresql,kubernetes"` |
| `DCG_DISABLE` | Disable packs | `"kubernetes.helm"` |
| `DCG_BYPASS` | Skip all checks | `1` (human-only escape hatch) |
| `DCG_VERBOSE` | Verbosity (0-3) | `2` |
| `DCG_FORMAT` | Default output | `json` |
| `DCG_CONFIG` | Config file path | `/path/to/config.toml` |
