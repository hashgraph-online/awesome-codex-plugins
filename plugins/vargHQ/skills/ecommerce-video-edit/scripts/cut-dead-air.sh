#!/usr/bin/env bash
# Cut pauses longer than MIN seconds out of a talking video, keeping PAD seconds of air on each side.
# usage: cut-dead-air.sh in.mp4 out.mp4 [noise_dB=-35] [min_s=0.5] [pad_s=0.12]
set -euo pipefail
IN=$1; OUT=$2; NOISE=${3:--35}; MIN=${4:-0.5}; PAD=${5:-0.12}
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
# keep-segments = complement of the detected silences, each silence shrunk by PAD
SEGS=$(ffmpeg -hide_banner -nostats -i "$IN" -af "silencedetect=noise=${NOISE}dB:d=${MIN}" -f null - 2>&1 |
  awk -v dur="$DUR" -v pad="$PAD" '
    /silence_start/ { s=$NF+pad }
    /silence_end/   { e=$5-pad; if (e>s) { starts[n]=s; ends[n]=e; n++ } }
    END {
      prev=0
      for (i=0;i<n;i++) { if (starts[i]>prev+0.05) printf "%.3f %.3f\n", prev, starts[i]; prev=ends[i] }
      if (dur>prev+0.05) printf "%.3f %.3f\n", prev, dur
    }')
[ -z "$SEGS" ] && { echo "no speech found; lower the noise floor"; exit 1; }
FILTER=""; LABELS=""; i=0
while read -r A B; do
  FILTER+="[0:v]trim=${A}:${B},setpts=PTS-STARTPTS[v$i];[0:a]atrim=${A}:${B},asetpts=PTS-STARTPTS[a$i];"
  LABELS+="[v$i][a$i]"; i=$((i+1))
done <<< "$SEGS"
FILTER+="${LABELS}concat=n=${i}:v=1:a=1[v][a]"
ffmpeg -hide_banner -loglevel error -y -i "$IN" -filter_complex "$FILTER" -map "[v]" -map "[a]" \
  -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 192k "$OUT"
echo "kept $i segments: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s of ${DUR}s"
