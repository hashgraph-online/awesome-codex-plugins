#!/usr/bin/env bash
# Put every hook clip in HOOKS_DIR in front of one body, one MP4 per hook, normalized to 1080x1920 30 fps.
# usage: hook-variants.sh body.mp4 hooks_dir out_dir [cut_s=0]   (cut_s: seconds to drop from the body's start)
set -euo pipefail
BODY=$1; HOOKS=$2; OUTDIR=$3; CUT=${4:-0}
mkdir -p "$OUTDIR"
NORM="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p"
ANORM="aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
for H in "$HOOKS"/*.mp4; do
  NAME=$(basename "$H" .mp4)
  ffmpeg -hide_banner -loglevel error -y -i "$H" -i "$BODY" -filter_complex \
    "[0:v]$NORM[v0];[0:a]$ANORM[a0];[1:v]trim=start=$CUT,setpts=PTS-STARTPTS,$NORM[v1];[1:a]atrim=start=$CUT,asetpts=PTS-STARTPTS,$ANORM[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
    -map "[v]" -map "[a]" -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 192k -movflags +faststart \
    "$OUTDIR/${NAME}__$(basename "$BODY" .mp4).mp4"
  echo "$OUTDIR/${NAME}__$(basename "$BODY" .mp4).mp4"
done
