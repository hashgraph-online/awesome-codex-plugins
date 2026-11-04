#!/usr/bin/env bash
# Join generated clips, lay the birthday song under them and export one file that plays everywhere
# (WhatsApp, iMessage, Instagram, a TV at the party): H.264 + AAC, yuv420p, faststart, -14 LUFS.
#
#   assemble.sh [-s SONG_START] [-W WIDTH -H HEIGHT] [-k] out.mp4 song.mp3 clip1.mp4 [clip2.mp4 …]
#
#   -s  second of the song to start from (skip a long intro: the sung name is the hook), default 0
#   -W -H  output size, default 1080x1920 (9:16); use -W 1920 -H 1080 for a party screen
#   -k  keep the clips' own sound (cheers, candles) under the song at 35 %
#
# The song is cut to the clips' total length and fades out over the last 1.5 s.
set -euo pipefail

START=0 W=1080 H=1920 KEEP=0
while getopts "s:W:H:k" o; do
  case $o in
    s) START=$OPTARG ;;
    W) W=$OPTARG ;;
    H) H=$OPTARG ;;
    k) KEEP=1 ;;
    *) exit 2 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -ge 3 ] || { echo "usage: assemble.sh [-s SONG_START] [-W W -H H] [-k] out.mp4 song.mp3 clip1.mp4 [clip2.mp4 …]" >&2; exit 2; }
OUT=$1 SONG=$2
shift 2

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# 1. Every clip to the same size, frame rate and audio layout (a silent track when a clip has none).
i=0
: > "$TMP/list.txt"
for c in "$@"; do
  i=$((i + 1))
  if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$c" | grep -q .; then
    AIN=(-i "$c")
    AMAP="0:a:0"
  else
    AIN=(-i "$c" -f lavfi -t 3600 -i anullsrc=r=48000:cl=stereo)
    AMAP="1:a:0"
  fi
  ffmpeg -v error -y "${AIN[@]}" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},fps=30,format=yuv420p" \
    -map 0:v:0 -map "$AMAP" -shortest -c:v libx264 -preset medium -crf 18 -c:a aac -ar 48000 -ac 2 \
    "$TMP/c$i.mp4"
  echo "file '$TMP/c$i.mp4'" >> "$TMP/list.txt"
done
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/joined.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/joined.mp4")
FADE=$(awk -v d="$DUR" 'BEGIN { s = d - 1.5; if (s < 0) s = 0; print s }')

# 2. The song from START, cut to the video, faded out; the clips' own sound under it with -k.
if [ "$KEEP" = 1 ]; then
  MIX="[1:a]atrim=start=${START},asetpts=PTS-STARTPTS,afade=t=out:st=${FADE}:d=1.5[s];[0:a]volume=0.35[c];[s][c]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
else
  MIX="[1:a]atrim=start=${START},asetpts=PTS-STARTPTS,afade=t=out:st=${FADE}:d=1.5,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
fi
ffmpeg -v error -y -i "$TMP/joined.mp4" -i "$SONG" -filter_complex "$MIX" \
  -map 0:v -map "[a]" -t "$DUR" -c:v copy -c:a aac -b:a 160k -ar 48000 -movflags +faststart "$OUT"

SIZE=$(($(wc -c < "$OUT") / 1024 / 1024))
echo "✓ $OUT  ${DUR%.*} s  ${W}x${H}  ${SIZE} MB"
[ "$SIZE" -lt 16 ] || echo "  note: over 16 MB; WhatsApp may recompress it. Send as a document to keep quality." >&2
