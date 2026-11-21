#!/usr/bin/env bash
# finish.sh: turn a rough render (MP4/MOV or a folder of PNG frames) into a
# delivery-ready MP4: exact size, frame rate, duration, H.264 + AAC, loudness.
#
#   finish.sh --in render.mp4 --out final.mp4 --seconds 12
#   finish.sh --in frames/ --out final.mp4 --seconds 8 --audio bed.wav
#
# Options
#   --in PATH        video file, or a folder of numbered PNGs (0001.png ...)
#   --out PATH       output MP4 (default final.mp4)
#   --seconds N      exact duration of the result (required)
#   --fps N          frame rate (default 30)
#   --size WxH       frame size (default 1920x1080); the picture is fitted, never stretched
#   --audio PATH     soundtrack to lay under the picture (replaces any audio in --in)
#   --keep-audio     keep the audio already inside --in
#   --lufs N         integrated loudness target (default -14)
#   --crf N          x264 quality, lower is better (default 18)
set -euo pipefail

IN="" OUT="final.mp4" SECONDS_="" FPS=30 SIZE="1920x1080" AUDIO="" KEEP=0 LUFS=-14 CRF=18
while [[ $# -gt 0 ]]; do
  case "$1" in
    --in) IN="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --seconds) SECONDS_="$2"; shift 2 ;;
    --fps) FPS="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --audio) AUDIO="$2"; shift 2 ;;
    --keep-audio) KEEP=1; shift ;;
    --lufs) LUFS="$2"; shift 2 ;;
    --crf) CRF="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "finish.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

[[ -n "$IN" && -n "$SECONDS_" ]] || { echo "finish.sh: --in and --seconds are required" >&2; exit 2; }
command -v ffmpeg >/dev/null || { echo "finish.sh: ffmpeg not found" >&2; exit 2; }
W="${SIZE%x*}" H="${SIZE#*x}"

# Picture input: a frame folder or a video file.
if [[ -d "$IN" ]]; then
  FIRST=""
  for f in "$IN"/*.png; do
    name="$(basename "$f")"
    if [[ "$name" =~ ^[0-9]+\.png$ ]] && { [[ -z "$FIRST" ]] || [[ "$name" < "$FIRST" ]]; }; then FIRST="$name"; fi
  done
  [[ -n "$FIRST" ]] || { echo "finish.sh: no numbered PNGs in $IN" >&2; exit 2; }
  DIGITS="${#FIRST}"; DIGITS=$((DIGITS - 4))
  START="$((10#${FIRST%.png}))"
  VIN=(-framerate "$FPS" -start_number "$START" -i "$IN/%0${DIGITS}d.png")
else
  [[ -f "$IN" ]] || { echo "finish.sh: $IN not found" >&2; exit 2; }
  VIN=(-i "$IN")
fi

# Fit inside the frame, pad the rest, hold the last frame if the render is short.
VF="scale=${W}:${H}:force_original_aspect_ratio=decrease:flags=lanczos,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},tpad=stop_mode=clone:stop_duration=${SECONDS_},format=yuv420p"
# Loudness: a soft limiter tames sharp hits (so short, peaky beds can still reach the target),
# then two-pass loudnorm: measure first, then apply linearly with the measured values. Single-pass
# loudnorm undershoots on short clips because it needs several seconds of look-ahead.
PRE="alimiter=limit=0.5:level=disabled"
TAIL="aresample=48000,apad,atrim=0:${SECONDS_},afade=t=out:st=$(awk "BEGIN{print ${SECONDS_}-0.4}"):d=0.4"
loudness_core() {  # loudness_core <input file> -> the normalising part of the chain ("" for silence)
  local m val k f="${PRE},loudnorm=I=${LUFS}:TP=-1.5:LRA=11"
  m="$(ffmpeg -hide_banner -nostats -t "$SECONDS_" -i "$1" -vn -af "${PRE},loudnorm=I=${LUFS}:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | awk '/^\{/,/^\}/')"
  for k in input_i input_tp input_lra input_thresh target_offset; do
    val="$(printf '%s\n' "$m" | sed -n "s/.*\"$k\" : \"\([^\"]*\)\".*/\1/p")"
    case "$val" in
      *inf*|*nan*) echo ""; return ;;                              # silent input: nothing to normalise
      "") echo "${PRE},loudnorm=I=${LUFS}:TP=-1.5:LRA=11"; return ;;
    esac
    case "$k" in
      input_i) f="$f:measured_I=$val" ;; input_tp) f="$f:measured_TP=$val" ;;
      input_lra) f="$f:measured_LRA=$val" ;; input_thresh) f="$f:measured_thresh=$val" ;;
      target_offset) f="$f:offset=$val" ;;
    esac
  done
  echo "$f:linear=true"
}

measured_i() {  # measured_i <input file> <chain> -> integrated loudness of the chain's output
  ffmpeg -hide_banner -nostats -t "$SECONDS_" -i "$1" -vn -af "$2,ebur128" -f null - 2>&1 \
    | awk '/Integrated loudness:/{f=1} f && /I:/{print $2; exit}'
}

loudness_filter() {  # loudness_filter <input file> -> prints the full -af chain
  # Peaky material (sparse hits, chimes) can need more gain than loudnorm's true-peak limit allows; it
  # then falls back to dynamic mode and lands short. Measure the result and close the gap through a
  # brick-wall limiter, at most twice, so the file reaches the target with peaks held under -1 dBTP.
  local core i d round
  core="$(loudness_core "$1")"
  [[ -n "$core" ]] || { echo "${TAIL}"; return; }
  for round in 1 2; do
    i="$(measured_i "$1" "$core")"
    d="$(awk -v t="$LUFS" -v i="$i" 'BEGIN{ if (i=="" || i ~ /inf|nan/) {print "0"; exit} d=t-i; if (d<0.5 && d>-0.5) print "0"; else printf "%.2f", d }')"
    [[ "$d" == 0 ]] && break
    core="${core},volume=${d}dB,alimiter=limit=0.79:level=disabled"
  done
  echo "${core},${TAIL}"
}

if [[ -n "$AUDIO" ]]; then
  AF="$(loudness_filter "$AUDIO")"
  ffmpeg -v error -y "${VIN[@]}" -i "$AUDIO" -map 0:v:0 -map 1:a:0 -vf "$VF" -af "$AF" \
    -t "$SECONDS_" -c:v libx264 -preset slow -crf "$CRF" -profile:v high -r "$FPS" \
    -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT"
elif [[ "$KEEP" == 1 ]]; then
  AF="$(loudness_filter "$IN")"
  ffmpeg -v error -y "${VIN[@]}" -map 0:v:0 -map 0:a:0 -vf "$VF" -af "$AF" \
    -t "$SECONDS_" -c:v libx264 -preset slow -crf "$CRF" -profile:v high -r "$FPS" \
    -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT"
else
  # No soundtrack: add a silent stereo track so every player and platform accepts the file.
  ffmpeg -v error -y "${VIN[@]}" -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
    -map 0:v:0 -map 1:a:0 -vf "$VF" -t "$SECONDS_" \
    -c:v libx264 -preset slow -crf "$CRF" -profile:v high -r "$FPS" \
    -c:a aac -b:a 128k -ar 48000 -ac 2 -movflags +faststart "$OUT"
fi
echo "finish.sh: wrote $OUT (${W}x${H}, ${FPS} fps, ${SECONDS_} s)"
