# Four-Surface Closure Check

> Mandatory validation step. Every completed feature must be checked across four surfaces.
> From spec-as-leverage-point analysis: code-only validation misses 40%+ of shipping gaps.

## The Four Surfaces

| Surface | What to Check | Gate Command |
|---------|---------------|--------------|
| **Code** | Implementation matches spec, tests pass, no regressions | `make test` or project-specific test command |
| **Documentation** | Docs reflect current behavior, no stale references. **CLI command/flag changes require regenerated reference docs.** | `validate-doc-release.sh`, grep for old behavior in docs, `scripts/generate-cli-reference.sh && git diff --quiet cli/docs/COMMANDS.md` |
| **Examples** | Usage examples work, CLI help is current | Run examples, check `--help` output |
| **Proof** | Acceptance criteria gates pass, new behavior has tests | Run acceptance criteria commands from plan |

## CLI Documentation Staleness (MANDATORY when CLI surface changed)

If the diff scope adds, removes, or modifies any `cobra.Command{...}` literal, any `.Flags()` call, or any file under `cli/cmd/` whose changes affect command shape, Documentation surface MUST include a CLI-reference-regen check:

```bash
CLI_CHANGED=0
if git diff --name-only "${BASE:-HEAD~1}"...HEAD | grep -qE '^cli/cmd/.*\.go$'; then
    if git diff "${BASE:-HEAD~1}"...HEAD -- 'cli/cmd/**.go' \
       | grep -qE '^\+.*(cobra\.Command\{|\.Flags\(\)|Use:|Short:)'; then
        CLI_CHANGED=1
    fi
fi

if [ "$CLI_CHANGED" = "1" ]; then
    bash scripts/generate-cli-reference.sh
    if ! git diff --quiet cli/docs/COMMANDS.md; then
        echo "FAIL: cli/docs/COMMANDS.md is stale — CLI surface changed but reference not regenerated before commit."
        exit 1
    fi
fi
```

Prevents the v2.41-evolve-run failure mode: a branch removed `--oscillation-sweep` from `ao defrag`, `cli/docs/COMMANDS.md` still listed it, validation and vibe both declared PASS.

## When to Run

This check runs as part of validation Step 1.5 (after vibe, before post-mortem):

```
Step 1: vibe (code quality)
Step 1.5: four-surface closure ← NEW
Step 2: post-mortem (learning extraction)
Step 3: retro
Step 4: forge
Step 5: phase summary
```

## Quick Check Script

```bash
# Surface 1: Code
echo "=== Code ==="
make test 2>&1 | tail -5

# Surface 2: Docs
echo "=== Documentation ==="
# Check for stale references to old behavior
git diff --name-only HEAD~5 | grep -E '\.(md|txt|rst)$' || echo "No doc changes"

# Surface 3: Examples
echo "=== Examples ==="
# Verify CLI help matches implementation
# Verify CLI help matches implementation (project-specific command)
echo "Check CLI --help output matches implementation"

# Surface 4: Proof
echo "=== Proof ==="
# Run acceptance criteria from plan (customize per project)
echo "Run acceptance criteria gates here"
```

## Verdict Rules

- **All 4 surfaces pass:** Proceed to post-mortem
- **Code passes, others fail:** WARN — complete documentation/examples/proof before closing
- **Code fails:** BLOCK — fix code before checking other surfaces
- **Proof missing:** WARN — acceptance criteria must be runnable, not just "verify it works"
