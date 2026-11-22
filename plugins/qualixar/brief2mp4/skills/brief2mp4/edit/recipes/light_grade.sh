#!/usr/bin/env bash
# light_grade.sh: LightCraft, headless. Grade one still to a warm look with a built-in preset and export it.
# Your original file is never changed. Pinned CLI: lightcraft 0.21.1.
#
#   light_grade.sh --out graded.jpg
#   light_grade.sh --in photo.jpg --preset lc.warm-glow --amount 120 --size 1920 --out graded.jpg
#
# Options
#   --in FILE        the still to grade (default: a 1280x720 gradient made with ffmpeg)
#   --preset ID      a LightCraft preset id (default lc.warm-glow; list them with `lightcraft-cli run --demo presets.list`)
#   --amount N       how much of the preset, 0 to 200 percent (default 100)
#   --size PX        long edge of the export in pixels (default 0, the full size)
#   --out FILE       output; the extension picks the format: .jpg .png .tif .webp (default light_grade.jpg)
# Command ids used (discover them again with `lightcraft-cli commands`; ids change between versions):
#   preset.apply app.export, started from `run --import FILE`
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=light_grade; source "$HERE/_lib.sh"

IN="" PRESET=lc.warm-glow AMOUNT=100 SIZE=0 OUT=light_grade.jpg
while [[ $# -gt 0 ]]; do
  case "$1" in
    --in) IN="$2"; shift 2 ;; --preset) PRESET="$2"; shift 2 ;; --amount) AMOUNT="$2"; shift 2 ;; --size) SIZE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;; -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
[[ "$AMOUNT" =~ ^[0-9]+$ && "$AMOUNT" -le 200 ]] || b2m_die "--amount must be a whole number from 0 to 200" 2
[[ "$SIZE" =~ ^[0-9]+$ ]] || b2m_die "--size must be a whole number of pixels (0 for the full size)" 2
b2m_need node
CLI="$(b2m_cli lightcraft)"
b2m_workdir
if [[ -z "$IN" ]]; then
  b2m_need ffmpeg
  IN="$B2M_WORK/sample.png"
  ffmpeg -v error -y -f lavfi -i "gradients=s=1280x720:c0=0x3c6e9e:c1=0xe6e6dc:seed=4,format=rgb24" -frames:v 1 "$IN" || b2m_die "could not make a sample still with ffmpeg"
fi
[[ -f "$IN" ]] || b2m_die "input not found: $IN" 2
mkdir -p "$(dirname "$OUT")"
LOG="$("$CLI" run --import "$(b2m_abs "$IN")" \
  preset.apply "{\"id\":$(b2m_str "$PRESET"),\"amount\":$AMOUNT}" \
  app.export "{\"path\":$(b2m_str "$(b2m_abs "$OUT")"),\"longEdge\":$SIZE}" 2>&1)" || b2m_die "lightcraft-cli failed: $LOG"
FAILED="$(printf '%s\n' "$LOG" | b2m_pick 'L.filter(x => x.ok === false).map(x => x.command + ": " + JSON.stringify(x.error)).join("; ")')"
[[ -z "$FAILED" ]] || b2m_die "lightcraft-cli reported: $FAILED"
[[ -s "$OUT" ]] || b2m_die "LightCraft reported success but $OUT is missing"
echo "ok: $OUT graded with $PRESET at $AMOUNT% by lightcraft"
