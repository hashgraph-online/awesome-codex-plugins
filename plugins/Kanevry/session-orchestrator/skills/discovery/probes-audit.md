> See probes-intro.md for confidence scoring reference.

## Category: `audit`

### Probe: harness-audit

**Activation:** `.orchestrator/bootstrap.lock` exists (always-on for session-orchestrator-integrated repos).

**Detection Method:**

```bash
# Step 1: Verify the script exists; skip if missing
test -f scripts/harness-audit.mjs || { echo "SKIPPED: harness-audit -- scripts/harness-audit.mjs not found"; exit 0; }

# Step 2: Run the audit. Capture stdout (JSON) and stderr (human summary) separately;
# the script writes the human summary to stderr and the JSON record to stdout.
AUDIT_OUTPUT="$(node scripts/harness-audit.mjs 2>/tmp/audit_summary_stderr)"
EXIT_CODE=$?

# Step 3: Validate the output is parseable JSON
echo "$AUDIT_OUTPUT" | node -e "
try {
  const data = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  process.stdout.write(JSON.stringify(data));
} catch(e) {
  process.stderr.write('PARSE_ERROR: ' + e.message);
  process.exit(1);
}" 2>/tmp/audit_parse_err

# If parse fails, report FAILED and stop
# If EXIT_CODE != 0, report FAILED with stderr content and stop
```

The script writes the same record to `.orchestrator/metrics/audit.jsonl` automatically. The probe reads from stdout only; no additional persistence step is needed.

**Severity Mapping (category-level):**

Evaluate `score_0_10` for each entry in the `categories` array of the JSON output:

| `score_0_10` range  | Action |
|---------------------|--------|
| `>= 7`              | Info only — record in `audit.jsonl`, **do NOT emit a discovery finding** |
| `>= 5` and `< 7`    | Emit finding with severity `medium` |
| `< 5`               | Emit finding with severity `high` |

Apply this mapping **per category**, not per individual check.

**Finding Emission (one finding per low-scoring category):**

For each category whose `score_0_10 < 7`, emit one finding using the following field values:

| Finding Field    | Value |
|------------------|-------|
| `probe`          | `harness-audit` |
| `category`       | `audit` |
| `severity`       | `high` if `score_0_10 < 5`, `medium` if `5 <= score_0_10 < 7` |
| `title`          | `harness-audit: <category name> below threshold (<score_0_10>/10)` |
| `file_path`      | `.orchestrator/metrics/audit.jsonl` |
| `line_number`    | `0` (category-level finding — not tied to a single line) |
| `matched_text`   | Composed from the category's failed checks — one line per failed check: `[<check_id>] <message>` |
| `description`    | `Harness audit category "<category name>" scored <score_0_10>/10 (earned <earned_points>/<max_points> points). See failed checks for details.` |
| `recommended_fix`| List each failed check with its `path` and `evidence` context: `<check_id>: <path> — <evidence>` |
| `confidence`     | `90` |

**Evidence Format:**
```
Audit Run: session_id=<session_id>  rubric_version=<rubric_version>  started_at=<started_at>
Overall:   score=<overall_mean_0_10>/10  band=<overall_band>  checks=<checks_passed>/<checks_total>
Repository: branch=<branch>  sha=<head_sha>

Category: <name>
  Score:  <score_0_10>/10  earned=<earned_points>/<max_points>  weight=<weight>
  Failed checks:
    - <check_id>  status=fail  points=<points>  path=<path>
      evidence: <evidence>
      message:  <message>
```

**Default Severity:** High if `score_0_10 < 5`; Medium if `5 <= score_0_10 < 7`.

**Labels for auto-created issues:** `type:discovery`, `area:harness` (new label — add to VCS label set if absent), `priority::high` or `priority::medium` per severity, `status:ready`.

**Skip Conditions:**

- If `scripts/harness-audit.mjs` is missing → `SKIPPED: harness-audit -- scripts/harness-audit.mjs not found`
- If the script exits with a non-zero code → `FAILED: harness-audit -- script exited <code>: <stderr excerpt>`
- If stdout is not valid JSON → `FAILED: harness-audit -- invalid JSON in script output: <parse error>`

A skip or failure here does NOT abort the rest of the discovery run. Continue with other probes.

**Out of Scope:**

This probe reports findings only. It does not attempt remediation or auto-fix. Issue creation follows the standard `/discovery` Phase 5/6 triage flow.

---
