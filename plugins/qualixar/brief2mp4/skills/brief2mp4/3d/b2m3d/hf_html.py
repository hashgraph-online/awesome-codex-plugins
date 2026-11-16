"""HTML for a b2m3d HyperFrames project: stage, titles and one paused GSAP timeline."""
from __future__ import annotations

import html
import json
from pathlib import Path

FONTS = {"Inter": "@fontsource-variable/inter/files/inter-latin-wght-normal.woff2",
         "Space Grotesk": "@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2"}

DEFAULT_BACKGROUND = "radial-gradient(120% 90% at 50% 35%, #2a2d35 0%, #0d0e11 72%)"
DEFAULT_ACCENT = "#e6e8ee"
DEFAULT_FONT = "Inter"

TITLE_POS = {
    "bottom-left": "left:7%;bottom:11%;text-align:left;",
    "top-left": "left:7%;top:10%;text-align:left;",
    "center": "left:0;right:0;top:42%;text-align:center;",
    "bottom-center": "left:0;right:0;bottom:10%;text-align:center;",
}


def js_json(value) -> str:
    """JSON that is safe inside a <script> element."""
    return json.dumps(value).replace("</", "<\\/").replace("<!--", "<\\!--")


def font_faces() -> str:
    return "\n".join(
        f'@font-face{{font-family:"{name}";src:url("fonts/{Path(rel).name}") format("woff2");'
        f'font-weight:100 900;font-display:block;}}' for name, rel in FONTS.items())


def _title_block(i: int, t: dict) -> tuple[str, list[str]]:
    pos = TITLE_POS.get(t.get("position", "bottom-left"), TITLE_POS["bottom-left"])
    kicker, sub = t.get("kicker", ""), t.get("sub", "")
    ids = []
    parts = []
    if kicker:
        parts.append(f'<div class="b2m3d-kicker" id="b2m3d-kick-{i}">{html.escape(kicker)}</div>')
        ids.append(f"#b2m3d-kick-{i}")
    parts.append(f'<div class="b2m3d-head" id="b2m3d-head-{i}" style="font-size:{int(t.get("size", 84))}px">'
                 f'{html.escape(t["text"])}</div>')
    ids.append(f"#b2m3d-head-{i}")
    if sub:
        parts.append(f'<div class="b2m3d-sub" id="b2m3d-sub-{i}">{html.escape(sub)}</div>')
        ids.append(f"#b2m3d-sub-{i}")
    block = f'<div class="b2m3d-title" id="b2m3d-title-{i}" style="{pos}">{"".join(parts)}</div>'
    return block, ids


def titles_html(titles: list[dict]) -> tuple[str, str]:
    """(markup, gsap tweens). Titles share the scene's paused timeline, so they seek like everything else."""
    blocks, tweens = [], []
    for i, t in enumerate(titles):
        block, ids = _title_block(i, t)
        blocks.append(block)
        start, dur = float(t["start"]), float(t["duration"])
        for j, sel in enumerate(ids):
            tweens.append(f'tl.fromTo("{sel}",{{y:38,opacity:0}},{{y:0,opacity:1,duration:0.7,'
                          f'ease:"power3.out"}},{start + 0.08 * j:.3f});')
        tweens.append(f'tl.to("#b2m3d-title-{i}",{{opacity:0,y:-18,duration:0.45,ease:"power2.in"}},'
                      f'{max(start, start + dur - 0.45):.3f});')
    return "\n".join(blocks), "\n".join(tweens)


def render_html(shot: dict, physics: dict | None) -> str:
    w, h, dur = shot["width"], shot["height"], shot["duration"]
    bg = shot.get("background", DEFAULT_BACKGROUND)
    accent = shot.get("accent", DEFAULT_ACCENT)
    head_font = shot.get("font", DEFAULT_FONT)
    blocks, tweens = titles_html(shot.get("titles", []))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<title>{html.escape(shot.get("name", "b2m3d shot"))}</title>
<script src="vendor/gsap.min.js"></script>
<script type="importmap">{{"imports":{{"three":"./vendor/three/build/three.module.js","three/addons/":"./vendor/three/addons/"}}}}</script>
<style>
{font_faces()}
body{{margin:0;background:#000;}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;}}
.b2m3d-stage{{position:absolute;inset:0;}}
.b2m3d-bg{{position:absolute;inset:0;background:{bg};}}
#b2m3d-canvas{{position:absolute;inset:0;width:100%;height:100%;display:block;}}
.b2m3d-title{{position:absolute;color:#f4f5f7;font-family:"Inter";max-width:80%;}}
.b2m3d-kicker{{font-family:"Inter";font-weight:600;font-size:26px;letter-spacing:.22em;text-transform:uppercase;color:{accent};margin-bottom:14px;}}
.b2m3d-head{{font-family:"{head_font}";font-weight:700;line-height:1.02;letter-spacing:-.02em;}}
.b2m3d-sub{{font-family:"Inter";font-weight:400;font-size:34px;color:#c9ccd3;margin-top:18px;}}
</style></head>
<body>
<div id="root" data-composition-id="b2m3d" data-start="0" data-width="{w}" data-height="{h}" data-duration="{dur}">
  <div id="b2m3d-stage" class="b2m3d-stage">
    <div class="b2m3d-bg" id="b2m3d-bg"></div>
    <canvas id="b2m3d-canvas" width="{w}" height="{h}"></canvas>
    {blocks}
  </div>
</div>
<script>
window.B2M3D_SHOT = {js_json(shot)};
window.B2M3D_PHYSICS = {js_json(physics) if physics else "null"};
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.to({{}}, {{ duration: {dur} }}, 0);
{tweens}
tl.eventCallback("onUpdate", () => window.__b2m3dRenderAt && window.__b2m3dRenderAt(tl.time()));
window.__timelines["b2m3d"] = tl;
</script>
<script type="module" src="b2m3d-runtime.js"></script>
</body></html>
"""
