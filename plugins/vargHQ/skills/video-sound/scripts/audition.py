#!/usr/bin/env python3
"""Voice audition: the same hard lines in several voices, measured, on one page a person listens to and picks from.

An agent cannot hear a voice, so it pre-screens with numbers and the person makes the call.

  audition.py plan LINES.md VOICES.json -o audition.json     write the take list (line x voice x take)
  audition.py render audition.json                           generate every take through the varg API
                                                             (needs VARG_API_KEY; prints the price first)
  audition.py score audition.json                            measure each take: length, words/min, pauses,
                                                             loudness, pitch range (librosa optional)
  audition.py page audition.json -o audition.html            one page: players, numbers, a pick button

LINES.md: one line per row as  `L01 | text exactly as sent, with tags and punctuation | direction note`
VOICES.json: [{"name": "Brian", "model": "eleven_v4", "voice": "nPczCjzI2devNBz1zQrb", "why": "deep, warm"}]
Takes made elsewhere (MCP, another TTS)? Put "file": "takes/L01_brian_1.mp3" on the take in audition.json and skip
`render`.
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.request

API = os.environ.get("VARG_API_URL", "https://api.varg.ai/v2")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def read_lines(path):
    rows = []
    for raw in open(path):
        raw = raw.strip()
        if not raw or raw.startswith("#") or "|" not in raw:
            continue
        parts = [p.strip() for p in raw.strip("|").split("|")]
        if parts[0].lower() in ("id", "---") or set(parts[0]) <= set("-: "):
            continue
        rows.append({"id": parts[0], "text": parts[1], "direction": parts[2] if len(parts) > 2 else ""})
    if not rows:
        die(f"no lines in {path}; format: L01 | text | direction")
    return rows


def cmd_plan(args):
    lines, voices = read_lines(args.lines), json.load(open(args.voices))
    takes = []
    for ln in lines:
        for v in voices:
            for k in range(1, args.takes + 1):
                slug = re.sub(r"[^a-z0-9]+", "-", v["name"].lower()).strip("-")
                takes.append({"line": ln["id"], "voice": v["name"], "take": k,
                              "file": os.path.join("takes", f"{ln['id']}_{slug}_{k}.mp3")})
    out = {"lines": lines, "voices": voices, "takes": takes}
    json.dump(out, open(args.o, "w"), indent=1)
    print(f"wrote {args.o}: {len(lines)} lines x {len(voices)} voices x {args.takes} takes = {len(takes)} takes")


def _req(method, path, body=None):
    key = os.environ.get("VARG_API_KEY")
    if not key:
        die("VARG_API_KEY is not set. Generate the takes with the varg MCP instead and put their files in audition.json")
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": "video-sound-audition/1"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        die(f"varg API {e.code} on {path}: {e.read().decode()[:300]}")


def cmd_render(args):
    a = json.load(open(args.audition))
    base = os.path.dirname(os.path.abspath(args.audition))
    lines = {l["id"]: l for l in a["lines"]}
    voices = {v["name"]: v for v in a["voices"]}
    todo = [t for t in a["takes"] if not os.path.exists(os.path.join(base, t["file"]))]
    if not todo:
        print("every take already has a file")
        return
    total = 0.0
    for t in todo[:1]:
        v = voices[t["voice"]]
        est = _req("POST", "/estimate", {"model": v["model"], "text": lines[t["line"]]["text"], "voice": v["voice"]})
        total = (est.get("pricing", {}).get("user_price_usd") or 0) * len(todo)
    print(f"{len(todo)} takes, about ${total:.2f} in all (estimate from the first take)", flush=True)
    if not args.yes:
        die("re-run with --yes after the person approves the price")
    jobs = []
    for t in todo:
        v = voices[t["voice"]]
        body = {"model": v["model"], "text": lines[t["line"]]["text"], "voice": v["voice"]}
        body.update(v.get("extra", {}))
        j = _req("POST", "/tools/speech/call", body)
        jobs.append((t, j.get("id") or j.get("job_id")))
    os.makedirs(os.path.join(base, "takes"), exist_ok=True)
    for t, jid in jobs:
        for _ in range(120):
            j = _req("GET", f"/jobs/{jid}")
            if j.get("status") in ("completed", "failed", "cancelled"):
                break
            time.sleep(2)
        if j.get("status") != "completed":
            print(f"  {t['line']} {t['voice']} #{t['take']}: {j.get('status')} {j.get('error', '')}")
            continue
        url = j["output"]["outputs"][0]["url"]
        subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "-o", os.path.join(base, t["file"]), url], check=True)
        t["url"] = url
        print(f"  {t['line']} {t['voice']} #{t['take']}: ok")
    json.dump(a, open(args.audition, "w"), indent=1)


def measure(path, text):
    def ff(af):
        return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"],
                              stderr=subprocess.PIPE, text=True).stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               stdout=subprocess.PIPE, text=True).stdout.strip() or 0)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", ff("loudnorm=print_format=json"), re.S)
    lufs = float(json.loads(m.group(0))["input_i"]) if m else None
    sil = ff("silencedetect=noise=-40dB:d=0.18")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", sil)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)]
    pauses = []  # inner pauses only: not the lead-in or the tail
    for s, e in zip(starts, ends):
        if s > 0.05 and e < dur - 0.05:
            pauses.append(round(e - s, 2))
    words = len(re.findall(r"[A-Za-z0-9']+", re.sub(r"\[[^\]]*\]|<[^>]*>", " ", text)))
    speech = max(0.1, dur - sum(pauses))
    r = {"seconds": round(dur, 2), "words_per_min": round(words / speech * 60), "pauses": len(pauses),
         "pause_s": round(sum(pauses), 2), "longest_pause": max(pauses) if pauses else 0, "lufs": lufs}
    try:
        import librosa, numpy as np
        y, sr = librosa.load(path, sr=16000)
        f0, voiced, prob = librosa.pyin(y, fmin=60, fmax=500, sr=sr)
        f0 = f0[voiced & ~np.isnan(f0)]  # voiced frames only: breaths and sniffs carry no pitch
        if len(f0) > 10:
            st = 12 * np.log2(f0 / np.median(f0))
            st = st[np.abs(st) < 9]  # drop octave jumps (pitch-tracker errors on breaths and creaks)
            r["pitch_range_st"] = round(float(np.percentile(st, 90) - np.percentile(st, 10)), 1)
            r["pitch_sd_st"] = round(float(np.std(st)), 2)
            r["median_hz"] = round(float(np.median(f0)))
            # digitalsamba/claude-code-video-toolkit pick_takes.py: pitch spread minus one point per 10 wpm
            # outside 140-170 wpm (narration); a spread under 2 semitones reads flat
            wpm = r["words_per_min"]
            r["narration_score"] = round(r["pitch_sd_st"] - max(0, wpm - 170, 140 - wpm) / 10, 2)
            r["flat"] = r["pitch_sd_st"] < 2
    except ImportError:
        pass
    return r


def cmd_score(args):
    a = json.load(open(args.audition))
    base = os.path.dirname(os.path.abspath(args.audition))
    lines = {l["id"]: l for l in a["lines"]}
    for t in a["takes"]:
        p = os.path.join(base, t["file"])
        if os.path.exists(p):
            t["m"] = measure(p, lines[t["line"]]["text"])
    json.dump(a, open(args.audition, "w"), indent=1)
    for t in a["takes"]:
        if "m" in t:
            m = t["m"]
            print(f"{t['line']} {t['voice']:<14} #{t['take']}  {m['seconds']:>5}s  {m['words_per_min']:>3} wpm  "
                  f"{m['pauses']} pauses ({m['pause_s']}s)  pitch sd {m.get('pitch_sd_st', '-')} st"
                  f"{' FLAT' if m.get('flat') else ''}  score {m.get('narration_score', '-')}  {m['lufs']} LUFS")
    print("\nNumbers screen, people choose. pitch sd under 2 semitones reads flat; narration score = pitch sd minus "
          "1 per 10 wpm outside 140-170 (digitalsamba pick_takes). Dialogue may sit outside that pace on purpose.")


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Voice audition</title><style>
:root{--bg:#f6f6f4;--card:#fff;--ink:#16181d;--mute:#6b7280;--line:#e5e5e0;--acc:#2f6fed}
@media (prefers-color-scheme:dark){:root{--bg:#121316;--card:#1b1d22;--ink:#eceae4;--mute:#9aa0a8;--line:#2a2d33;--acc:#6c9cff}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Inter,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 80px}h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--mute);margin:0 0 24px}.line{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
.text{font-size:17px;margin:0 0 4px}.dir{color:var(--mute);font-size:13px;margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.take{border:1px solid var(--line);border-radius:8px;padding:10px}.take.picked{border-color:var(--acc);box-shadow:0 0 0 2px var(--acc) inset}
.v{font-weight:600}.n{color:var(--mute);font-size:12px;font-variant-numeric:tabular-nums}audio{width:100%;margin:6px 0}
button{font:inherit;border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;justify-content:center}
</style></head><body><main><h1>Voice audition</h1><p class="sub">Listen with headphones, then on a phone speaker. Pick one take per line, or one voice for all.</p>
<div id="app"></div></main><div class="bar"><span id="count">0 picked</span><button id="copy">Copy picks as JSON</button></div>
<script>const A=__DATA__;const picks={};const app=document.getElementById('app');
for(const l of A.lines){const box=document.createElement('section');box.className='line';
box.innerHTML=`<p class="text"></p><p class="dir"></p><div class="grid"></div>`;box.querySelector('.text').textContent=l.id+'  '+l.text;
box.querySelector('.dir').textContent=l.direction||'';const g=box.querySelector('.grid');
for(const t of A.takes.filter(t=>t.line===l.id)){const m=t.m||{};const d=document.createElement('div');d.className='take';
d.innerHTML=`<div class="v"></div><audio controls preload="none"></audio><div class="n"></div><button>Pick</button>`;
d.querySelector('.v').textContent=t.voice+' · take '+t.take;d.querySelector('audio').src=t.url||t.file;
d.querySelector('.n').textContent=m.seconds?`${m.seconds}s · ${m.words_per_min} wpm · ${m.pauses} pauses · pitch sd ${m.pitch_sd_st??'–'} st${m.flat?' · flat':''}`:'not measured';
d.querySelector('button').onclick=()=>{picks[l.id]={voice:t.voice,take:t.take,file:t.file};
g.querySelectorAll('.take').forEach(x=>x.classList.remove('picked'));d.classList.add('picked');
document.getElementById('count').textContent=Object.keys(picks).length+' picked';};g.appendChild(d);}
app.appendChild(box);}
document.getElementById('copy').onclick=()=>{navigator.clipboard.writeText(JSON.stringify(picks,null,1));};
</script></body></html>"""


def cmd_page(args):
    a = json.load(open(args.audition))
    data = json.dumps({"lines": a["lines"], "takes": a["takes"]}).replace("</", "<\\/")
    open(args.o, "w").write(PAGE.replace("__DATA__", data))
    print(f"wrote {args.o}: open it next to the takes/ folder")


def main():
    if not shutil.which("ffmpeg"):
        die("ffmpeg is not on PATH")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("plan"); a.add_argument("lines"); a.add_argument("voices"); a.add_argument("-o", default="audition.json")
    a.add_argument("--takes", type=int, default=2); a.set_defaults(fn=cmd_plan)
    a = sp.add_parser("render"); a.add_argument("audition"); a.add_argument("--yes", action="store_true")
    a.set_defaults(fn=cmd_render)
    a = sp.add_parser("score"); a.add_argument("audition"); a.set_defaults(fn=cmd_score)
    a = sp.add_parser("page"); a.add_argument("audition"); a.add_argument("-o", default="audition.html")
    a.set_defaults(fn=cmd_page)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
