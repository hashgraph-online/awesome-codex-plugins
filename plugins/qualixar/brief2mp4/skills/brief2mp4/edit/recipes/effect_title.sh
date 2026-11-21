#!/usr/bin/env bash
# effect_title.sh: EffectCraft, headless. Render an animated title: a text layer with the Tracking In
# animation preset, a fade and a rise, plus an accent bar that grows underneath. Pinned CLI: effectcraft 0.24.1.
#
#   effect_title.sh --out title.mp4
#   effect_title.sh --text "Chapter one" --seconds 4 --size 1920x1080 --out title.mp4
#
# Options
#   --text TEXT          the title (default "Edit pack")
#   --seconds S          length (default 3)
#   --size WxH, --fps N  composition format (default 1280x720, 30)
#   --bg HEX, --ink HEX, --accent HEX   colours (default #1b2a41, #f5f5f5, #ffb224)
#   --save-project FILE  also keep the EffectCraft project (.ecproj)
#   --out FILE           output MP4, H.264, silent (default effect_title.mp4)
# Command ids used (discover them again with `effectcraft-cli commands`; ids change between versions):
#   comp.new layer.newSolid layer.newText layer.applyTextPreset prop.addKey, and `render` for the file
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
B2M_RECIPE=effect_title; source "$HERE/_lib.sh"

TEXT="Edit pack" SECS=3 SIZE=1280x720 FPS=30 BG="#1b2a41" INK="#f5f5f5" ACCENT="#ffb224" KEEP="" OUT=effect_title.mp4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --text) TEXT="$2"; shift 2 ;; --seconds) SECS="$2"; shift 2 ;; --size) SIZE="$2"; shift 2 ;; --fps) FPS="$2"; shift 2 ;;
    --bg) BG="$2"; shift 2 ;; --ink) INK="$2"; shift 2 ;; --accent) ACCENT="$2"; shift 2 ;;
    --save-project) KEEP="$2"; shift 2 ;; --out) OUT="$2"; shift 2 ;; -h|--help) b2m_usage "$0"; exit 0 ;;
    *) b2m_die "unknown option $1" 2 ;;
  esac
done
b2m_need ffprobe; b2m_need node
CLI="$(b2m_cli effectcraft)"; W="${SIZE%x*}"; H="${SIZE#*x}"; b2m_workdir
CX=$((W / 2)); CY=$((H / 2)); FS=$((H / 6)); BAR=$((W * 3 / 10))

cat > "$B2M_WORK/c.jsonl" <<JSON
{"command":"comp.new","params":{"name":"Title","width":$W,"height":$H,"frameRate":$FPS,"duration":$SECS,"background":$(b2m_str "$BG")}}
{"command":"layer.newText","params":{"name":"Headline","text":$(b2m_str "$TEXT"),"size":$FS,"fill":$(b2m_str "$INK"),"position":[$CX,$CY]}}
{"command":"layer.applyTextPreset","params":{"layer":"Headline","preset":"trackingIn"}}
{"command":"prop.addKey","params":{"layer":"Headline","path":"transform/position","time":0,"value":[$CX,$((CY + H / 12)),0]}}
{"command":"prop.addKey","params":{"layer":"Headline","path":"transform/position","time":1,"value":[$CX,$CY,0]}}
{"command":"prop.addKey","params":{"layer":"Headline","path":"transform/opacity","time":0,"value":0}}
{"command":"prop.addKey","params":{"layer":"Headline","path":"transform/opacity","time":0.6,"value":100}}
{"command":"layer.newSolid","params":{"name":"Bar","color":$(b2m_str "$ACCENT"),"width":$BAR,"height":$((H / 90 + 4))}}
{"command":"prop.set","params":{"layer":"Bar","path":"transform/position","value":[$CX,$((CY + H / 6)),0]}}
{"command":"prop.addKey","params":{"layer":"Bar","path":"transform/scale","time":0.4,"value":[0,100,100]}}
{"command":"prop.addKey","params":{"layer":"Bar","path":"transform/scale","time":1.4,"value":[100,100,100]}}
JSON
PROJ="$(b2m_abs "$B2M_WORK/p.ecproj")"; mkdir -p "$(dirname "$OUT")"
"$CLI" --empty run --commands "$(b2m_abs "$B2M_WORK/c.jsonl")" --save-as "$PROJ" --json > "$B2M_WORK/run.log" 2>&1 || b2m_die "effectcraft-cli failed: $(cat "$B2M_WORK/run.log")"
"$CLI" --project "$PROJ" render --out "$(b2m_abs "$OUT")" --format h264 --audio off > "$B2M_WORK/render.log" 2>&1 || b2m_die "render failed: $(cat "$B2M_WORK/render.log")"
[[ -z "$KEEP" ]] || cp "$B2M_WORK/p.ecproj" "$KEEP"
[[ -s "$OUT" ]] || b2m_die "EffectCraft reported success but $OUT is missing"
echo "ok: $OUT ($(b2m_secs "$OUT") s, ${W}x${H}) rendered with effectcraft"
