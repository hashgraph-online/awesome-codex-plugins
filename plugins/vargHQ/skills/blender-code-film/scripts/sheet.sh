#!/usr/bin/env bash
# Contact sheet of a rendered sequence: every Nth frame in a 4-wide grid, frame numbers burned in.
#   scripts/sheet.sh render/draft 12 sheet.png
set -euo pipefail
dir=${1:?frames folder}; every=${2:-12}; out=${3:-$dir/sheet.png}
n=$(ls "$dir"/frame_*.png | wc -l | tr -d ' ')
rows=$(( (n / every + 3) / 4 ))
label=""
# frame numbers on the tiles when this ffmpeg has drawtext (built with freetype); tiles run left to right
ffmpeg -hide_banner -filters 2>/dev/null | grep -q drawtext && label=",drawtext=text='%{n}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6"
ffmpeg -v error -y -pattern_type glob -i "$dir/frame_*.png" \
  -vf "select='not(mod(n\,$every))',scale=480:-2$label,tile=4x$rows" \
  -frames:v 1 "$out"
echo "$out ($n frames, every $every)"
