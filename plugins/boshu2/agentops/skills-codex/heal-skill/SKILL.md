---
name: heal-skill
description: "Run heal skill."
---
# $heal-skill — Automated Skill Maintenance

> **Purpose:** Detect and auto-fix common skill hygiene issues across the skills/ directory.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

---

## Quick Start

```bash
$heal-skill                    # Check all skills (report only)
$heal-skill --fix              # Auto-repair all fixable issues
$heal-skill --strict           # Check all skills, exit 1 on findings (CI mode)
$heal-skill skills/council     # Check a specific skill
$heal-skill --fix skills/vibe  # Fix a specific skill
```

---

## What It Detects

Ten checks, run in order:

| Code | Issue | Auto-fixable? |
|------|-------|---------------|
| `MISSING_NAME` | No `name:` field in SKILL.md frontmatter | Yes -- adds name from directory |
| `MISSING_DESC` | No `description:` field in SKILL.md frontmatter | Yes -- adds placeholder |
| `NAME_MISMATCH` | Frontmatter `name` differs from directory name | Yes -- updates to match directory |
| `UNLINKED_REF` | File in references/ not linked in SKILL.md | Yes -- converts bare backtick refs to markdown links |
| `EMPTY_DIR` | Skill directory exists but has no SKILL.md | Yes -- removes empty directory |
| `DEAD_REF` | SKILL.md references a non-existent references/ file | No -- warn only |
| `SCRIPT_REF_MISSING` | SKILL.md references a scripts/ file that does not exist | No -- warn only |
| `INVALID_AO_CMD` | SKILL.md references an `ao` subcommand that does not exist (only runs if `ao` is on PATH) | No -- warn only |
| `DEAD_XREF` | SKILL.md references a `/skill-name` that has no matching skill directory | No -- warn only |
| `CATALOG_MISSING` | A user-invocable skill is missing from the using-agentops catalog | No -- warn only |

---

## Execution Steps

### Step 1: Run the heal script

```bash
# Check mode (default) -- report only, no changes
bash skills/heal-skill/scripts/heal.sh --check

# Fix mode -- auto-repair what it can
bash skills/heal-skill/scripts/heal.sh --fix

# Target a specific skill
bash skills/heal-skill/scripts/heal.sh --check skills/council
bash skills/heal-skill/scripts/heal.sh --fix skills/council
```

### Step 1A: Audit Codex Parity Drift When The Codex Bundle Looks Wrong

When the problem is not source-skill hygiene but `skills-codex/` drift, run the Codex parity audit first:

```bash
bash scripts/audit-codex-parity.sh
bash scripts/audit-codex-parity.sh --skill swarm
```


**Repair rule:** keep canonical shared behavior in `skills/<name>/SKILL.md`. Update `skills-codex/<name>/SKILL.md` when the shipped Codex artifact is wrong, and keep durable Codex-only tailoring in `skills-codex-overrides/<name>/SKILL.md`.

After repair:

```bash
bash scripts/audit-codex-parity.sh
bash scripts/validate-codex-override-coverage.sh
bash scripts/validate-codex-generated-artifacts.sh --scope worktree
```

### Step 2: Interpret results

- **Exit 0:** All clean, no findings. Also exit 0 for `--check` mode with findings (report-only).
- **Exit 1:** Findings reported with `--strict` or `--fix` flag. In `--fix` mode, fixable issues were repaired; re-run `--check` to confirm.

### Step 3: Report to user

Show the output. If `--fix` was used, summarize what changed. If `DEAD_REF` findings remain, advise the user to remove or update the broken references manually.

---

## Output Format

One line per finding:

```
[MISSING_NAME] skills/foo: No name field in frontmatter
[MISSING_DESC] skills/foo: No description field in frontmatter
[NAME_MISMATCH] skills/foo: Frontmatter name 'bar' != directory 'foo'
[UNLINKED_REF] skills/foo: refs/bar.md not linked in SKILL.md
[EMPTY_DIR] skills/foo: Directory exists but no SKILL.md
[DEAD_REF] skills/foo: SKILL.md links to non-existent refs/bar.md
[SCRIPT_REF_MISSING] skills/foo: references scripts/bar.sh but file not found
[INVALID_AO_CMD] skills/foo: references 'ao badcmd' which is not a valid subcommand
[DEAD_XREF] skills/foo: references /nonexistent but skill directory not found
[CATALOG_MISSING] using-agentops: bar is user-invocable but missing from catalog
```

---

## Notes

- The script is **idempotent** -- running `--fix` twice produces the same result.
- `DEAD_REF`, `SCRIPT_REF_MISSING`, `INVALID_AO_CMD`, `DEAD_XREF`, and `CATALOG_MISSING` are warn-only because the correct resolution requires human judgment.
- `INVALID_AO_CMD` only runs if the `ao` CLI is available on PATH. Skipped silently otherwise.
- `CATALOG_MISSING` is a global check (not per-skill) and only runs when `using-agentops/SKILL.md` exists.
- When run without a path argument, scans all directories under `skills/`.
- Use `--strict` for CI gates: exits 1 on any finding. Without `--strict`, check mode exits 0 even with findings.
- For Codex parity drift, use the audit script plus override-layer repair workflow in [references/codex-parity.md](references/codex-parity.md). The shell fixer is intentionally not allowed to rewrite generated Codex bodies directly.

## Examples

### Running a health check across all skills

**User says:** `$heal-skill`

**What happens:**
1. The heal script scans every directory under `skills/`, checking each for the ten issue types (missing name, missing description, name mismatch, unlinked references, empty directories, dead references, script reference integrity, CLI command validation, cross-reference validation, catalog completeness).
2. Findings are printed one per line with issue codes (e.g., `[NAME_MISMATCH] skills/foo: Frontmatter name 'bar' != directory 'foo'`).
3. The script exits with code 0 in check mode (even with findings), or code 1 with `--strict` or `--fix` flags.

**Result:** A diagnostic report showing all skill hygiene issues across the repository, with no files modified.

### Auto-fixing a specific skill

**User says:** `$heal-skill --fix skills/vibe`

**What happens:**
1. The heal script inspects only `skills/vibe/`, running all per-skill checks against that skill.
2. For each fixable issue found (e.g., `MISSING_NAME`, `UNLINKED_REF`), the script applies the repair automatically -- adding the name from the directory, converting bare backtick references to markdown links, etc.
3. Any `DEAD_REF` findings are reported as warnings since they require human judgment to resolve.

**Result:** The `skills/vibe/SKILL.md` is repaired in place, with a summary of changes applied and any remaining warnings.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `DEAD_REF` findings persist after `--fix` | Dead references are warn-only because the correct fix (delete, create, or update) requires human judgment | Manually inspect each dead reference and either create the missing file, remove the link from SKILL.md, or update the path |
| Script reports `EMPTY_DIR` for a skill in progress | The skill directory was created but SKILL.md has not been written yet | Either add a SKILL.md to the directory or remove the empty directory. Running `--fix` will remove it automatically |
| `NAME_MISMATCH` fix changed the wrong name | The script always updates the frontmatter `name` to match the directory name, not the other way around | If the directory name is wrong, rename the directory first, then re-run `--fix` |
| Script exits 0 but a skill still has issues | The issue type is not one of the ten checks the heal script detects | The heal script covers structural hygiene only. Content quality issues require manual review or `$council` validation |
| Running `--fix` twice produces different output | This should not happen -- the script is idempotent | File a bug. Check if another process modified the skill files between runs |
| `skills-codex/` keeps regressing after sync | Mechanical conversion is preserving the wrong semantics | Run `bash scripts/audit-codex-parity.sh`, then move the durable Codex body rewrite into `skills-codex-overrides/<name>/SKILL.md` instead of patching generated output |

## See Also

- skill-auditor — extends heal's structural checks (Pass 1) with 8 content-discipline checks (Pass 2: rationale, output spec, quality rubric, etc.)
- skill-builder — scaffolds new skills against the unified template; runs heal-skill + skill-auditor as self-checks

## References

- [references/skill-stocktake.md](references/skill-stocktake.md)
- [references/codex-parity.md](references/codex-parity.md)

## Local Resources

### references/

- [references/codex-parity.md](references/codex-parity.md)

### scripts/

- `scripts/heal.sh`
- `scripts/validate.sh`

