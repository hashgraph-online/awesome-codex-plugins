#!/usr/bin/env bash
# Frames (+ optional music) → MP4. The music is cut to the film and faded out over the last second.
#   scripts/mux.sh render/final film.mp4 [music.mp3] [fps]
set -euo pipefail
dir=${1:?frames folder}; out=${2:-film.mp4}; music=${3:-}; fps=${4:-24}
n=$(ls "$dir"/frame_*.png | wc -l | tr -d ' ')
dur=$(python3 -c "print(round($n/$fps,3))")
if [[ -n "$music" ]]; then
  fade=$(python3 -c "print(max(0,$dur-1))")
  ffmpeg -v error -y -framerate "$fps" -pattern_type glob -i "$dir/frame_*.png" -i "$music" \
    -map 0:v -map 1:a -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
    -af "afade=t=out:st=$fade:d=1,loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -t "$dur" -movflags +faststart "$out"
else
  ffmpeg -v error -y -framerate "$fps" -pattern_type glob -i "$dir/frame_*.png" \
    -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart "$out"
fi
echo "$out  ${dur}s  $(du -h "$out" | cut -f1)"
