#!/usr/bin/env bash
# List the uncut takes in a clip and cut the long ones out.
#   takes.sh <video> [min_seconds=5] [max_seconds=30] [out_dir=takes]
# Prints one row per take (start, end, length), and for every take of at least
# min_seconds writes take_NN.mp4 (re-encoded, with sound) and take_NN.jpg (a frame
# every 1.5 s, ten at most) so a person or a vision model can pick. A take longer
# than max_seconds is kept as its first max_seconds and marked in the table.
set -euo pipefail
in="${1:?usage: takes.sh <video> [min_seconds] [max_seconds] [out_dir]}"
min="${2:-5}"; max="${3:-30}"; out="${4:-takes}"
[ -f "$in" ] || { echo "takes.sh: no such file: $in" >&2; exit 1; }
for tool in ffmpeg ffprobe bc; do command -v "$tool" >/dev/null || { echo "takes.sh: $tool is not installed" >&2; exit 1; }; done
mkdir -p "$out"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
# Cut threshold 0.17 on ffmpeg's scene score, measured by looking at the frames around
# every candidate in a 3 minute handheld scene: all real cuts scored 0.177 or more,
# all pans, runs and blows without a cut scored 0.168 or less. The usual 0.3 missed
# about 15 real cuts there. The margin is thin, so the script errs toward splitting: a
# false split only shortens a take, a missed cut ruins one.
cuts=$(ffmpeg -hide_banner -i "$in" -vf "select='gt(scene,0.17)',showinfo" -an -f null - 2>&1 \
  | { grep -oE "pts_time:[0-9.]+" || true; } | cut -d: -f2 | awk '$1>0.2' | tr '\n' ' ')   # no cut at all is a valid answer
n=0; prev=0
printf "%-4s %8s %8s %7s  %s\n" take start end length file
for t in $cuts "$dur"; do
  len=$(echo "$t - $prev" | bc -l)
  if (( $(echo "$len >= $min" | bc -l) )); then
    n=$((n+1)); id=$(printf "%02d" "$n")
    # 0.15 s inside both cuts so no frame of the neighbouring shot leaks in
    s=$(printf "%.3f" "$(echo "$prev + 0.15" | bc -l)"); l=$(printf "%.3f" "$(echo "$len - 0.30" | bc -l)")
    note=""
    if (( $(echo "$l > $max" | bc -l) )); then l=$max; note="  (first $max s kept)"; fi
    ffmpeg -v error -y -ss "$s" -t "$l" -i "$in" -map 0:v:0 -map 0:a:0? -map_chapters -1 \
      -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac "$out/take_$id.mp4"
    # one frame every 1.5 s, ten at most, so a person entering late still shows on the sheet
    k=$(echo "t=$l/1.5; scale=0; if (t>10) 10 else if (t<4) 4 else t/1" | bc -l)
    ffmpeg -v error -y -i "$out/take_$id.mp4" -vf "fps=$k/$l,scale=320:-2,tile=${k}x1" -frames:v 1 "$out/take_$id.jpg"
    printf "%-4s %8.2f %8.2f %7.2f  %s%s\n" "$id" "$prev" "$t" "$len" "$out/take_$id.mp4" "$note"
  fi
  prev=$t
done
[ "$n" -gt 0 ] || echo "no uncut take of $min s or more: lower min_seconds or pick another scene" >&2
