---
name: goals
description: "Maintain measurable project goals."
---
# $goals — Fitness Goal Maintenance

> Maintain GOALS.yaml and GOALS.md fitness specifications. Use `ao goals` CLI for all operations.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Quick Start

```bash
$goals                    # Measure fitness (default)
$goals init               # Bootstrap GOALS.md interactively
$goals steer              # Manage directives
$goals add                # Add a new goal
$goals drift              # Compare snapshots for regressions
$goals scenarios          # Link directives to behavioral scenarios (the `ao eval scenario` family)
$goals history            # Show measurement history
$goals export             # Export snapshot as JSON for CI
$goals meta               # Run meta-goals only
$goals validate           # Validate structure
$goals prune              # Remove stale gates
$goals migrate            # Migrate YAML to Markdown
```

## Format Support

| Format | File | Version | Features |
|--------|------|---------|----------|
| YAML | GOALS.yaml | 1-3 | Goals with checks, weights, pillars |
| Markdown | GOALS.md | 4 | Goals + mission + north/anti stars + directives |

When both files exist, GOALS.md takes precedence.

## Mode Selection

Parse the user's input:

| Input | Mode | CLI Command |
|-------|------|-------------|
| `$goals`, `$goals measure`, "goal status" | **measure** | `ao goals measure` |
| `$goals init`, "bootstrap goals" | **init** | `ao goals init` |
| `$goals steer`, "manage directives" | **steer** | `ao goals steer` |
| `$goals add`, "add goal" | **add** | `ao goals add` |
| `$goals drift`, "goal drift" | **drift** | `ao goals drift` |
| `$goals history`, "goal history" | **history** | `ao goals history` |
| `$goals export`, "export goals" | **export** | `ao goals export` |
| `$goals meta`, "meta goals" | **meta** | `ao goals meta` |
| `$goals validate`, "validate goals" | **validate** | `ao goals validate` |
| `$goals prune`, "prune goals", "clean goals" | **prune** | `ao goals prune` |
| `$goals migrate`, "migrate goals" | **migrate** | `ao goals migrate` |

## Measure Mode (default) — Observe

### Step 1: Run Measurement

```bash
ao goals measure --json
```

Parse the JSON output. Extract per-goal pass/fail, overall fitness score.

### Step 2: Directive Gap Assessment (GOALS.md only)

If the goals file is GOALS.md format:

```bash
ao goals measure --directives
```

For each directive, assess whether recent work has addressed it:
- Check git log for commits mentioning the directive title
- Check beads/issues related to the directive topic
- Rate each directive: addressed / partially-addressed / gap

### Step 3: Report

Present fitness dashboard:
```
Fitness: 5/7 passing (71%)

Gates:
  [PASS] build-passing (weight 8)
  [FAIL] test-passing (weight 7)
    └─ 3 test failures in pool_test.go

Directives:
  1. Expand Test Coverage — gap (no recent test additions)
  2. Reduce Complexity — partially-addressed (2 refactors this week)
```

## Init Mode

```bash
ao goals init
```

Or with defaults:
```bash
ao goals init --non-interactive
```

Creates a new GOALS.md with mission, north/anti stars, first directive, and auto-detected gates. Error if file already exists.

### Post-Init Enrichment

After `ao goals init` creates the scaffold, enrich it with product-aware content that the CLI cannot auto-detect:

#### Enrich North Stars with Outcomes

Review the generated north stars. If they are all feature-focused (e.g., "skills work across 4 runtimes"), nudge toward outcome-focused stars:

- **Feature-focused (weaker):** "Skills work across 4 runtimes"
- **Outcome-focused (stronger):** "A new user goes from install to first validated workflow in under 5 minutes"

Ask the user: "Your north stars describe features. What user outcome would tell you the product is actually working?" Add at least one outcome-focused star.

#### Enrich Anti-Stars from Failure Modes

Scan for proven failure patterns:
1. Check `.agents/retros/` — extract failure themes from retrospectives
2. Check `.agents/council/` or council index — look for FAIL verdicts and their root causes
3. Check `.agents/learnings/` — look for learnings tagged as anti-patterns

Convert the top 3 most common failure modes into anti-stars. Examples from real data:
- "Product promises with no automated verification" (from council FAILs where claims had no gates)
- "Goals that measure code metrics instead of user outcomes" (from retros where passing gates didn't improve product)
- "Capture without compounding" (from flywheel analysis where knowledge was stored but never retrieved)

If no `.agents/` data exists, use the defaults from `ao goals init`.

#### Add Product Directives

The CLI generates engineering-flavored directives (test coverage, complexity, lint). After init, also suggest product/growth directives by asking:

1. "What's your biggest product gap right now?" → directive with `steer: decrease`
2. "What user behavior do you want to increase?" → directive with `steer: increase`
3. "What metric would tell you the product is working?" → directive with measurable target

Product directives sit alongside engineering ones in the same `## Directives` section. See `references/generation-heuristics.md` for product directive patterns.

#### Add Product Gates

Check what product infrastructure exists and suggest appropriate gates:

| Infrastructure | Suggested Gate |
|---------------|----------------|
| `.agents/learnings/` exists | `flywheel-compounding` — knowledge above escape velocity |
| `skills/status/` exists | `quickstart-under-5min` — onboarding time gate |
| `docs/comparisons/` exists | `competitive-freshness` — comparison docs updated within 45 days |
| `PRODUCT.md` exists | `product-gaps-tracked` — Known Gaps section has entries |
| `ao flywheel status` works | `flywheel-promotion-rate` — learnings promoted above threshold |

Only suggest gates for infrastructure that actually exists. Don't create gates for aspirational features.

## Steer Mode — Orient/Decide

### Step 1: Show Current State

Run measure mode first to show current fitness and directive status.

### Step 2: Propose Adjustments

Based on measurement:
- If a directive is fully addressed → suggest removing or replacing
- If fitness is declining → suggest new gates
- If idle rate is high → suggest new directives

**Product-aware steering:** Also check for product dimension gaps:
- If all directives are engineering-flavored (test, lint, build, refactor) → suggest at least one product/growth directive
- If no directive cites a specific metric → flag: "Vague directives are a smell. Can any of these reference a specific number?"
- If `.agents/retros/` has new failure patterns not represented in anti-stars → suggest adding them
- If PRODUCT.md has Known Gaps not covered by any directive → suggest a directive to close the gap

### Step 3: Execute Changes

Use CLI commands:
```bash
ao goals steer add "Title" --description="..." --steer=increase
ao goals steer remove 3
ao goals steer prioritize 2 1
```

## Add Mode

Add a single goal to the goals file. Format-aware — writes to GOALS.yaml or GOALS.md depending on which format is detected.

```bash
ao goals add <id> <check-command> --weight=5 --description="..." --type=health
```

| Flag | Default | Description |
|------|---------|-------------|
| `--weight` | 5 | Goal weight (1-10) |
| `--description` | — | Human-readable description |
| `--type` | — | Goal type (health, architecture, quality, meta) |

Example:
```bash
ao goals add go-coverage-floor "bash scripts/check-coverage.sh" --weight=3 --description="Go test coverage above 60%"
```

## Drift Mode

Compare the latest measurement snapshot against a previous one to detect regressions.

```bash
ao goals drift                    # Compare latest vs previous snapshot
```

Reports which goals improved, regressed, or stayed unchanged.

## History Mode

Show measurement history over time for all goals or a specific goal.

```bash
ao goals history                        # All goals, all time
ao goals history --goal go-coverage     # Single goal
ao goals history --since 2026-02-01     # Since a specific date
ao goals history --goal go-coverage --since 2026-02-01  # Combined
```

Useful for spotting trends and identifying oscillating goals.

## Export Mode

Export the latest fitness snapshot as JSON for CI consumption or external tooling.

```bash
ao goals export
```

Outputs the snapshot to stdout in the fitness snapshot schema (see `references/goals-schema.md`).

## Meta Mode

Run only meta-goals (goals that validate the validation system itself). Useful for checking allowlist hygiene, skip-list freshness, and other self-referential checks.

```bash
ao goals meta --json
```

See `references/goals-schema.md` for the meta-goal pattern.

## Validate Mode

```bash
ao goals validate --json
```

Reports: goal count, version, format, directive count, any structural errors or warnings.

## Prune Mode

```bash
ao goals prune --dry-run    # List stale gates
ao goals prune              # Remove stale gates
```

Identifies gates whose check commands reference nonexistent paths. Removes them and re-renders the file.

## Migrate Mode

Convert between goal file formats.

```bash
ao goals migrate --to-md      # Convert GOALS.yaml → GOALS.md
ao goals migrate               # Migrate GOALS.yaml to latest YAML version
```

The `--to-md` flag creates a GOALS.md with mission, north/anti stars sections, and converts existing goals into the Gates table format. The original YAML file is backed up.

## Examples

### Checking fitness and directive gaps

**User says:** `$goals`

**What happens:**
1. Runs `ao goals measure --json` to get gate results
2. If GOALS.md format, runs `ao goals measure --directives` to get directive list
3. Assesses each directive against recent work
4. Reports combined fitness + directive gap dashboard

**Result:** Dashboard showing gate pass rates and directive progress.

### Bootstrapping goals for a new project

**User says:** `$goals init`

**What happens:**
1. Runs `ao goals init` which prompts for mission, stars, directives, and auto-detects gates
2. Creates GOALS.md in the project root

**Result:** New GOALS.md ready for `$evolve` consumption.

### Adding a new goal after a post-mortem

**User says:** `$goals add go-parser-fuzz "cd cli && go test -fuzz=. ./internal/goals/ -fuzztime=10s" --weight=3 --description="Markdown parser survives fuzz testing"`

**What happens:**
1. Runs `ao goals add` with the provided arguments
2. Writes the new goal in the correct format (YAML or Markdown)

**Result:** New goal added, measurable on next `$goals` run.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "goals file already exists" | Init called on existing project | Use `$goals` to measure, or delete file to re-init |
| "directives require GOALS.md format" | Tried steer on YAML file | Run `ao goals migrate --to-md` first |
| No directives in measure output | GOALS.yaml doesn't support directives | Migrate to GOALS.md with `ao goals migrate --to-md` |
| Gates referencing deleted scripts | Scripts were renamed or removed | Run `$goals prune` to clean up |
| Drift shows no history | No prior snapshots saved | Run `ao goals measure` at least twice first |
| Export returns empty | No snapshot file exists | Run `ao goals measure` to create initial snapshot |

## See Also

- `$evolve` — consumes goals for fitness-scored improvement loops
- `references/goals-schema.md` — schema definition for both formats
- `references/generation-heuristics.md` — goal quality criteria

## Reference Documents

- [references/generation-heuristics.md](references/generation-heuristics.md)
- [references/goals-schema.md](references/goals-schema.md)

## Local Resources

### references/

- [references/generation-heuristics.md](references/generation-heuristics.md)
- [references/goals-schema.md](references/goals-schema.md)

### scripts/

- `scripts/validate.sh`

