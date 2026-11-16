#!/usr/bin/env bash
# sound_bed.sh: a quiet, original placeholder soundtrack made from sine waves,
# so a render is never delivered silent by accident. Swap in real music or a
# voiceover whenever you have one.
#
#   sound_bed.sh bed.wav --seconds 12
#   sound_bed.sh bed.wav --seconds 10 --bpm 96 --hits 2.0,6.5
#
# Options
#   --seconds N   length (required)
#   --bpm N       pulse tempo (default 100)
#   --hits LIST   extra low "boom" accents at these seconds (e.g. on a reveal or a landing)
#   --ticks LIST  short bright clicks at these seconds (e.g. a cut, a new label, a UI tap)
set -euo pipefail

OUT="${1:-}"; shift || true
SECONDS_="" BPM=100 HITS="" TICKS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seconds) SECONDS_="$2"; shift 2 ;;
    --bpm) BPM="$2"; shift 2 ;;
    --hits) HITS="$2"; shift 2 ;;
    --ticks) TICKS="$2"; shift 2 ;;
    *) echo "sound_bed.sh: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -n "$OUT" && -n "$SECONDS_" ]] || { echo "usage: sound_bed.sh OUT.wav --seconds N [--bpm N] [--hits t1,t2] [--ticks t1,t2]" >&2; exit 2; }

BEAT="$(awk -v b="$BPM" 'BEGIN{print 60/b}')"
# Pad: an A-minor-ish chord with a slow swell. Pulse: a soft low thump on every beat.
PAD="0.06*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.25*t))+0.045*sin(2*PI*261.63*t)+0.04*sin(2*PI*329.63*t)*(0.7+0.3*sin(2*PI*0.5*t))"
PULSE="0.22*sin(2*PI*55*t)*exp(-9*mod(t\,${BEAT}))"
EXPR="${PAD}+${PULSE}"
if [[ -n "$HITS" ]]; then
  IFS=',' read -r -a H <<< "$HITS"
  for h in "${H[@]}"; do
    EXPR="${EXPR}+0.5*sin(2*PI*45*(t-${h}))*exp(-4*max(t-${h}\,0))*gte(t\,${h})"
  done
fi

if [[ -n "$TICKS" ]]; then
  IFS=',' read -r -a K <<< "$TICKS"
  for k in "${K[@]}"; do
    EXPR="${EXPR}+0.35*sin(2*PI*2400*(t-${k}))*exp(-90*max(t-${k}\,0))*gte(t\,${k})"
  done
fi

ffmpeg -v error -y -f lavfi -i "aevalsrc=${EXPR}|${EXPR}:s=48000:d=${SECONDS_}" \
  -af "afade=t=in:d=0.6,afade=t=out:st=$(awk -v s="$SECONDS_" 'BEGIN{print s-1}'):d=1,lowpass=f=6000" \
  -c:a pcm_s16le "$OUT"
# Guard: a NaN anywhere in the expression silences the whole file, so never report success on silence.
peak="$(ffmpeg -hide_banner -nostats -i "$OUT" -af volumedetect -f null - 2>&1 | sed -n 's/.*max_volume: *\(-*[0-9.inf]*\) dB.*/\1/p')"
case "$peak" in ""|-inf|-9[0-9]*|-[1-9][0-9][0-9]*) echo "sound_bed.sh: generated audio is silent (max volume ${peak:-unknown} dB); check --hits/--ticks times" >&2; exit 1 ;; esac
echo "sound_bed.sh: wrote $OUT (${SECONDS_} s, ${BPM} bpm)"
