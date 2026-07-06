# Tracking and Validation Blocks

> Codex-native companion for `$plan` Step 7. Covers br issue creation,
> validation-block embedding, dependency edges, and post-creation verification.

## Step 7: Create Durable Tracking

Prefer br issues when the br CLI is available. They survive compaction, expose
dependency edges to `$crank`, and keep ratchet progress inspectable.

```bash
# Create epic first
br create --title "<goal>" --type epic --label "planned"

# Create child issues and keep the returned IDs
br create --title "<wave-1-task>" --body "<description>" --parent <epic-id> --label "planned"
br create --title "<wave-2-task-depends-on-wave-1>" --body "<description>" --parent <epic-id> --label "planned"

# Add blocking dependencies to form waves
br dep add <wave-1-id> <wave-2-id>
```

If br is unavailable or degraded, keep the plan file and execution packet
accurate. File-backed mode is acceptable as long as `$crank` and `$validate`
can read the handoff artifacts.

## Include Conformance Checks

Embed the conformance checks from the plan as a fenced validation block in each
issue body. This feeds `$crank` worker validation metadata.

````
br create --title "<task>" --body "Description...

\`\`\`validation
{\"files_exist\": [\"src/auth.go\"], \"content_check\": {\"file\": \"src/auth.go\", \"pattern\": \"func Authenticate\"}}
\`\`\`
" --parent <epic-id>
````

## Include Cross-Cutting Constraints

"Always" boundaries from the plan should be added to the epic description as a
`## Cross-Cutting Constraints` section. `$crank` reads these from the epic, not
from each individual issue, and applies them to every worker's validation
metadata.

## Waves Are Formed By Dependencies

- Issues with no blockers -> Wave 1 and appear in `br ready` immediately.
- Issues blocked by Wave 1 -> Wave 2 once Wave 1 closes.
- Issues blocked by Wave 2 -> Wave 3, and so on.

`br ready` returns the current executable wave: all unblocked issues that can
run in parallel.

## Step 7b: Verify Validation Blocks

After creating all br issues, verify that every issue body contains a fenced
validation block. Missing validation blocks weaken the plan-to-crank pipeline.

```bash
if command -v br &>/dev/null && [[ -n "$EPIC_ID" ]]; then
    MISSING_VALIDATION=()
    for ISSUE_ID in $ALL_CREATED_ISSUES; do
        if ! BEADS_DIR="$(ao beads dir)" br show "$ISSUE_ID" 2>/dev/null | grep -q '```validation'; then
            MISSING_VALIDATION+=("$ISSUE_ID")
        fi
    done
    if [[ ${#MISSING_VALIDATION[@]} -gt 0 ]]; then
        echo "WARNING: ${#MISSING_VALIDATION[@]} issue(s) missing validation blocks: ${MISSING_VALIDATION[*]}"
        echo "  $crank will fall back to default files_exist checks for these issues."
    else
        echo "All ${#ALL_CREATED_ISSUES[@]} issues have validation blocks."
    fi
fi
```

This is a warning gate, not a blocker. Plans can proceed without validation
blocks, but execution will use weaker fallback checks.
