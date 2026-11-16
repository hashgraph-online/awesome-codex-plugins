#!/usr/bin/env bash
# contact_sheet.sh: pull frames from a video so you can LOOK at it before you
# say it is done. Writes one PNG per sample, named by its time, plus a grid.
#
#   contact_sheet.sh final.mp4                 # a frame every second
#   contact_sheet.sh final.mp4 --at 0.5,3,7.2  # exactly these moments (seconds)
#   contact_sheet.sh final.mp4 --every 0.5 --out checks/
#   contact_sheet.sh final.mp4 --at 9.5 --keep  # add moments, keep the stills already in checks/
#
# By default the stills from an earlier run are deleted first, so a re-render never leaves stale
# frames behind. Use --keep only when adding moments for the SAME render.
#
# Output: <out>/t_003.00s.png ... and <out>/sheet.png (6 columns, read left to
# right, top to bottom, in time order).
set -euo pipefail

FILE="${1:-}"; shift || true
EVERY=1 AT="" OUT="checks" KEEP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --every) EVERY="$2"; shift 2 ;;
    --at) AT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --keep) KEEP=1; shift ;;
    *) echo "contact_sheet.sh: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$FILE" ]] || { echo "usage: contact_sheet.sh FILE [--every S | --at t1,t2] [--out DIR] [--keep]" >&2; exit 2; }
mkdir -p "$OUT"
if [[ "$KEEP" == 1 ]]; then rm -f "$OUT"/sheet.png; else rm -f "$OUT"/t_*.png "$OUT"/sheet.png; fi

dur="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$FILE")"
if [[ -z "$AT" ]]; then
  AT="$(awk -v d="$dur" -v e="$EVERY" 'BEGIN{s=""; for(t=0; t<d-0.01; t+=e){s=s (s==""?"":",") t}; print s}')"
fi

IFS=',' read -r -a TIMES <<< "$AT"
for t in "${TIMES[@]}"; do
  name="$(awk -v t="$t" 'BEGIN{printf "t_%06.2fs.png", t}')"
  ffmpeg -v error -y -ss "$t" -i "$FILE" -frames:v 1 "$OUT/$name"
done

n="$(ls "$OUT"/t_*.png | wc -l | tr -d " ")"; cols=6; rows=$(( (n + cols - 1) / cols ))
ffmpeg -v error -y -pattern_type glob -i "$OUT/t_*.png" \
  -vf "scale=480:-1,tile=${cols}x${rows}:padding=6:color=0x222222" -frames:v 1 "$OUT/sheet.png"
echo "contact_sheet.sh: $n frames in $OUT/, grid at $OUT/sheet.png (6 per row, time order)"
