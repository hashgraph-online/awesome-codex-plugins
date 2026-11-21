#!/bin/bash
# YouTube Shorts Generator — Platform-aware preset over the AI Clipping primitive.
#
# Picks platform-specific defaults (aspect ratio + clip count) for short-form
# social and delegates to muapi.ai's /ai-clipping endpoint, which handles
# transcription, highlight ranking, dedupe, and face-tracked auto-crop server-side.
#
# Usage:
#   bash run-youtube-shorts.sh --source "<URL>" [options]
#
# Requires: bash 3.2+, jq, muapi-cli

set -euo pipefail

# ============================================================
# Locate skills root
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
AI_CLIPPING_SCRIPT="$SKILLS_ROOT/library/edit/ai-clipping/scripts/run-ai-clipping.sh"

if [ -f "$SKILLS_ROOT/.env" ]; then
    set +u; source "$SKILLS_ROOT/.env" 2>/dev/null || true; set -u
fi

# ============================================================
# Defaults
# ============================================================
SOURCE=""
PLATFORM="shorts"
NUM_CLIPS=""
ASPECT_RATIO=""
OUTPUT_JSON=""
VIEW=false
ASYNC=false
POLL_INTERVAL="${MUAPI_POLL_INTERVAL:-5}"
POLL_TIMEOUT="${MUAPI_POLL_TIMEOUT:-1800}"

# ============================================================
# Argument parsing
# ============================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --source|-s)        SOURCE="$2";        shift 2 ;;
        --platform|-p)      PLATFORM="$2";      shift 2 ;;
        --num-clips|-n)     NUM_CLIPS="$2";     shift 2 ;;
        --aspect-ratio|-a)  ASPECT_RATIO="$2";  shift 2 ;;
        --output-json|-o)   OUTPUT_JSON="$2";   shift 2 ;;
        --view)             VIEW=true;          shift   ;;
        --async)            ASYNC=true;         shift   ;;
        --poll-interval)    POLL_INTERVAL="$2"; shift 2 ;;
        --poll-timeout)     POLL_TIMEOUT="$2";  shift 2 ;;
        --help|-h)
            cat <<'HELP'
YouTube Shorts Generator — platform-aware preset over AI Clipping
Usage: bash run-youtube-shorts.sh --source "<URL>" [options]

REQUIRED
  --source, -s URL          YouTube URL, hosted mp4 URL, or local file path

PLATFORM PRESETS  (sets ratio + clip-count defaults)
  --platform shorts         9:16, 3 clips    (YouTube Shorts — default)
  --platform tiktok         9:16, 5 clips    (TikTok)
  --platform reels          9:16, 3 clips    (Instagram Reels)
  --platform feed           1:1,  3 clips    (Instagram Feed)

OVERRIDES
  --num-clips, -n N         Override clip count
  --aspect-ratio, -a RATIO  Override ratio: 9:16 | 1:1 | 4:5

OUTPUT
  --output-json, -o PATH    Dump full result here (use "-" for stdout)
  --view                    Download clips and open in system viewer (macOS)
  --async                   Return request_id immediately without polling

POLLING
  --poll-interval SEC       Seconds between job-status polls (default: 5)
  --poll-timeout SEC        Give up after this long (default: 1800)

EXAMPLES
  # Defaults — three 9:16 YouTube Shorts
  bash run-youtube-shorts.sh --source "https://youtube.com/watch?v=VIDEO_ID"

  # TikTok — 5 clips, view in player
  bash run-youtube-shorts.sh -s "<URL>" -p tiktok --view

  # Instagram Feed — square clips
  bash run-youtube-shorts.sh -s "<URL>" -p feed -n 3
HELP
            exit 0
            ;;
        *)  echo "Unknown flag: $1" >&2; exit 2 ;;
    esac
done

# ============================================================
# Validation
# ============================================================
if [[ -z "$SOURCE" ]]; then
    echo "ERROR: --source is required" >&2
    exit 2
fi
if [[ ! -f "$AI_CLIPPING_SCRIPT" ]]; then
    echo "ERROR: ai-clipping primitive not found at $AI_CLIPPING_SCRIPT" >&2
    exit 3
fi

# ============================================================
# Platform preset → defaults
# ============================================================
case "$PLATFORM" in
    shorts)  PLATFORM_RATIO="9:16"; PLATFORM_NUM=3 ;;
    tiktok)  PLATFORM_RATIO="9:16"; PLATFORM_NUM=5 ;;
    reels)   PLATFORM_RATIO="9:16"; PLATFORM_NUM=3 ;;
    feed)    PLATFORM_RATIO="1:1";  PLATFORM_NUM=3 ;;
    *)
        echo "ERROR: --platform must be one of: shorts, tiktok, reels, feed (got: $PLATFORM)" >&2
        exit 2
        ;;
esac

[[ -z "$ASPECT_RATIO" ]] && ASPECT_RATIO="$PLATFORM_RATIO"
[[ -z "$NUM_CLIPS"    ]] && NUM_CLIPS="$PLATFORM_NUM"

# ============================================================
# Delegate to AI Clipping primitive
# ============================================================
echo ">> Platform: $PLATFORM (ratio=$ASPECT_RATIO, num=$NUM_CLIPS)"

ARGS=(
    --video "$SOURCE"
    --num-clips "$NUM_CLIPS"
    --aspect-ratio "$ASPECT_RATIO"
    --poll-interval "$POLL_INTERVAL"
    --poll-timeout "$POLL_TIMEOUT"
)
[[ -n "$OUTPUT_JSON" ]] && ARGS+=(--output-json "$OUTPUT_JSON")
[[ "$VIEW"  == true  ]] && ARGS+=(--view)
[[ "$ASYNC" == true  ]] && ARGS+=(--async)

exec bash "$AI_CLIPPING_SCRIPT" "${ARGS[@]}"
