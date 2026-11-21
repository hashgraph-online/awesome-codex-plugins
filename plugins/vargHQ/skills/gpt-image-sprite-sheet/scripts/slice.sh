#!/usr/bin/env bash
# slice.sh - cut a sprite sheet into equal frames, then write a looping GIF, a clean atlas PNG
# and a JSON atlas (TexturePacker "JSON Hash", which Phaser's load.atlas reads).
#
# Usage: slice.sh <sheet.png> <cols> <rows> [options]
#   --fps N        playback speed for the GIF and the JSON meta (default 12)
#   --frames N     use only the first N cells, in reading order (default cols x rows)
#   --key COLOR    make this background colour transparent, e.g. white or "#ffffff" (default: keep it)
#   --fuzz P       colour tolerance for --key and --align, in percent (default 8)
#   --align        move every frame so the feet sit on one ground line (the median bottom edge)
#   --center       with --align, also centre every frame on the median horizontal centre
#   --name NAME    frame and file prefix (default: the sheet's file name)
#   --out DIR      output folder (default: <sheet folder>/<name>_sprites)
#
# Writes DIR/frames/NAME_00.png..., DIR/NAME.gif, DIR/NAME_atlas.png, DIR/NAME.json.
# Needs ImageMagick 7 (magick). Tested with bash 3.2 (macOS) and ImageMagick 7.1.
set -euo pipefail

usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
[ $# -ge 3 ] || usage 1
case "$1" in -h|--help) usage 0 ;; esac
SHEET="$1"; COLS="$2"; ROWS="$3"; shift 3
FPS=12; FRAMES=""; KEY=""; FUZZ=8; ALIGN=0; CENTER=0; NAME=""; OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --fps) FPS="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    --key) KEY="$2"; shift 2 ;;
    --fuzz) FUZZ="$2"; shift 2 ;;
    --align) ALIGN=1; shift ;;
    --center) CENTER=1; shift ;;
    --name) NAME="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) echo "unknown option: $1" >&2; usage 1 ;;
  esac
done

[ -f "$SHEET" ] || { echo "no such file: $SHEET" >&2; exit 1; }
command -v magick >/dev/null || { echo "ImageMagick 7 (magick) is required" >&2; exit 1; }
for v in "$COLS" "$ROWS" "$FPS"; do
  case "$v" in ''|*[!0-9]*|0) echo "cols, rows and --fps must be whole numbers above 0" >&2; exit 1 ;; esac
done
TOTAL=$((COLS * ROWS))
[ -n "$FRAMES" ] || FRAMES=$TOTAL
[ "$FRAMES" -ge 1 ] && [ "$FRAMES" -le "$TOTAL" ] || { echo "--frames must be 1..$TOTAL" >&2; exit 1; }
[ -n "$NAME" ] || { NAME="$(basename "$SHEET")"; NAME="${NAME%.*}"; }
[ -n "$OUT" ] || OUT="$(dirname "$SHEET")/${NAME}_sprites"
mkdir -p "$OUT/frames"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

SW=$(magick identify -quiet -format "%w" "$SHEET"); SH=$(magick identify -quiet -format "%h" "$SHEET")
CW=$((SW / COLS)); CH=$((SH / ROWS))
[ $((SW % COLS)) -eq 0 ] && [ $((SH % ROWS)) -eq 0 ] || \
  echo "note: ${SW}x${SH} does not split evenly into ${COLS}x${ROWS}; cells are ${CW}x${CH}, the rest is dropped"

# 1. cut equal cells in reading order (left to right, top to bottom)
for ((i = 0; i < FRAMES; i++)); do
  x=$(( (i % COLS) * CW )); y=$(( (i / COLS) * CH ))
  f="$TMP/$(printf '%02d' "$i").png"
  if [ -n "$KEY" ]; then
    magick -quiet "$SHEET" -crop "${CW}x${CH}+${x}+${y}" +repage -strip -alpha set \
      -fuzz "${FUZZ}%" -transparent "$KEY" "$f"
  else
    magick -quiet "$SHEET" -crop "${CW}x${CH}+${x}+${y}" +repage -strip "$f"
  fi
done

# 2. optional: put every frame on one ground line (and centre), measured from the drawn pixels
BG="none"; [ -n "$KEY" ] || BG=$(magick -quiet "$SHEET" -format "%[pixel:p{0,0}]" info:)
if [ "$ALIGN" = 1 ]; then
  BOTTOMS=(); CENTERS=()
  for ((i = 0; i < FRAMES; i++)); do
    f="$TMP/$(printf '%02d' "$i").png"
    # trim box of the drawing: W H X Y
    box=$(magick -quiet "$f" -fuzz "${FUZZ}%" -format "%@" info:)
    bw=${box%%x*}; rest=${box#*x}; bh=${rest%%+*}; rest=${rest#*+}; bx=${rest%%+*}; by=${rest#*+}
    BOTTOMS+=("$((by + bh))"); CENTERS+=("$((bx + bw / 2))")
  done
  median() { printf '%s\n' "$@" | sort -n | awk '{ a[NR] = $1 } END { print a[int((NR + 1) / 2)] }'; }
  MB=$(median "${BOTTOMS[@]}"); MC=$(median "${CENTERS[@]}")
  for ((i = 0; i < FRAMES; i++)); do
    f="$TMP/$(printf '%02d' "$i").png"
    dy=$((MB - BOTTOMS[i])); dx=0
    [ "$CENTER" = 1 ] && dx=$((MC - CENTERS[i]))
    if [ "$dx" != 0 ] || [ "$dy" != 0 ]; then
      magick -quiet -size "${CW}x${CH}" "xc:$BG" "$f" -geometry "$(printf '%+d%+d' "$dx" "$dy")" \
        -composite "$f"
      echo "frame $i moved by x $dx, y $dy"
    fi
  done
  echo "ground line at y=$MB of each ${CW}x${CH} cell"
fi

# 3. frames, GIF, atlas PNG, JSON
DELAY=$(awk -v f="$FPS" 'BEGIN { d = int(100 / f + 0.5); if (d < 2) d = 2; print d }')   # GIF delay in 1/100 s
FRAME_FILES=()
for ((i = 0; i < FRAMES; i++)); do
  dst="$OUT/frames/${NAME}_$(printf '%02d' "$i").png"
  cp "$TMP/$(printf '%02d' "$i").png" "$dst"
  FRAME_FILES+=("$dst")
done
magick -quiet -delay "$DELAY" -dispose background "${FRAME_FILES[@]}" -loop 0 -layers OptimizeTransparency "$OUT/$NAME.gif"

# atlas: the frames again in a cols x rows grid (empty cells stay background)
FILL="$BG"; [ -n "$KEY" ] && FILL="none"
ROW_FILES=()
for ((r = 0; r < ROWS; r++)); do
  cells=()
  for ((c = 0; c < COLS; c++)); do
    i=$((r * COLS + c))
    if [ "$i" -lt "$FRAMES" ]; then cells+=("${FRAME_FILES[i]}"); else cells+=(-size "${CW}x${CH}" "xc:$FILL"); fi
  done
  magick -quiet "${cells[@]}" -background "$FILL" +append +repage "$TMP/row_$r.png"
  ROW_FILES+=("$TMP/row_$r.png")
done
magick -quiet "${ROW_FILES[@]}" -background "$FILL" -append +repage "$OUT/${NAME}_atlas.png"
AW=$(magick identify -quiet -format "%w" "$OUT/${NAME}_atlas.png"); AH=$(magick identify -quiet -format "%h" "$OUT/${NAME}_atlas.png")

{
  echo "{"
  echo "  \"frames\": {"
  for ((i = 0; i < FRAMES; i++)); do
    x=$(( (i % COLS) * CW )); y=$(( (i / COLS) * CH ))
    sep=","; [ "$i" -eq $((FRAMES - 1)) ] && sep=""
    printf '    "%s_%02d": {"frame": {"x": %d, "y": %d, "w": %d, "h": %d}, "rotated": false, "trimmed": false, "spriteSourceSize": {"x": 0, "y": 0, "w": %d, "h": %d}, "sourceSize": {"w": %d, "h": %d}, "duration": %d}%s\n' \
      "$NAME" "$i" "$x" "$y" "$CW" "$CH" "$CW" "$CH" "$CW" "$CH" "$((DELAY * 10))" "$sep"
  done
  echo "  },"
  printf '  "animations": {"%s": [' "$NAME"
  for ((i = 0; i < FRAMES; i++)); do
    sep=", "; [ "$i" -eq $((FRAMES - 1)) ] && sep=""
    printf '"%s_%02d"%s' "$NAME" "$i" "$sep"
  done
  echo "]},"
  printf '  "meta": {"app": "vargHQ/skills gpt-image-sprite-sheet slice.sh", "version": "1.0", "image": "%s_atlas.png", "format": "RGBA8888", "size": {"w": %d, "h": %d}, "scale": "1", "grid": {"cols": %d, "rows": %d, "cellWidth": %d, "cellHeight": %d}, "frameRate": %d}\n' \
    "$NAME" "$AW" "$AH" "$COLS" "$ROWS" "$CW" "$CH" "$FPS"
  echo "}"
} > "$OUT/$NAME.json"

echo "sheet   $SHEET (${SW}x${SH}) -> $FRAMES frames of ${CW}x${CH}"
echo "frames  $OUT/frames/${NAME}_00.png ... ${NAME}_$(printf '%02d' $((FRAMES - 1))).png"
echo "gif     $OUT/$NAME.gif ($FPS fps, ${DELAY}0 ms per frame, loops forever)"
echo "atlas   $OUT/${NAME}_atlas.png (${AW}x${AH}) + $OUT/$NAME.json"
