#!/bin/bash
# AI Clipping — Direct wrapper around muapi.ai's /ai-clipping endpoint.
#
# Long video in → ranked vertical short clips out, in one managed API call.
# Transcription, highlight ranking, dedupe, and face-tracked auto-crop all run
# server-side. No local Whisper, no local LLM, no GPU.
#
# Usage:
#   bash run-ai-clipping.sh --video "<URL>" [options]
#
# Requires: bash 3.2+, jq, muapi-cli

set -euo pipefail

# ============================================================
# Locate skills root (works regardless of CWD when invoked)
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# Load .env from skills root if present
if [ -f "$SKILLS_ROOT/.env" ]; then
    set +u; source "$SKILLS_ROOT/.env" 2>/dev/null || true; set -u
fi

# ============================================================
# Defaults
# ============================================================
VIDEO=""
NUM_CLIPS=3
ASPECT_RATIO="9:16"
COORDS_ONLY=false
OUTPUT_JSON=""
VIEW=false
ASYNC=false
POLL_INTERVAL="${MUAPI_POLL_INTERVAL:-5}"
POLL_TIMEOUT="${MUAPI_POLL_TIMEOUT:-1800}"
DOWNLOAD_DIR=""

# ============================================================
# Argument parsing
# ============================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --video|-v)         VIDEO="$2";         shift 2 ;;
        --num-clips|-n)     NUM_CLIPS="$2";     shift 2 ;;
        --aspect-ratio|-a)  ASPECT_RATIO="$2";  shift 2 ;;
        --coords-only)      COORDS_ONLY=true;   shift   ;;
        --output-json|-o)   OUTPUT_JSON="$2";   shift 2 ;;
        --download)         DOWNLOAD_DIR="$2";  shift 2 ;;
        --view)             VIEW=true;          shift   ;;
        --async)            ASYNC=true;         shift   ;;
        --poll-interval)    POLL_INTERVAL="$2"; shift 2 ;;
        --poll-timeout)     POLL_TIMEOUT="$2";  shift 2 ;;
        --help|-h)
            cat <<'HELP'
AI Clipping — long video → ranked vertical clips via muapi.ai's /ai-clipping
Usage: bash run-ai-clipping.sh --video "<URL>" [options]

REQUIRED
  --video, -v URL_OR_PATH   Hosted mp4 URL, local file path (auto-uploaded), or YouTube URL

OPTIONS
  --num-clips, -n N         Number of highlights to extract (default: 3)
  --aspect-ratio, -a RATIO  9:16 | 1:1 | 4:5  (default: 9:16)
  --coords-only             Return highlight time ranges only, skip cropping
  --output-json, -o PATH    Dump full result here (use "-" for stdout)
  --download DIR            Download generated clips into DIR
  --view                    Download clips and open in system viewer (macOS)
  --async                   Submit and return request_id without polling
  --poll-interval SEC       Seconds between job-status polls (default: 5)
  --poll-timeout SEC        Give up after this long (default: 1800)

EXAMPLES
  # Defaults — three 9:16 clips from a hosted URL
  bash run-ai-clipping.sh --video "https://example.com/podcast.mp4"

  # 8 clips, view in player
  bash run-ai-clipping.sh -v "<URL>" -n 8 --view

  # Square Instagram-feed clips, dump full result JSON
  bash run-ai-clipping.sh -v "<URL>" -a 1:1 -n 3 -o result.json

  # Just timestamps — render locally yourself
  bash run-ai-clipping.sh -v "<URL>" --coords-only -o result.json

  # Async — fire-and-forget, poll later
  REQUEST_ID=$(bash run-ai-clipping.sh -v "<URL>" --async -o - | jq -r '.request_id')
  muapi predict wait "$REQUEST_ID" --download ./outputs

  # Local file
  bash run-ai-clipping.sh -v ./recording.mp4 -n 5 --view
HELP
            exit 0
            ;;
        *)  echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

# ============================================================
# Validation
# ============================================================
if [[ -z "$VIDEO" ]]; then
    echo "ERROR: --video is required" >&2
    exit 2
fi
case "$ASPECT_RATIO" in
    9:16|1:1|4:5) ;;
    *) echo "ERROR: --aspect-ratio must be one of: 9:16, 1:1, 4:5 (got: $ASPECT_RATIO)" >&2; exit 2 ;;
esac
if ! command -v muapi >/dev/null 2>&1; then
    echo "ERROR: muapi-cli not found. Install with: npm install -g muapi-cli" >&2
    exit 3
fi
if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq not found on PATH" >&2
    exit 3
fi
if [[ -z "${MUAPI_API_KEY:-}" ]]; then
    if ! muapi auth status >/dev/null 2>&1; then
        echo "ERROR: MUAPI_API_KEY not set and muapi-cli not authenticated. Run: muapi auth configure" >&2
        exit 3
    fi
fi

# ============================================================
# Stage 1 — Resolve --video to a hosted URL
# ============================================================
VIDEO_URL=""
case "$VIDEO" in
    http*://*)
        VIDEO_URL="$VIDEO"
        ;;
    *)
        if [[ ! -f "$VIDEO" ]]; then
            echo "ERROR: local file not found: $VIDEO" >&2
            exit 2
        fi
        echo ">> Uploading local file"
        VIDEO_URL=$(muapi upload file "$VIDEO" --output-json --jq '.url' | tr -d '"')
        ;;
esac
echo ">> Source: $VIDEO_URL"

# ============================================================
# Stage 2 — Call /ai-clipping
# ============================================================
ARGS=(
    edit clipping
    --video "$VIDEO_URL"
    --num-highlights "$NUM_CLIPS"
    --aspect-ratio "$ASPECT_RATIO"
    --poll-interval "$POLL_INTERVAL"
    --poll-timeout "$POLL_TIMEOUT"
    --output-json
)
[[ "$COORDS_ONLY" == true ]] && ARGS+=(--return-coordinates-only)
[[ "$ASYNC"       == true ]] && ARGS+=(--no-wait)
if [[ "$VIEW" == true || -n "$DOWNLOAD_DIR" ]]; then
    DOWNLOAD_DIR="${DOWNLOAD_DIR:-./ai-clipping-output}"
    ARGS+=(--download "$DOWNLOAD_DIR")
fi
[[ "$VIEW" == true ]] && ARGS+=(--view)

echo ">> Calling muapi edit clipping (num=$NUM_CLIPS, ratio=$ASPECT_RATIO)"
RAW_RESULT=$(muapi "${ARGS[@]}")

if [[ "$ASYNC" == true ]]; then
    echo "$RAW_RESULT"
    exit 0
fi

# ============================================================
# Stage 3 — Report
# ============================================================
SHORTS_COUNT=$(echo "$RAW_RESULT" | jq '(.shorts // []) | length')
echo ""
echo "========================================================================"
echo "AI Clipping:   $SHORTS_COUNT clip(s) returned"
echo "========================================================================"
echo ""

echo "$RAW_RESULT" | jq -r '
    (.shorts // [])
    | to_entries[]
    | "#\(.key + 1)  score=\(.value.score // "?")  \(.value.start_time)s → \(.value.end_time)s
     title:  \(.value.title // "—")
     hook:   \"\(.value.hook_sentence // "")\"
     reason: \(.value.virality_reason // "—")
     clip:   \(.value.clip_url // "(coords-only)")
"'

if [[ -n "$OUTPUT_JSON" ]]; then
    if [[ "$OUTPUT_JSON" == "-" ]]; then
        echo "$RAW_RESULT"
    else
        echo "$RAW_RESULT" > "$OUTPUT_JSON"
        echo "Full result written to: $OUTPUT_JSON"
    fi
fi
