#!/usr/bin/env python3
"""Check a finished cut with numbers, then make the sheets you must look at yourself.

  python3 qa_cut.py out.mp4 --edl edit/edl.json --heard heard.json --intended edit/intended.json

--heard is a fresh transcript of out.mp4 (not the source transcript). A pass here never
means the edit is good: it means nothing measurable is broken. Watch it and listen to it.
"""
import argparse, array, json, math, os, re, subprocess, sys
from difflib import SequenceMatcher


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower().replace("-", " "))


def toks(path):
    w = json.load(open(path)); w = w["words"] if isinstance(w, dict) else w
    out = []
    for x in w:
        out += [norm(p) for p in re.split(r"[\s-]+", x["text"]) if norm(p)]
    return out


def audio_slices(video):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    pcm = array.array("h"); pcm.frombytes(raw[: len(raw) - len(raw) % 2])
    db = []
    for i in range(0, len(pcm) - 159, 160):
        rms = math.sqrt(sum(x * x for x in pcm[i:i + 160]) / 160) / 32768
        db.append(20 * math.log10(rms) if rms > 0 else -120.0)
    return db


def hot_joins(video, ts):
    """Joins where speech is still loud right at the cut: a clipped word. A fresh transcript misses these."""
    db = audio_slices(video)
    live = sorted(d for d in db if d > -80)
    if not live:
        return [], 0
    floor, voice = live[int(len(live) * 0.1)], live[int(len(live) * 0.9)]
    th = floor + 0.4 * (voice - floor)
    bad = []
    for t in ts:
        i = int(t / 0.01)
        before, after = db[max(0, i - 2):i], db[i:i + 2]
        if (before and max(before) > th) or (after and max(after) > th):
            bad.append({"join": round(t, 3), "before_db": round(max(before), 1) if before else None, "after_db": round(max(after), 1) if after else None})
    return bad, round(th, 1)


def join_flashes(video, ts, fps, limit=30.0):
    """A frame beside a join that looks nothing like its own side of the join.

    Frames are indexed, not seeked: a seek can land on the join and compare across the cut,
    which flags every real camera change.
    """
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    size = 64 * 36
    n = len(raw) // size
    frame = lambda i: raw[i * size:(i + 1) * size]
    differs = lambda x, y: sum(abs(p - q) for p, q in zip(x, y)) / size
    bad = []
    for t in ts:
        j = round(t * fps)
        for near, far, side in ((j, j + 4, "after"), (j - 1, j - 5, "before")):
            if 0 <= near < n and 0 <= far < n:
                v = differs(frame(near), frame(far))
                if v > limit:
                    bad.append({"join": round(t, 3), "side": side, "difference": round(v, 1)})
    return bad


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video"); p.add_argument("--edl"); p.add_argument("--heard"); p.add_argument("--intended")
    p.add_argument("--max-pause", type=float, default=0.6); p.add_argument("--silence-db", type=float, default=-35)
    p.add_argument("--lufs", type=float, default=-14); p.add_argument("--lufs-tol", type=float, default=1.0)
    p.add_argument("--no-loudness", action="store_true", help="for a rough cut: measure loudness but do not fail on it")
    p.add_argument("--tp", type=float, default=-1.5); p.add_argument("--min-match", type=float, default=0.95)
    p.add_argument("--accept-join", type=float, action="append", default=[], help="a join you reviewed and accept, in seconds. Repeat for each")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    d = a.out or os.path.join(os.path.dirname(a.video) or ".", "qa"); os.makedirs(d, exist_ok=True)
    r, fails = {}, []
    if not os.path.exists(a.video):
        sys.exit("no such file: %s" % a.video)
    info = json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt",
                          "-of", "json", a.video).stdout)
    dur = float(info["format"]["duration"]); r["duration"] = round(dur, 3)
    r["streams"] = [{k: s.get(k) for k in ("codec_type", "codec_name", "width", "height", "r_frame_rate", "pix_fmt") if s.get(k)} for s in info["streams"]]
    if not any(s["codec_type"] == "audio" for s in info["streams"]):
        fails.append("no audio stream")
    if a.edl:
        edl = json.load(open(a.edl)); fps = edl["fps"]
        r["edl_duration"] = edl["duration"]
        # AAC frames can pad a muxed file by a few hundredths, so allow two video frames
        if abs(dur - edl["duration"]) > 2 / fps + 0.05:
            fails.append("duration %.3f s differs from the EDL's %.3f s" % (dur, edl["duration"]))
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-af", "silencedetect=noise=%sdB:d=0.2" % a.silence_db, "-f", "null", "-").stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    gaps = [(round(s, 2), round(e, 2), round(e - s, 2)) for s, e in zip(st, en)]
    long_gaps = [g for g in gaps if g[2] > a.max_pause]
    r["pauses_over_limit"] = long_gaps; r["pauses_seen"] = len(gaps)
    if long_gaps:
        fails.append("%d pauses over %.2f s, first at %.2f s" % (len(long_gaps), a.max_pause, long_gaps[0][0]))
    if gaps and gaps[0][0] < 0.05 and gaps[0][2] > 0.3:
        fails.append("opens on %.2f s of silence" % gaps[0][2])
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-af", "loudnorm=print_format=json", "-f", "null", "-").stderr
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", err, re.S)
    if m:
        ld = json.loads(m.group(0)); r["lufs"] = float(ld["input_i"]); r["true_peak"] = float(ld["input_tp"])
        if not a.no_loudness and abs(r["lufs"] - a.lufs) > a.lufs_tol:
            fails.append("loudness %.1f LUFS, target %.1f" % (r["lufs"], a.lufs))
        if not a.no_loudness and r["true_peak"] > a.tp:
            fails.append("true peak %.1f dBTP, limit %.1f" % (r["true_peak"], a.tp))
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vf", "blackdetect=d=0.1:pix_th=0.1,freezedetect=n=-60dB:d=1.0", "-an", "-f", "null", "-").stderr
    black = re.findall(r"black_start:([\d.]+)", err); frozen = re.findall(r"freeze_start: ([\d.]+)", err)
    r["black_at"] = black; r["frozen_at"] = frozen
    if black:
        fails.append("black frames at %s s" % ", ".join(black[:5]))
    # a flash frame: the picture changes hard and changes back within a few frames
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vf", "scale=320:-2,select='gt(scene,0.2)',metadata=print:file=-", "-an", "-f", "null", "-")
    hits = [float(x) for x in re.findall(r"pts_time:([\d.]+)", err.stdout)]
    flash = sorted({round(hits[k], 3) for k in range(len(hits) - 1) if hits[k + 1] - hits[k] <= 0.25})
    r["hard_changes"] = [round(h, 3) for h in hits][:60]; r["flash_at"] = flash
    if a.edl:
        hot, th = hot_joins(a.video, [x["at"] for x in edl["segments"][1:]])
        r["hot_joins"], r["hot_join_threshold_db"] = hot, th
        hot = [h for h in hot if not any(abs(h["join"] - t) < 0.05 for t in a.accept_join)]
        r["accepted_joins"] = a.accept_join
        if hot:
            fails.append("%d of %d joins cut through speech, first at %.2f s: clipped words that a transcript will not show" % (len(hot), len(edl["segments"]) - 1, hot[0]["join"]))
        at_joins = join_flashes(a.video, [x["at"] for x in edl["segments"][1:]], fps)
        r["join_flash"] = at_joins
        flash += [x["join"] for x in at_joins]
    if flash:
        fails.append("flash frame near %s s: widen the cut, then look at qa/joins.jpg" % ", ".join(str(x) for x in sorted(set(flash))[:5]))
    if a.heard and a.intended:
        h, i = toks(a.heard), toks(a.intended)
        sm = SequenceMatcher(None, i, h, autojunk=False)
        match = sm.ratio()
        r["word_diff"] = [{"intended": " ".join(i[x:y]), "heard": " ".join(h[u:v])} for tag, x, y, u, v in sm.get_opcodes() if tag != "equal"][:30]
        r["words_heard"], r["words_intended"], r["word_match"] = len(h), len(i), round(match, 3)
        if match < a.min_match:
            fails.append("heard text matches the intended cut at %.1f%%, need %.0f%%; read word_diff in qa.json: a stutter the first transcript hid is a note, a clipped word is a bug" % (100 * match, 100 * a.min_match))
        r["doubled_words"] = sorted({" ".join(h[k:k + n]) for n in (1, 2, 3) for k in range(len(h) - 2 * n + 1) if h[k:k + n] == h[k + n:k + 2 * n]})[:12]
        rep = []
        for n in range(7, 3, -1):
            for k in range(len(h) - 2 * n + 1):
                if h[k:k + n] == h[k + n:k + 2 * n]:
                    rep.append(" ".join(h[k:k + n]))
        if rep:
            fails.append("a phrase is said twice in a row: \"%s\"" % rep[0]); r["repeats"] = rep[:5]
    # the sheets: what numbers cannot judge
    run("ffmpeg", "-y", "-v", "error", "-i", a.video, "-vf", "fps=%f,scale=480:-2,tile=5x4" % (20 / max(dur, 1)), "-frames:v", "1", os.path.join(d, "contact.jpg"))
    if a.edl:
        ts = [s["at"] for s in edl["segments"][1:]][:24]
        if ts:
            pick = "+".join("between(t,%.3f,%.3f)" % (t - 1.1 / fps, t + 1.1 / fps) for t in ts)
            run("ffmpeg", "-y", "-v", "error", "-i", a.video, "-vf", "select='%s',scale=320:-2,tile=6x%d" % (pick, max(1, len(ts) * 3 // 6 + 1)),
                "-fps_mode", "vfr", "-frames:v", "1", os.path.join(d, "joins.jpg"))
    r["sheets"] = [f for f in ("contact.jpg", "joins.jpg") if os.path.exists(os.path.join(d, f))]
    r["pass"] = not fails; r["fails"] = fails
    r["still_on_you"] = ["settle each doubled word: transcribe that stretch alone and read its energy, since ASR invents some and hides others","look at qa/joins.jpg: does each join read as one thought?", "listen: can you hear each join, is the music under the voice?",
                         "does the first 3 seconds earn the next 3?"]
    json.dump(r, open(os.path.join(d, "qa.json"), "w"), indent=1)
    print(json.dumps({k: r[k] for k in ("pass", "fails", "duration", "lufs", "true_peak", "word_match", "sheets") if k in r}, indent=1))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
