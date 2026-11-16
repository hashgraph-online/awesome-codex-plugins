#!/usr/bin/env bash
# sound_mix.sh: SoundCraft, headless. Mix a voice track over a music bed, duck the bed while the voice
# speaks (volume automation on the music track), and bounce a WAV. Pinned CLI: soundcraft 0.20.1.
#
#   sound_mix.sh --out mix.wav
#   sound_mix.sh --voice vo.wav --music bed.mp3 --voice-start 2 --duck-db -18 --out mix.wav
#
# Options
#   --voice FILE, --music FILE     any audio ffmpeg can read (default: a generated voice-like tone and a chord bed)
#   --voice-start S                where the voice starts on the timeline (default 2)
#   --bed-db DB                    music level while nobody speaks (default -6)
#   --duck-db DB                   music level while the voice speaks (default -18)
#   --ramp S                       length of each duck down and back up (default 0.3)
#   --out FILE                     bounced WAV, 48 kHz stereo (default sound_mix.wav)
# Command ids used (discover them again with `soundcraft-cli commands`; ids change between versions):
#   session.new file.import_audio mix.volume automation.set_point, and `run --bounce` for the bounce
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=sound_mix; source "$HERE/_lib.sh"

VOICE="" MUSIC="" VS=2 BED=-6 DUCK=-18 RAMP=0.3 OUT=sound_mix.wav
while [[ $# -gt 0 ]]; do
  case "$1" in
    --voice) VOICE="$2"; shift 2 ;; --music) MUSIC="$2"; shift 2 ;; --voice-start) VS="$2"; shift 2 ;;
    --bed-db) BED="$2"; shift 2 ;;  --duck-db) DUCK="$2"; shift 2 ;; --ramp) RAMP="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;     -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
b2m_need ffmpeg; b2m_need ffprobe; b2m_need node
CLI="$(b2m_cli soundcraft)"; b2m_workdir

# The files are copied in as voice.wav and music.wav, so the tracks are named "voice" and "music".
if [[ -z "$VOICE" ]]; then
  ffmpeg -v error -y -f lavfi -i "sine=frequency=140:duration=5,tremolo=f=4:d=0.9,volume=4" "$B2M_WORK/v_in.wav"; VOICE="$B2M_WORK/v_in.wav"
fi
if [[ -z "$MUSIC" ]]; then
  ffmpeg -v error -y -f lavfi -i "sine=frequency=220:duration=10" -f lavfi -i "sine=frequency=277:duration=10" \
    -f lavfi -i "sine=frequency=330:duration=10" -filter_complex "amix=inputs=3:normalize=0,volume=4" "$B2M_WORK/m_in.wav"; MUSIC="$B2M_WORK/m_in.wav"
fi
ffmpeg -v error -y -i "$VOICE" -ar 48000 -c:a pcm_s24le "$B2M_WORK/voice.wav"
ffmpeg -v error -y -i "$MUSIC" -ar 48000 -c:a pcm_s24le "$B2M_WORK/music.wav"
VDUR="$(b2m_secs "$B2M_WORK/voice.wav")"

# Duck times: down just before the voice, back up just after it.
T() { awk -v a="$VS" -v b="$VDUR" -v r="$RAMP" -v w="$1" 'BEGIN {
  s = a - r; if (s < 0) s = 0
  if (w == "down0") print s; if (w == "down1") print s + r
  if (w == "up0") print a + b; if (w == "up1") print a + b + r }'; }
P() { printf '{"track":"music","param":"volume","at":{"seconds":%s},"value":%s}' "$1" "$2"; }

mkdir -p "$(dirname "$OUT")"
"$CLI" run \
  --cmd 'session.new={"name":"b2m-mix","sample_rate":48000}' \
  --cmd "file.import_audio={\"path\":$(b2m_str "$(b2m_abs "$B2M_WORK/music.wav")")}" \
  --cmd "file.import_audio={\"path\":$(b2m_str "$(b2m_abs "$B2M_WORK/voice.wav")"),\"at\":{\"seconds\":$VS}}" \
  --cmd "mix.volume={\"track\":\"music\",\"db\":$BED}" \
  --cmd "automation.set_point=$(P 0 "$BED")" \
  --cmd "automation.set_point=$(P "$(T down0)" "$BED")" \
  --cmd "automation.set_point=$(P "$(T down1)" "$DUCK")" \
  --cmd "automation.set_point=$(P "$(T up0)" "$DUCK")" \
  --cmd "automation.set_point=$(P "$(T up1)" "$BED")" \
  --bounce "$(b2m_abs "$OUT")" > "$B2M_WORK/run.log" 2>&1 || b2m_die "soundcraft-cli failed: $(cat "$B2M_WORK/run.log")"
[[ -s "$OUT" ]] || b2m_die "SoundCraft reported success but $OUT is missing"
echo "ok: $OUT ($(b2m_secs "$OUT") s) mixed with soundcraft; $(tail -1 "$B2M_WORK/run.log")"
