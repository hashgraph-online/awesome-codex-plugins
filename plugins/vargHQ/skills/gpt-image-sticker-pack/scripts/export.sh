#!/usr/bin/env bash
# export.sh - fit one animated sticker GIF to a messenger's sticker spec, then check the result.
#
# Usage: export.sh <sticker.gif> <platform> [out_dir]
#   platform: telegram | whatsapp | line | wechat | discord | slack | all
#   out_dir:  default <gif folder>/<name>_stickers
#
# Limits (checked 2026-11-05 on each platform's official docs; sources in ../SKILL.md):
#   telegram  WEBM VP9, no audio, one side 512 px, <= 256 KB, <= 3 s, <= 30 fps
#   whatsapp  animated WebP 512x512, <= 500 KB, <= 10 s, frames >= 8 ms; tray icon PNG 96x96 <= 50 KB
#   line      APNG <= 320x270 (one side >= 270), 5-20 frames, 1-4 plays, <= 4 s in all, <= 1 MB,
#             transparent; main image APNG 240x240; chat tab PNG 96x74
#   wechat    GIF 240x240 <= 500 KB, looping; cover PNG 240x240 <= 500 KB; chat icon PNG 50x50 <= 100 KB
#   discord   APNG (or GIF) 320x320, <= 512 KiB, <= 5 s
#   slack     GIF, square (128x128 here: Slack names no pixel size), < 128 KB, <= 50 frames
# KB is taken as 1,000 bytes so the files stay under the limit either way.
#
# Needs ffmpeg + ffprobe (with libvpx-vp9 for Telegram) and ImageMagick 7 (magick, with WebP for WhatsApp).
# Uses gifsicle for smaller GIFs when it is installed. Exit code 1 if any check fails.
set -euo pipefail

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
[ $# -ge 2 ] || usage 1
IN="$1"; PLATFORM="$2"; OUT_DIR="${3:-}"
[ -f "$IN" ] || { echo "no such file: $IN" >&2; exit 1; }
for t in ffmpeg ffprobe magick; do command -v "$t" >/dev/null || { echo "$t is required" >&2; exit 1; }; done

NAME="$(basename "$IN")"; NAME="${NAME%.*}"
[ -n "$OUT_DIR" ] || OUT_DIR="$(dirname "$IN")/${NAME}_stickers"
mkdir -p "$OUT_DIR"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FAILS=0

bytes() { wc -c < "$1" | tr -d ' '; }
kb() { awk -v b="$1" 'BEGIN { printf "%.0f KB", b / 1000 }'; }
check() { # check <label> <value> <op> <limit> [shown value] [shown limit]
  local label="$1" v="$2" op="$3" lim="$4" shown="${5:-$2}" showlim="${6:-$4}" ok
  ok=$(awk -v v="$v" -v l="$lim" -v op="$op" 'BEGIN {
    if (op == "<=") r = (v <= l); else if (op == ">=") r = (v >= l); else r = (v == l); print r }')
  if [ "$ok" = 1 ]; then printf "  PASS  %-22s %s (limit %s %s)\n" "$label" "$shown" "$op" "$showlim"
  else printf "  FAIL  %-22s %s (limit %s %s)\n" "$label" "$shown" "$op" "$showlim"; FAILS=$((FAILS + 1)); fi
}
note() { printf "  NOTE  %s\n" "$1"; }

# ---- read the GIF once: frames (coalesced, metadata stripped) and per-frame delays ----
magick -quiet "$IN" -coalesce -strip "$TMP/src_%03d.png"
DELAYS=()
while read -r cs; do
  [ -n "$cs" ] || continue
  [ "$cs" -gt 0 ] || cs=10            # a 0 delay plays as 100 ms in browsers
  DELAYS+=("$((cs * 10))")            # ms
done < <(magick identify -quiet -format "%T\n" "$IN")
N=${#DELAYS[@]}
LOOP_MS=0; MIN_MS=999999
for d in "${DELAYS[@]}"; do LOOP_MS=$((LOOP_MS + d)); [ "$d" -lt "$MIN_MS" ] && MIN_MS=$d; done
SRC_W=$(magick identify -quiet -format "%w" "$TMP/src_000.png")
SRC_H=$(magick identify -quiet -format "%h" "$TMP/src_000.png")
OPAQUE=$(magick identify -quiet -format "%[opaque]" "$TMP/src_000.png")
echo "input  $IN: ${SRC_W}x${SRC_H}, $N frames, loop ${LOOP_MS} ms, $(kb "$(bytes "$IN")")"
[ "$OPAQUE" = "False" ] || echo "  NOTE  the GIF has no transparent pixels; LINE needs a transparent background"

# fit_frames <w> <h> <dir>: every frame scaled to fit w x h, centred on a transparent canvas
fit_frames() {
  mkdir -p "$3"
  local f
  for f in "$TMP"/src_*.png; do
    magick -quiet "$f" -resize "${1}x${2}" -background none -gravity center -extent "${1}x${2}" \
      "$3/$(basename "$f")"
  done
}

# pick_frames <max_frames> <min_frames> <max_total_ms>: sets SEL (frame indexes) and SEL_MS (delays)
pick_frames() {
  local maxf="$1" minf="$2" maxms="$3" i k step acc
  SEL=(); SEL_MS=()
  step=1; [ "$N" -gt "$maxf" ] && step=$(( (N + maxf - 1) / maxf ))
  i=0
  while [ "$i" -lt "$N" ]; do        # keep every step-th frame; it takes the dropped frames' time
    acc=0; k=0
    while [ "$k" -lt "$step" ] && [ $((i + k)) -lt "$N" ]; do acc=$((acc + DELAYS[i + k])); k=$((k + 1)); done
    SEL+=("$i"); SEL_MS+=("$acc"); i=$((i + step))
  done
  local base=${#SEL[@]}                # too few frames: play the loop again inside the file
  while [ "${#SEL[@]}" -lt "$minf" ]; do
    for ((k = 0; k < base; k++)); do SEL+=("${SEL[k]}"); SEL_MS+=("${SEL_MS[k]}"); done
  done
  local total=0; for d in "${SEL_MS[@]}"; do total=$((total + d)); done
  if [ "$total" -gt "$maxms" ]; then  # too long: speed every frame up by the same factor
    for ((k = 0; k < ${#SEL_MS[@]}; k++)); do
      SEL_MS[k]=$(awk -v d="${SEL_MS[k]}" -v t="$total" -v m="$maxms" 'BEGIN { x = int(d * m / t / 10) * 10; if (x < 20) x = 20; print x }')
    done
  fi
  SEL_TOTAL=0; for d in "${SEL_MS[@]}"; do SEL_TOTAL=$((SEL_TOTAL + d)); done
}

# make_apng <frames_dir> <plays> <out> [pal8]: APNG from SEL / SEL_MS (plays 0 = forever)
make_apng() {
  local dir="$1" plays="$2" out="$3" pal="${4:-}" list="$TMP/list.txt" k
  echo "ffconcat version 1.0" > "$list"
  for ((k = 0; k < ${#SEL[@]}; k++)); do
    printf "file '%s'\nduration %s\n" "$dir/$(printf 'src_%03d.png' "${SEL[k]}")" \
      "$(awk -v d="${SEL_MS[k]}" 'BEGIN { printf "%.3f", d / 1000 }')" >> "$list"
  done
  if [ -n "$pal" ]; then
    ffmpeg -y -v error -f concat -safe 0 -i "$list" -vf \
      "split[a][b];[a]palettegen=reserve_transparent=1:stats_mode=full[p];[b][p]paletteuse=alpha_threshold=128" \
      -plays "$plays" -f apng "$out"
  else
    ffmpeg -y -v error -f concat -safe 0 -i "$list" -plays "$plays" -f apng "$out"
  fi
}

# shrink_gif <frames_dir> <out> <max_bytes>: looping GIF from the fitted frames, smaller until it fits
shrink_gif() {
  local dir="$1" out="$2" max="$3" colors args k
  args=()
  for ((k = 0; k < N; k++)); do args+=(-delay "$((DELAYS[k] / 10))" "$dir/$(printf 'src_%03d.png' "$k")"); done
  for colors in 256 128 64 32; do
    magick -quiet -dispose background "${args[@]}" -loop 0 -colors "$colors" -layers OptimizeTransparency "$out"
    if command -v gifsicle >/dev/null; then gifsicle -O3 --batch "$out" 2>/dev/null || true; fi
    [ "$(bytes "$out")" -le "$max" ] && { GIF_COLORS=$colors; return; }
  done
  if command -v gifsicle >/dev/null; then
    gifsicle -O3 --lossy=80 --batch "$out" 2>/dev/null || true; GIF_COLORS="32 + lossy"
  else GIF_COLORS=32; fi
}

png_still() { # png_still <w> <h> <out>: first frame on a transparent canvas
  magick -quiet "$TMP/src_000.png" -resize "${1}x${2}" -background none -gravity center -extent "${1}x${2}" "$3"
}

telegram() {
  local out="$OUT_DIR/$NAME.telegram.webm" crf vf
  echo "telegram -> $out"
  if [ "$SRC_W" -ge "$SRC_H" ]; then vf="scale=512:-2"; else vf="scale=-2:512"; fi
  for crf in 30 36 42 48 54 60 63; do
    ffmpeg -y -v error -i "$IN" -t 3 -vf "$vf:flags=lanczos,fps=30,format=yuva420p" \
      -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf "$crf" -deadline good -cpu-used 2 \
      -row-mt 1 -an "$out"
    [ "$(bytes "$out")" -le 256000 ] && break
  done
  local w h fps dur audio alpha
  w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$out")
  h=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$out")
  fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$out" | awk -F/ '{ printf "%.2f", $1 / ($2 ? $2 : 1) }')
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
  audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$out" | wc -l | tr -d ' ')
  alpha=$(ffprobe -v error -select_streams v:0 -show_entries stream_tags=alpha_mode -of csv=p=0 "$out")
  check "longest side px" "$(( w > h ? w : h ))" "==" 512
  check "shorter side px" "$(( w < h ? w : h ))" "<=" 512
  check "file size" "$(bytes "$out")" "<=" 256000 "$(kb "$(bytes "$out")") at crf $crf" "256 KB"
  check "duration s" "$dur" "<=" 3
  check "frame rate" "$fps" "<=" 30
  check "audio streams" "$audio" "==" 0
  [ "$alpha" = 1 ] && note "VP9 alpha kept (transparent background)" || note "no alpha channel in the WEBM"
  [ "$LOOP_MS" -le 3000 ] || note "the GIF loop is ${LOOP_MS} ms; Telegram allows 3 s, so it was cut at 3 s"
  note "build the set with the @Stickers bot in Telegram (a video sticker set)"
}

whatsapp() {
  local out="$OUT_DIR/$NAME.whatsapp.webp" tray="$OUT_DIR/$NAME.whatsapp_tray.png" q k args
  echo "whatsapp -> $out"
  magick -list format 2>/dev/null | grep -qi '^ *WEBP' || { echo "  FAIL  ImageMagick has no WebP support" ; FAILS=$((FAILS + 1)); return; }
  fit_frames 512 512 "$TMP/wa"
  args=(); for ((k = 0; k < N; k++)); do args+=(-delay "$((DELAYS[k] / 10))" "$TMP/wa/$(printf 'src_%03d.png' "$k")"); done
  for q in 80 70 60 50 40 30 20; do
    magick -quiet -dispose background "${args[@]}" -loop 0 -quality "$q" -define webp:method=6 "$out"
    [ "$(bytes "$out")" -le 500000 ] && break
  done
  check "size px" "$(magick identify -quiet -format '%wx%h\n' "$out" | head -1)" "==" "512x512"
  check "file size" "$(bytes "$out")" "<=" 500000 "$(kb "$(bytes "$out")") at quality $q" "500 KB"
  check "duration ms" "$LOOP_MS" "<=" 10000
  check "shortest frame ms" "$MIN_MS" ">=" 8
  png_still 96 96 "$tray"
  check "tray icon file size" "$(bytes "$tray")" "<=" 50000 "$(kb "$(bytes "$tray")") ($tray)" "50 KB"
  note "WhatsApp ends the animation on the first frame: make frame 1 the full pose"
  note "a pack holds 3-30 stickers, all animated or all static"
}

line() {
  local out="$OUT_DIR/$NAME.line.png" main="$OUT_DIR/$NAME.line_main.png" tab="$OUT_DIR/$NAME.line_tab.png"
  local w h plays
  echo "line -> $out"
  # fit inside 320x270; a square sticker becomes 270x270, which meets "one side >= 270"
  w=$(awk -v w="$SRC_W" -v h="$SRC_H" 'BEGIN { s = 320 / w; if (270 / h < s) s = 270 / h; printf "%d", w * s }')
  h=$(awk -v w="$SRC_W" -v h="$SRC_H" 'BEGIN { s = 320 / w; if (270 / h < s) s = 270 / h; printf "%d", h * s }')
  [ "$w" -ge 270 ] || [ "$h" -ge 270 ] || h=270
  fit_frames "$w" "$h" "$TMP/line"
  pick_frames 20 5 4000
  plays=$(( 4000 / SEL_TOTAL )); [ "$plays" -gt 4 ] && plays=4; [ "$plays" -lt 1 ] && plays=1
  make_apng "$TMP/line" "$plays" "$out"
  [ "$(bytes "$out")" -le 1000000 ] || make_apng "$TMP/line" "$plays" "$out" pal8
  check "width px" "$w" "<=" 320
  check "height px" "$h" "<=" 270
  check "longest side px" "$(( w > h ? w : h ))" ">=" 270
  check "frames" "${#SEL[@]}" ">=" 5
  check "frames" "${#SEL[@]}" "<=" 20
  check "plays" "$plays" "<=" 4
  check "total time ms" "$((SEL_TOTAL * plays))" "<=" 4000 "$((SEL_TOTAL * plays)) ms ($plays x ${SEL_TOTAL} ms)"
  check "file size" "$(bytes "$out")" "<=" 1000000 "$(kb "$(bytes "$out")")" "1 MB"
  [ "$OPAQUE" = "False" ] && note "background is transparent" || { echo "  FAIL  LINE needs a transparent background"; FAILS=$((FAILS + 1)); }
  fit_frames 240 240 "$TMP/line_main"
  make_apng "$TMP/line_main" "$plays" "$main"
  png_still 96 74 "$tab"
  note "main image (APNG 240x240): $main; chat tab (PNG 96x74): $tab"
  note "a LINE set has 8, 16 or 24 animated stickers"
}

wechat() {
  local out="$OUT_DIR/$NAME.wechat.gif" cover="$OUT_DIR/$NAME.wechat_cover.png" icon="$OUT_DIR/$NAME.wechat_icon.png"
  echo "wechat -> $out"
  fit_frames 240 240 "$TMP/wx"
  shrink_gif "$TMP/wx" "$out" 500000
  check "size px" "$(magick identify -quiet -format '%wx%h\n' "$out" | head -1)" "==" "240x240"
  check "file size" "$(bytes "$out")" "<=" 500000 "$(kb "$(bytes "$out")") ($GIF_COLORS colours)" "500 KB"
  png_still 240 240 "$cover"
  png_still 50 50 "$icon"
  check "cover file size" "$(bytes "$cover")" "<=" 500000 "$(kb "$(bytes "$cover")") ($cover)" "500 KB"
  check "chat icon file size" "$(bytes "$icon")" "<=" 100000 "$(kb "$(bytes "$icon")") ($icon)" "100 KB"
  note "an album holds 8-24 stickers, all animated or all static; single stickers may not show real people's portraits"
}

discord() {
  local out="$OUT_DIR/$NAME.discord.png" k
  echo "discord -> $out"
  fit_frames 320 320 "$TMP/dc"
  pick_frames 1000 1 5000
  make_apng "$TMP/dc" 0 "$out"
  if [ "$(bytes "$out")" -gt 524288 ]; then make_apng "$TMP/dc" 0 "$out" pal8; note "palette APNG (256 colours) to fit 512 KiB"; fi
  if [ "$(bytes "$out")" -gt 524288 ]; then
    out="$OUT_DIR/$NAME.discord.gif"; shrink_gif "$TMP/dc" "$out" 524288; note "APNG too big, wrote a GIF instead: $out"
  fi
  check "size px" "$(magick identify -quiet -format '%wx%h\n' "$out" | head -1)" "==" "320x320"
  check "file size" "$(bytes "$out")" "<=" 524288 "$(kb "$(bytes "$out")")" "512 KiB"
  check "duration ms" "$SEL_TOTAL" "<=" 5000
}

slack() {
  local out="$OUT_DIR/$NAME.slack.gif" frames
  echo "slack -> $out"
  fit_frames 128 128 "$TMP/sl"
  shrink_gif "$TMP/sl" "$out" 128000
  frames=$(magick identify -quiet -format "%n\n" "$out" | head -1)
  check "frames" "$frames" "<=" 50
  check "file size" "$(bytes "$out")" "<=" 128000 "$(kb "$(bytes "$out")") ($GIF_COLORS colours)" "128 KB"
  note "Slack names no pixel size; 128x128 is this script's choice"
}

case "$PLATFORM" in
  telegram|whatsapp|line|wechat|discord|slack) "$PLATFORM" ;;
  all) for p in telegram whatsapp line wechat discord slack; do "$p"; done ;;
  *) echo "unknown platform: $PLATFORM" >&2; usage 1 ;;
esac

if [ "$FAILS" -gt 0 ]; then echo "$FAILS check(s) failed"; exit 1; fi
echo "all checks passed -> $OUT_DIR"
