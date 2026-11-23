#!/usr/bin/env bash
# check_delivery.sh: measure a finished MP4 against the delivery spec.
# Prints one PASS / WARN / FAIL / SKIP line per check. Exit 0 = RESULT: PASS, 1 = a check FAILed (or could not run),
# 2 = bad arguments, 3 = RESULT: INCOMPLETE (nothing failed, but a check was skipped and not measured).
#
#   check_delivery.sh final.mp4 --seconds 12
#   check_delivery.sh final.mp4 --seconds 8 --size 1080x1920 --fps 30 --silent-ok
#
# Options
#   --seconds N    expected duration (required); tolerance is one frame
#   --size WxH     expected frame size (default 1920x1080)
#   --fps N        expected frame rate (default 30; a ratio such as 30000/1001 is fine)
#   --lufs N       loudness target (default -14), checked within +/-1.5 LU
#   --silent-ok    a silent soundtrack is what the brief asked for
#   --joins T,T    times (s) where separately rendered acts were joined: each is checked for a pop (SSIM)
#   --flash-ok T,T times (s) of planned one-frame flashes (reported as INFO, not flicker)
#   --strict-flicker  any flicker not listed in --flash-ok is a FAIL (default: WARN)
set -uo pipefail

FILE="${1:-}"; shift || true
SECONDS_="" SIZE="1920x1080" FPS=30 LUFS=-14 SILENT_OK=0 JOINS="" FLASH_OK="" STRICT_FLICKER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seconds) SECONDS_="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --fps) FPS="$2"; shift 2 ;;
    --lufs) LUFS="$2"; shift 2 ;;
    --silent-ok) SILENT_OK=1; shift ;;
    --joins) JOINS="$2"; shift 2 ;;
    --flash-ok) FLASH_OK="$2"; shift 2 ;;
    --strict-flicker) STRICT_FLICKER=1; shift ;;
    *) echo "check_delivery.sh: unknown option $1" >&2; exit 2 ;;
  esac
done
[[ -f "$FILE" && -n "$SECONDS_" ]] || { echo "usage: check_delivery.sh FILE --seconds N [--size WxH] [--fps N]" >&2; exit 2; }
NUM='[0-9]+([.][0-9]+)?'
bad_arg() { echo "check_delivery.sh: $1" >&2; exit 2; }
[[ "$SECONDS_" =~ ^$NUM$ ]] || bad_arg "--seconds must be a number of seconds, got '$SECONDS_'"
[[ "$FPS" =~ ^$NUM(/[0-9]+)?$ ]] || bad_arg "--fps must be a number (or a ratio like 30000/1001), got '$FPS'"
[[ "$SIZE" =~ ^[0-9]+x[0-9]+$ ]] || bad_arg "--size must be WxH, got '$SIZE'"
[[ -z "$JOINS" || "$JOINS" =~ ^$NUM(,$NUM)*$ ]] || bad_arg "--joins must be comma-separated seconds, got '$JOINS'"
[[ -z "$FLASH_OK" || "$FLASH_OK" =~ ^$NUM(,$NUM)*$ ]] || bad_arg "--flash-ok must be comma-separated seconds, got '$FLASH_OK'"

FAILS=0 SKIPS=0
FPS_V="$(awk -v f="$FPS" 'BEGIN{n=split(f,a,"/"); print (n==2 && a[2]>0)?a[1]/a[2]:a[1]}')"
skip() { echo "SKIP  $1"; SKIPS=$((SKIPS + 1)); }
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
fps_ok="$(awk -v r="$rate" -v f="$FPS_V" 'BEGIN{split(r,a,"/"); v=(a[2]>0)?a[1]/a[2]:a[1]; print (v>f-0.01 && v<f+0.01)?1:0}')"
[[ "$fps_ok" == 1 ]] && pass "frame rate $rate" || fail "frame rate $rate, want $FPS"
dur_ok="$(awk -v d="$dur" -v s="$SECONDS_" -v f="$FPS_V" 'BEGIN{diff=d-s; if(diff<0)diff=-diff; print (diff<=1.0/f+0.001)?1:0}')"
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

# Seams and freezes: one-frame flicker, pops at joins, cut classification, true freezes (check_seams.py).
# Its PASS / WARN / FAIL / INFO lines are printed as they are; a FAIL counts here too.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=""
for cand in python3 python; do   # the first that really runs 3.8+ (on Windows python3 can be the Store stub)
  c="$(command -v "$cand" 2>/dev/null)" || continue
  if "$c" -c "import sys; sys.exit(sys.version_info < (3, 8))" 2>/dev/null; then PY="$c"; break; fi
done
if [[ -z "$PY" ]]; then
  skip "seam and freeze checks: Python 3.8+ not found, so flicker, joins and freezes were not measured (install it, then rerun)"
else
  seam_args=("$FILE")
  [[ -n "$JOINS" ]] && seam_args+=(--joins "$JOINS")
  [[ -n "$FLASH_OK" ]] && seam_args+=(--flash-ok "$FLASH_OK")
  [[ "$STRICT_FLICKER" == 1 ]] && seam_args+=(--strict)
  seams="$("$PY" "$HERE/check_seams.py" "${seam_args[@]}" 2>&1)"; seam_rc=$?
  echo "$seams"
  seam_fails="$(echo "$seams" | grep -c '^FAIL' || true)"
  FAILS=$((FAILS + seam_fails))
  # A check that did not run must never read as a pass: a crash, a usage error, or a FAIL exit with no FAIL line.
  if [[ "$seam_rc" -gt 1 || ( "$seam_rc" == 1 && "$seam_fails" == 0 ) || ( "$seam_rc" == 0 && -z "$(echo "$seams" | grep '^PASS' || true)" ) ]]; then
    fail "seam and freeze checks could not run (check_seams.py exit $seam_rc): see its output above"
  fi
fi

echo "----"
if [[ "$FAILS" != 0 ]]; then echo "RESULT: FAIL, $FAILS check(s) ($FILE)"; exit 1; fi
if [[ "$SKIPS" != 0 ]]; then echo "RESULT: INCOMPLETE, $SKIPS check(s) skipped and not measured ($FILE)"; exit 3; fi
echo "RESULT: PASS ($FILE)"; exit 0
