"""film_build.py: the build stage: a HyperFrames project in the archive desk look, from the re-timed storyboard.

For the whole film (`project/`) or one act (`project_acts/A1/`, times shifted to start at 0, so acts render side by side and join
with stream copy). The page is templates/film/ (index.html, film.css, film.js): this module writes each beat as markup with
data- attributes, copies the pictures the beats use, inlines the maps (ids made unique per beat), vendors GSAP and the two fonts so
the render never touches the network, and writes the two small files `npx hyperframes` expects.

Between acts the film dips to dark: the last beat of an act fades out and the first beat of the next fades in, so two separately
rendered acts meet on the same near-dark frame. The root duration is whole frames minus 1 ms (references/render-traps.md, trap 4).
Standard library only; vendoring needs npm once (or its cache).
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_lib import SKILL, FilmError, Project  # noqa: E402

HF_PACKAGE = "hyperframes@0.8.216"
FONTS = "playfair-display,ibm-plex-mono"
TEMPLATE = SKILL / "templates" / "film"
EPSILON = 0.001
NUMBER_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "twenty", "thirty", "forty", "fifty", "sixty",
                "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion", "trillion", "point", "percent", "%"}


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def is_number(word: str) -> bool:
    w = re.sub(r"[^\w%.]", "", word.lower())
    return bool(re.match(r"^\d", w)) or w in NUMBER_WORDS


def counter_window(beat: dict, timings: dict) -> tuple[float, float]:
    """(start, end) in seconds from the beat start: counting begins with the line, and ends when the spoken number does."""
    lid = beat["counter"]["line"]
    start = beat["line_starts"][lid]
    line = timings["lines"][lid]
    at = max(0.4, start + line["speech_start"] - beat["start"])
    words = line["words"]
    run = []
    for i, w in enumerate(words):
        if is_number(w["text"]):
            run.append(i)
        elif run:
            break
    end_abs = start + (words[run[-1]]["end"] if run else line["speech_end"])
    end = min(max(end_abs - beat["start"], at + 0.6), max(at + 0.6, beat["duration"] - 0.4))
    return round(at, 3), round(end, 3)


def credit_text(entry: dict | None) -> str:
    if not entry or entry.get("licence_code") in ("user", "pdm-map", "synth") or entry.get("kind") != "archive":
        return ""
    who = entry.get("author") or "unknown"
    where = {"wikimedia-commons": "Wikimedia Commons"}.get(entry.get("source", ""), (entry.get("source") or "").capitalize())
    text = f"{who} / {entry.get('licence', '')} / {where}".strip(" /")
    return text if len(text) <= 112 else text[:109].rstrip() + "..."


def _svg(path: Path, prefix: str) -> str:
    text = re.sub(r"^<\?xml[^>]*\?>\s*", "", path.read_text(encoding="utf-8")).strip()
    return re.sub(r'\bid="(route-\d+)"', rf'id="{prefix}-\1"', text)


def beat_html(beat: dict, index: int, total: int, ctx: dict) -> str:
    t0 = ctx["t0"]
    cam = beat["camera"]
    attrs = [("data-t0", round(beat["start"] - t0, 4)), ("data-t1", round(beat["end"] - t0, 4)), ("data-kind", beat["kind"]), ("data-fx", cam["fx"]), ("data-fy", cam["fy"]),
             ("data-s0", cam["s0"]), ("data-rate", cam["rate"]), ("data-vx", cam["vx"]), ("data-vy", cam["vy"])]
    if ctx.get("dip_in"):
        attrs.append(("data-dip-in", ctx["dip_in"]))
    if ctx.get("dip_out"):
        attrs.append(("data-dip-out", ctx["dip_out"]))
    counter = beat.get("counter")
    if counter:
        at, end = counter_window(beat, ctx["timings"])
        attrs += [("data-count-from", _num(counter["from"])), ("data-count-to", _num(counter["to"])), ("data-count-at", at), ("data-count-end", end)]
    caption = beat.get("caption") or beat["id"]
    kind = beat["kind"]
    if kind == "map":
        plate = f'<figure class="plate"><div class="mapbox">{_svg(ctx["root"] / beat["map_file"], beat["id"])}</div></figure>'
    elif kind == "archive":
        inset = f'<div class="inset">{_svg(ctx["root"] / beat["inset_file"], beat["id"] + "i")}</div>' if beat.get("inset_file") else ""
        plate = f'<figure class="plate"><img class="shot" src="{esc(beat["asset"])}" alt="{esc(caption)}" />{inset}</figure>'
    else:
        plate = f'<figure class="plate title"><h2 class="big">{esc(caption)}</h2></figure>'
    stamp = f'No. {index + 1:02d} / {total:02d}' + (f'<br />{esc(beat["date"])}' if beat.get("date") else "")
    parts = [plate, f'<p class="stamp">{stamp}</p>']
    if kind != "title":
        parts.append(f'<h2 class="caption">{esc(caption)}</h2>')
    if counter:
        digits = len(f"{counter['to']:,.0f}") if float(counter["to"]).is_integer() else len(f"{counter['to']:,}")
        size = min(104, int(384 / (max(digits, 1) * 0.62)))                       # the biggest number must fit the 384 px column
        # one text block: the number and its label are inline lines of one paragraph, so the layout check reads them as one
        # block (two blocks would overlap: the number's glyph box is taller than its line) and the beat keeps four blocks
        parts.append(f'<p class="ledger"><span class="n" style="font-size:{size}px">{_num(counter["from"])}</span><br />'
                     f'<span class="l">{esc(counter["label"])}</span></p>')
    credit = "" if ctx["burn"] else credit_text(ctx["assets"].get(beat.get("asset") or ""))
    if credit:
        parts.append(f'<p class="credit">{esc(credit)}</p>')
    cls = "beat first" if index == 0 and not ctx.get("dip_in") else "beat"
    return f'<section class="{cls}" id="{beat["id"]}" ' + " ".join(f'{k}="{v}"' for k, v in attrs) + ">\n  " + "\n  ".join(parts) + "\n</section>"


def subs_html(cues: list[dict], t0: float, t1: float) -> str:
    out = []
    for c in cues:
        if c["end"] <= t0 or c["start"] >= t1:
            continue
        text = esc(c["text"]).replace("\n", "<br />")
        out.append(f'<p class="sub" data-t0="{max(0.0, c["start"] - t0):.3f}" data-t1="{min(t1, c["end"]) - t0:.3f}">{text}</p>')
    return "\n".join(out)


def vendor(project_dir: Path) -> None:
    from character_project import vendor_command            # lazy: it adds the character kit to sys.path
    cmd = vendor_command(project_dir, False)
    cmd += ["-Fonts", FONTS] if cmd[0] == "powershell" else ["--fonts", FONTS]
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        raise FilmError(f"vendoring GSAP and the fonts failed (needs npm and the network once, then its cache works offline): {done.stderr.strip()[-300:]}")


def build_project(project: Project, sb: dict, timings: dict, assets: dict, out_dir: Path, act: str | None = None, burn: bool = False,
                  cues: list[dict] | None = None, vendor_from: Path | None = None) -> dict:
    beats = [b for b in sb["beats"] if act is None or b["act"] == act]
    if not beats:
        raise FilmError(f"no beats in act {act}")
    if "start" not in beats[0]:
        raise FilmError("the storyboard is not re-timed yet: run `film.py retime` (after the voice stage) first")
    fps = sb["fps"]
    t0, t1 = beats[0]["start"], beats[-1]["end"]
    total_beats = len(sb["beats"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_map = {a["file"]: a for a in assets.get("assets", [])}
    all_beats = sb["beats"]
    markup = []
    for i, beat in enumerate(beats):
        gi = all_beats.index(next(b for b in all_beats if b["id"] == beat["id"]))
        nxt = all_beats[gi + 1] if gi + 1 < len(all_beats) else None
        dip_in = beat["transition"]["duration"] if beat["transition"]["type"] == "dip" else 0
        dip_out = nxt["transition"]["duration"] if nxt and nxt["transition"]["type"] == "dip" else 0
        ctx = {"t0": t0, "timings": timings, "root": project.root, "assets": asset_map, "burn": burn, "dip_in": dip_in, "dip_out": dip_out}
        markup.append(beat_html(beat, gi, total_beats, ctx))
        if beat.get("asset"):
            dest = out_dir / beat["asset"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project.p(beat["asset"]), dest)
    page = (TEMPLATE / "index.html").read_text(encoding="utf-8")
    frames = round((t1 - t0) * fps)
    rate = f' data-fps="{int(fps)}"' if float(fps).is_integer() else ""     # a plain `npx hyperframes render` of this folder uses the film's rate
    page = page.replace('data-duration="0"', f'data-duration="{frames / fps - EPSILON:.4f}"{rate}', 1)
    page = page.replace('<script src="film.js"></script>', "<script>\n" + (TEMPLATE / "film.js").read_text(encoding="utf-8").strip() + "\n    </script>")    # inline, so the timeline registration is on the page
    page = page.replace("<!--BEATS-->", "\n".join(markup)).replace("<!--SUBS-->", subs_html(cues or [], t0, t1) if burn else "")
    (out_dir / "index.html").write_text(page, encoding="utf-8", newline="\n")
    shutil.copyfile(TEMPLATE / "film.css", out_dir / "film.css")
    if vendor_from and (Path(vendor_from) / "vendor").is_dir():
        shutil.copytree(Path(vendor_from) / "vendor", out_dir / "vendor", dirs_exist_ok=True)
    elif not (out_dir / "vendor" / "gsap.min.js").is_file():
        vendor(out_dir)
    from character_project import write_hf_files
    write_hf_files(out_dir, f"film-{act or 'all'}".lower())
    return {"dir": str(out_dir), "beats": [b["id"] for b in beats], "frames": frames, "seconds": frames / fps, "start": t0, "end": t1}
