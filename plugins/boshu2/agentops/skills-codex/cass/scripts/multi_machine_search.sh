#!/usr/bin/env bash
# multi_machine_search.sh — fan-out a cass search across the fleet
#
# Usage: ./multi_machine_search.sh "QUERY" [host1 host2 ...]
# Default hosts: css csd ts1 ts2
#
# - Local + remote searches run in parallel
# - One bad/unreachable host doesn't kill the rest (set -e disabled)
# - Query is passed via stdin to ssh, never interpolated into the command line,
#   so quotes/specials in the query are safe

set -uo pipefail
shopt -s nullglob   # unmatched globs expand to empty so `jq -s "$FANOUT_DIR"/*.json` is safe

QUERY="${1:?usage: $0 \"QUERY\" [host1 host2 ...]}"
shift
HOSTS=("$@")
[ ${#HOSTS[@]} -eq 0 ] && HOSTS=(css csd ts1 ts2)

# Per-host wall-clock cap (post-connect). ssh's ConnectTimeout only covers TCP
# handshake; if the remote `cass search` hangs we'd block indefinitely.
PER_HOST_TIMEOUT="${CASS_FANOUT_TIMEOUT:-30}"

# Required tools.
for tool in jq timeout ssh; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: '$tool' not on PATH" >&2
    exit 2
  fi
done

# Refuse multi-line queries early — `read -r q` on the remote only sees the first line.
case "$QUERY" in
  *$'\n'*)
    echo "error: multi-line queries are not supported (only the first line would be sent to remotes)" >&2
    exit 2
    ;;
esac

# Do NOT name this TMPDIR — that shadows the standard temp-dir env var for cass,
# jq, and ssh spawned below. Use a private name and ALWAYS remove it on exit
# (the old cleanup only printed a path and leaked the dir every run). No
# retention path: the skill's output contract states no artifact directory
# persists, and per-host errors are already surfaced to stderr before this trap.
FANOUT_DIR=$(mktemp -d -t cass-fanout-XXXXXX)
cleanup() {
  rm -rf "$FANOUT_DIR"
}
trap cleanup EXIT

# Local-host search runs in a function so a local cass failure produces "[]"
# rather than a missing file (which would later break the merge glob).
# Wrap every cass invocation in `timeout` — cass search has been observed
# to hang on certain inputs (e.g. --limit 0).
local_search() {
  local raw
  raw=$(timeout "$PER_HOST_TIMEOUT" cass search "$QUERY" --json --fields summary --limit 20 2>/dev/null) || raw=""
  if [ -z "$raw" ]; then
    echo "[]" > "$FANOUT_DIR/local.json"
    return
  fi
  printf '%s' "$raw" \
    | jq '[(.hits // [])[] | . + {origin_host: "local"}]' > "$FANOUT_DIR/local.json" \
    || echo "[]" > "$FANOUT_DIR/local.json"
}

# Pass the query via stdin so it's never spliced into the command line.
# `timeout` here covers post-connect hangs (ssh ConnectTimeout only covers TCP).
remote_search() {
  local h="$1"
  local raw
  # shellcheck disable=SC2016 # Remote shell expands $q after reading it from stdin.
  raw=$(timeout "$PER_HOST_TIMEOUT" ssh -o ConnectTimeout=5 -o BatchMode=yes "$h" \
        'IFS= read -r q && cass search "$q" --json --fields summary --limit 20 2>/dev/null' \
        <<<"$QUERY" 2>"$FANOUT_DIR/$h.err") || raw=""
  if [ -z "$raw" ]; then
    echo "[]" > "$FANOUT_DIR/$h.json"
    return
  fi
  printf '%s' "$raw" \
    | jq --arg h "$h" '[(.hits // [])[] | . + {origin_host: $h}]' > "$FANOUT_DIR/$h.json" \
    || echo "[]" > "$FANOUT_DIR/$h.json"
}

echo "→ local" >&2
local_search &

for h in "${HOSTS[@]}"; do
  echo "→ $h" >&2
  remote_search "$h" &
done

wait

# Surface ssh errors (don't fail; just inform)
for h in "${HOSTS[@]}"; do
  if [ -s "$FANOUT_DIR/$h.err" ]; then
    echo "  ! $h: $(head -c 200 "$FANOUT_DIR/$h.err" | tr '\n' ' ')" >&2
  fi
done

# Merge + dedup by source_path:line, sort by score
files=( "$FANOUT_DIR"/*.json )
if [ ${#files[@]} -eq 0 ]; then
  echo "[]"
  exit 0
fi

jq -s '
  (add // [])
  | map(select(type == "object"))
  | unique_by((.source_path // "") + ":" + ((.line_number // 0)|tostring))
  | sort_by(-(.score // 0))
  | .[0:50]
  | map({
      host:  (.origin_host // "?"),
      agent: (.agent       // ""),
      line:  (.line_number // null),
      score: (.score       // null),
      title: ((.title      // "") | .[0:100]),
      path:  (.source_path // "")
    })
' "${files[@]}"
