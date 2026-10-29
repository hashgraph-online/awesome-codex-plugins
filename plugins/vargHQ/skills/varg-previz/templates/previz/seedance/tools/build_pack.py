#!/usr/bin/env python3
"""Builds a Seedance 2.5 video-to-video pack from clean previz frames. All project data lives in seedance/pack.json
(refs, runs, look); per-shot actions come from the storyboard's "action" field (or pack.json "actions").

  python3 tools/build_pack.py --check          validate pack.json against the storyboard (no frames needed)
  python3 tools/build_pack.py --plan           shot list for capture.mjs (last shot of each run padded to whole seconds)
  bun tools/capture.mjs <frames> "$(python3 tools/build_pack.py --plan)"   render frames from the running previz
  python3 tools/build_pack.py <frames>         encode shots, cut one @video1 clip per run, write requests.json,
                                               PROMPTS.md and the index.html review board
  add --runs A,C to any of these to work on some runs only (a retake, or one cheap test run first)
Nothing here calls varg: the pack is for review; generation runs only after the user says go.
"""
import html, json, math, shutil, struct, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # previz/seedance
PREVIZ = HERE.parent                                    # previz/
ROOT = PREVIZ.parent                                    # project root
FPS = 24
CFG = json.loads((PREVIZ / "config.json").read_text())
SB_DATA = json.loads((PREVIZ / CFG.get("storyboard", "../storyboard.json")).resolve().read_text())
SB = {s["id"]: s for s in SB_DATA["shots"]}
PACK = json.loads((HERE / "pack.json").read_text())
ASPECT = CFG.get("aspect") or SB_DATA.get("aspect") or "9:16"
REF = PACK.get("refs", {})
RUNS = PACK.get("runs", [])
if "--runs" in sys.argv:
    _keep = sys.argv[sys.argv.index("--runs") + 1].split(",")
    del sys.argv[sys.argv.index("--runs"):sys.argv.index("--runs") + 2]
    RUNS = [r for r in RUNS if r["key"] in _keep]
    if not RUNS: sys.exit(f"--runs {','.join(_keep)}: no such run (have {', '.join(r['key'] for r in PACK.get('runs', []))})")
MODEL = PACK.get("model", "byteplus:dreamina-seedance-2-5-260628")
RES = PACK.get("resolution", "480p")
LOOK = "Look: " + PACK.get("look", "").strip()
RULES = PACK.get("rules") or (f"Full-bleed {ASPECT} frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere "
                              "in the frame (all graphics are added later). No dialogue, no lip-sync.")
VIDEO = PACK.get("video_line") or (
    "@video1 is a grey-box 3D previz of this sequence. Copy from @video1 ONLY the camera (framing, lens, camera position and "
    "movement), the hard-cut timing and the blocking (where everyone is and what they do). Do not copy its look: no flat grey "
    "shapes, no 3D render style, none of its colours.")
MIN_REF_PX = 300  # byteplus rejects reference images narrower than this


def action(i):
    return PACK.get("actions", {}).get(i) or SB[i].get("action") or SB[i].get("picture", "")


def image_size(p: Path):
    """(w, h) of a PNG/JPEG without dependencies, or None."""
    try:
        b = p.read_bytes()
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", b[16:24])
        if b[:2] == b"\xff\xd8":
            i = 2
            while i < len(b):
                if b[i] != 0xFF:
                    i += 1; continue
                m = b[i + 1]
                if m in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", b[i + 5:i + 9]); return w, h
                i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    except OSError:
        pass
    return None


def check():
    """Problems that cost money if found late. Returns a list of strings (empty = ok)."""
    errs, warn = [], []
    seen = {}
    for r in RUNS:
        for i in r["shots"]:
            if i not in SB: errs.append(f"run {r['key']}: shot {i} is not in the storyboard")
            elif i in seen: warn.append(f"shot {i} is in runs {seen[i]} and {r['key']}")
            seen.setdefault(i, r["key"])
        for k in r.get("refs", []):
            if k not in REF: errs.append(f"run {r['key']}: unknown ref '{k}'")
        if not r.get("refs") and not r.get("allow_no_refs"):
            errs.append(f"run {r['key']}: no image refs. Without them Seedance renders the previz mannequins and grey props as real "
                        "objects (tested). Add a sheet for every character/product in frame, or set \"allow_no_refs\": true")
        if len(r.get("refs", [])) > 9: errs.append(f"run {r['key']}: {len(r['refs'])} images, the model takes at most 9")
        ids = [i for i in r["shots"] if i in SB]
        if ids:
            d = sum(SB[i]["end"] - SB[i]["start"] for i in ids)
            if d > 15: warn.append(f"run {r['key']}: {d:.1f} s; runs of 4-11 s follow the previz better and retake cheaper")
            missing = [i for i in ids if not action(i)]
            if missing: errs.append(f"run {r['key']}: no action text for {', '.join(missing)} (storyboard 'action' or pack 'actions')")
    if len(RUNS) == len(PACK.get("runs", [])):
        for i, s in SB.items():
            if i not in seen and i not in PACK.get("reuse", {}) and s.get("source", "gen") not in ("reuse", "code"):
                warn.append(f"shot {i} is in no run and not marked reuse")
    used = {k for r in RUNS for k in r.get("refs", [])}
    for k, v in REF.items():
        if k not in used: continue
        p = HERE / "refs" / v["file"]
        src = ROOT / v["copy_from"] if v.get("copy_from") else None
        f = p if p.exists() else src if src and src.exists() else None
        if not f and not v.get("url"): errs.append(f"ref {k}: no local file ({p.relative_to(ROOT)}) and no url")
        if f:
            wh = image_size(f)
            if wh and min(wh) < MIN_REF_PX: errs.append(f"ref {k}: {wh[0]}x{wh[1]} px, pad it to at least {MIN_REF_PX} px on the short side")
        if not v.get("role"): errs.append(f"ref {k}: no 'role' line (what this image locks); the prompt needs it")
    return errs, warn


def run(*a):
    subprocess.run(a, check=True)


def build(frames: Path):
    errs, warn = check()
    for w in warn: print("warn:", w)
    if errs:
        for e in errs: print("ERROR:", e)
        sys.exit(1)
    for d in ("video", "shots", "refs"):
        (HERE / d).mkdir(exist_ok=True)
    for key, v in REF.items():
        if v.get("copy_from") and not (HERE / "refs" / v["file"]).exists():
            shutil.copy(ROOT / v["copy_from"], HERE / "refs" / v["file"])
    gens = []
    order = [x["key"] for x in PACK.get("runs", [])]
    for r in RUNS:
        n = order.index(r["key"]) + 1  # keep the pack-wide index, so file names stay stable when building some runs
        key, title, ids, refs, extra = r["key"], r.get("title", ""), r["shots"], r.get("refs", []), r.get("notes", [])
        # each shot: frames in the clip; the last shot carries the tail that pads the clip to whole seconds
        nfr = [len(list((frames / i).glob("*.png"))) for i in ids]
        if not all(nfr): sys.exit(f"no frames for {[i for i, f in zip(ids, nfr) if not f]} in {frames}: run capture.mjs first")
        for i in ids:
            run("ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / i / "%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-movflags", "+faststart", str(HERE / "shots" / f"{i}.mp4"))
        dur = sum(nfr) / FPS
        video = f"video_{n:02d}__{key}__{'-'.join(ids)}.mp4"
        lst = HERE / "video" / "_list.txt"
        lst.write_text("".join(f"file '{HERE / 'shots' / f'{i}.mp4'}'\n" for i in ids))
        run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(HERE / "video" / video))
        lst.unlink()
        rows, t = [], 0.0
        for i, f in zip(ids, nfr):
            s = SB[i]; d = s["end"] - s["start"]
            rows.append(dict(id=i, a=t, b=t + d, at=s["start"], line=s.get("line") or s.get("lyric") or ""))
            t += f / FPS
        D = round(dur)
        lines = [VIDEO] + [f"@image{k + 1} is {REF[x]['role']}" for k, x in enumerate(refs)] + extra + ([LOOK] if PACK.get("look") else []) + [""]
        lines.append(f"{len(ids)} shots, hard cuts exactly as in @video1:" if len(ids) > 1 else "One continuous shot, as in @video1:")
        for k, x in enumerate(rows, 1):
            end = D if k == len(rows) else x["b"]
            lines.append(f"{k}. {x['a']:.1f}–{end:.1f} s. {action(x['id'])}")
        lines += ["", f"Camera: one move per shot, as in @video1. {RULES}"]
        prompt = "\n".join(lines)
        files = [{"url": REF[x].get("url") or f"<upload refs/{REF[x]['file']} first>"} for x in refs] + [{"url": f"<upload video/{video} first>"}]
        provider = MODEL.split(":")[0]
        req = {"tool": "video", "input": {
            "model": MODEL, "prompt": prompt, "files": files,
            "aspect_ratio": ASPECT, "resolution": RES, "duration": D, "audio": False}}
        if provider == "byteplus":
            req["input"]["provider_options"] = {"byteplus": {"omni_reference_task_type": "reference", "generate_audio": False, "watermark": False}}
        gens.append(dict(n=n, key=key, title=title, ids=ids, refs=refs, video=video, D=D, rows=rows, prompt=prompt, req=req))
    write_outputs(gens)


def write_outputs(gens):
    total = sum(g["D"] for g in gens)
    cps = PACK.get("credits_per_second")
    est = f"≈{round(total * cps):,} credits at the last billed rate ({cps}/s)".replace(",", " ") if cps else "run estimate_cost for the price"
    uploads = sorted({REF[r]["file"] for g in gens for r in g["refs"] if not REF[r].get("url")})
    reuse, lips = PACK.get("reuse", {}), PACK.get("lipsync", [])
    json.dump({"note": "Seedance video-to-video requests (varg call_tool). NOT RUN. Before running: upload the reference videos "
                       "and the refs marked <upload …>, paste their URLs, then estimate_cost and get a go.",
               "requests": {f"{g['n']:02d}_{g['key']}": g["req"] for g in gens}},
              open(HERE / "requests.json", "w"), indent=1, ensure_ascii=False)
    title = PACK.get("title") or CFG.get("title") or "Seedance pack"
    md = [f"# Seedance pack · {title}", "",
          "Not generated. Each run = consecutive shots from ONE location, with its own grey-box previz clip as @video1 "
          "(camera, cuts and blocking only) and still references for everything that is in frame.", "",
          f"- Model route `{MODEL}` (video-to-video), {RES}, {ASPECT}, no audio, reference mode.",
          f"- {len(gens)} runs, {total} s in total; {est}.",
          *( [f"- Reused, not generated: " + ", ".join(f"{k} ({v})" for k, v in reuse.items()) + "."] if reuse else []),
          *( [f"- After generation: lip-sync {', '.join(lips)} from the vocal/voice slices."] if lips else []),
          f"- To upload before running: the {len(gens)} files in `video/`" + (", and " + ", ".join(f"`refs/{u}`" for u in uploads) if uploads else "") + ".", "",
          "| # | run | shots | @video1 | length | refs |", "|---|---|---|---|---|---|"]
    for g in gens:
        md.append(f"| {g['n']:02d} | {g['key']} · {g['title']} | {' '.join(g['ids'])} | `video/{g['video']}` | {g['D']} s | "
                  + ", ".join(f"@image{k + 1} {r}" for k, r in enumerate(g["refs"])) + " |")
    for g in gens:
        md += ["", f"## {g['n']:02d} · {g['key']} · {g['title']}", "", "| shot | in the clip | on the timeline | line |", "|---|---|---|---|"]
        md += [f"| {r['id']} | {r['a']:.2f}–{r['b']:.2f} s | at {r['at']:.3f} s | {r['line']} |" for r in g["rows"]]
        md += ["", "References:", ""] + [f"- @image{k + 1} `refs/{REF[r]['file']}`" + ("" if REF[r].get("url") else " (upload first)") for k, r in enumerate(g["refs"])]
        md += [f"- @video1 `video/{g['video']}`", "", "```", g["prompt"], "```"]
    (HERE / "PROMPTS.md").write_text("\n".join(md) + "\n")

    aw, ah = (int(x) for x in ASPECT.split(":"))
    vw = 200 if aw < ah else 360
    cards = []
    for g in gens:
        imgs = "".join(f'<figure><img src="refs/{REF[r]["file"]}" alt="{r}" loading="lazy"><figcaption><b>@image{k + 1}</b> {r}'
                       f'{"" if REF[r].get("url") else " <em>upload first</em>"}</figcaption></figure>' for k, r in enumerate(g["refs"]))
        rows = "".join(f"<tr><td><b>{r['id']}</b></td><td>{r['a']:.2f}–{r['b']:.2f} s</td><td>→ {r['at']:.3f} s</td><td>{html.escape(r['line'])}</td></tr>" for r in g["rows"])
        cards.append(f"""<section id="g{g['n']:02d}"><h2><span class="n">{g['n']:02d}</span> {g['key']} · {html.escape(g['title'])} <small>{' '.join(g['ids'])} · {g['D']} s</small></h2>
<div class="row"><figure class="vid"><video src="video/{g['video']}" controls loop muted playsinline preload="metadata"></video><figcaption><b>@video1</b> previz: camera, cuts, blocking</figcaption></figure>
<div class="imgs">{imgs}</div></div><table>{rows}</table>
<details><summary>Prompt</summary><pre>{html.escape(g['prompt'])}</pre></details></section>""")
    nav = "".join(f'<a href="#g{g["n"]:02d}">{g["n"]:02d} {g["key"]}</a>' for g in gens)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Seedance Pack</title>
<style>:root{{--bg:#0b0d14;--p:#12151f;--l:#232838;--t:#e6e9f2;--m:#8a91a6;--o:#ff5315}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--t);font:14px/1.45 system-ui,sans-serif;padding:20px}}
h1{{font-size:20px;margin:0 0 4px}}.sub{{color:var(--m);margin-bottom:12px;max-width:1100px}}nav{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}}
nav a{{color:var(--t);text-decoration:none;border:1px solid var(--l);border-radius:6px;padding:3px 8px;font:12px ui-monospace,Menlo,monospace}}nav a:hover{{border-color:var(--o)}}
section{{background:var(--p);border:1px solid var(--l);border-radius:10px;padding:16px;margin-bottom:16px}}h2{{margin:0 0 12px;font-size:16px}}h2 small{{color:var(--m);font-weight:400}}
.n{{color:var(--o);font-family:ui-monospace,Menlo,monospace}}.row{{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}}figure{{margin:0}}
video{{width:{vw}px;max-width:100%;aspect-ratio:{aw}/{ah};background:#000;border-radius:6px;display:block}}.imgs{{display:flex;gap:12px;flex-wrap:wrap;flex:1}}
.imgs img{{height:190px;max-width:100%;border-radius:6px;border:1px solid var(--l);display:block}}figcaption{{font-size:12px;margin-top:5px;color:var(--m)}}figcaption b{{color:var(--t)}}em{{color:#ffb020;font-style:normal}}
table{{margin-top:12px;border-collapse:collapse;font:12px ui-monospace,Menlo,monospace}}td{{padding:2px 14px 2px 0}}
pre{{white-space:pre-wrap;background:#0b0d14;border:1px solid var(--l);border-radius:6px;padding:12px;font:12px/1.5 ui-monospace,Menlo,monospace}}summary{{cursor:pointer;margin-top:10px;color:var(--o)}}</style></head><body>
<h1>Seedance pack · {html.escape(title)}</h1>
<div class="sub">Not generated. {len(gens)} short video-to-video runs, {total} s total; {html.escape(est)}. Each run takes one previz clip (@video1: camera, cuts, blocking) plus stills for what is in frame.
{('Reused, not generated: ' + ', '.join(reuse) + '. ') if reuse else ''}{('Lip-sync after: ' + ', '.join(lips) + '. ') if lips else ''}Requests: requests.json · prompts: PROMPTS.md</div>
<nav>{nav}</nav>{''.join(cards)}</body></html>"""
    (HERE / "index.html").write_text(page)
    print(f"{len(gens)} runs, {total} s; {est}")


def plan():
    """Shot list for capture.mjs: every shot of every run; the last shot of a run gets the tail to whole seconds (min 4 s)."""
    out = []
    for r in RUNS:
        ids = r["shots"]
        fr = [round((SB[i]["end"] - SB[i]["start"]) * FPS) for i in ids]
        tail = max(4, math.ceil(sum(fr) / FPS - 1e-3)) * FPS - sum(fr)
        out += [f"{i}:{tail / FPS:.4f}" if i == ids[-1] and tail else i for i in ids]
    return ",".join(out)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if arg == "--plan":
        print(plan())
    elif arg == "--check":
        errs, warn = check()
        for w in warn: print("warn:", w)
        for e in errs: print("ERROR:", e)
        print("ok" if not errs else f"{len(errs)} error(s)")
        sys.exit(1 if errs else 0)
    else:
        build(Path(arg))
