#!/bin/bash
# Social Media Video Generator — Orchestrator
#
# Generates reference images (if requested) then produces a Seedance 2.0 video,
# all wired to platform-specific defaults (aspect ratio, duration, tier).
#
# Usage:
#   bash run-social-video.sh --prompt "director brief" --platform instagram [options]
#
# Requires: bash 3.2+, curl, jq

set -euo pipefail

# ============================================================
# Locate skills root (works regardless of CWD when invoked)
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
GENERATE_IMAGE="$SKILLS_ROOT/core/media/generate-image.sh"
GENERATE_SEEDANCE="$SKILLS_ROOT/library/motion/seedance-2/scripts/generate-seedance.sh"

# Load .env from skills root
if [ -f "$SKILLS_ROOT/.env" ]; then
    set +u; source "$SKILLS_ROOT/.env" 2>/dev/null || true; set -u
fi

# ============================================================
# Defaults
# ============================================================
PROMPT=""
PLATFORM="instagram"
CAMERA=""
MODE="t2v"
TIER="chinese"
FAST=false
ASPECT=""
DURATION=""
QUALITY="basic"
VIEW=false
ASYNC=false
IMAGE_FILES=()

# Reference image generation
GEN_REF_FIRST=""      # --gen-ref "prompt"       → generate first frame ref
GEN_REF_LAST=""       # --gen-ref-last "prompt"  → generate last frame ref
REF_MODEL="google-imagen4-ultra"

# ============================================================
# Argument parsing
# ============================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --prompt|-p)        PROMPT="$2";         shift 2 ;;
        --platform)         PLATFORM="$2";       shift 2 ;;
        --camera)           CAMERA="$2";         shift 2 ;;
        --mode)             MODE="$2";           shift 2 ;;
        --tier)             TIER="$2";           shift 2 ;;
        --fast)             FAST=true;           shift   ;;
        --aspect)           ASPECT="$2";         shift 2 ;;
        --duration)         DURATION="$2";       shift 2 ;;
        --quality|-q)       QUALITY="$2";        shift 2 ;;
        --view)             VIEW=true;           shift   ;;
        --async)            ASYNC=true;          shift   ;;
        --file|-f)          IMAGE_FILES+=("$2"); shift 2 ;;
        --gen-ref)          GEN_REF_FIRST="$2";  shift 2 ;;
        --gen-ref-last)     GEN_REF_LAST="$2";   shift 2 ;;
        --ref-model)        REF_MODEL="$2";      shift 2 ;;
        --help|-h)
            cat <<'HELP'
Social Media Video Generator
Usage: bash run-social-video.sh --prompt "director brief" [options]

REQUIRED
  --prompt, -p TEXT     Seedance 2.0 Director Brief (the full cinematic prompt)

PLATFORM (sets aspect/duration defaults)
  --platform NAME       instagram | tiktok | linkedin | youtube | youtube-short |
                        twitter | pinterest | instagram-feed  (default: instagram)

CAMERA STYLE (appends camera directive to prompt)
  --camera TYPE         fpv | drone | flythrough | reveal | epic | product |
                        narrative | tracking | orbit  (default: from --platform)

VIDEO OPTIONS
  --mode MODE           t2v | i2v | first-last | omni  (default: t2v)
  --tier TIER           chinese | global | vip  (default: chinese)
                        Note: first-last requires global or vip
  --fast                Use fast-queue variant (global/vip only)
  --aspect RATIO        Override platform default aspect ratio
  --duration N          Override platform default duration (seconds)
  --quality Q           basic | high  (Chinese tier only; default: basic)
  --view                Download and open output (macOS)
  --async               Return request_id without waiting

REFERENCE IMAGES
  --file, -f PATH       Provide an existing image file (repeatable, up to 9)
  --gen-ref TEXT        Generate a first-frame reference image from this prompt
  --gen-ref-last TEXT   Generate a last-frame reference image (triggers first-last mode)
  --ref-model MODEL     Image model for reference generation
                        (default: google-imagen4-ultra)
                        Options: flux-kontext-pro-t2i | hidream-i1-full |
                                 google-imagen4-fast | ideogram-v3-t2i

EXAMPLES
  # Instagram Reel — drone shot, auto-generate ref image, t2v
  bash run-social-video.sh \
    --prompt "Drone descends over rooftop at sunrise, product reveal..." \
    --platform instagram --camera drone --duration 10

  # TikTok — FPV, with generated first frame
  bash run-social-video.sh \
    --prompt "First-person rush through..." \
    --platform tiktok --camera fpv \
    --gen-ref "Hero product on table, soft morning light, close-up" \
    --tier global --view

  # LinkedIn landscape — product orbit, existing reference image
  bash run-social-video.sh \
    --prompt "Precision orbit around product, specular highlights..." \
    --platform linkedin --camera product --mode i2v --file product.jpg \
    --quality high --view

  # YouTube Short — first-last frame interpolation
  bash run-social-video.sh \
    --prompt "Dramatic reveal from foggy landscape to clear skyline..." \
    --platform youtube-short \
    --gen-ref "Morning fog over mountain valley, sunrise" \
    --gen-ref-last "Clear blue sky, mountain peak, golden hour" \
    --tier global --view
HELP
            exit 0 ;;
        *)
            echo "Warning: Unknown argument '$1' — skipping." >&2
            shift ;;
    esac
done

# ============================================================
# Validate
# ============================================================
if [ -z "$PROMPT" ]; then
    echo "Error: --prompt is required. Provide the Seedance Director Brief." >&2
    exit 1
fi
if [ -z "${MUAPI_KEY:-}" ]; then
    echo "Error: MUAPI_KEY is not set. Export it or add to $SKILLS_ROOT/.env" >&2
    exit 1
fi

# ============================================================
# Platform → aspect ratio + duration defaults
# ============================================================
case "$PLATFORM" in
    instagram|tiktok|youtube-short)
        DEFAULT_ASPECT="9:16"; DEFAULT_DURATION=10 ;;
    instagram-feed)
        DEFAULT_ASPECT="1:1";  DEFAULT_DURATION=10 ;;
    linkedin|youtube|twitter)
        DEFAULT_ASPECT="16:9"; DEFAULT_DURATION=10 ;;
    pinterest)
        DEFAULT_ASPECT="4:3";  DEFAULT_DURATION=10 ;;
    *)
        DEFAULT_ASPECT="16:9"; DEFAULT_DURATION=10 ;;
esac

ASPECT="${ASPECT:-$DEFAULT_ASPECT}"
DURATION="${DURATION:-$DEFAULT_DURATION}"

# Formats requiring global/vip tier
if [[ "$ASPECT" == "1:1" || "$ASPECT" == "21:9" ]] && [[ "$TIER" == "chinese" ]]; then
    echo "Note: Aspect ratio $ASPECT requires global or vip tier. Switching to global." >&2
    TIER="global"
fi

# ============================================================
# Camera → intent mapping (for generate-seedance.sh --intent)
# ============================================================
case "$CAMERA" in
    fpv)                INTENT="fpv" ;;
    drone|flythrough)   INTENT="drone" ;;
    reveal)             INTENT="reveal" ;;
    epic)               INTENT="epic" ;;
    product)            INTENT="product" ;;
    narrative|tracking) INTENT="narrative" ;;
    orbit)              INTENT="epic" ;;
    *)                  INTENT="cinematic" ;;
esac

# ============================================================
# Generate reference images if requested
# ============================================================
OUTPUT_DIR="$SKILLS_ROOT/media_outputs"
mkdir -p "$OUTPUT_DIR"

generate_ref_image() {
    local REF_PROMPT="$1"
    local LABEL="$2"
    local OUTPUT_PATH="$OUTPUT_DIR/social_ref_${LABEL}_$(date +%s).jpg"

    echo "" >&2
    echo "Generating $LABEL reference image with $REF_MODEL..." >&2
    echo "Prompt: $REF_PROMPT" >&2

    local RESULT
    RESULT=$(cd "$SKILLS_ROOT" && bash "$GENERATE_IMAGE" \
        --model "$REF_MODEL" \
        --prompt "$REF_PROMPT" \
        --aspect-ratio "$ASPECT" \
        --json)

    local IMG_URL
    IMG_URL=$(echo "$RESULT" | jq -r '.outputs[0] // empty')

    if [ -z "$IMG_URL" ]; then
        echo "Error: Failed to generate reference image. Raw response:" >&2
        echo "$RESULT" >&2
        exit 1
    fi

    echo "Downloading reference image to $OUTPUT_PATH..." >&2
    curl -s -o "$OUTPUT_PATH" "$IMG_URL"

    if [ "$VIEW" = true ] && [[ "$OSTYPE" == "darwin"* ]]; then
        open "$OUTPUT_PATH"
    fi

    echo "$OUTPUT_PATH"
}

# Generate first-frame reference
if [ -n "$GEN_REF_FIRST" ]; then
    FIRST_REF_PATH=$(generate_ref_image "$GEN_REF_FIRST" "first")
    IMAGE_FILES=("$FIRST_REF_PATH" "${IMAGE_FILES[@]}")
    echo "First-frame reference: $FIRST_REF_PATH" >&2
fi

# Generate last-frame reference
LAST_REF_PATH=""
if [ -n "$GEN_REF_LAST" ]; then
    LAST_REF_PATH=$(generate_ref_image "$GEN_REF_LAST" "last")
    echo "Last-frame reference: $LAST_REF_PATH" >&2
fi

# ============================================================
# Determine mode from available images
# ============================================================
# If we have a last-frame reference, use first-last mode
if [ -n "$LAST_REF_PATH" ]; then
    MODE="first-last"
    IMAGE_FILES+=("$LAST_REF_PATH")
    if [ "$TIER" = "chinese" ]; then
        echo "Note: first-last mode requires global/vip tier. Switching to global." >&2
        TIER="global"
    fi
fi

# If we have images and mode is still t2v, switch to i2v
if [ ${#IMAGE_FILES[@]} -gt 0 ] && [ "$MODE" = "t2v" ]; then
    MODE="i2v"
fi

# ============================================================
# Build generate-seedance.sh command
# ============================================================
SEEDANCE_ARGS=(
    --mode "$MODE"
    --tier "$TIER"
    --subject "$PROMPT"
    --intent "$INTENT"
    --aspect "$ASPECT"
    --duration "$DURATION"
)

# Quality only applies to Chinese tier
if [ "$TIER" = "chinese" ]; then
    SEEDANCE_ARGS+=(--quality "$QUALITY")
fi

# Fast flag (global/vip only)
if [ "$FAST" = true ]; then
    SEEDANCE_ARGS+=(--fast)
fi

# Attach reference images
for IMG in "${IMAGE_FILES[@]}"; do
    SEEDANCE_ARGS+=(--file "$IMG")
done

# Pass-through flags
[ "$VIEW" = true ]  && SEEDANCE_ARGS+=(--view)
[ "$ASYNC" = true ] && SEEDANCE_ARGS+=(--async)

# ============================================================
# Summary
# ============================================================
echo "" >&2
echo "======================================" >&2
echo " Social Media Video Generator" >&2
echo "======================================" >&2
echo " Platform  : $PLATFORM" >&2
echo " Aspect    : $ASPECT" >&2
echo " Duration  : ${DURATION}s" >&2
echo " Mode      : $MODE" >&2
echo " Tier      : $TIER" >&2
echo " Camera    : ${CAMERA:-default}" >&2
echo " Intent    : $INTENT" >&2
echo " Ref images: ${#IMAGE_FILES[@]}" >&2
echo " Ref model : $REF_MODEL" >&2
echo "======================================" >&2
echo "" >&2

# ============================================================
# Execute Seedance generation
# ============================================================
cd "$SKILLS_ROOT"
exec bash "$GENERATE_SEEDANCE" "${SEEDANCE_ARGS[@]}"
