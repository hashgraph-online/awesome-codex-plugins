#!/usr/bin/env python3
"""Make the presenter-mode video of a wokify.py set as a HyperFrames project (HTML -> MP4).

  python3 presenter.py wokify-out                       # writes wokify-out/presenter/ (silent)
  python3 presenter.py wokify-out --music music.mp3     # with a music bed + a soft tick on every slide change (ffmpeg)
  cd wokify-out/presenter && npx hyperframes@0.9.15 check && npx hyperframes@0.9.15 render -o final.mp4 --crf 20

Layout (1920x1080, 30 fps, 42 s): the current slide on a big stage; NOW (title + one-line note) and a NEXT preview
on the right; every slide on a timeline at the bottom with a rainbow highlight that steps to the current one, a
progress bar, a SLIDE n / 12 counter and a presenter clock. The collage opens (9 s, scrolling top to bottom), then
11 slides of 3 s. GIF slides step through their frames on the timeline, so renders are identical every time.
Needs Pillow, plus ffmpeg for --music. Run collage.py first: the opener is collage.jpg.
"""
import argparse, glob, json, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageSequence

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("out"); ap.add_argument("--music", help="an mp3 of at least 42 s (120 BPM keeps every cut on a beat)")
ap.add_argument("--pronouns", default="they/them")
A = ap.parse_args()
OUT = Path(A.out)
ROOT = OUT / "presenter"
for d in ("assets/stage", "assets/gif", "assets/thumbs", "assets/audio", "compositions"):
    (ROOT / d).mkdir(parents=True, exist_ok=True)


def find(tid):
    for ext in ("gif", "png", "jpg", "jpeg", "webp"):
        hits = glob.glob(f"{OUT}/{tid}.{ext}")
        if hits:
            return Path(hits[0])


SLIDES = [  # id, label, file, note (7 words or fewer: each slide is on screen 3 s)
    ("all", "ALL OF ME", OUT / "collage.jpg", "1 selfie · 11 prompts · GPT Image 2.6"),
    ("me", "ME", find("me"), "My face in all 8 views."),
    ("friends", "MY FRIENDS", find("friends"), "The 5 most-memed woke friends on X."),
    ("linkedin", "MY LINKEDIN", find("linkedin"), f"Chief Purpose Officer. {A.pronouns[:1].upper() + A.pronouns[1:]}."),
    ("colleagues", "MY COLLEAGUES", find("colleagues"), "Unconscious Bias 101. I’m eating cereal."),
    ("social", "MY SOCIAL LIFE", find("social"), "“Honestly? I’m here for the vibes.”"),
    ("figure", "MY FIGURE", find("figure"), "Now with extra opinions!"),
    ("card", "MY CARD", find("card"), "Moral superiority 99. Actual activism 4."),
    ("pet", "MY PET", find("pet"), "#1 woke animal on X: the cat."),
    ("drink", "MY FAV DRINK", find("drink"), "Oat milk, extra hot, extra shot."),
    ("home", "MY HOME", find("home"), "Science is real. Private road."),
    ("game", "MY FAVORITE GAME", find("game"), "The game of moral capital."),
]
missing = [s[0] for s in SLIDES if not s[2] or not Path(s[2]).exists()]
if missing:
    sys.exit(f"missing in {OUT}: {', '.join(missing)} (run wokify.py and collage.py first)")

meta = []
for sid, label, src, note in SLIDES:
    im = Image.open(src)
    gif = src.suffix == ".gif"
    frames = [(f.convert("RGB"), f.info.get("duration", 100)) for f in ImageSequence.Iterator(im)] if gif else [(im.convert("RGB"), 0)]
    first = frames[0][0]; w, h = first.size
    k = min(1, 1600 / w, 1000 / h); sw, sh = round(w * k), round(h * k)
    if gif:   # a GIF becomes a frame strip that the timeline steps through
        strip = Image.new("RGB", (sw * len(frames), sh))
        for i, (f, _) in enumerate(frames):
            strip.paste(f.resize((sw, sh), Image.LANCZOS), (i * sw, 0))
        strip.save(ROOT / "assets" / "gif" / f"{sid}_strip.jpg", quality=90)
    first.resize((sw, sh), Image.LANCZOS).save(ROOT / "assets" / "stage" / f"{sid}.jpg", quality=92)
    tw, th = 260, 174
    s = max(tw / w, th / h); r = first.resize((round(w * s), round(h * s)), Image.LANCZOS)
    l, t = (r.width - tw) // 2, (r.height - th) // 2
    r.crop((l, t, l + tw, t + th)).save(ROOT / "assets" / "thumbs" / f"{sid}.jpg", quality=88)
    meta.append({"id": sid, "label": label, "note": note, "w": sw, "h": sh, "gif": gif, "frames": len(frames), "delay": (frames[0][1] or 100) / 1000})
(ROOT / "slides.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
(ROOT / "package.json").write_text(json.dumps({"name": "wokify-presenter", "private": True, "type": "module", "scripts": {
    "dev": "npx hyperframes@0.9.15 preview", "check": "npx hyperframes@0.9.15 check", "render": "npx hyperframes@0.9.15 render -o final.mp4 --crf 20"}}, indent=2))
(ROOT / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}}, indent=2))

AUDIO = ""
if A.music:
    if not shutil.which("ffmpeg"):
        sys.exit("--music needs ffmpeg")
    a = ROOT / "assets" / "audio"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=1900:duration=0.07", "-f", "lavfi", "-i",
                    "anoisesrc=d=0.03:c=pink:a=0.3", "-filter_complex", "[0]afade=t=out:st=0:d=0.07,volume=0.35[a];[1]highpass=f=3000,afade=t=out:st=0:d=0.03[b];[a][b]amix=inputs=2:normalize=0",
                    str(a / "tick.wav")], check=True)
    cuts = [9000 + 3000 * i for i in range(11)]   # slide changes, ms
    fc = f"[1]asplit={len(cuts)}" + "".join(f"[k{i}]" for i in range(len(cuts))) + ";" + "".join(f"[k{i}]adelay={c}|{c}[t{i}];" for i, c in enumerate(cuts))
    fc += "[0]" + "".join(f"[t{i}]" for i in range(len(cuts))) + f"amix=inputs={len(cuts) + 1}:normalize=0:duration=first,atrim=0:42"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", A.music, "-i", str(a / "tick.wav"), "-filter_complex", fc, "-c:a", "libmp3lame", "-b:a", "192k", str(a / "mix.mp3")], check=True)
    AUDIO = '      <audio id="music" class="clip" src="assets/audio/mix.mp3" data-start="0" data-duration="42.0" data-track-index="20" data-volume="0.9"></audio>\n'

# ------------------------------------------------------------------ the HyperFrames scenes
COMP = ROOT / "compositions"; COMP.mkdir(exist_ok=True)
SL = json.loads((ROOT / "slides.json").read_text())
SHORT = ["ALL OF ME", "ME", "FRIENDS", "LINKEDIN", "COLLEAGUES", "SOCIAL LIFE", "FIGURE", "CARD", "PET", "FAV DRINK", "HOME", "FAV GAME"]
N = len(SL)
DUR = [9.0] + [3.0] * (N - 1)
START = [sum(DUR[:i]) for i in range(N)]
TOTAL = sum(DUR)

BG, INK, MUTED, CARD = "#111111", "#f4f2ee", "#a6a29c", "#1c1c1e"
RAINBOW = "linear-gradient(180deg,#e40303 0 16.66%,#ff8c00 16.66% 33.33%,#ffed00 33.33% 50%,#008026 50% 66.66%,#004dff 66.66% 83.33%,#750787 83.33% 100%)"
RAINBOW_H = "linear-gradient(90deg,#e40303,#ff8c00,#ffed00,#008026,#004dff,#750787)"
SX, SY, SW, SH = 56, 124, 1240, 698            # stage
PX, PW = 1336, 528                              # right panel
NY, NH = 525, 297                               # NEXT card
TX, TY, TW, TH = 56, 872, 130, 87               # timeline thumbs
TGAP = (1808 - N * TW) / (N - 1)
def slot(i): return round(TX + i * (TW + TGAP), 2)

def nb(t):
    a, _, z = t.rpartition(" "); return f"{a}&nbsp;{z}" if a else t

def fit(w, h, bw, bh):
    k = min(bw / w, bh / h); return round(w * k), round(h * k)

HELPERS = """function gifSteps(tl, sel, n, fd, t0, t1){ for(let i=0;;i++){ const t=t0+i*fd; if(t>=t1-0.001) break; tl.set(sel,{xPercent:-100*(i%n)/n},t); } }"""

def scene(cid, css, body, js):
    return f"""<template>
  <style>
#root{{position:absolute;inset:0;overflow:hidden;font-family:"Montserrat",sans-serif;color:{INK};}}
{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080">
    {body}
  </div>
  <script>
  (function(){{
{HELPERS}
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  }})();
  </script>
</template>
"""

# ------------------------------------------------------------------ chrome: header, labels, timeline, progress (whole film)
thumbs = "\n    ".join(
    f'<div class="th" id="th{i}" style="left:{slot(i)}px"><img src="assets/thumbs/{s["id"]}.jpg" alt=""><span class="no" data-layout-ignore>{i + 1:02d}</span></div>'
    f'<div class="tl-lbl" data-layout-ignore id="tlb{i}" style="left:{slot(i)}px">{SHORT[i]}</div>' for i, s in enumerate(SL))
ticks = "".join(f'<div class="tick" style="left:{round(START[i] / TOTAL * 1808, 1)}px"></div>' for i in range(1, N))
chrome_css = f"""
#hdr{{position:absolute;left:{SX}px;top:34px;font-weight:900;font-size:52px;letter-spacing:-0.01em;white-space:nowrap;}}
#hdr .rb{{background:{RAINBOW};-webkit-background-clip:text;background-clip:text;color:transparent;}}
#meta{{position:absolute;right:56px;top:46px;display:flex;gap:28px;align-items:center;font-weight:700;font-size:26px;color:{MUTED};white-space:nowrap;}}
#meta b{{color:{INK};font-weight:800;}}
#clk{{font-family:"JetBrains Mono",monospace;font-weight:700;color:{INK};}}
.dot{{display:inline-block;width:14px;height:14px;border-radius:50%;background:#ff3b30;margin-right:10px;vertical-align:1px;}}
.plbl{{position:absolute;left:{PX}px;font-weight:800;font-size:20px;letter-spacing:0.18em;color:{MUTED};}}
#hl{{position:absolute;left:{TX - 6}px;top:{TY - 6}px;width:{TW + 12}px;height:{TH + 12}px;border-radius:13px;background:{RAINBOW_H};}}
.th{{position:absolute;top:{TY}px;width:{TW}px;height:{TH}px;border-radius:8px;overflow:hidden;background:{CARD};opacity:0.38;}}
.th img{{width:100%;height:100%;object-fit:cover;display:block;}}
.th .no{{position:absolute;left:6px;top:5px;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:13px;color:#fff;background:rgba(0,0,0,.6);padding:1px 5px;border-radius:4px;}}
.tl-lbl{{position:absolute;top:{TY + TH + 12}px;width:{TW}px;text-align:center;font-weight:800;font-size:14px;letter-spacing:0.04em;color:{MUTED};white-space:nowrap;}}
#track{{position:absolute;left:{TX}px;top:1028px;width:1808px;height:4px;border-radius:2px;background:#2b2b2d;}}
#fill{{position:absolute;left:0;top:0;width:1808px;height:4px;border-radius:2px;background:{RAINBOW_H};transform-origin:0 50%;}}
.tick{{position:absolute;top:-4px;width:2px;height:12px;background:#3d3d40;}}
#ph{{position:absolute;left:{TX - 7}px;top:1023px;width:14px;height:14px;border-radius:50%;background:#fff;box-shadow:0 0 0 4px rgba(255,255,255,.18);}}
"""
chrome_body = f"""<div id="hdr">I MADE ME <span class="rb">WOKE</span></div>
    <div id="meta" data-layout-ignore><span>SLIDE <b id="cnt">01</b> / {N:02d}</span><span><span class="dot"></span><span id="clk">00:00</span></span></div>
    <div class="plbl" data-layout-ignore style="top:{SY}px">NOW</div>
    <div class="plbl" data-layout-ignore style="top:{NY - 34}px">NEXT</div>
    <div id="hl"></div>
    {thumbs}
    <div id="track"><div id="fill"></div>{ticks}</div>
    <div id="ph"></div>"""
cj = [f"    tl.fromTo('#hdr',{{opacity:0,y:-12}},{{opacity:1,y:0,duration:0.5,ease:'expo.out'}},0);",
      f"    tl.fromTo('#meta,.plbl',{{opacity:0}},{{opacity:1,duration:0.4,ease:'power2.out'}},0.1);",
      f"    tl.fromTo('#fill',{{scaleX:0}},{{scaleX:1,duration:{TOTAL},ease:'none'}},0);",
      f"    tl.fromTo('#ph',{{x:0}},{{x:1808,duration:{TOTAL},ease:'none'}},0);"]
for s in range(1, int(TOTAL) + 1):
    cj.append(f"    tl.set('#clk',{{textContent:'00:{s:02d}'}},{s});")
for i in range(N):
    t = START[i]
    cj.append(f"    tl.set('#cnt',{{textContent:'{i + 1:02d}'}},{t});")
    if i: cj.append(f"    tl.to('#hl',{{x:{round(slot(i) - TX, 2)},duration:0.42,ease:'expo.out'}},{t});")
    cj.append(f"    tl.to('#th{i}',{{opacity:1,y:-8,duration:0.32,ease:'expo.out'}},{t});")
    cj.append(f"    tl.to('#hl',{{y:-8,duration:0.32,ease:'expo.out'}},{t});" if i == 0 else "")
    cj.append(f"    tl.to('#tlb{i}',{{color:'{INK}',duration:0.2}},{t});")
    if i:
        cj.append(f"    tl.to('#th{i - 1}',{{opacity:0.62,y:0,duration:0.3,ease:'power2.out'}},{t});")
        cj.append(f"    tl.to('#tlb{i - 1}',{{color:'{MUTED}',duration:0.2}},{t});")
# finale: every slide lights up
cj.append(f"    tl.to('.th',{{opacity:1,duration:0.5,stagger:0.03,ease:'power2.out'}},{START[-1] + 0.6});")
chrome = scene("chrome", chrome_css, chrome_body, "\n".join(c for c in cj if c))

# ------------------------------------------------------------------ one scene per slide: stage + NOW title/note + NEXT card
SCENES = []
for i, s in enumerate(SL):
    cid = f"s{i:02d}"; d = DUR[i]
    fw, fh = fit(s["w"], s["h"], SW, SH)
    left, top = SX + (SW - fw) // 2, SY + (SH - fh) // 2
    scroll = s["id"] == "all"
    if scroll:   # the collage is 4:5: show it at stage width and scroll down through it
        fw, fh = SW, round(s["h"] * SW / s["w"]); left, top = SX, SY
    if s["gif"]:
        media = (f'<div class="gw" id="{cid}-gw" style="left:{left - SX}px;top:{top - SY}px;width:{fw}px;height:{fh}px">'
                 f'<img class="strip" id="{cid}-strip" src="assets/gif/{s["id"]}_strip.jpg" alt="" style="width:{fw * s["frames"]}px;height:{fh}px"></div>')
    else:
        media = (f'<div class="gw" id="{cid}-gw" style="left:{left - SX}px;top:{top - SY}px;width:{fw}px;height:{fh}px">'
                 f'<img id="{cid}-img" src="assets/stage/{s["id"]}.jpg" alt="" style="width:{fw}px;height:{fh}px"></div>')
    if i < N - 1:
        nx = SL[i + 1]
        nxt = (f'<div class="nx" id="{cid}-nx"><img src="assets/stage/{nx["id"]}.jpg" alt="" style="object-fit:{"contain" if nx["h"] > nx["w"] * 0.75 else "cover"}">'
               f'<span class="chip" data-layout-ignore>{i + 2:02d} · {nx["label"]}</span></div>')
    else:
        nxt = f'<div class="nx end" id="{cid}-nx"><div class="endt">THE END</div><div class="ends">made with GPT Image 2.6 on varg.ai</div></div>'
    css = f"""
#{cid}-stage{{position:absolute;left:{SX}px;top:{SY}px;width:{SW}px;height:{SH}px;border-radius:20px;overflow:hidden;background:{CARD};box-shadow:0 40px 90px -30px rgba(0,0,0,.85),0 0 0 1px rgba(255,255,255,.06);}}
.gw{{position:absolute;overflow:hidden;}}
.gw img{{position:absolute;left:0;top:0;display:block;max-width:none;}}
#{cid}-txt{{position:absolute;left:{PX}px;top:{SY + 36}px;width:{PW}px;display:flex;flex-direction:column;gap:22px;}}
#{cid}-t{{font-weight:900;font-size:58px;line-height:1.02;letter-spacing:-0.01em;margin:0;}}
#{cid}-n{{font-weight:500;font-size:28px;line-height:1.32;color:#d4d0ca;margin:0;}}
#{cid}-bar{{width:96px;height:6px;border-radius:3px;background:{RAINBOW_H};}}
.nx{{position:absolute;left:{PX}px;top:{NY}px;width:{PW}px;height:{NH}px;border-radius:14px;overflow:hidden;background:{CARD};box-shadow:0 0 0 1px rgba(255,255,255,.06);}}
.nx img{{width:100%;height:100%;display:block;opacity:0.85;}}
.chip{{position:absolute;left:12px;bottom:12px;font-weight:800;font-size:18px;letter-spacing:0.04em;padding:7px 12px;border-radius:999px;background:rgba(17,17,17,.85);white-space:nowrap;}}
.nx.end{{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:12px;}}
.endt{{font-weight:900;font-size:44px;}}
.ends{{font-weight:600;font-size:28px;text-align:center;color:{MUTED};}}
"""
    body = f"""<div id="{cid}-stage">{media}</div>
    <div id="{cid}-txt"><h2 id="{cid}-t">{s["label"]}</h2><div id="{cid}-bar"></div><p id="{cid}-n">{nb(s["note"])}</p></div>
    {nxt}"""
    js = [f"    tl.fromTo('#{cid}-stage',{{opacity:0,x:46,scale:0.985}},{{opacity:1,x:0,scale:1,duration:0.42,ease:'expo.out'}},0);",
          f"    tl.fromTo('#{cid}-t',{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.4,ease:'expo.out'}},0.08);",
          f"    tl.fromTo('#{cid}-bar',{{scaleX:0}},{{scaleX:1,duration:0.45,ease:'expo.out',transformOrigin:'0% 50%'}},0.16);",
          f"    tl.fromTo('#{cid}-n',{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.4,ease:'expo.out'}},0.24);",
          f"    tl.fromTo('#{cid}-nx',{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.4,ease:'expo.out'}},0.34);"]
    if s["gif"]:
        js.append(f"    gifSteps(tl,'#{cid}-strip',{s['frames']},{s['delay']},0,{d});")
    elif scroll:
        js.append(f"    tl.fromTo('#{cid}-gw',{{y:0}},{{y:{SH - fh},duration:{d - 1.2},ease:'sine.inOut'}},0.5);")
    else:
        js.append(f"    tl.fromTo('#{cid}-img',{{scale:1}},{{scale:1.035,duration:{d},ease:'none'}},0);")
    if i < N - 1:   # quick dip out on the cut
        js.append(f"    tl.to(['#{cid}-stage','#{cid}-txt','#{cid}-nx'],{{opacity:0,duration:0.16,ease:'power2.in'}},{d - 0.17});")
    SCENES.append((cid, START[i], d, scene(cid, css, body, "\n".join(js))))

(COMP / "chrome.html").write_text(chrome)
for cid, st, d, html in SCENES: (COMP / f"{cid}.html").write_text(html)
hosts = "\n".join(
    f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{st}" data-duration="{d}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:3"></div>'
    for cid, st, d, _ in SCENES)
index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: {BG}; }}
      #root {{ width: 100%; height: 100%; position: relative; }}
      #bg {{ position: absolute; inset: 0; z-index: 0;
        background: radial-gradient(1100px 700px at 30% 40%, rgba(255,140,0,0.05), rgba(255,140,0,0) 70%),
                    radial-gradient(900px 700px at 100% 100%, rgba(117,7,135,0.08), rgba(117,7,135,0) 70%), {BG}; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="bg" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="0"></div>
      <div id="chrome" data-composition-id="chrome" data-composition-src="compositions/chrome.html" data-start="0" data-duration="{TOTAL}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:2"></div>
{hosts}
{AUDIO}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
(ROOT / "index.html").write_text(index)
print(f"wrote {ROOT}: chrome + {len(SCENES)} slides, {TOTAL} s{' with music' if AUDIO else ' (silent)'}")
print(f"next: cd {ROOT} && npx hyperframes@0.9.15 check && npx hyperframes@0.9.15 render -o final.mp4 --crf 20")
