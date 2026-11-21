#!/usr/bin/env bash
# check_delivery.sh: measure a finished MP4 against the delivery spec.
# Prints one PASS / WARN / FAIL line per check and exits 1 if anything FAILs.
#
#   check_delivery.sh final.mp4 --seconds 12
#   check_delivery.sh final.mp4 --seconds 8 --size 1080x1920 --fps 30 --silent-ok
#
# Options
#   --seconds N    expected duration (required); tolerance is one frame
#   --size WxH     expected frame size (default 1920x1080)
#   --fps N        expected frame rate (default 30)
#   --lufs N       loudness target (default -14), checked within +/-1.5 LU
#   --silent-ok    a silent soundtrack is what the brief asked for
set -uo pipefail

FILE="${1:-}"; shift || true
SECONDS_="" SIZE="1920x1080" FPS=30 LUFS=-14 SILENT_OK=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seconds) SECONDS_="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --fps) FPS="$2"; shift 2 ;;
    --lufs) LUFS="$2"; shift 2 ;;
    --silent-ok) SILENT_OK=1; shift ;;
    *) echo "check_delivery.sh: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$FILE" && -n "$SECONDS_" ]] || { echo "usage: check_delivery.sh FILE --seconds N [--size WxH] [--fps N]" >&2; exit 2; }

FAILS=0
pass() { echo "PASS  $1"; }
warn() { echo "WARN  $1"; }
fail() { echo "FAIL  $1"; FAILS=$((FAILS + 1)); }
probe() { ffprobe -v error -select_streams "$1" -show_entries "$2" -of default=nw=1:nk=1 "$FILE" | head -1; }

W="${SIZE%x*}" H="${SIZE#*x}"
vcodec="$(probe v:0 stream=codec_name)"
pix="$(probe v:0 stream=pix_fmt)"
vw="$(probe v:0 stream=width)"; vh="$(probe v:0 stream=height)"
rate="$(probe v:0 stream=avg_frame_rate)"
dur="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$FILE")"
acodec="$(probe a:0 stream=codec_name)"
arate="$(probe a:0 stream=sample_rate)"
ach="$(probe a:0 stream=channels)"

[[ "$vcodec" == "h264" ]] && pass "video codec h264" || fail "video codec is '$vcodec', want h264"
[[ "$pix" == "yuv420p" ]] && pass "pixel format yuv420p" || fail "pixel format is '$pix', want yuv420p"
[[ "$vw" == "$W" && "$vh" == "$H" ]] && pass "frame size ${vw}x${vh}" || fail "frame size ${vw}x${vh}, want ${W}x${H}"
fps_ok="$(awk -v r="$rate" -v f="$FPS" 'BEGIN{split(r,a,"/"); v=(a[2]>0)?a[1]/a[2]:a[1]; print (v>f-0.01 && v<f+0.01)?1:0}')"
[[ "$fps_ok" == 1 ]] && pass "frame rate $rate" || fail "frame rate $rate, want $FPS"
dur_ok="$(awk -v d="$dur" -v s="$SECONDS_" -v f="$FPS" 'BEGIN{diff=d-s; if(diff<0)diff=-diff; print (diff<=1.0/f+0.001)?1:0}')"
[[ "$dur_ok" == 1 ]] && pass "duration ${dur}s" || fail "duration ${dur}s, want ${SECONDS_}s (+/- one frame)"

if [[ -z "$acodec" ]]; then
  fail "no audio stream (add one, even silent: finish.sh does this)"
else
  [[ "$acodec" == "aac" ]] && pass "audio codec aac" || fail "audio codec is '$acodec', want aac"
  [[ "$arate" == "48000" ]] && pass "audio 48 kHz" || warn "audio sample rate $arate (48000 preferred)"
  [[ "$ach" == "2" ]] && pass "audio stereo" || warn "audio has $ach channel(s) (stereo preferred)"
  stats="$(ffmpeg -nostats -hide_banner -i "$FILE" -map 0:a:0 -af ebur128=peak=true -f null - 2>&1 | tail -14)"
  il="$(echo "$stats" | awk '/I:/{v=$2} END{print v}')"
  tp="$(echo "$stats" | awk '/Peak:/{v=$2} END{print v}')"
  if [[ -z "$il" || "$il" == "-inf" ]] || awk -v i="$il" 'BEGIN{exit !(i < -60)}'; then
    [[ "$SILENT_OK" == 1 ]] && pass "soundtrack silent (brief allows it)" || fail "soundtrack is silent; fix the audio, or pass --silent-ok if the brief asked for silence"
  else
    awk -v i="$il" -v t="$LUFS" 'BEGIN{d=i-t; if(d<0)d=-d; exit !(d<=1.5)}' \
      && pass "loudness ${il} LUFS (target ${LUFS})" || fail "loudness ${il} LUFS, target ${LUFS} +/- 1.5"
    awk -v p="$tp" 'BEGIN{exit !(p<=-1.0)}' && pass "true peak ${tp} dBTP" || fail "true peak ${tp} dBTP, want <= -1.0"
  fi
fi

# Picture health: long black stretches and long frozen stretches.
# pix_th=0.03 counts only true black (luma within 3% of black), so a dark designed background
# such as #101114 is not mistaken for a black frame.
black="$(ffmpeg -nostats -hide_banner -i "$FILE" -vf "blackdetect=d=0.5:pic_th=0.98:pix_th=0.03" -an -f null - 2>&1 | grep -c black_start || true)"
[[ "$black" == 0 ]] && pass "no black stretch over 0.5 s" || warn "$black black stretch(es) over 0.5 s: intended?"
frozen="$(ffmpeg -nostats -hide_banner -i "$FILE" -vf "freezedetect=n=0.001:d=1.5" -an -f null - 2>&1 | grep -c freeze_start || true)"
[[ "$frozen" == 0 ]] && pass "nothing frozen over 1.5 s" || warn "$frozen frozen stretch(es) over 1.5 s: expected where the brief asks for a hold (say so in REPORT.md), otherwise dead air"

echo "----"
if [[ "$FAILS" == 0 ]]; then echo "RESULT: PASS ($FILE)"; exit 0; else echo "RESULT: FAIL, $FAILS check(s) ($FILE)"; exit 1; fi
