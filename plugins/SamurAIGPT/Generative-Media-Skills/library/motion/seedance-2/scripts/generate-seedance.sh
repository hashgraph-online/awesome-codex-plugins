#!/bin/bash
# Expert Skill: Seedance 2 Cinema Expert
# Translates creative intent into 'Director-Level' technical directives for Seedance 2.0.
#
# Modes:   t2v | i2v | extend | first-last | omni | omni-train | character | video-edit | watermark-remove
# Tiers:   chinese (default) | global | vip
# Options: --fast for fast-queue variants (global/vip only)
#
# Requires: bash 3.2+, curl, jq, python3

set -euo pipefail

SUBJECT=""
INTENT="cinematic"
ASPECT="16:9"
DURATION=5
QUALITY="basic"
AUDIO_FLAG=""
VIEW=false
MODE="t2v"
TIER="chinese"
FAST=false
IMAGE_URLS=()
IMAGE_FILES=()
VIDEO_URLS=()
VIDEO_FILES=()
AUDIO_URLS=()
AUDIO_FILES=()
EXTEND_REQUEST_ID=""
CHARACTER_NAME=""
CHARACTER_DESC=""
REMOVE_WATERMARK=false
PRO_WATERMARK=false
ASYNC=false
JSON_ONLY=false
MAX_WAIT=600
POLL_INTERVAL=5

MUAPI_BASE="https://api.muapi.ai/api/v1"

# Load .env if present (suppress errors, disable nounset temporarily)
if [ -f ".env" ]; then
    set +u; source .env 2>/dev/null || true; set -u
fi

# ============================================================
# Argument parsing
# ============================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)             MODE="$2";             shift 2 ;;
        --tier)             TIER="$2";             shift 2 ;;
        --fast)             FAST=true;             shift   ;;
        --subject)          SUBJECT="$2";          shift 2 ;;
        --intent)           INTENT="$2";           shift 2 ;;
        --aspect)           ASPECT="$2";           shift 2 ;;
        --duration)         DURATION="$2";         shift 2 ;;
        --quality)          QUALITY="$2";          shift 2 ;;
        --no-audio)         AUDIO_FLAG="--no-audio"; shift ;;
        --view)             VIEW=true;             shift   ;;
        --image|--image-url) IMAGE_URLS+=("$2");  shift 2 ;;
        --file|--image-file) IMAGE_FILES+=("$2"); shift 2 ;;
        --video-url)        VIDEO_URLS+=("$2");    shift 2 ;;
        --video-file)       VIDEO_FILES+=("$2");   shift 2 ;;
        --audio-url)        AUDIO_URLS+=("$2");    shift 2 ;;
        --audio-file)       AUDIO_FILES+=("$2");   shift 2 ;;
        --request-id)       EXTEND_REQUEST_ID="$2"; shift 2 ;;
        --character-name)   CHARACTER_NAME="$2";   shift 2 ;;
        --character-desc)   CHARACTER_DESC="$2";   shift 2 ;;
        --remove-watermark) REMOVE_WATERMARK=true; shift   ;;
        --pro)              PRO_WATERMARK=true;    shift   ;;
        --async)            ASYNC=true;            shift   ;;
        --json)             JSON_ONLY=true;        shift   ;;
        --help|-h)
            cat <<'HELP'
Seedance 2 Cinema Expert
Usage: bash generate-seedance.sh --mode MODE [options]

MODES
  t2v              Text-to-Video
  i2v              Image-to-Video (1–9 images)
  extend           Extend an existing Seedance 2.0 video (Chinese tier only)
  first-last       First & Last Frame interpolation (Global/VIP; 1–2 images)
  omni             Omni Reference — images + audio + optional @character refs
  omni-train       Train a custom Omni Reference character (one reference image)
  character        Build a character sheet from 1–3 images
  video-edit       Edit a video with prompt + optional reference images (Chinese tier)
  watermark-remove Remove watermark from a Seedance 2.0 video

TIERS  (default: chinese)
  chinese          seedance-v2.0-* endpoints — lower cost, low censorship
  global           seedance-2-* endpoints — 21:9/1:1 aspect ratios, flexible 4–15s duration
  vip              seedance-2-vip-* endpoints — fast queue + low censorship

OPTIONS
  --fast           Use fast-queue variant (global/vip tiers only)
  --subject TEXT   Scene description / prompt (required for most modes)
  --intent TYPE    reveal|tense|epic|narrative|product|educational|comedy|fpv|drone|flythrough (default: cinematic)
  --aspect RATIO   16:9|9:16|4:3|3:4  — global/vip also support: 21:9|1:1  (default: 16:9)
  --duration N     Chinese: 5|10|15 s  — global/vip: any integer 4–15 s  (default: 5)
  --quality Q      basic|high  (Chinese tier only; default: basic)
  --view           Download and open the output file (macOS)
  --async          Return request_id immediately without polling
  --json           Raw JSON output only

INPUTS
  --image URL        Image URL (repeatable, up to 9)
  --file PATH        Local image file — auto-uploaded (repeatable)
  --video-url URL    Reference video URL (repeatable, up to 3; Chinese i2v/omni only)
  --video-file PATH  Local video file — auto-uploaded (repeatable)
  --audio-url URL    Reference audio URL (repeatable, up to 3)
  --audio-file PATH  Local audio file — auto-uploaded (repeatable)

MODE-SPECIFIC OPTIONS
  extend:           --request-id ID          request_id of the original Seedance 2.0 video
  character:        --character-name NAME    optional character label
                    --subject TEXT           optional outfit/costume description
  omni-train:       --character-name NAME    character name for @omni-character ref
                    --character-desc TEXT    optional character description
  video-edit:       --video-url/--video-file  source video (1 max, 10MB, 15s)
                    --remove-watermark         strip watermark from edited output
  watermark-remove: --video-url/--video-file  Seedance 2.0 video URL
                    --pro                      use Pro remover (100MB limit)

EXAMPLES
  # Chinese T2V (default)
  bash generate-seedance.sh --subject "hidden Andes temple at dawn" --intent epic --view

  # Global T2V — 21:9, 12s, fast queue
  bash generate-seedance.sh --tier global --fast --subject "neon cyberpunk alley" --aspect "21:9" --duration 12

  # VIP I2V
  bash generate-seedance.sh --mode i2v --tier vip --fast --file hero.jpg --subject "hero strides forward"

  # First & Last Frame (global)
  bash generate-seedance.sh --mode first-last --tier global --file start.jpg --file end.jpg \
    --subject "smooth cinematic transition"

  # Omni Reference (global, with character ref)
  bash generate-seedance.sh --mode omni --tier global --file portrait.jpg \
    --subject "@image1 walks through a neon-lit city at night"

  # Train Omni Reference character
  bash generate-seedance.sh --mode omni-train --file portrait.jpg \
    --character-name "Alex" --character-desc "A brave explorer"

  # Chinese character sheet
  bash generate-seedance.sh --mode character --file ref1.jpg --file ref2.jpg \
    --character-name "Hero" --subject "red leather jacket"

  # Video Edit
  bash generate-seedance.sh --mode video-edit \
    --video-url "https://example.com/input.mp4" --file replacement.jpg \
    --subject "Replace the runner with @image1, preserve exact motion and camera"

  # Watermark Remove (Pro)
  bash generate-seedance.sh --mode watermark-remove --video-url "https://example.com/v.mp4" --pro
HELP
            exit 0 ;;
        *)
            echo "Warning: Unknown argument '$1' — skipping." >&2
            shift ;;
    esac
done

# ============================================================
# Validate API key
# ============================================================
if [ -z "${MUAPI_KEY:-}" ]; then
    echo "Error: MUAPI_KEY is not set. Export it or add to .env" >&2
    exit 1
fi

HEADERS=(-H "x-api-key: $MUAPI_KEY" -H "Content-Type: application/json")

# ============================================================
# Director's Cinematography Grammar
# ============================================================
case "$INTENT" in
    reveal)
        MOVEMENT="Slow crane up and tilt down, wide establishing shot."
        LIGHTING="Volumetric god rays, golden hour atmosphere, warm bloom."
        OPTICS="Deep focus, anamorphic widescreen, ultra-high clarity."
        ;;
    tense)
        MOVEMENT="Handheld jittery movement, dutch angle close-up, unstable framing."
        LIGHTING="Low key, harsh shadows, flickering magenta neon, split lighting."
        OPTICS="Shallow depth of field, anamorphic lens flare, slight motion blur."
        ;;
    epic)
        MOVEMENT="Dolly in with circular orbit, low hero angle, sweeping arc."
        LIGHTING="Dramatic rim lighting, high contrast cinematic grade, specular highlights."
        OPTICS="Anamorphic 35mm, sharp focus on subject, chromatic aberration edges."
        ;;
    narrative)
        MOVEMENT="Smooth tracking shot following subject, natural Steadicam motion."
        LIGHTING="Natural soft light, blue hour tones, practical light sources."
        OPTICS="Standard 50mm, realistic bokeh, minimal distortion."
        ;;
    product)
        MOVEMENT="Static camera with slow macro orbit, precision product reveal."
        LIGHTING="Perfect even exposure, specular highlights on product surface."
        OPTICS="Macro lens, zero distortion, commercial grade clarity."
        ;;
    educational)
        MOVEMENT="Slow push in, clinical camera movements, no handheld jitter."
        LIGHTING="Even neutral lighting, high clarity, no dramatic shadows."
        OPTICS="Standard lens, deep focus, semi-transparent CGI visualization."
        ;;
    comedy)
        MOVEMENT="Reactive handheld, punchy cuts, exaggerated zooms."
        LIGHTING="Bright even lighting, warm comedic tone, no harsh shadows."
        OPTICS="Slight wide angle, expressive framing, snappy focus pulls."
        ;;
    fpv)
        MOVEMENT="Immersive first-person POV, continuous forward motion at eye level, slight natural stabilization with GoPro-style wide angle. No cuts throughout."
        LIGHTING="Natural ambient light matching environment, subtle lens flare, peripheral depth-of-field blur."
        OPTICS="Ultra-wide fisheye-adjacent lens, slight barrel distortion, high motion clarity, natural vignette edges."
        ;;
    drone)
        MOVEMENT="Cinematic aerial drone shot, smooth gimbal-stabilized descent from high altitude, sweeping lateral arc resolving into establishing medium shot. DJI Inspire aesthetic."
        LIGHTING="Golden hour atmosphere, long directional shadows across terrain, volumetric haze on horizon."
        OPTICS="Wide-angle aerial lens, deep focus across entire frame, high altitude clarity, natural atmospheric haze."
        ;;
    flythrough)
        MOVEMENT="Continuous ground-level architectural dolly-through, seamless forward movement through connected spaces. One-take no-cut trajectory."
        LIGHTING="Practical interior lighting with natural window light spill, soft even exposure transitions between zones."
        OPTICS="Wide-angle rectilinear lens, deep focus, minimal distortion, smooth exposure transitions."
        ;;
    *)
        MOVEMENT="Smooth cinematic pan, balanced stable framing."
        LIGHTING="Natural studio lighting, balanced highlights and shadows."
        OPTICS="Standard cinematic lens, high-fidelity optics."
        ;;
esac

# ============================================================
# Helper: upload a local file — prints CDN URL to stdout, errors to stderr
# Returns 1 on failure (caller should handle with || exit 1)
# ============================================================
upload_file() {
    local FPATH="$1"
    if [ ! -f "$FPATH" ]; then
        echo "Error: File not found: $FPATH" >&2
        return 1
    fi
    [ "$JSON_ONLY" = false ] && echo "Uploading $(basename "$FPATH")..." >&2
    local RESP URL
    RESP=$(curl -s -X POST "${MUAPI_BASE}/upload_file" \
        -H "x-api-key: $MUAPI_KEY" \
        -F "file=@${FPATH}")
    URL=$(echo "$RESP" | jq -r '.url // empty')
    if [ -z "$URL" ]; then
        echo "Error: Upload failed for $(basename "$FPATH"): $(echo "$RESP" | jq -r '.error // .detail // "unknown"')" >&2
        return 1
    fi
    echo "$URL"
}

# ============================================================
# Helper: build a JSON array string from positional args
# Usage: build_json_array "${MY_ARRAY[@]}"   — empty array safe
# ============================================================
build_json_array() {
    local JSON="[" i=0 elem
    for elem in "$@"; do
        [ "$i" -gt 0 ] && JSON="${JSON},"
        JSON="${JSON}\"${elem}\""
        i=$(( i + 1 ))
    done
    echo "${JSON}]"
}

# ============================================================
# Helper: JSON-encode a string (handles quotes, backslashes, newlines)
# Usage: echo "text" | json_string
# ============================================================
json_string() {
    python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().rstrip()))'
}

# ============================================================
# Helper: poll predictions/<id>/result until completed or failed
# Prints final JSON to stdout; status lines go to stderr.
# ============================================================
poll_result() {
    local REQ_ID="$1"
    local ELAPSED=0 LAST_STATUS="" RESULT STATUS URL EXT OUTPUT_DIR TEMP_FILE

    while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
        sleep "$POLL_INTERVAL"
        ELAPSED=$(( ELAPSED + POLL_INTERVAL ))

        RESULT=$(curl -s -X GET "${MUAPI_BASE}/predictions/${REQ_ID}/result" \
            -H "x-api-key: $MUAPI_KEY" \
            -H "Content-Type: application/json")

        STATUS=$(echo "$RESULT" | jq -r '.status // "unknown"')

        if [ "$STATUS" != "$LAST_STATUS" ] && [ "$JSON_ONLY" = false ]; then
            echo "Status: $STATUS (${ELAPSED}s elapsed)" >&2
            LAST_STATUS="$STATUS"
        fi

        if [ "$STATUS" = "completed" ]; then
            URL=$(echo "$RESULT" | jq -r '.outputs[0] // empty')
            [ "$JSON_ONLY" = false ] && echo "Done! Output: $URL" >&2
            if [ "$VIEW" = true ] && [ -n "$URL" ]; then
                EXT="${URL##*.}"
                # Detect non-extension fragment (query strings, etc.) → default mp4
                case "$EXT" in
                    mp4|mov|webm|jpg|jpeg|png|gif|webp) ;;
                    *) EXT="mp4" ;;
                esac
                OUTPUT_DIR="$(dirname "$0")/../../../../media_outputs"
                mkdir -p "$OUTPUT_DIR"
                TEMP_FILE="$OUTPUT_DIR/muapi_$(date +%s).$EXT"
                [ "$JSON_ONLY" = false ] && echo "Downloading → $TEMP_FILE" >&2
                curl -s -o "$TEMP_FILE" "$URL"
                [[ "$OSTYPE" == "darwin"* ]] && open "$TEMP_FILE"
            fi
            echo "$RESULT"
            return 0

        elif [ "$STATUS" = "failed" ]; then
            echo "Error: Job failed — $(echo "$RESULT" | jq -r '.output.error // .error // "unknown"')" >&2
            echo "$RESULT"
            return 1
        fi
    done

    echo "Error: Timeout after ${MAX_WAIT}s for request_id=$REQ_ID" >&2
    return 1
}

# ============================================================
# Helper: submit JSON payload to endpoint, then poll (or return async)
# Usage: submit_and_poll ENDPOINT PAYLOAD [LABEL]
# ============================================================
submit_and_poll() {
    local ENDPOINT="$1"
    local PAYLOAD="$2"
    local LABEL="${3:-$1}"
    local SUBMIT API_ERROR REQUEST_ID

    [ "$JSON_ONLY" = false ] && echo "Submitting to $LABEL..." >&2

    SUBMIT=$(curl -s -X POST "${MUAPI_BASE}/${ENDPOINT}" "${HEADERS[@]}" -d "$PAYLOAD")

    API_ERROR=$(echo "$SUBMIT" | jq -r '.error // .detail // empty')
    if [ -n "$API_ERROR" ]; then
        echo "Error: $API_ERROR" >&2
        echo "$SUBMIT" >&2
        exit 1
    fi

    REQUEST_ID=$(echo "$SUBMIT" | jq -r '.request_id // empty')
    if [ -z "$REQUEST_ID" ]; then
        echo "Error: No request_id returned from $ENDPOINT" >&2
        echo "$SUBMIT" >&2
        exit 1
    fi

    [ "$JSON_ONLY" = false ] && echo "Request ID: $REQUEST_ID" >&2

    if [ "$ASYNC" = true ]; then
        echo "$SUBMIT"
        exit 0
    fi

    [ "$JSON_ONLY" = false ] && echo "Waiting for completion..." >&2
    poll_result "$REQUEST_ID"
}

# ============================================================
# MODE: t2v — Text-to-Video
#
# Chinese: seedance-v2.0-t2v          (16:9/9:16/4:3/3:4, quality, duration 5|10|15)
# Global:  seedance-2-text-to-video{-fast}    (+ 21:9/1:1, any 4–15s, no quality)
# VIP:     seedance-2-vip-text-to-video{-fast}
# ============================================================
if [ "$MODE" = "t2v" ]; then
    [ -z "$SUBJECT" ] && { echo "Error: --subject is required for t2v." >&2; exit 1; }

    DIRECTOR_PROMPT="[SCENE] $SUBJECT. [LIGHTING] $LIGHTING [ACTION] Fluid continuous motion. [CAMERA] $MOVEMENT [STYLE] $OPTICS High-fidelity production grade, 24fps. Maintain high character consistency, zero flicker."

    if [ "$TIER" = "chinese" ]; then
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
        CORE_SCRIPT="$SCRIPT_DIR/../../../../core/media/generate-video.sh"
        [ ! -f "$CORE_SCRIPT" ] && { echo "Error: Core script not found at $CORE_SCRIPT" >&2; exit 1; }

        VIEW_FLAG="";   [ "$VIEW" = true ]      && VIEW_FLAG="--view"
        ASYNC_FLAG="";  [ "$ASYNC" = true ]     && ASYNC_FLAG="--async"
        JSON_FLAG="";   [ "$JSON_ONLY" = true ] && JSON_FLAG="--json"

        # shellcheck disable=SC2086
        bash "$CORE_SCRIPT" \
            --prompt "$DIRECTOR_PROMPT" \
            --model "seedance-v2.0-t2v" \
            --aspect-ratio "$ASPECT" \
            --duration "$DURATION" \
            $AUDIO_FLAG $VIEW_FLAG $ASYNC_FLAG $JSON_FLAG
    else
        PROMPT_JSON=$(echo "$DIRECTOR_PROMPT" | json_string)
        [ "$TIER" = "vip" ] && ENDPOINT="seedance-2-vip-text-to-video" || ENDPOINT="seedance-2-text-to-video"
        [ "$FAST" = true ]  && ENDPOINT="${ENDPOINT}-fast"
        PAYLOAD="{\"prompt\": $PROMPT_JSON, \"aspect_ratio\": \"$ASPECT\", \"duration\": $DURATION}"
        submit_and_poll "$ENDPOINT" "$PAYLOAD"
    fi

# ============================================================
# MODE: i2v — Image-to-Video
#
# Chinese: seedance-v2.0-i2v   (images_list + videos_list + audios_list, quality)
# Global:  seedance-2-image-to-video{-fast}   (1 img=first frame, 2-9=omni ref; no quality)
# VIP:     seedance-2-vip-image-to-video{-fast}
# ============================================================
elif [ "$MODE" = "i2v" ]; then
    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done
    for FPATH in "${VIDEO_FILES[@]+"${VIDEO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; VIDEO_URLS+=("$URL")
    done
    for FPATH in "${AUDIO_FILES[@]+"${AUDIO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; AUDIO_URLS+=("$URL")
    done

    [ ${#IMAGE_URLS[@]} -eq 0 ] && { echo "Error: At least one --image or --file is required for i2v." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 9 ] && { echo "Error: Maximum 9 images allowed." >&2; exit 1; }

    if [ -n "$SUBJECT" ]; then
        DIRECTOR_PROMPT="[ACTION] $SUBJECT. [CAMERA] $MOVEMENT [STYLE] $OPTICS Fluid continuous motion. Maintain high character consistency, zero flicker."
    else
        DIRECTOR_PROMPT="[CAMERA] $MOVEMENT [STYLE] $OPTICS Fluid continuous motion. Animate the provided image with cinematic realism."
    fi
    PROMPT_JSON=$(echo "$DIRECTOR_PROMPT" | json_string)
    IMAGES_JSON=$(build_json_array "${IMAGE_URLS[@]}")

    if [ "$TIER" = "chinese" ]; then
        [ ${#VIDEO_URLS[@]} -gt 3 ] && { echo "Error: Maximum 3 reference videos allowed." >&2; exit 1; }
        [ ${#AUDIO_URLS[@]} -gt 3 ] && { echo "Error: Maximum 3 reference audio files allowed." >&2; exit 1; }

        PAYLOAD="{\"prompt\": $PROMPT_JSON, \"images_list\": $IMAGES_JSON, \"aspect_ratio\": \"$ASPECT\", \"duration\": $DURATION, \"quality\": \"$QUALITY\""
        [ ${#VIDEO_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"videos_list\": $(build_json_array "${VIDEO_URLS[@]}")"
        [ ${#AUDIO_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"audios_list\": $(build_json_array "${AUDIO_URLS[@]}")"
        PAYLOAD="${PAYLOAD}}"
        submit_and_poll "seedance-v2.0-i2v" "$PAYLOAD" "seedance-v2.0-i2v (${#IMAGE_URLS[@]} image(s))"
    else
        [ "$TIER" = "vip" ] && ENDPOINT="seedance-2-vip-image-to-video" || ENDPOINT="seedance-2-image-to-video"
        [ "$FAST" = true ]  && ENDPOINT="${ENDPOINT}-fast"
        PAYLOAD="{\"prompt\": $PROMPT_JSON, \"images_list\": $IMAGES_JSON, \"duration\": $DURATION}"
        submit_and_poll "$ENDPOINT" "$PAYLOAD" "$ENDPOINT (${#IMAGE_URLS[@]} image(s))"
    fi

# ============================================================
# MODE: extend — Extend a Seedance 2.0 video (Chinese tier)
# Endpoint: seedance-v2.0-extend
# ============================================================
elif [ "$MODE" = "extend" ]; then
    [ -z "$EXTEND_REQUEST_ID" ] && { echo "Error: --request-id is required for extend." >&2; exit 1; }

    if [ -n "$SUBJECT" ]; then
        EXT_PROMPT="[CONTINUATION] $SUBJECT. [CAMERA] $MOVEMENT [STYLE] $OPTICS Seamless continuation of previous scene."
        PROMPT_JSON=$(echo "$EXT_PROMPT" | json_string)
        PAYLOAD="{\"request_id\": \"$EXTEND_REQUEST_ID\", \"prompt\": $PROMPT_JSON, \"duration\": $DURATION, \"quality\": \"$QUALITY\"}"
    else
        PAYLOAD="{\"request_id\": \"$EXTEND_REQUEST_ID\", \"duration\": $DURATION, \"quality\": \"$QUALITY\"}"
    fi

    submit_and_poll "seedance-v2.0-extend" "$PAYLOAD"

# ============================================================
# MODE: first-last — First & Last Frame interpolation (Global/VIP only)
#
# Global: seedance-2-first-last-frame{-fast}    (1 img=anchor, 2 imgs=first+last)
# VIP:    seedance-2-vip-first-last-frame{-fast}
# Note:   Aspect ratio is inferred from the reference image.
# ============================================================
elif [ "$MODE" = "first-last" ]; then
    [ "$TIER" = "chinese" ] && { echo "Error: --mode first-last requires --tier global or --tier vip." >&2; exit 1; }

    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done

    [ ${#IMAGE_URLS[@]} -eq 0 ] && { echo "Error: At least 1 --image or --file required for first-last." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 2 ] && { echo "Error: first-last accepts 1 (anchor) or 2 (first+last) images." >&2; exit 1; }

    IMAGES_JSON=$(build_json_array "${IMAGE_URLS[@]}")
    PROMPT_JSON=$(echo "$SUBJECT" | json_string)

    [ "$TIER" = "vip" ] && ENDPOINT="seedance-2-vip-first-last-frame" || ENDPOINT="seedance-2-first-last-frame"
    [ "$FAST" = true ]  && ENDPOINT="${ENDPOINT}-fast"

    PAYLOAD="{\"prompt\": $PROMPT_JSON, \"images_list\": $IMAGES_JSON, \"duration\": $DURATION}"
    submit_and_poll "$ENDPOINT" "$PAYLOAD" "$ENDPOINT (${#IMAGE_URLS[@]} frame(s))"

# ============================================================
# MODE: omni — Omni Reference (full multimodal)
#
# Chinese: seedance-2.0-omni-reference
#   params: images_list, video_files, audio_files, aspect_ratio, duration, quality
#   tags:   @image1…@image9, @video1…@video3, @audio1…@audio3
#   also:   @character:<request_id>, @omni-character:<character_id>
#
# Global:  seedance-2-omni-reference-no-video{-fast}
#   params: images_list, audio_files, aspect_ratio, duration  (no video, no quality)
#
# VIP:     seedance-2-vip-omni-reference{-fast}
#   params: images_list, audio_files, aspect_ratio, duration  (no video, no quality)
# ============================================================
elif [ "$MODE" = "omni" ]; then
    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done
    for FPATH in "${VIDEO_FILES[@]+"${VIDEO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; VIDEO_URLS+=("$URL")
    done
    for FPATH in "${AUDIO_FILES[@]+"${AUDIO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; AUDIO_URLS+=("$URL")
    done

    [ -z "$SUBJECT" ]           && { echo "Error: --subject is required for omni." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 9 ] && { echo "Error: Maximum 9 images allowed." >&2; exit 1; }
    [ ${#VIDEO_URLS[@]} -gt 3 ] && { echo "Error: Maximum 3 reference videos allowed." >&2; exit 1; }
    [ ${#AUDIO_URLS[@]} -gt 3 ] && { echo "Error: Maximum 3 reference audio files allowed." >&2; exit 1; }

    PROMPT_JSON=$(echo "$SUBJECT" | json_string)

    if [ "$TIER" = "chinese" ]; then
        PAYLOAD="{\"prompt\": $PROMPT_JSON, \"aspect_ratio\": \"$ASPECT\", \"duration\": $DURATION, \"quality\": \"$QUALITY\""
        [ ${#IMAGE_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"images_list\": $(build_json_array "${IMAGE_URLS[@]}")"
        [ ${#VIDEO_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"video_files\": $(build_json_array "${VIDEO_URLS[@]}")"
        [ ${#AUDIO_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"audio_files\": $(build_json_array "${AUDIO_URLS[@]}")"
        PAYLOAD="${PAYLOAD}}"
        submit_and_poll "seedance-2.0-omni-reference" "$PAYLOAD" "seedance-v2.0-omni-reference"
    else
        if [ ${#VIDEO_URLS[@]} -gt 0 ]; then
            echo "Warning: $TIER omni does not support video references — ignoring --video-url/--video-file." >&2
        fi
        [ "$TIER" = "vip" ] && ENDPOINT="seedance-2-vip-omni-reference" || ENDPOINT="seedance-2-omni-reference-no-video"
        [ "$FAST" = true ]  && ENDPOINT="${ENDPOINT}-fast"
        PAYLOAD="{\"prompt\": $PROMPT_JSON, \"aspect_ratio\": \"$ASPECT\", \"duration\": $DURATION"
        [ ${#IMAGE_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"images_list\": $(build_json_array "${IMAGE_URLS[@]}")"
        [ ${#AUDIO_URLS[@]} -gt 0 ] && PAYLOAD="${PAYLOAD}, \"audio_files\": $(build_json_array "${AUDIO_URLS[@]}")"
        PAYLOAD="${PAYLOAD}}"
        submit_and_poll "$ENDPOINT" "$PAYLOAD"
    fi

# ============================================================
# MODE: omni-train — Train a custom Omni Reference character
# Endpoint: seedance-2-omni-reference-train
# Params:   image_url (single portrait), character_name, description
# Output:   character_id — reference as @omni-character:<character_id>
# ============================================================
elif [ "$MODE" = "omni-train" ]; then
    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done

    [ ${#IMAGE_URLS[@]} -eq 0 ] && { echo "Error: Exactly 1 --image or --file required for omni-train." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 1 ] && { echo "Error: omni-train accepts only 1 reference image." >&2; exit 1; }

    PAYLOAD="{\"image_url\": \"${IMAGE_URLS[0]}\""
    if [ -n "$CHARACTER_NAME" ]; then
        NAME_JSON=$(echo "$CHARACTER_NAME" | json_string)
        PAYLOAD="${PAYLOAD}, \"character_name\": $NAME_JSON"
    fi
    if [ -n "$CHARACTER_DESC" ]; then
        DESC_JSON=$(echo "$CHARACTER_DESC" | json_string)
        PAYLOAD="${PAYLOAD}, \"description\": $DESC_JSON"
    fi
    PAYLOAD="${PAYLOAD}}"

    [ "$JSON_ONLY" = false ] && echo "Submitting omni-reference-train..." >&2
    SUBMIT=$(curl -s -X POST "${MUAPI_BASE}/seedance-2-omni-reference-train" "${HEADERS[@]}" -d "$PAYLOAD")

    API_ERROR=$(echo "$SUBMIT" | jq -r '.error // .detail // empty')
    if [ -n "$API_ERROR" ]; then
        echo "Error: $API_ERROR" >&2; echo "$SUBMIT" >&2; exit 1
    fi

    REQUEST_ID=$(echo "$SUBMIT" | jq -r '.request_id // empty')
    if [ -z "$REQUEST_ID" ]; then
        echo "Error: No request_id in response" >&2; echo "$SUBMIT" >&2; exit 1
    fi

    [ "$JSON_ONLY" = false ] && echo "Request ID: $REQUEST_ID" >&2
    [ "$JSON_ONLY" = false ] && echo "Training started — use @omni-character:<character_id> once complete." >&2

    if [ "$ASYNC" = true ]; then echo "$SUBMIT"; exit 0; fi

    [ "$JSON_ONLY" = false ] && echo "Waiting for training to complete..." >&2
    RESULT=$(poll_result "$REQUEST_ID")
    echo "$RESULT"
    CHAR_ID=$(echo "$RESULT" | jq -r '.outputs[0] // empty')
    if [ "$JSON_ONLY" = false ] && [ -n "$CHAR_ID" ]; then
        echo "Character trained! Reference as: @omni-character:$CHAR_ID" >&2
    fi

# ============================================================
# MODE: character — Build a reusable character sheet from 1–3 images
# Endpoint: seedance-2-character
# Params:   images_list (1–3), prompt (outfit description), character_name
# Output:   request_id — reference as @character:<request_id>
# ============================================================
elif [ "$MODE" = "character" ]; then
    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done

    [ ${#IMAGE_URLS[@]} -eq 0 ] && { echo "Error: At least 1 --image or --file required for character." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 3 ] && { echo "Error: Maximum 3 reference images for character training." >&2; exit 1; }

    IMAGES_JSON=$(build_json_array "${IMAGE_URLS[@]}")
    PAYLOAD="{\"images_list\": $IMAGES_JSON"
    if [ -n "$SUBJECT" ]; then
        OUTFIT_JSON=$(echo "$SUBJECT" | json_string)
        PAYLOAD="${PAYLOAD}, \"prompt\": $OUTFIT_JSON"
    fi
    if [ -n "$CHARACTER_NAME" ]; then
        NAME_JSON=$(echo "$CHARACTER_NAME" | json_string)
        PAYLOAD="${PAYLOAD}, \"character_name\": $NAME_JSON"
    fi
    PAYLOAD="${PAYLOAD}}"

    [ "$JSON_ONLY" = false ] && echo "Submitting character training (${#IMAGE_URLS[@]} image(s))..." >&2
    SUBMIT=$(curl -s -X POST "${MUAPI_BASE}/seedance-2-character" "${HEADERS[@]}" -d "$PAYLOAD")

    API_ERROR=$(echo "$SUBMIT" | jq -r '.error // .detail // empty')
    if [ -n "$API_ERROR" ]; then
        echo "Error: $API_ERROR" >&2; echo "$SUBMIT" >&2; exit 1
    fi

    REQUEST_ID=$(echo "$SUBMIT" | jq -r '.request_id // empty')
    if [ -z "$REQUEST_ID" ]; then
        echo "Error: No request_id in response" >&2; echo "$SUBMIT" >&2; exit 1
    fi

    [ "$JSON_ONLY" = false ] && echo "Request ID: $REQUEST_ID" >&2
    [ "$JSON_ONLY" = false ] && echo "Use in prompts as: @character:$REQUEST_ID" >&2

    if [ "$ASYNC" = true ]; then echo "$SUBMIT"; exit 0; fi

    [ "$JSON_ONLY" = false ] && echo "Waiting for character sheet to complete..." >&2
    poll_result "$REQUEST_ID"

# ============================================================
# MODE: video-edit — Edit a video with a prompt + optional reference images
# Endpoint: seedance-v2.0-video-edit
# Params:   prompt, video_urls (1 max, 10MB/15s), images_list (up to 9),
#           aspect_ratio, quality, remove_watermark
# ============================================================
elif [ "$MODE" = "video-edit" ]; then
    for FPATH in "${IMAGE_FILES[@]+"${IMAGE_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; IMAGE_URLS+=("$URL")
    done
    for FPATH in "${VIDEO_FILES[@]+"${VIDEO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; VIDEO_URLS+=("$URL")
    done

    [ -z "$SUBJECT" ]            && { echo "Error: --subject (edit prompt) is required for video-edit." >&2; exit 1; }
    [ ${#VIDEO_URLS[@]} -eq 0 ]  && { echo "Error: --video-url or --video-file is required for video-edit." >&2; exit 1; }
    [ ${#VIDEO_URLS[@]} -gt 1 ]  && { echo "Error: video-edit supports 1 source video only (max 10MB, 15s)." >&2; exit 1; }
    [ ${#IMAGE_URLS[@]} -gt 9 ]  && { echo "Error: Maximum 9 reference images allowed." >&2; exit 1; }

    PROMPT_JSON=$(echo "$SUBJECT" | json_string)
    PAYLOAD="{\"prompt\": $PROMPT_JSON, \"video_urls\": [\"${VIDEO_URLS[0]}\"], \"aspect_ratio\": \"$ASPECT\", \"quality\": \"$QUALITY\""
    [ ${#IMAGE_URLS[@]} -gt 0 ]  && PAYLOAD="${PAYLOAD}, \"images_list\": $(build_json_array "${IMAGE_URLS[@]}")"
    [ "$REMOVE_WATERMARK" = true ] && PAYLOAD="${PAYLOAD}, \"remove_watermark\": true"
    PAYLOAD="${PAYLOAD}}"

    submit_and_poll "seedance-v2.0-video-edit" "$PAYLOAD"

# ============================================================
# MODE: watermark-remove — Strip watermark from a Seedance 2.0 video
#
# Basic: seedance-2.0-watermark-remover
# Pro:   seedance-2-video-watermark-remover-pro  (--pro flag; up to 100MB)
# ============================================================
elif [ "$MODE" = "watermark-remove" ]; then
    for FPATH in "${VIDEO_FILES[@]+"${VIDEO_FILES[@]}"}"; do
        URL=$(upload_file "$FPATH") || exit 1; VIDEO_URLS+=("$URL")
    done

    [ ${#VIDEO_URLS[@]} -eq 0 ] && { echo "Error: --video-url or --video-file is required for watermark-remove." >&2; exit 1; }

    PAYLOAD="{\"video_url\": \"${VIDEO_URLS[0]}\"}"

    if [ "$PRO_WATERMARK" = true ]; then
        submit_and_poll "seedance-2-video-watermark-remover-pro" "$PAYLOAD"
    else
        submit_and_poll "seedance-2.0-watermark-remover" "$PAYLOAD"
    fi

else
    echo "Error: Unknown mode '$MODE'." >&2
    echo "Valid: t2v | i2v | extend | first-last | omni | omni-train | character | video-edit | watermark-remove" >&2
    exit 1
fi
