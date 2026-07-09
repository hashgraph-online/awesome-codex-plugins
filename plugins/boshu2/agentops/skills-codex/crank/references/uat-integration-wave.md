# UAT Integration Wave Template

Cross-cutting validation wave added after all feature implementation waves complete.

## When to Add

Add a UAT integration wave when:
- An epic spans 3+ features that interact at runtime
- Features share state (filesystem, config, CLI flags)
- Pipeline flows cross feature boundaries (e.g., harvest → mine → defrag)
- The epic's pre-mortem identified cross-feature risk

## Read-Only Wave Concept

Integration workers **validate but don't modify code**. They run scenarios that exercise multi-feature pipelines and report pass/fail. If a scenario fails, the lead creates a targeted fix issue for the next wave rather than having the integration worker attempt a fix.

This prevents integration workers from making conflicting edits to files owned by feature workers.

## Pre-flight: Verify Binary Version

Before running any UAT scenario, confirm the `ao` binary in PATH matches the
expected release. Stale binaries are the #1 cause of false UAT failures.

```bash
# Run the pre-flight check (exits non-zero on mismatch):
bash scripts/preflight-uat-binary.sh

# Or inline:
ao version   # confirm output matches the release under test
```

Record the version string below. If it does not match the target version for
this UAT, **STOP** — rebuild or reinstall before proceeding:

```bash
cd cli && make build && cp bin/ao "$(command -v ao)"
```

- **Expected version:** _fill in before UAT starts_
- **Observed version:** _paste `ao version` output_

This is **Scenario 0** in every UAT integration wave — it must pass before any
functional scenarios execute.

## Example Integration Scenarios

### Pipeline Flow Test
```bash
# Lookup knowledge → mine signals → defrag cleanup
ao lookup --query "research" --no-cite
ao mine --sources git --since 1d --quiet
ao defrag --dedup --quiet
```

### Cross-Feature State Test
```bash
# Handoff creates artifact → lookup reads it
ao handoff --dry-run "integration test"
ao lookup --query "integration test" --no-cite
```

### CLI Flag Interaction Test
```bash
# Global flags (--json, --dry-run) work across all subcommands
ao defrag --dry-run --json
ao mine --quiet --sources git
ao lookup --query "integration test" --json --no-cite
```

## Worker Prompt Template

```
You are a read-only integration validator. Do NOT modify any source files.

Run each scenario below and report:
- PASS: scenario completed without error
- FAIL: scenario failed (include error message and stderr)
- SKIP: scenario prerequisites not met (explain why)

Scenarios:
1. [description]
2. [description]

After running all scenarios, write results to:
  .agents/crank/integration-wave-results.json

Format:
{
  "wave": N,
  "scenarios": [
    {"id": 1, "status": "PASS|FAIL|SKIP", "detail": "..."}
  ],
  "verdict": "PASS|FAIL"
}
```

## When to Skip

Skip the integration wave when:
- All issues are independent (no shared state or pipeline flows)
- Epic is pure documentation or process changes
- Epic has fewer than 3 issues
