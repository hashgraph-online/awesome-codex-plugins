#!/usr/bin/env bash
# gif2web.sh - turn a GIF into an animated WebP and an MP4, then print a size report.
#
# Usage: gif2web.sh <in.gif> [out_dir] [--loops N] [--bg COLOR] [--quality Q] [--crf N]
#   out_dir      where to write <name>.webp and <name>.mp4 (default: next to the GIF)
#   --loops N    how many times the loop plays in the MP4 (default 3). An MP4 has no loop flag;
#                a page can still loop it with <video loop>.
#   --bg COLOR   background for the MP4, which has no alpha (default white; any ffmpeg colour or 0xRRGGBB)
#   --quality Q  WebP quality 1-100 (default 80)
#   --crf N      H.264 quality for the MP4, lower = better and bigger (default 23)
#
# Needs ffmpeg + ffprobe. The WebP comes from the first tool found: ffmpeg with libwebp_anim,
# gif2webp (libwebp tools) or ImageMagick 7 (magick) with WebP support.
# Force one with GIF2WEB_WEBP=ffmpeg|gif2webp|magick.
set -euo pipefail

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

[ $# -ge 1 ] || usage 1
case "$1" in -h|--help) usage 0 ;; esac
IN="$1"; shift
OUT_DIR=""
LOOPS=3
BG="white"
QUALITY=80
CRF=23
while [ $# -gt 0 ]; do
  case "$1" in
    --loops) LOOPS="$2"; shift 2 ;;
    --bg) BG="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    --crf) CRF="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    -*) echo "unknown option: $1" >&2; usage 1 ;;
    *) OUT_DIR="$1"; shift ;;
  esac
done

[ -f "$IN" ] || { echo "no such file: $IN" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is required" >&2; exit 1; }
command -v ffprobe >/dev/null || { echo "ffprobe is required" >&2; exit 1; }
case "$LOOPS" in ''|*[!0-9]*) echo "--loops must be a whole number" >&2; exit 1 ;; esac
[ "$LOOPS" -ge 1 ] || LOOPS=1

[ -n "$OUT_DIR" ] || OUT_DIR="$(dirname "$IN")"
mkdir -p "$OUT_DIR"
NAME="$(basename "$IN")"; NAME="${NAME%.*}"
WEBP="$OUT_DIR/$NAME.webp"
MP4="$OUT_DIR/$NAME.mp4"

bytes() { wc -c < "$1" | tr -d ' '; }
kb() { awk -v b="$1" 'BEGIN { printf "%.0f KB", b / 1024 }'; }
pct() { awk -v a="$1" -v b="$2" 'BEGIN { printf "%.0f%%", 100 * a / b }'; }

read -r W H FRAMES < <(ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=width,height,nb_read_frames -of csv=p=0 "$IN" | tr ',' ' ')
DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$IN")
TOTAL=$(awk -v d="$DUR" -v n="$LOOPS" 'BEGIN { printf "%.3f", d * n }')

# --- animated WebP ---------------------------------------------------------
pick_webp_tool() {
  if [ -n "${GIF2WEB_WEBP:-}" ]; then echo "$GIF2WEB_WEBP"; return; fi
  if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libwebp_anim; then echo ffmpeg; return; fi
  if command -v gif2webp >/dev/null; then echo gif2webp; return; fi
  if command -v magick >/dev/null && magick -list format 2>/dev/null | grep -qi '^ *WEBP'; then echo magick; return; fi
  echo none
}
TOOL=$(pick_webp_tool)
case "$TOOL" in
  ffmpeg)   ffmpeg -y -v error -i "$IN" -c:v libwebp_anim -lossless 0 -q:v "$QUALITY" \
              -compression_level 6 -loop 0 "$WEBP" ;;
  gif2webp) gif2webp -quiet -mixed -q "$QUALITY" -m 6 "$IN" -o "$WEBP" ;;
  magick)   magick "$IN" -coalesce -quality "$QUALITY" -define webp:method=6 -loop 0 "$WEBP" ;;
  *)        echo "no WebP encoder found (need ffmpeg with libwebp, gif2webp or magick)" >&2; TOOL="" ;;
esac

# --- MP4 (H.264, yuv420p, even size, alpha flattened onto --bg) -------------
# tpad holds the last frame so the final loop keeps its full length; -t cuts at exactly N loops.
EW=$(( W / 2 * 2 )); EH=$(( H / 2 * 2 ))
ffmpeg -y -v error -i "$IN" -filter_complex \
  "[0:v]loop=loop=$((LOOPS - 1)):size=32767:start=0,tpad=stop_mode=clone:stop_duration=2,format=rgba,crop=$EW:$EH:0:0[fg];\
color=c=$BG:s=${EW}x${EH}:r=50[bg];[bg][fg]overlay=shortest=1:format=auto,format=yuv420p[v]" \
  -map "[v]" -t "$TOTAL" -c:v libx264 -preset slow -crf "$CRF" -movflags +faststart -an "$MP4"

# --- report -----------------------------------------------------------------
GB=$(bytes "$IN")
echo "GIF   $IN"
echo "      ${W}x${H}, $FRAMES frames, $(printf '%.2f' "$DUR") s per loop, $(kb "$GB")"
if [ -n "$TOOL" ] && [ -f "$WEBP" ]; then
  WB=$(bytes "$WEBP")
  echo "WebP  $WEBP  $(kb "$WB")  ($(pct "$WB" "$GB") of the GIF, via $TOOL, quality $QUALITY)"
fi
MB=$(bytes "$MP4")
MD=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$MP4")
echo "MP4   $MP4  $(kb "$MB")  ($(pct "$MB" "$GB") of the GIF, $(printf '%.2f' "$MD") s = $LOOPS loop(s), crf $CRF, bg $BG)"
