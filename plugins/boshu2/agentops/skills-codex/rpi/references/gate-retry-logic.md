# Gate and Retry Logic

Detailed retry behavior for each gated phase. All gates use a max-3-attempts pattern (1 initial + 2 retries).

## Pre-mortem Gate (Phase 3)

Extract verdict from council report:

```bash
REPORT=$(ls -t .agents/council/*pre-mortem*.md 2>/dev/null | head -1)
```

Read the report file and find the verdict line (`## Council Verdict: PASS / WARN / FAIL`).

Gate logic:
- **PASS:** Auto-proceed. Log: "Pre-mortem: PASS"
- **WARN:** Auto-proceed. Log: "Pre-mortem: WARN -- see report for concerns"
- **FAIL:** Retry loop (max 2 retries):
  1. Read the full pre-mortem report to extract specific failure reasons
  1a. Extract ALL findings with structured fields (group by category if >20):
      ```
      For each finding, extract:
        FINDING: <description> | FIX: <fix or recommendation> | REF: <ref or location>

      Fallback for v1 findings: fix = finding.fix || finding.recommendation || "No fix specified"
                                 ref = finding.ref || finding.location || "No reference"
      ```
  2. Log: "Pre-mortem: FAIL (attempt N/3) -- retrying plan with feedback"
  3. Re-invoke `$plan` with the goal AND the failure context including structured findings:
     ```
     $plan <goal> --auto --context 'Pre-mortem FAIL: <key concerns>\nStructured findings:\nFINDING: X | FIX: Y | REF: Z\nFINDING: A | FIX: B | REF: C'
     ```
  4. Re-invoke `$pre-mortem` on the new plan
  5. If still FAIL after 3 total attempts, stop with message:
     "Pre-mortem failed 3 times. Last report: <path>. Manual intervention needed."

Store verdict in `rpi_state.verdicts.pre_mortem`.

## Implementation Gate (Phase 2)

Check completion status from crank's output. Look for `<promise>` tags:

- **`<promise>DONE</promise>`:** Proceed to Validation (Phase 3)
- **`<promise>BLOCKED</promise>`:** Retry (max 2 retries):
  1. Read crank output to extract block reason
  2. Log: "Crank: BLOCKED (attempt N/3) -- retrying with context"
  3. Re-invoke `$crank` with epic-id and block context (include `--test-first` by default; omit only when `--no-test-first` is set)
  4. If still BLOCKED after 3 total attempts, stop with message:
     "Crank blocked 3 times. Reason: <reason>. Manual intervention needed."
- **`<promise>PARTIAL</promise>`:** Retry remaining (max 2 retries):
  1. Read crank output to identify remaining items
  2. Log: "Crank: PARTIAL (attempt N/3) -- retrying remaining items"
  3. Re-invoke `$crank` with epic-id (it picks up unclosed issues; include `--test-first` by default; omit only when `--no-test-first` is set)
  4. If still PARTIAL after 3 total attempts, stop with message:
     "Crank partial after 3 attempts. Remaining: <items>. Manual intervention needed."

## Validation Gate (Phase 3)

Extract verdict from council report:

```bash
REPORT=$(ls -t .agents/council/*vibe*.md 2>/dev/null | head -1)
```

Read and extract verdict.

Gate logic:
- **PASS:** Auto-proceed. Log: "Vibe: PASS"
- **WARN:** Auto-proceed. Log: "Vibe: WARN -- see report for concerns"
- **FAIL:** Retry loop (max 2 retries):
  1. Read the full vibe report to extract specific failure reasons
  1a. Extract ALL findings with structured fields (group by category if >20):
      ```
      For each finding, extract:
        FINDING: <description> | FIX: <fix or recommendation> | REF: <ref or location>

      Fallback for v1 findings: fix = finding.fix || finding.recommendation || "No fix specified"
                                 ref = finding.ref || finding.location || "No reference"
      ```
  2. Log: "Vibe: FAIL (attempt N/3) -- retrying crank with feedback"
  3. Re-invoke `$crank` with the epic-id AND the failure context including structured findings:
     ```
     $crank <epic-id> --context 'Vibe FAIL: <key issues>\nStructured findings:\nFINDING: X | FIX: Y | REF: Z' --test-first   # default strict-quality path
     $crank <epic-id> --context 'Vibe FAIL: <key issues>\nStructured findings:\nFINDING: X | FIX: Y | REF: Z'                 # only when --no-test-first opted out
     ```
  4. Re-invoke `$validate` on the new changes
  5. If still FAIL after 3 total attempts, stop with message:
     "Vibe failed 3 times. Last report: <path>. Manual intervention needed."

Store verdict in `rpi_state.verdicts.vibe`.
