# Post-Verdict Actions (Steps 9 & 9.5)

Procedural detail extracted from SKILL.md so the billboard stays compact.

## Step 9: Record Ratchet Progress

After council verdict:
1. If verdict is PASS or WARN:
   - Run: `ao ratchet record vibe --output "<report-path>" 2>/dev/null || true`
   - Suggest: "Run /post-mortem to capture learnings and complete the cycle."
2. If verdict is FAIL:
   - Do NOT record ratchet progress.
   - Extract ALL findings from the council report for structured retry context (group by category if >20):
     ```
     Read the council report. For each finding, format as:
     FINDING: <description> | FIX: <fix or recommendation> | REF: <ref or location>

     Fallback for v1 findings (no fix/why/ref fields):
       fix = finding.fix || finding.recommendation || "No fix specified"
       ref = finding.ref || finding.location || "No reference"
     ```
   - Tell user to fix issues and re-run /vibe, including the formatted findings as actionable guidance.

## Step 9.5: Feed Findings to Flywheel

**If verdict is WARN or FAIL**, persist reusable findings to `.agents/findings/registry.jsonl` and optionally mirror the broader narrative to a learning file.

Registry write rules:

- persist only reusable issues that should change future review or implementation behavior
- require `dedup_key`, provenance, `pattern`, `detection_question`, `checklist_item`, `applicable_when`, and `confidence`
- `applicable_when` must use the controlled vocabulary from the finding-registry contract
- append or merge by `dedup_key`
- use the contract's temp-file-plus-rename atomic write rule

If a broader prose summary still helps, also write the existing anti-pattern learning file to `.agents/learnings/YYYY-MM-DD-vibe-<target>.md`. Skip both if verdict is PASS.

After the registry update, if `hooks/finding-compiler.sh` exists, run:

```bash
bash hooks/finding-compiler.sh --quiet 2>/dev/null || true
```

This keeps the same-session post-mortem path synchronized with the latest reusable findings. `session-end-maintenance.sh` remains the idempotent backstop.
