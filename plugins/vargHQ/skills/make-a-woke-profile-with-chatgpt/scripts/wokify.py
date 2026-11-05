#!/usr/bin/env python3
"""Turn one selfie into the 12-tile "I MADE ME WOKE" set on varg (GPT Image 2.6). Standard library only.

  python3 wokify.py --selfie me.jpg --name "Alex" --pronouns "he/they" --out wokify-out --dry-run
  python3 wokify.py --selfie me.jpg --name "Alex" --pronouns "he/they" --out wokify-out
  python3 wokify.py --out wokify-out --only figure,card            # re-run some tiles (and their GIFs)
  python3 wokify.py --out wokify-out --fix-face figure             # likeness pass on one tile
  python3 wokify.py --out wokify-out --fix-logo figure --where "the sneakers"
  python3 wokify.py --out wokify-out --gif-only --only card        # re-animate after a fix

Key: VARG_API_KEY, else ~/.varg/credentials {"api_key": ...}. Tiles and prompts: tiles.json next to this file.
Every job is logged to <out>/run.json (job id, credits, output URL, prompt).
"""
import argparse, concurrent.futures as cf, json, os, shutil, sys, threading, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.varg.ai"
UA = "Mozilla/5.0 (wokify; +https://varg.ai/how-to)"   # the file CDN refuses requests without a browser-like UA
EST = {"selfie": 8, "gif": 7, "fix": 8, "fresh": 7}       # credits per call, measured 2026-11-05
LOCK = threading.Lock()                                  # run.json is shared by the worker threads


def key():
    k = os.environ.get("VARG_API_KEY")
    if not k:
        p = os.path.expanduser("~/.varg/credentials")
        if os.path.exists(p):
            k = json.load(open(p)).get("api_key")
    if not k:
        sys.exit("No varg key: set VARG_API_KEY (https://varg.ai/dashboard) or sign in with the varg CLI.")
    return k


def req(method, path, body=None, raw=None, ctype="application/json"):
    h = {"Authorization": f"Bearer {KEY}", "User-Agent": UA}
    data = None
    if body is not None:
        data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
    elif raw is not None:
        data, h["Content-Type"] = raw, ctype
    for attempt in range(6):
        try:
            r = urllib.request.Request(API + path, data=data, headers=h, method=method)
            return json.load(urllib.request.urlopen(r, timeout=180))
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:800]
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(5 * (attempt + 1)); continue
            raise SystemExit(f"HTTP {e.code} on {path}: {msg}")


def download(url, path):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=180) as resp, open(path, "wb") as f:
        shutil.copyfileobj(resp, f)


def upload(path):
    if path.startswith("http"):
        return path
    ext = os.path.splitext(path)[1].lower()
    ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext)
    if not ctype:
        sys.exit("The selfie must be PNG, JPEG or WebP.")
    return req("POST", "/v2/files", raw=open(path, "rb").read(), ctype=ctype)["url"]


def run_job(body):
    job = req("POST", "/v2/image", body)
    jid = job["id"]
    while job.get("status") not in ("completed", "failed", "cancelled"):
        time.sleep(5)
        job = req("GET", f"/v2/jobs/{jid}")
    if job["status"] != "completed":
        raise RuntimeError(f"{jid} {job['status']}: {json.dumps(job.get('error') or job)[:600]}")
    return jid, job["output"]["outputs"][0]["url"], job.get("actual_cost_cents")


def fill(text):
    return text.replace("{NAME}", A.name).replace("{PRONOUNS}", A.pronouns)


def log(rec):
    p = os.path.join(A.out, "run.json")
    with LOCK:
        data = json.load(open(p)) if os.path.exists(p) else {"jobs": []}
        data.setdefault("jobs", []).append(rec)
        json.dump(data, open(p, "w"), indent=1, ensure_ascii=False)


def last_url(tile, step):
    p = os.path.join(A.out, "run.json")
    with LOCK:
        jobs = json.load(open(p)).get("jobs", []) if os.path.exists(p) else []
    for r in reversed(jobs):
        if r["tile"] == tile and r["step"] == step:
            return r["url"]


def image_body(prompt, files, t, gif=None):
    body = {"model": t.get("route", "gpt_image_2_6"), "prompt": prompt}
    if files:
        body["files"] = [{"url": u} for u in files]
    if t.get("quality"):
        body["quality"] = t["quality"]
    fal = {}
    if gif:
        w, h = gif["size"]
        fal = {"output_format": "gif", "frame_count": gif["frames"], "frame_duration_ms": gif["frame_ms"], "image_size": {"width": w, "height": h}}
    elif t.get("image_size"):
        fal = {"image_size": {"width": t["image_size"][0], "height": t["image_size"][1]}}
    else:
        body["aspect_ratio"] = t.get("aspect_ratio", "1:1")
    if fal:
        body["provider_options"] = {"fal": fal}
    return body


def do_tile(t, selfie_url):
    tid, out = t["id"], A.out
    done = []
    if t["kind"] == "selfie-copy":
        if not A.selfie: download(selfie_url, f"{out}/before.png")
        elif A.selfie.startswith("http"): download(A.selfie, f"{out}/before.png")
        else: shutil.copy(A.selfie, f"{out}/before{os.path.splitext(A.selfie)[1].lower()}")
        return [f"{tid}: copied"]
    if t["kind"] == "shared" and not A.fresh:
        dst = f"{out}/{tid}.{t['ext']}"
        if not os.path.exists(dst) or A.force:
            download(t["shared"], dst)
        return [f"{tid}: shared file"]
    if t["kind"] == "shared":   # --fresh: make it from its prompt
        f = t["fresh"]
        if f.get("gif") and not f.get("aspect_ratio"):   # prompt-only GIF
            body = image_body(fill(f["prompt"]), [], t, gif=f["gif"])
            jid, url, c = run_job(body); download(url, f"{out}/{tid}.gif")
            log({"tile": tid, "step": "gif", "job": jid, "credits": c, "url": url, "prompt": body["prompt"]})
            return [f"{tid}: {jid} {c} cr"]
        body = image_body(fill(f["prompt"]), [], dict(t, aspect_ratio=f["aspect_ratio"]))
        jid, url, c = run_job(body); download(url, f"{out}/{tid}.png")
        log({"tile": tid, "step": "still", "job": jid, "credits": c, "url": url, "prompt": body["prompt"]})
        done.append(f"{tid}: {jid} {c} cr")
        if f.get("gif"):
            body = image_body(f["gif"]["prompt"], [url], t, gif=f["gif"])
            jid, gurl, c = run_job(body); download(gurl, f"{out}/{tid}.gif")
            log({"tile": tid, "step": "gif", "job": jid, "credits": c, "url": gurl, "prompt": body["prompt"]})
            done.append(f"{tid} gif: {jid} {c} cr")
        return done
    # selfie tiles: [base, selfie] or [selfie]
    still = f"{out}/{tid}.png"
    if not A.gif_only and (not os.path.exists(still) or A.force or A.only):
        files = [t["base"], selfie_url] if t.get("base") else [selfie_url]
        prompt = fill(t["prompt"]) + t.get("identity_line", SPEC["identity_line"])
        jid, url, c = run_job(image_body(prompt, files, t))
        download(url, still)
        log({"tile": tid, "step": "still", "job": jid, "credits": c, "url": url, "prompt": prompt, "files": files})
        done.append(f"{tid}: {jid} {c} cr")
    if t.get("gif") and (A.gif_only or A.force or A.only or done or not os.path.exists(f"{out}/{tid}.gif")):
        src = last_url(tid, "still")
        body = image_body(t["gif"]["prompt"], [src], t, gif=t["gif"])
        jid, url, c = run_job(body)
        download(url, f"{out}/{tid}.gif")
        log({"tile": tid, "step": "gif", "job": jid, "credits": c, "url": url, "prompt": body["prompt"], "files": [src]})
        done.append(f"{tid} gif: {jid} {c} cr")
    return done


def fix(tid, kind):
    t = TILES[tid]
    src = last_url(tid, "still")
    if not src:
        sys.exit(f"No still for {tid} in run.json: run the tile first.")
    if kind == "face":
        prompt = SPEC["face_fix_prompt"].replace("{WHO}", A.who or t.get("face_fix_who", ""))
        files = [src, SELFIE_URL()]
        body = image_body(prompt, files, dict(t, route="fal:openai/gpt-image-2.6/flare/edit"))
    else:
        if not A.where:
            sys.exit("--fix-logo needs --where, e.g. --where \"the sneakers\"")
        prompt = SPEC["logo_fix_prompt"].replace("{WHERE}", A.where)
        files = [src]
        body = image_body(prompt, files, t)
    still = f"{A.out}/{tid}.png"
    if os.path.exists(still):
        shutil.copy(still, f"{A.out}/{tid}.before-{kind}-fix.png")
    jid, url, c = run_job(body)
    download(url, still)
    log({"tile": tid, "step": "still", "fix": kind, "job": jid, "credits": c, "url": url, "prompt": prompt, "files": files})
    print(f"{tid} {kind} fix: {jid} {c} cr -> {still}")
    if t.get("gif"):
        print(f"  {tid} has a GIF: re-animate it with  --gif-only --only {tid}")


def SELFIE_URL():
    p = os.path.join(A.out, "run.json")
    with LOCK:
        data = json.load(open(p)) if os.path.exists(p) else {"jobs": []}
    if not A.selfie:
        if data.get("selfie_url"):
            return data["selfie_url"]
        sys.exit("--selfie is needed (no uploaded selfie recorded in run.json yet).")
    url = upload(A.selfie)   # the API dedupes by content, so re-uploading the same photo is free
    with LOCK:
        data = json.load(open(p)) if os.path.exists(p) else {"jobs": []}
        data["selfie_url"] = url
        json.dump(data, open(p, "w"), indent=1, ensure_ascii=False)
    return url


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selfie", help="your own photo: a path or URL (front-facing, sharp, good light)")
    ap.add_argument("--name", default="Alex", help="name for the profile page and the call tile")
    ap.add_argument("--pronouns", default="they/them")
    ap.add_argument("--out", default="wokify-out")
    ap.add_argument("--only", help="comma-separated tile ids: " + "before,me,friends,linkedin,colleagues,social,figure,card,pet,drink,home,game")
    ap.add_argument("--fresh", action="store_true", help="make pet, drink and home from their prompts instead of the shared files")
    ap.add_argument("--force", action="store_true", help="re-make tiles that already exist")
    ap.add_argument("--gif-only", action="store_true", help="only (re)run the GIF steps")
    ap.add_argument("--fix-face", metavar="TILE"); ap.add_argument("--who", help="override who the face fix targets")
    ap.add_argument("--fix-logo", metavar="TILE"); ap.add_argument("--where", help="where the logo is, for --fix-logo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    A = ap.parse_args()
    SPEC = json.load(open(os.path.join(HERE, "tiles.json")))
    TILES = {t["id"]: t for t in SPEC["tiles"]}
    os.makedirs(A.out, exist_ok=True)
    pick = [TILES[i.strip()] for i in A.only.split(",")] if A.only else SPEC["tiles"]

    if A.dry_run:
        total = 0
        for t in pick:
            if t["kind"] == "selfie":
                c = (0 if A.gif_only else EST["selfie"]) + (EST["gif"] if t.get("gif") else 0)
            elif t["kind"] == "shared":
                c = (EST["fresh"] + (EST["gif"] if t["fresh"].get("gif") and t["fresh"].get("aspect_ratio") else 0)) if A.fresh else 0
            else:
                c = 0
            total += c
            print(f"{t['id']:<11} {t['kind']:<12} {'gif ' if t.get('gif') or (A.fresh and t.get('fresh', {}).get('gif')) else '    '}~{c} credits")
        print(f"total ~{total} credits (~${total / 100:.2f}); 1 credit = $0.01. Run without --dry-run to make them.")
        sys.exit(0)

    KEY = key()
    if A.fix_face or A.fix_logo:
        fix(A.fix_face or A.fix_logo, "face" if A.fix_face else "logo"); sys.exit(0)

    need_selfie = any(t["kind"] in ("selfie", "selfie-copy") for t in pick) and not A.gif_only
    selfie_url = SELFIE_URL() if need_selfie else None   # reuses the selfie recorded in run.json when --selfie is left out
    t0 = time.time()
    with cf.ThreadPoolExecutor(A.workers) as ex:
        futs = {ex.submit(do_tile, t, selfie_url): t["id"] for t in pick}
        for f in cf.as_completed(futs):
            try:
                for line in f.result(): print(line, flush=True)
            except Exception as e:
                print(f"{futs[f]}: FAILED {e}", flush=True)
    rp = os.path.join(A.out, "run.json")
    spent = sum((r.get("credits") or 0) for r in (json.load(open(rp)).get("jobs", []) if os.path.exists(rp) else []))
    print(f"done in {time.time() - t0:.0f}s; credits logged in run.json so far: {spent}. Next: look at every face, then python3 {HERE}/collage.py {A.out}")
