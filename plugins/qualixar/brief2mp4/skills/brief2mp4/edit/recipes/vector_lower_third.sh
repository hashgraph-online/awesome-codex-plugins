#!/usr/bin/env bash
# vector_lower_third.sh: VectorCraft, headless. Draw a lower third (rounded panel, accent bar, name and
# role) and export it as an SVG you can place in a video. Pinned CLI: vectorcraft 0.24.1.
#
#   vector_lower_third.sh --out lower_third.svg
#   vector_lower_third.sh --name "Alex Doe" --role "Video editor" --out lower_third.svg
#
# Options
#   --name TEXT, --role TEXT       defaults "Presenter Name" and "Role or topic line"
#   --width N, --height N          artboard in pixels (default 1280 x 200)
#   --panel HEX, --ink HEX, --accent HEX   colours (default #1b2a41, #f5f5f5, #ffb224)
#   --out FILE                     output SVG (default vector_lower_third.svg); transparent background
# Command ids used (discover them again with `vectorcraft-cli commands`; ids change between versions):
#   file.new shape.rectangle paint.setFill paint.setStroke text.create, then `run --export`
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=vector_lower_third; source "$HERE/_lib.sh"

NAME="Presenter Name" ROLE="Role or topic line" W=1280 H=200 PANEL="#1b2a41" INK="#f5f5f5" ACCENT="#ffb224" OUT=vector_lower_third.svg
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;; --role) ROLE="$2"; shift 2 ;; --width) W="$2"; shift 2 ;; --height) H="$2"; shift 2 ;;
    --panel) PANEL="$2"; shift 2 ;; --ink) INK="$2"; shift 2 ;; --accent) ACCENT="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;; -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
b2m_need node
CLI="$(b2m_cli vectorcraft)"; b2m_workdir
PW=$((W * 70 / 100)); PY=$((H / 5)); PH=$((H * 3 / 5)); NS=$((PH * 36 / 100)); RS=$((PH * 22 / 100)); TX=$((PW / 20))
NONE='{"none":true}'
cat > "$B2M_WORK/c.jsonl" <<JSON
{"command":"file.new","params":{"name":"LowerThird","width":$W,"height":$H,"units":"Pixels","backgroundContents":"transparent"}}
{"command":"shape.rectangle","params":{"x":0,"y":$PY,"width":$PW,"height":$PH,"radius":8}}
{"command":"paint.setFill","params":{"color":$(b2m_str "$PANEL")}}
{"command":"paint.setStroke","params":$NONE}
{"command":"shape.rectangle","params":{"x":0,"y":$PY,"width":12,"height":$PH}}
{"command":"paint.setFill","params":{"color":$(b2m_str "$ACCENT")}}
{"command":"paint.setStroke","params":$NONE}
{"command":"text.create","params":{"x":$TX,"y":$((PY + PH * 5 / 9)),"text":$(b2m_str "$NAME"),"size":$NS,"color":$(b2m_str "$INK")}}
{"command":"text.create","params":{"x":$TX,"y":$((PY + PH * 5 / 6)),"text":$(b2m_str "$ROLE"),"size":$RS,"color":$(b2m_str "$ACCENT")}}
JSON
mkdir -p "$(dirname "$OUT")"
LOG="$("$CLI" run --commands "$(b2m_abs "$B2M_WORK/c.jsonl")" --export "$(b2m_abs "$OUT")" 2>&1)" || b2m_die "vectorcraft-cli failed: $LOG"
[[ -s "$OUT" ]] || b2m_die "VectorCraft reported success but $OUT is missing"
echo "ok: $OUT (${W}x${H} SVG) drawn with vectorcraft"
