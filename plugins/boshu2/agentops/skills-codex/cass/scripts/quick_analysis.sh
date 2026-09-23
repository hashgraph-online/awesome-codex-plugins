#!/bin/bash
#
# Quick Analysis — One-command project overview using cass
#
# Usage:
#     ./quick_analysis.sh /data/projects/PROJECT_NAME
#
# Output:
#     - Index health
#     - Indexed hits by agent
#     - Activity by date
#
# Read-only. Requires: cass, jq, GNU timeout (or gtimeout).

set -euo pipefail

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

if command -v timeout >/dev/null 2>&1; then
    CASS_TIMEOUT=timeout
elif command -v gtimeout >/dev/null 2>&1; then
    CASS_TIMEOUT=gtimeout
else
    echo "Error: GNU timeout or gtimeout is required for bounded reads" >&2
    exit 1
fi

failed=0
read_cass() {
    local rc
    "$CASS_TIMEOUT" 15 cass "$@" || {
        rc=$?
        echo "CASS observation unavailable (exit $rc): $1" >&2
        return "$rc"
    }
}

echo "=============================================="
echo "CASS QUICK ANALYSIS: $WORKSPACE"
echo "=============================================="
echo ""

# 1. Health check
echo "--- Index Health ---"
read_cass status --robot-format json | jq -e '{
    conversations: .database.conversations,
    messages: .database.messages,
    index_fresh: .index.fresh,
    rebuilding: (.index.rebuilding // .rebuild.active // false),
    recommended: .recommended_action
}' || { echo "Index state unavailable; no recovery attempted" >&2; failed=1; }
echo ""

# 2. Agent breakdown (aggregation counts are hits, not distinct sessions)
echo "--- Indexed Hits by Agent ---"
read_cass search "*" --workspace "$WORKSPACE" --mode lexical --aggregate agent --limit 1 --fields minimal --json \
    | jq -r '.aggregations.agent.buckets[] | "\(.key): \(.count) hits"' \
    || { echo "Agent counts unavailable" >&2; failed=1; }
echo ""

# 3. Date breakdown (last 7 days of activity)
echo "--- Recent Activity (by date) ---"
read_cass search "*" --workspace "$WORKSPACE" --mode lexical --aggregate date --limit 1 --fields minimal --json \
    | jq -r '.aggregations.date.buckets | sort_by(.key) | reverse | .[0:7] | .[] | "\(.key): \(.count) hits"' \
    || { echo "Date counts unavailable" >&2; failed=1; }
echo ""

# 4. Quick tips
echo "--- Next Steps ---"
echo "Search a task-relevant keyword with an explicit workspace, limit and time cap."
echo "Use cass pack/view/expand for cited excerpts; verify user roles in native records."
echo "Repetition is a candidate signal, not evidence that an approach worked."
echo "Empty aggregates describe this indexed workspace only; failed reads are unavailable."
echo ""
echo "=============================================="
exit "$failed"
