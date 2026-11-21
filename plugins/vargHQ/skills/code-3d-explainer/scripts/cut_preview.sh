#!/usr/bin/env bash
# cut_preview.sh: cut the catalog preview (1280x720, H.264, no audio, faststart) from the 1080p master and
# check it: 6-10 s long, 0.4-2 MB. Pick the most striking seconds; keep content >= 64 px from the sides.
#
#   bash scripts/cut_preview.sh <master.mp4> <start-s> <duration-s> [out.mp4]   (default out: preview.mp4)
#   bash scripts/cut_preview.sh examples/animal-cell/renders/master.mp4 12.6 8.4 preview.mp4
#
# Default crf 20. Film grain costs bitrate: if the file is over 2 MB, raise it (CRF=22 bash ...); under 0.4 MB, lower it.
set -euo pipefail
src="${1:?usage: cut_preview.sh <master.mp4> <start> <duration> [out.mp4]}"; ss="${2:?start}"; dur="${3:?duration}"; out="${4:-preview.mp4}"
crf="${CRF:-20}"
ffmpeg -v error -y -ss "$ss" -i "$src" -t "$dur" -vf scale=1280:-2:flags=lanczos -c:v libx264 -preset slow -crf "$crf" -pix_fmt yuv420p -an -movflags +faststart "$out"
w=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=nw=1:nk=1 "$out")
h=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=nw=1:nk=1 "$out")
d=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$out")
bytes=$(stat -f%z "$out" 2>/dev/null || stat -c%s "$out")
mb=$(awk -v b="$bytes" 'BEGIN{printf "%.2f", b/1e6}')
ok=yes; awk -v d="$d" 'BEGIN{exit !(d>=6 && d<=10.05)}' || { ok=no; echo "WARN duration ${d}s is outside 6-10 s"; }
awk -v m="$mb" 'BEGIN{exit !(m>=0.4 && m<=2)}' || { ok=no; echo "WARN size ${mb} MB is outside 0.4-2 MB (set CRF)"; }
echo "$out: ${w}x${h}, ${d}s, ${mb} MB, crf $crf, ok=$ok"
