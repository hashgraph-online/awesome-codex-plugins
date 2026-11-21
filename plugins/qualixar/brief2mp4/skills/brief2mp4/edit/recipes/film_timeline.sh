#!/usr/bin/env bash
# film_timeline.sh: FilmCraft, headless. Cut two clips together on a timeline with a cross dissolve and
# a title, then export an MP4. Pinned CLI: filmcraft 0.20.1.
#
#   film_timeline.sh --out cut.mp4
#   film_timeline.sh --clip-a a.mp4 --clip-b b.mp4 --title "Step one" --out cut.mp4
#
# Options
#   --clip-a FILE, --clip-b FILE   footage with audio (default: two generated 4 s test clips)
#   --title TEXT                   title burned in from 0.5 s for 2 s (default "Hello edit pack")
#   --each S                       seconds taken from each clip (default 2.5)
#   --dissolve S                   cross dissolve length, centred on the cut (default 1)
#   --size WxH, --fps N            sequence format (default 1280x720, 30)
#   --crf N                        x264 quality for the export, lower is better (default 23)
#   --save-project FILE            also keep the FilmCraft project (.fcproj)
#   --out FILE                     output MP4 (default film_timeline.mp4)
# Command ids used (discover them again with `filmcraft-cli commands`; ids change between versions):
#   file.newProject file.newSequence file.import timeline.place sequence.applyVideoTransition
#   graphics.newText file.exportMedia
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=film_timeline; source "$HERE/_lib.sh"

A="" B="" TITLE="Hello edit pack" EACH=2.5 DISSOLVE=1 SIZE=1280x720 FPS=30 CRF=23 KEEP="" OUT=film_timeline.mp4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --clip-a) A="$2"; shift 2 ;;  --clip-b) B="$2"; shift 2 ;;  --title) TITLE="$2"; shift 2 ;;
    --each) EACH="$2"; shift 2 ;; --dissolve) DISSOLVE="$2"; shift 2 ;; --size) SIZE="$2"; shift 2 ;;
    --fps) FPS="$2"; shift 2 ;;   --crf) CRF="$2"; shift 2 ;;  --save-project) KEEP="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;   -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
b2m_need ffmpeg; b2m_need ffprobe; b2m_need node
CLI="$(b2m_cli filmcraft)"; W="${SIZE%x*}"; H="${SIZE#*x}"
b2m_workdir
TICKS() { awk -v s="$1" 'BEGIN { printf "%.0f", s * 254016000000 }'; }

if [[ -z "$A" ]]; then
  ffmpeg -v error -y -f lavfi -i "testsrc2=size=${SIZE}:rate=$FPS:duration=4" -f lavfi -i "sine=frequency=440:duration=4" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$B2M_WORK/a.mp4"; A="$B2M_WORK/a.mp4"
fi
if [[ -z "$B" ]]; then
  ffmpeg -v error -y -f lavfi -i "gradients=size=${SIZE}:rate=$FPS:duration=4" -f lavfi -i "sine=frequency=330:duration=4" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$B2M_WORK/b.mp4"; B="$B2M_WORK/b.mp4"
fi
NEED="$(awk -v e="$EACH" -v d="$DISSOLVE" 'BEGIN { print e + d / 2 }')"
for f in "$A" "$B"; do
  awk -v have="$(b2m_secs "$f")" -v need="$NEED" 'BEGIN { exit !(have + 0.001 >= need) }' \
    || b2m_die "$f is shorter than $NEED s (--each plus half the dissolve, so the dissolve has spare frames to blend)" 2
done

PROJ="$(b2m_abs "$B2M_WORK/p.fcproj")"; OUT_ABS="$(b2m_abs "$OUT")"; mkdir -p "$(dirname "$OUT")"
run() { local out; out="$("$CLI" "$@" 2>&1)" || b2m_die "filmcraft-cli failed: $out"; printf '%s\n' "$out"; }

# Stage 1: project, sequence, import.
cat > "$B2M_WORK/s1.jsonl" <<JSON
{"id":"file.newProject","params":{"name":"b2m-film"}}
{"id":"file.newSequence","params":{"name":"Main","width":$W,"height":$H,"fps":$FPS}}
{"id":"file.import","params":{"paths":[$(b2m_str "$(b2m_abs "$A")"),$(b2m_str "$(b2m_abs "$B")")]}}
JSON
OUT1="$(run run "$(b2m_abs "$B2M_WORK/s1.jsonl")" --save-as "$PROJ")"
ERR="$(b2m_pick 'L.find(x => x.id === "file.import").result.errors.length' <<<"$OUT1")"
[[ "$ERR" == 0 ]] || b2m_die "FilmCraft could not import the clips: $OUT1"
IDS=($(b2m_pick 'L.find(x => x.id === "file.import").result.items' <<<"$OUT1"))

# Stage 2: place both clips back to back; the second one starts DISSOLVE/2 early in its source (spare frames).
HALF="$(awk -v d="$DISSOLVE" 'BEGIN { print d / 2 }')"
cat > "$B2M_WORK/s2.jsonl" <<JSON
{"id":"timeline.place","params":{"item":${IDS[0]},"track":"V1","seconds":0,"sourceIn":{"seconds":0},"duration":{"seconds":$EACH}}}
{"id":"timeline.place","params":{"item":${IDS[1]},"track":"V1","seconds":$EACH,"sourceIn":{"seconds":$HALF},"duration":{"seconds":$EACH}}}
JSON
OUT2="$(run --project "$PROJ" --save run "$(b2m_abs "$B2M_WORK/s2.jsonl")")"
VIDEO_A="$(b2m_pick 'L[0].result.clips[0]' <<<"$OUT2")"

# Stage 3: dissolve at the cut, title on V2, export.
FRAMES="$(awk -v d="$DISSOLVE" -v f="$FPS" 'BEGIN { printf "%d", d * f + 0.5 }')"
cat > "$B2M_WORK/s3.jsonl" <<JSON
{"id":"sequence.applyVideoTransition","params":{"clip":$VIDEO_A,"effect":"cross_dissolve","edge":"out","frames":$FRAMES,"align":"center"}}
{"id":"graphics.newText","params":{"text":$(b2m_str "$TITLE"),"size":$((H / 8)),"position":[$((W / 12)),$((H * 5 / 6))],"seconds":2,"time":$(TICKS 0.5),"track":2}}
{"id":"file.exportMedia","params":{"path":$(b2m_str "$OUT_ABS"),"format":"h264","bitrateMode":"crf","crf":$CRF,"wait":true}}
JSON
run --project "$PROJ" --save run "$(b2m_abs "$B2M_WORK/s3.jsonl")" >/dev/null
[[ -z "$KEEP" ]] || cp "$B2M_WORK/p.fcproj" "$KEEP"
[[ -s "$OUT" ]] || b2m_die "FilmCraft reported success but $OUT is missing"
echo "ok: $OUT ($(b2m_secs "$OUT") s, ${W}x${H}) cut with filmcraft"
