#!/bin/bash
#
# Quick Analysis — One-command project overview using cass
#
# Usage:
#     ./quick_analysis.sh /data/projects/PROJECT_NAME
#
# Output:
#     - Index health
#     - Session counts by agent
#     - Activity by date
#     - Top 5 ritual opener candidates
#
# Requires: cass, jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_MINER="$SCRIPT_DIR/prompt_miner.py"

WORKSPACE="${1:-}"

if [ -z "$WORKSPACE" ]; then
    echo "Usage: $0 /data/projects/PROJECT_NAME"
    echo ""
    echo "Examples:"
    echo "  $0 /data/projects/beads_rust"
    echo "  $0 /data/projects/rich_rust"
    exit 1
fi

# Expand path
WORKSPACE=$(realpath "$WORKSPACE" 2>/dev/null || echo "$WORKSPACE")

if ! command -v cass >/dev/null 2>&1; then
    echo "Error: cass is not installed or not in PATH"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is not installed or not in PATH"
    exit 1
fi

echo "=============================================="
echo "CASS QUICK ANALYSIS: $WORKSPACE"
echo "=============================================="
echo ""

# 1. Health check
echo "--- Index Health ---"
cass status --robot-format json 2>/dev/null | jq '{
    conversations: .database.conversations,
    messages: .database.messages,
    index_fresh: .index.fresh,
    rebuilding: (.index.rebuilding // .rebuild.active // false),
    recommended: .recommended_action
}' 2>/dev/null || echo "Error: Could not get cass status"
echo ""

# 2. Refresh index (quick, incremental)
echo "--- Refreshing Index ---"
cass index --json 2>/dev/null | jq '.indexed // "Index refreshed"' -r 2>/dev/null || echo "Index refresh attempted"
echo ""

# 3. Agent breakdown
echo "--- Sessions by Agent ---"
cass search "*" --workspace "$WORKSPACE" --aggregate agent --limit 1 --json 2>/dev/null \
    | jq '.aggregations.agent.buckets[] | "\(.key): \(.count) sessions"' -r 2>/dev/null \
    || echo "No sessions found for this workspace"
echo ""

# 4. Date breakdown (last 7 days of activity)
echo "--- Recent Activity (by date) ---"
cass search "*" --workspace "$WORKSPACE" --aggregate date --limit 1 --json 2>/dev/null \
    | jq '.aggregations.date.buckets | sort_by(.key) | reverse | .[0:7] | .[] | "\(.key): \(.count) hits"' -r 2>/dev/null \
    || echo "No date information available"
echo ""

# 5. Ritual opener candidates (prompts at lines 1-3 that appear multiple times)
echo "--- Ritual Opener Candidates ---"
echo "(Prompts appearing at session start, sorted by frequency)"
echo ""

# Search for common ritual opener patterns
for pattern in "First read ALL" "AGENTS.md" "comprehensive deep dive" "ultrathink" "think super hard"; do
    count=$(cass search "$pattern" --workspace "$WORKSPACE" --json --limit 100 2>/dev/null \
        | jq '.total_matches // 0' 2>/dev/null || echo "0")
    if [ "$count" -gt 2 ]; then
        printf "  %3dx: \"%s\"\n" "$count" "$pattern"
    fi
done
echo ""

# 6. Quick tips
echo "--- Next Steps ---"
echo "1. Find ritual opener:    cass search \"First read ALL\" --workspace $WORKSPACE --json --limit 5"
echo "2. View a session:        cass view /path/to/session.jsonl -n 1 -C 10"
echo "3. Find user prompts:     cass search \"KEYWORD\" --workspace $WORKSPACE --json | jq '[.hits[] | select(.line_number <= 3)]'"
echo "4. Mine all prompts:      python \"$PROMPT_MINER\" --workspace $WORKSPACE"
echo ""
echo "=============================================="
