#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["opencv-python-headless>=4.9", "numpy", "pyspellchecker", "rapidocr-onnxruntime"]
# ///
"""media-judge: measure a finished video, image or track. Facts with timestamps and evidence, not grades.

  uv run judge.py video film.mp4 --out runs/film
  uv run judge.py video film.mp4 --out runs/film --refs ref.mp4 --template tpl.mp4 --one-character --allow "varg,Seedance"
  uv run judge.py image poster.png --out runs/poster --ref reference.png
  uv run judge.py audio track.mp3 --out runs/track
  uv run judge.py rank runs/a runs/b runs/c --out runs/ranking
  uv run judge.py reverse film.mp4 --out runs/film_reverse
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Stay polite on a shared laptop. MEDIA_JUDGE_THREADS raises the cap.
THREADS = os.environ.get("MEDIA_JUDGE_THREADS", "4")
for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(var, THREADS)

import cv2
import numpy as np

cv2.setNumThreads(int(THREADS))

import mj_attention
import mj_audio
import mj_common as C
import mj_compare
import mj_compress
import mj_continuity
import mj_frames
import mj_motion
import mj_observe
import mj_rank
import mj_text


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


def contact_sheet(path: str, shots: list[dict], ev: Path) -> list[str]:
    """First, middle and last frame of every shot. The picture the vision judge reads first."""
    rows, pages = [], []
    per_page = 8
    for s in shots:
        ts = [s["start"] + 0.02, s["start"] + s["duration"] / 2, max(s["end"] - 0.06, s["start"])]
        fs = [C.grab(path, t, 400) for t in ts]
        if any(f is None for f in fs):
            continue
        fs = [C.label_frame(f, f"#{s['index']} {C.fmt_t(t)}") for f, t in zip(fs, ts)]
        rows.append(cv2.hconcat(fs))
        if len(rows) == per_page:
            pages.append(rows)
            rows = []
    if rows:
        pages.append(rows)
    out = []
    ev.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(pages):
        w = page[0].shape[1]
        page = [cv2.resize(r, (w, page[0].shape[0])) for r in page]
        p = ev / f"contact_sheet_{i + 1}.jpg"
        cv2.imwrite(str(p), cv2.vconcat(page), [cv2.IMWRITE_JPEG_QUALITY, 85])
        out.append(str(p))
    return out


def spec_check(meta, want_size: str | None) -> dict:
    problems = []
    if meta.pix_fmt and meta.pix_fmt not in ("yuv420p", "yuvj420p"):
        problems.append(f"pixel format {meta.pix_fmt}, phones and platforms expect yuv420p")
    if meta.vcodec and meta.vcodec not in ("h264", "hevc", "av1", "vp9"):
        problems.append(f"codec {meta.vcodec}")
    if meta.width % 2 or meta.height % 2:
        problems.append("odd frame size")
    if want_size and f"{meta.width}x{meta.height}" != want_size:
        problems.append(f"size {meta.width}x{meta.height}, asked for {want_size}")
    return C.check("spec", "broken frames", "flagged" if problems else "clear", {**meta.to_json(), "problems": problems})


def first_seconds(tr, shots: list[dict], text: dict, path: str) -> dict:
    """What an ad has to do early, as facts. Windows follow Google's ABCD detector."""
    ts = [x for x in text.get("tracks", [])]
    first_text = min((x["t0"] for x in ts), default=None)
    shots_5s = sum(1 for s in shots if s["start"] < 5.0)
    return C.check("first_seconds", "ads and reels", "info",
                   {"first_frame_luma": round(float(tr.luma[0]), 1), "first_frame_is_black": bool(tr.luma[0] < C.th("black_luma")),
                    "first_cut_s": round(shots[0]["duration"], 2) if shots else None, "shots_in_first_5s": shots_5s,
                    "first_text_s": first_text},
                   note="ABCD's defaults: first shot under 3 s, 5 shots in any 5 s. Take the bar from your reference, not from here.")


def questions(facts: dict, sheets: list[str]) -> list[dict]:
    """What only eyes can settle. Each question names the frames to open and the fact to answer with."""
    by = {c["check"]: c for c in facts["checks"]}
    q = []
    def ev(name):
        return [e["evidence"] for e in by.get(name, {}).get("events", []) if isinstance(e, dict) and e.get("evidence")]
    q.append({"id": "story", "covers": "reverse engineering", "open": sheets, "ask": "Describe each shot in one line and name its subject. Do not judge it."})
    q.append({"id": "lead", "covers": "2 nothing leads the eye", "open": [by.get("leads_the_eye", {}).get("measured", {}).get("attention_sheet")], "ask": "The heat map is a measurement. For each shot, write the subject, then yes or no: does the top peak sit on the subject? Give the shot number."})
    q.append({"id": "scale", "covers": "1 everything is the same size", "open": sheets, "ask": "Per shot: name the largest element and the second largest. Write 'same size' when they are about equal."})
    q.append({"id": "product", "covers": "3 product is not readable", "open": sheets, "ask": "At each shot that shows the product: can you read its name and tell what it is from the frame alone? Quote what you can read."})
    q.append({"id": "cause", "covers": "4 motion has no cause", "open": ev("motion_cause") or sheets, "ask": "For each move: name what makes it start (a hit, a person, an earlier element, a sound). If you cannot name one, write 'no visible cause'."})
    q.append({"id": "pinned", "covers": "5 graphics are pinned to the screen", "open": ev("pinned_graphics") or sheets, "ask": "For each marked region: is it a caption or logo on the glass, or does it claim to belong to the scene? Quote it."})
    q.append({"id": "labels", "covers": "6 labels slide off", "open": ev("label_drift") or sheets, "ask": "For each label: name what it points at, then say whether it still touches that thing in the last frame of the strip."})
    q.append({"id": "continuity", "covers": "9 face, outfit, light", "open": ev("face_identity") + ev("outfit_change") + ev("face_light_change") + sheets, "ask": "List every change of person, clothing, hair, props or light direction between neighbouring shots that share a scene. Give both shot numbers."})
    q.append({"id": "spelling", "covers": "11 spelling", "open": ev("spelling"), "ask": "Read each crop letter by letter. Write the exact text on screen. Is the flagged word really misspelled, or did OCR misread it?"})
    q.append({"id": "artifacts", "covers": "AI artefacts", "open": sheets, "ask": "Name every object in each frame, then describe anything unusual about hands, faces, text, logos or counts. Give the shot number and where in the frame."})
    q.append({"id": "template", "covers": "12 template or references", "open": [e.get("evidence") for e in by.get("template_vs_references", {}).get("events", [])] + sheets, "ask": "Name three concrete things in these frames that could only have come from this brief. If you cannot name three, write how many you found."})
    return [x for x in q if any(x["open"])]


def report_md(facts: dict) -> str:
    s = mj_rank.summarize(facts)
    L = [f"# Facts: {Path(facts['file']).name}", "", f"State: **{s['ship_state']}**. {s['checks_clear']} of {s['checks_ran']} measured checks are clear. "
         f"Blockers: {len(s['blockers'])}. Major: {len(s['majors'])}. Minor: {len(s['minors'])}.", ""]
    if s["not_run"]:
        L += [f"Did not run: {', '.join(s['not_run'])}. Absence of a flag here says nothing.", ""]
    L += ["| Check | Covers | State | Key numbers |", "|---|---|---|---|"]
    for c in facts["checks"]:
        items = []
        for k, v in c["measured"].items():
            if isinstance(v, (int, float, str, bool)) and len(items) < 5:
                items.append(f"{k}={v}")
        L.append(f"| {c['check']} | {c['covers']} | {c['state']} | {'; '.join(items)} |")
    L.append("")
    flagged = [c for c in facts["checks"] if c["state"] == "flagged"]
    if flagged:
        L += ["## Flagged", ""]
        for c in flagged:
            sev = mj_rank.SEVERITY.get(c["check"], "minor")
            L.append(f"### {c['check']} ({sev})")
            if c["note"]:
                L.append(c["note"])
            for e in c["events"][:10]:
                if isinstance(e, dict):
                    t = e.get("t")
                    head = f"{C.fmt_t(t)}" if isinstance(t, (int, float)) else "-"
                    rest = "; ".join(f"{k}={v}" for k, v in e.items() if k not in ("t", "evidence", "per_shot") and not isinstance(v, (dict, list)))
                    L.append(f"- {head} {rest}" + (f" [evidence]({e['evidence']})" if e.get("evidence") else ""))
            L.append("")
    untested = [c for c in facts["checks"] if c["state"] in ("info", "not_run")]
    if untested:
        L += ["## Not settled by this run", "", "These are numbers without a pass or fail. A clear report does not cover them.", ""]
        for c in untested:
            L.append(f"- {c['check']} ({c['covers']})" + (f": {c['note']}" if c["note"] else ""))
        L.append("")
    L += ["## Shots", "", "| # | Start | Length |", "|---|---|---|"]
    for sh in facts.get("shots", [])[:80]:
        L.append(f"| {sh['index']} | {C.fmt_t(sh['start'])} | {sh['duration']:.2f} s |")
    L.append("")
    return "\n".join(L)


def video(args) -> dict:
    t0 = time.time()
    path = args.file
    out = Path(args.out)
    ev = out / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    for stale in ev.glob("*.jpg"):  # A picture from an earlier run must not pass as evidence for this one.
        stale.unlink()
    print("probe", flush=True)
    meta = C.probe(path)
    checks = [spec_check(meta, args.size)]
    if not meta.width:
        sys.exit("No video stream.")
    print(f"{meta.width}x{meta.height} {meta.fps:.2f} fps {meta.duration:.2f} s, reading every frame", flush=True)
    tr = mj_frames.trace(path, meta.pts, meta.v_start)
    shots = mj_frames.detect_shots(tr)
    print(f"{len(shots)} shots", flush=True)
    checks += mj_frames.frame_checks(path, tr, shots, meta.decode_errors, ev)
    sheets = contact_sheet(path, shots, ev)

    allow = {x.strip() for x in (args.allow or "").split(",") if x.strip()}
    expected = [l.strip() for l in Path(args.expected).read_text().splitlines() if l.strip()] if args.expected else []
    print("reading on-screen text", flush=True)
    text = mj_text.read_text(path, meta, shots)
    checks += mj_text.spelling_check(path, text, allow, expected, ev)
    checks += mj_text.layout_checks(path, meta, text, ev, args.platform)
    checks += mj_text.counter_check(path, meta, text, ev)
    checks.append(first_seconds(tr, shots, text, path))

    print("attention and load", flush=True)
    checks += mj_attention.attention_checks(path, meta, shots, {}, ev)

    print("sound", flush=True)
    script = Path(args.script).read_text() if args.script else None
    audio_res, onsets = mj_audio.audio_checks(path, meta, shots, script, args.music_only, ev)
    checks += audio_res

    print("motion", flush=True)
    gray = mj_motion.load_gray(path)
    n = min(len(gray), len(tr.t))
    gray = gray[:n]
    if n > 10:
        fps = 1 / float(np.median(np.diff(tr.t[:n])))
        cam = mj_motion.camera_track(gray, shots)
        checks += mj_motion.motion_cause_check(path, cam, shots, tr.t[:n], onsets, text, ev)
        pinned, _ = mj_motion.pinned_check(path, gray, cam, shots, tr.t[:n], text, fps, ev)
        checks += pinned
        labels = json.loads(Path(args.labels).read_text()) if args.labels else None
        checks += mj_motion.label_drift_check(path, gray, tr.t[:n], shots, text, labels, ev)
    del gray

    print("continuity", flush=True)
    groups = json.loads(args.groups) if args.groups else None
    checks += mj_continuity.continuity_checks(path, meta, shots, ev, args.one_character, groups)
    checks += mj_continuity.shot_colour_jumps(path, shots, ev, groups)

    if not args.no_upload:
        print("upload simulation and banding", flush=True)
        checks += mj_compress.compression_check(path, meta, shots, tr.luma, tr.t, ev, args.platform or "x")

    if args.refs or args.template:
        print("comparing with references", flush=True)
        checks += mj_compare.compare_checks(path, args.refs or [], args.template or [], ev)

    facts = {"file": path, "kind": "video", "probe": meta.to_json(), "shots": shots, "checks": checks, "contact_sheets": sheets,
             "elapsed_s": round(time.time() - t0, 1), "text_engine": text.get("engine"),
             "text_lines": [t["last"] for t in text.get("tracks", [])][:120]}
    facts["questions"] = questions(facts, sheets)
    return facts


def image(args) -> dict:
    t0 = time.time()
    out = Path(args.out)
    ev = out / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(args.file)
    if img is None:
        sys.exit("Could not read the image.")
    h, w = img.shape[:2]
    checks = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(img, (960, int(960 * h / w / 2) * 2), interpolation=cv2.INTER_AREA)
    sharp = float(cv2.Laplacian(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    checks.append(C.check("image_sharpness", "image", "flagged" if sharp < C.th("sharpness_var") else "clear", {"laplacian_variance": round(sharp, 1)}, thresholds=["sharpness_var"]))
    lo, hi = float((gray <= 2).mean()), float((gray >= 253).mean())
    checks.append(C.check("image_exposure", "image", "flagged" if lo > C.th("clip_share") or hi > C.th("clip_share") else "clear",
                          {"crushed_black_share": round(lo, 4), "blown_white_share": round(hi, 4), "mean_luma": round(float(gray.mean()), 1)}, thresholds=["clip_share"]))
    # Reuse the video tools by wrapping the still in a one-second clip for OCR and CAMBI.
    a = mj_attention.attention_map(small)
    ff = mj_attention.focus_facts(a)
    cf = mj_attention.clutter_facts(small)
    heat = cv2.applyColorMap((a * 255).astype(np.uint8), cv2.COLORMAP_JET)
    sheet = ev / "attention.jpg"
    cv2.imwrite(str(sheet), cv2.addWeighted(small, 0.55, heat, 0.45, 0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    no_lead = ff["peaks"] >= C.th("no_lead_peaks") and ff["dominance"] < C.th("no_lead_dominance")
    checks.append(C.check("leads_the_eye", "2 nothing leads the eye", "flagged" if no_lead else "clear", {**ff, "attention_sheet": str(sheet)}, thresholds=["no_lead_peaks", "no_lead_dominance"]))
    same = ff["peaks"] >= 4 and ff["biggest_over_second"] and ff["biggest_over_second"] < C.th("blob_scale_ratio")
    checks.append(C.check("object_scale", "1 everything is the same size", "flagged" if same else "clear", {"biggest_over_second": ff["biggest_over_second"]}, thresholds=["blob_scale_ratio"]))
    crowded = cf["edge_density"] > C.th("clutter_edges") or cf["element_count"] > C.th("clutter_elements")
    checks.append(C.check("frame_load", "3 too much on screen", "flagged" if crowded else "clear", cf, thresholds=["clutter_edges", "clutter_elements"]))
    name, ocr = mj_text._load_engine()
    lines = []
    if ocr:
        w_ocr = min(w, 1600)
        scaled = cv2.resize(img, (w_ocr, int(h * w_ocr / w))) if w_ocr != w else img
        dets = [d for d in ocr(scaled) if d["conf"] >= 0.45]
        lines = [d["text"] for d in dets]
        H_, W_ = scaled.shape[:2]
        tmp = ev / "image_tmp.mp4"
        C.run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-loop", "1", "-t", "0.6", "-i", args.file, "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-r", "10", str(tmp)], check=False)
        text = {"engine": name, "ocr_width": W_, "ocr_height": H_, "samples": [{"t": 0.1, "dets": dets}], "tracks": [{"t0": 0.1, "t_last": 0.1, "box": d["box"], "last": d["text"], "readings": [(0.1, d["text"], d["conf"])], "heights": [d["box"][3]], "boxes": [(0.1, d["box"])]} for d in dets]}
        allow = {x.strip() for x in (args.allow or "").split(",") if x.strip()}
        expected = [l.strip() for l in Path(args.expected).read_text().splitlines() if l.strip()] if args.expected else []
        if tmp.exists():
            checks += mj_text.spelling_check(str(tmp), text, allow, expected, ev)
            checks += [c for c in mj_text.layout_checks(str(tmp), C.probe(str(tmp), check_decode=False), text, ev, args.platform) if c["check"] != "reading_time"]
            tmp.unlink(missing_ok=True)
    else:
        checks.append(C.not_run("spelling", "11 spelling", "No OCR engine."))
    if args.ref:
        ref = cv2.imread(args.ref)
        if ref is not None:
            d = mj_compare.feature_distance(mj_compare.frame_features(img), mj_compare.frame_features(ref))
            checks.append(C.check("reference_match", "compare with the reference", "info", {"distance": {k: round(v, 3) for k, v in d.items()}, "blend": round(mj_compare.blend(d), 3), "reference": args.ref, "references": [{"blend": round(mj_compare.blend(d), 3)}]}))
    facts = {"file": args.file, "kind": "image", "probe": {"width": w, "height": h}, "checks": checks, "shots": [], "elapsed_s": round(time.time() - t0, 1), "text_lines": lines}
    return facts


def audio(args) -> dict:
    t0 = time.time()
    meta = C.probe(args.file)
    script = Path(args.script).read_text() if args.script else None
    res, _ = mj_audio.audio_checks(args.file, meta, [], script, args.music_only, Path(args.out) / "evidence")
    return {"file": args.file, "kind": "audio", "probe": meta.to_json(), "checks": res, "shots": [], "elapsed_s": round(time.time() - t0, 1)}


def reverse(args) -> dict:
    """A shot list with measurable fields: what a clone needs before anyone writes a prompt."""
    path = args.file
    ev = Path(args.out) / "evidence"
    meta = C.probe(path, check_decode=False)
    tr = mj_frames.trace(path, meta.pts, meta.v_start)
    shots = mj_frames.detect_shots(tr)
    text = mj_text.read_text(path, meta, shots)
    gray = mj_motion.load_gray(path)
    n = min(len(gray), len(tr.t))
    cam = mj_motion.camera_track(gray[:n], shots)
    fps = 1 / float(np.median(np.diff(tr.t[:n]))) if n > 1 else 24
    onsets, beats, tempo = np.zeros(0), np.zeros(0), 0.0
    audio_facts = {}
    if meta.has_audio:
        y = mj_audio.decode(path)
        mag = mj_audio.stft_mag(y)
        env = mj_audio.onset_envelope(mag)
        onsets, _ = mj_audio.pick_onsets(env)
        tempo, beats, _ = mj_audio.track_beats(env)
        audio_facts = {"tempo_bpm": round(tempo, 1), **mj_audio.loudness(path), "onsets_per_s": round(len(onsets) / max(meta.duration, 1e-6), 2)}
    rows = []
    for s in shots:
        f = C.grab(path, s["start"] + s["duration"] / 2, 480)
        d = mj_motion.describe_shot(cam, s, fps)
        row = {"shot": s["index"], "start": s["start"], "length_s": s["duration"], **d}
        if f is not None:
            cen, wgt = mj_compare._palette(f)
            order = np.argsort(-wgt)
            lab = cen[order][:4]
            bgr = cv2.cvtColor(np.clip(lab.reshape(1, -1, 3), [0, -127, -127], [100, 127, 127]).astype(np.float32), cv2.COLOR_Lab2BGR).reshape(-1, 3)
            row["palette"] = ["#%02x%02x%02x" % tuple(int(max(min(c, 1), 0) * 255) for c in (b[2], b[1], b[0])) for b in bgr]
            row["median_L"] = round(float(np.median(cv2.cvtColor(f.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[..., 0])), 1)
            row["focus"] = mj_attention.focus_facts(mj_attention.attention_map(f))["focus_xy"]
        row["text"] = [t["last"] for t in text.get("tracks", []) if t["t_last"] >= s["start"] and t["t0"] <= s["end"]][:8]
        row["sound_events"] = int(((onsets >= s["start"]) & (onsets < s["end"])).sum())
        rows.append(row)
    sheets = contact_sheet(path, shots, ev)
    durs = np.array([s["duration"] for s in shots]) if shots else np.zeros(1)
    return {"file": path, "kind": "reverse", "probe": meta.to_json(), "rhythm": {"shots": len(shots), "average_shot_s": round(float(durs.mean()), 2), "shortest_s": round(float(durs.min()), 2),
            "longest_s": round(float(durs.max()), 2), "first_cut_s": round(float(shots[0]["duration"]), 2) if shots else None, "cuts_per_10s": round(len(shots) / max(meta.duration, 1e-6) * 10, 2)},
            "audio": audio_facts, "shots": rows, "contact_sheets": sheets, "checks": []}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("video")
    v.add_argument("file")
    v.add_argument("--out", required=True)
    v.add_argument("--refs", nargs="*", help="reference videos it should resemble")
    v.add_argument("--template", nargs="*", help="template renders it should not resemble")
    v.add_argument("--allow", help="comma separated words the spell check should accept: brand and product names")
    v.add_argument("--expected", help="text file with the exact lines that must appear on screen")
    v.add_argument("--script", help="text file with the voice-over script")
    v.add_argument("--labels", help="JSON list of {t0, t1, label_box, anchor_box, text} in 480 px wide coordinates")
    v.add_argument("--groups", help="JSON list of shot-index lists that share one scene, like [[0,1,2],[5,6]]")
    v.add_argument("--one-character", action="store_true", help="every face should be the same person")
    v.add_argument("--platform", choices=["x", "youtube", "reels", "tiktok", "shorts"], help="sets safe zones and the upload simulation")
    v.add_argument("--size", help="required frame size like 1080x1920")
    v.add_argument("--music-only", action="store_true", help="no voice in this piece")
    v.add_argument("--no-upload", action="store_true", help="skip the upload simulation")
    i = sub.add_parser("image")
    i.add_argument("file")
    i.add_argument("--out", required=True)
    i.add_argument("--ref")
    i.add_argument("--allow")
    i.add_argument("--expected")
    i.add_argument("--platform", choices=["x", "youtube", "reels", "tiktok", "shorts"])
    a = sub.add_parser("audio")
    a.add_argument("file")
    a.add_argument("--out", required=True)
    a.add_argument("--script")
    a.add_argument("--music-only", action="store_true")
    o = sub.add_parser("observed", help="compare two takes from a judge's observation files")
    o.add_argument("--a", nargs="+", required=True, help="one or more observation JSON files for take A")
    o.add_argument("--b", nargs="+", required=True, help="one or more for take B")
    o.add_argument("--margin", type=int, default=2)
    r = sub.add_parser("rank")
    r.add_argument("runs", nargs="+")
    r.add_argument("--out", required=True)
    b = sub.add_parser("reverse")
    b.add_argument("file")
    b.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.cmd == "observed":
        print(json.dumps(mj_observe.compare(mj_observe.tally(args.a), mj_observe.tally(args.b), args.margin), indent=1))
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "rank":
        res = mj_rank.rank(args.runs)
        (out / "ranking.json").write_text(json.dumps(clean(res), indent=1))
        (out / "ranking.md").write_text(mj_rank.rank_md(res))
        print(mj_rank.rank_md(res))
        return
    facts = {"video": video, "image": image, "audio": audio, "reverse": reverse}[args.cmd](args)
    facts = clean(facts)
    (out / "facts.json").write_text(json.dumps(facts, indent=1))
    if args.cmd == "reverse":
        print(json.dumps({k: facts[k] for k in ("rhythm", "audio", "contact_sheets")}, indent=1))
        print(f"\nWrote {out / 'facts.json'}")
        return
    (out / "report.md").write_text(report_md(facts))
    s = mj_rank.summarize(facts)
    print(json.dumps({k: s[k] for k in ("ship_state", "blockers", "majors", "minors", "checks_clear", "checks_ran", "not_run")}, indent=1))
    print(f"\nWrote {out / 'report.md'} and {out / 'facts.json'} in {facts.get('elapsed_s')} s")
    # 0 nothing flagged, 1 flags to look at, 2 the tool itself failed
    sys.exit(1 if s["blockers"] or s["majors"] or s["minors"] else 0)


if __name__ == "__main__":
    main()
