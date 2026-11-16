#!/usr/bin/env bash
# photo_thumbnail.sh: PhotoCraft, headless. Make a thumbnail or title-card PNG: a gradient background
# with a large title and a subtitle. Pinned CLI: photocraft 0.23.1.
#
#   photo_thumbnail.sh --out thumb.png
#   photo_thumbnail.sh --title "Cut faster" --subtitle "Three editing habits" --size 1920x1080 --out card.png
#
# Options
#   --title TEXT, --subtitle TEXT   defaults "Edit pack" and "real editing, headless"
#   --size WxH                      default 1280x720
#   --from HEX, --to HEX            gradient colours (default #1b2a41 to #324a5f)
#   --ink HEX, --accent HEX         title and subtitle colours (default #f5f5f5, #ffb224)
#   --out FILE                      output PNG (default photo_thumbnail.png)
# Command ids used (discover them again with `photocraft-cli commands`; ids change between versions):
#   layer.newFillLayer.gradient type.create, started from `run --new`
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=photo_thumbnail; source "$HERE/_lib.sh"

TITLE="Edit pack" SUB="real editing, headless" SIZE=1280x720 FROM="#1b2a41" TO="#324a5f" INK="#f5f5f5" ACCENT="#ffb224" OUT=photo_thumbnail.png
while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE="$2"; shift 2 ;; --subtitle) SUB="$2"; shift 2 ;; --size) SIZE="$2"; shift 2 ;;
    --from) FROM="$2"; shift 2 ;; --to) TO="$2"; shift 2 ;; --ink) INK="$2"; shift 2 ;; --accent) ACCENT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;; -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
b2m_need node
CLI="$(b2m_cli photocraft)"; W="${SIZE%x*}"; H="${SIZE#*x}"
X=$((W * 7 / 100)); TS=$((H / 6)); SS=$((H / 16))   # type sizes are in points, which are pixels at 72 ppi
mkdir -p "$(dirname "$OUT")"
LOG="$("$CLI" run --new "{\"width\":$W,\"height\":$H,\"background\":$(b2m_str "$FROM")}" \
  --cmd layer.newFillLayer.gradient --params "{\"from\":$(b2m_str "$FROM"),\"to\":$(b2m_str "$TO"),\"angle\":45}" \
  --cmd type.create --params "{\"x\":$X,\"y\":$((H / 2)),\"text\":$(b2m_str "$TITLE"),\"size\":$TS,\"color\":$(b2m_str "$INK")}" \
  --cmd type.create --params "{\"x\":$((X + 4)),\"y\":$((H / 2 + H / 8)),\"text\":$(b2m_str "$SUB"),\"size\":$SS,\"color\":$(b2m_str "$ACCENT")}" \
  --out "$(b2m_abs "$OUT")" 2>&1)" || b2m_die "photocraft-cli failed: $LOG"
[[ -s "$OUT" ]] || b2m_die "PhotoCraft reported success but $OUT is missing"
echo "ok: $OUT (${W}x${H}) made with photocraft"
