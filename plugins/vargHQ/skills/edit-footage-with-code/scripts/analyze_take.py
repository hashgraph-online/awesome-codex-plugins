#!/usr/bin/env python3
"""Read a take before cutting it. Needs ffmpeg and ffprobe, nothing else.

  python3 analyze_take.py take.mp4 --words transcript.json --out edit/

Writes edit/take.json (speech regions, pauses, retake and filler candidates),
edit/edl.json (a draft cut list to change by hand), edit/intended.json (the words
the cut should still say) and edit/review.md.

Word timestamps say WHICH words were said, not WHERE to cut. ASR stretches
words across pauses, so every cut point here comes from the audio itself.
"""
import argparse, array, json, math, os, re, subprocess, sys

WIN = 0.01  # 10 ms loudness slices


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,r_frame_rate,avg_frame_rate,sample_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    def rate(x):
        n, _, m = (x or "0/1").partition("/")
        return float(n) / float(m or 1) if float(m or 1) else 0.0
    fps = rate(v["r_frame_rate"]) if v else 30.0
    avg = rate(v["avg_frame_rate"]) if v else fps
    return {"duration": float(d["format"]["duration"]), "fps": round(fps, 3), "avg_fps": round(avg, 3),
            "vfr": bool(v) and abs(fps - avg) > 0.005, "has_audio": a is not None,
            "sample_rate": int(a["sample_rate"]) if a else None}


def loudness_slices(path):
    """RMS of each 10 ms slice in dBFS, mono at 16 kHz."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    pcm = array.array("h"); pcm.frombytes(raw[: len(raw) - len(raw) % 2])
    if sys.byteorder == "big":
        pcm.byteswap()
    n = int(16000 * WIN)
    db = []
    for i in range(0, len(pcm) - n + 1, n):
        rms = math.sqrt(sum(s * s for s in pcm[i:i + n]) / n) / 32768
        db.append(20 * math.log10(rms) if rms > 0 else -120.0)
    return db


def picture_changes(path):
    """Hard changes and black stretches in the source: slates, fades and camera switches a cut must not touch."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
                        "scale=320:-2,select='gt(scene,0.25)',metadata=print:file=-", "-f", "null", "-"], capture_output=True, text=True)
    hard = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stdout)]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", "blackdetect=d=0.05:pix_th=0.1", "-f", "null", "-"],
                       capture_output=True, text=True)
    black = [[float(a), float(b)] for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    return hard, black


def pct(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, int(len(s) * p))] if s else -120.0


def threshold(db):
    """Sit between the room and the voice, measured on this take rather than fixed."""
    live = [d for d in db if d > -80]  # digital silence says nothing about the room
    if not live:
        raise SystemExit("no audio above -80 dBFS")
    floor, voice = pct(live, 0.10), pct(live, 0.90)
    return max(floor + 0.4 * (voice - floor), voice - 30), floor, voice


def speech_regions(db, th, fill=0.12, blip=0.08):
    regs, start = [], None
    for i, d in enumerate(db + [-120.0]):
        if d >= th and start is None:
            start = i
        elif d < th and start is not None:
            regs.append([start * WIN, i * WIN]); start = None
    merged = []
    for r in regs:
        if merged and r[0] - merged[-1][1] < fill:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [r for r in merged if r[1] - r[0] >= blip]


def overlap(a, b, regs):
    return sum(max(0.0, min(b, y) - max(a, x)) for x, y in regs)


def norm(t):
    return re.sub(r"[^a-z0-9']", "", t.lower())


def retimed(words, regs):
    """Flag words ASR placed inside silence or stretched across a pause. Their times are not moved."""
    out = []
    for w in words:
        a, b = float(w["start"]), float(w["end"])
        cover = overlap(a, b, regs) / max(b - a, 0.01)
        out.append({"text": w["text"].strip(), "start": round(a, 3), "end": round(b, 3), "voiced": round(cover, 2),
                    "drifted": cover < 0.25 or b - a > 1.2})
    return out


def retake_candidates(words, regs, min_run=4, window=40):
    toks = [norm(w["text"]) for w in words]
    found, i = [], 0
    while i < len(toks):
        best = None
        for j in range(i + 1, min(i + window, len(toks))):
            run = 0
            while j + run < len(toks) and i + run < j and toks[i + run] == toks[j + run] and toks[i + run]:
                run += 1
            if run >= min_run and (best is None or run > best[1]):
                best = (j, run)
        if best:
            j, run = best
            found.append({"attempt_from": i, "attempt_to": j - 1, "kept_from": j, "kept_to": j + run - 1,
                          "start": words[i]["start"], "end": words[j]["start"],
                          "text": " ".join(w["text"] for w in words[i:j]),
                          "repeated": " ".join(w["text"] for w in words[j:j + run]), "run": run,
                          "cover": round(run / (j - i), 2),
                          # the repeat must cover most of the attempt, or it is parallel wording, not a retake
                          "sure": run / (j - i) >= 0.6,
                          "default": "draft cuts the earlier attempt: check which take is really better" if run / (j - i) >= 0.6
                          else "listen first: this looks like parallel wording, so it is not cut"})
            i = j
        else:
            i += 1
    for n in (1, 2, 3):  # a stutter: the same one to three words twice in a row
        for k in range(len(toks) - 2 * n + 1):
            if all(toks[k:k + n]) and toks[k:k + n] == toks[k + n:k + 2 * n] and len("".join(toks[k:k + n])) > 1:
                found.append({"attempt_from": k, "attempt_to": k + n - 1, "kept_from": k + n, "kept_to": k + 2 * n - 1,
                              "start": words[k]["start"], "end": words[k + n]["start"], "text": " ".join(w["text"] for w in words[k:k + n]),
                              "repeated": " ".join(w["text"] for w in words[k + n:k + 2 * n]), "run": n, "cover": 1.0, "sure": False,
                              "default": "check this one: transcribe the stretch alone. A stutter here can be emphasis, or ASR's invention"})
    return sorted(found, key=lambda r: r["start"])


FILLERS = [(r"^(um+|uh+|er+|ah+|hm+|mm+)$", 1, "high"), (r"^you know$", 2, "medium"), (r"^i mean$", 2, "medium"),
           (r"^sort of$", 2, "low"), (r"^kind of$", 2, "low"), (r"^like$", 1, "low"), (r"^basically$", 1, "low")]


def filler_candidates(words):
    toks = [norm(w["text"]) for w in words]
    out = []
    for i in range(len(toks)):
        for rx, n, conf in FILLERS:
            if i + n <= len(toks) and re.match(rx, " ".join(toks[i:i + n])):
                out.append({"from": i, "to": i + n - 1, "start": words[i]["start"], "end": words[i + n - 1]["end"],
                            "text": " ".join(w["text"] for w in words[i:i + n]), "confidence": conf,
                            "context": " ".join(w["text"] for w in words[max(0, i - 4):i + n + 4])})
    return out


def quietest(db, a, b):
    """The quietest 10 ms slice between two times: the safest place for a cut."""
    i0, i1 = max(0, int(a / WIN)), min(len(db), max(int(a / WIN) + 1, int(b / WIN)))
    return (min(range(i0, i1), key=lambda i: db[i]) + 0.5) * WIN if i1 > i0 else a


def pauses_between(regs, words, db, duration, min_len, punct=None):
    out = []
    for k in range(len(regs) - 1):
        a, b = regs[k][1], regs[k + 1][0]
        if b - a < min_len:
            continue
        # the last word that began before the pause ended: nearest-time matching mislabels sentence ends
        before = [w for w in words if w["start"] < b - 0.02]
        prev = before[-1] if before else None
        out.append({"start": round(a, 3), "end": round(b, 3), "len": round(b - a, 3),
                    "after_word": prev["text"] if prev else None,
                    # island transcripts end every island with a period, so punctuation comes from the whole-file pass when given
                    "sentence_end": (any(a - 0.6 <= float(w["end"]) <= b + 0.6 and re.search(r"[.?!]$", w["text"].strip()) for w in punct)
                                     if punct else bool(prev and re.search(r"[.?!]$", prev["text"])))})
    return out


def snap(t, fps, up=False):
    f = t * fps
    return round((math.ceil(f - 1e-6) if up else math.floor(f + 1e-6)) / fps, 4)


def build_edl(info, regs, pauses, retakes, fillers, words, db, a, hard=(), black=()):
    fps = info["fps"]
    if not regs:
        raise SystemExit("no speech found")
    span = [max(0.0, regs[0][0] - a.lead), min(info["duration"], regs[-1][1] + a.tail)]
    raw = []

    def starts_near(t):
        """The speech region this word really opens, judged by the pause in front of it."""
        best = None
        for k in range(1, len(regs)):
            if t - 0.4 <= regs[k][0] <= t + 1.0 and regs[k][0] - regs[k - 1][1] >= 0.15:
                gap = regs[k][0] - regs[k - 1][1]
                if best is None or gap > best[0]:
                    best = (gap, regs[k][0])
        return best[1] if best else None

    for r in retakes:
        if r["run"] < a.min_run or not r["sure"]:
            continue
        opened = starts_near(r["start"])
        s0 = opened - a.lead if opened is not None else quietest(db, max(0, r["start"] - 0.25), r["start"] + 0.1)
        opened = starts_near(r["end"])
        e0 = opened - a.lead if opened is not None else quietest(db, max(s0 + 0.1, r["end"] - 0.3), r["end"] + 0.15)
        if e0 > s0:
            raw.append([s0, e0, "retake: " + r["text"][:80]])
    for p in pauses:
        hold = a.keep_sentence if p["sentence_end"] else a.keep_pause
        if p["len"] >= a.min_pause and p["len"] > hold + 0.05:
            # taking out under 0.2 s is a jump cut for nothing on a locked shot
            if p["len"] - hold >= 0.2:
                raw.append([p["start"] + hold - a.lead, p["end"] - a.lead, "pause %.2f s, hold %.2f s" % (p["len"], hold)])
    if a.cut_fillers:
        for f in fillers:
            if f["confidence"] == "high":
                raw.append([quietest(db, f["start"] - 0.08, f["start"] + 0.05), quietest(db, f["end"] - 0.05, f["end"] + 0.08), "filler: " + f["text"]])
    raw.sort()
    cuts = []
    for s0, e0, why in raw:
        # two cuts with no speech between them are one cut
        if cuts and s0 - cuts[-1]["end"] < 0.25 and overlap(cuts[-1]["end"], s0, regs) < 0.1:
            cuts[-1]["end"] = max(cuts[-1]["end"], e0); cuts[-1]["why"] += "; " + why
        elif cuts and s0 <= cuts[-1]["end"]:
            cuts[-1]["end"] = max(cuts[-1]["end"], e0); cuts[-1]["why"] += "; " + why
        else:
            cuts.append({"start": s0, "end": e0, "why": why})
    keep, at = [], span[0]
    for c in cuts:
        if c["start"] > at:
            keep.append([at, min(c["start"], span[1])])
        at = max(at, c["end"])
    if at < span[1]:
        keep.append([at, span[1]])
    # keep clear of slates, fades and camera switches: a stray frame there flashes at the join
    room, moved = 0.5, []
    for k in keep:
        for h in hard:
            if k[0] <= h <= k[0] + room:
                moved.append(round(k[0], 3)); k[0] = h + 1 / info["fps"]
            elif k[1] - room <= h <= k[1]:
                moved.append(round(k[1], 3)); k[1] = h - 1 / info["fps"]
        for b0, b1 in black:
            if b0 < k[1] <= b1 + 1 / info["fps"] or (k[0] < b0 < k[1] and k[1] - b0 < room):
                moved.append(round(k[1], 3)); k[1] = b0 - 1 / info["fps"]
            if b0 <= k[0] < b1 or (k[0] < b1 < k[1] and b1 - k[0] < room):
                moved.append(round(k[0], 3)); k[0] = b1 + 1 / info["fps"]
    keep = [k for k in keep if k[1] > k[0] and overlap(k[0], k[1], regs) >= 0.1]
    for c in cuts:
        c["start"], c["end"] = round(c["start"], 3), round(c["end"], 3)
    segs, t = [], 0
    for s, e in keep:
        s, e = snap(s, fps), snap(e, fps, up=True)
        frames = round((e - s) * fps)
        if frames < 2:
            continue
        segs.append({"id": "s%03d" % (len(segs) + 1), "in": s, "out": round(s + frames / fps, 4), "frames": frames,
                     "at": round(t / fps, 4)})
        t += frames
    return {"source": os.path.basename(a.take), "fps": fps, "frames": t, "duration": round(t / fps, 3),
            "source_duration": info["duration"], "segments": segs, "cuts": sorted(cuts, key=lambda c: c["start"]),
            "moved_for_picture": moved}


def review(info, th, floor, voice, words, pauses, retakes, fillers, edl):
    gaps = sum(1 for i in range(1, len(words)) if words[i]["start"] - words[i - 1]["end"] >= 0.4)
    long_p = [p for p in pauses if p["len"] >= 0.4]
    drift = [w for w in words if w["drifted"]]
    L = ["# Take review", "",
         "| | |", "|---|---|",
         "| Source | %.2f s at %s fps%s |" % (info["duration"], info["fps"], " **VARIABLE FRAME RATE: conform first**" if info["vfr"] else ""),
         "| Voice / room / cut threshold | %.1f / %.1f / %.1f dBFS |" % (voice, floor, th),
         "| Pauses of 0.4 s or more | audio: %d, word gaps: %d |" % (len(long_p), gaps),
         "| Words ASR placed badly | %d |" % len(drift),
         "| Hard picture changes in the source | %d |" % edl.get("hard_count", 0),
         "| Draft | %.2f s, %d segments |" % (edl["duration"], len(edl["segments"])), ""]
    if edl.get("moved_for_picture"):
        L += ["Moved %d cut edges away from a slate, fade or camera change: check them on the join sheet." % len(edl["moved_for_picture"]), ""]
    if drift:
        L += ["Do not cut from these word times: " + ", ".join("%s (%.2f-%.2f)" % (w["text"], w["start"], w["end"]) for w in drift[:12]), ""]
    L += ["## Retake candidates", ""]
    L += ["- %.2f s: \"%s\" then again \"%s\". %s" % (r["start"], r["text"][:90], r["repeated"][:60], r["default"]) for r in retakes] or ["None found. Reading the transcript yourself still matters: ASR hides some."]
    L += ["", "## Filler candidates (not cut unless you say so)", ""]
    L += ["- %.2f s [%s] \"%s\" in: %s" % (f["start"], f["confidence"], f["text"], f["context"]) for f in fillers] or ["None found. Whisper-family models often drop um and uh from text; listen before trusting this."]
    L += ["", "## Draft cuts", ""] + ["- %.2f to %.2f: %s" % (c["start"], c["end"], c["why"]) for c in edl["cuts"]]
    return "\n".join(L) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("take"); p.add_argument("--words", required=True, help="JSON list of {text,start,end} in seconds")
    p.add_argument("--out", default="edit")
    p.add_argument("--min-pause", type=float, default=0.32, help="pauses longer than this get shortened")
    p.add_argument("--keep-pause", type=float, default=0.22, help="hold inside a thought")
    p.add_argument("--keep-sentence", type=float, default=0.36, help="hold after a sentence end")
    p.add_argument("--lead", type=float, default=0.05, help="room before a first word")
    p.add_argument("--tail", type=float, default=0.15, help="room after the very last word")
    p.add_argument("--min-run", type=int, default=4, help="repeated words that count as a retake")
    p.add_argument("--punct-from", help="whole-file transcript for sentence ends, when --words is an island pass")
    p.add_argument("--cut-fillers", action="store_true", help="also cut um and uh")
    a = p.parse_args()
    info = probe(a.take)
    if not info["has_audio"]:
        raise SystemExit("this take has no audio; nothing to read")
    words = json.load(open(a.words))
    words = words["words"] if isinstance(words, dict) else words
    db = loudness_slices(a.take)
    th, floor, voice = threshold(db)
    regs = speech_regions(db, th)
    hard, black = picture_changes(a.take)
    wr = retimed(words, regs)
    punct = json.load(open(a.punct_from)) if a.punct_from else None
    pauses = pauses_between(regs, wr, db, info["duration"], 0.2, punct)
    retakes = retake_candidates(wr, regs, a.min_run)
    fillers = filler_candidates(wr)
    edl = build_edl(info, regs, pauses, retakes, fillers, wr, db, a, hard, black)
    edl["hard_count"] = len(hard)
    os.makedirs(a.out, exist_ok=True)
    json.dump({"info": info, "threshold_db": round(th, 1), "room_db": round(floor, 1), "voice_db": round(voice, 1),
               "speech": [[round(x, 3), round(y, 3)] for x, y in regs], "hard_picture_changes": hard, "black": black, "pauses": pauses, "retakes": retakes,
               "fillers": fillers, "words": wr}, open(os.path.join(a.out, "take.json"), "w"), indent=1)
    json.dump(edl, open(os.path.join(a.out, "edl.json"), "w"), indent=1)
    gone = set()
    for r in retakes:
        if r["sure"] and r["run"] >= a.min_run:
            gone.update(range(r["attempt_from"], r["attempt_to"] + 1))
    if a.cut_fillers:
        for f in fillers:
            if f["confidence"] == "high":
                gone.update(range(f["from"], f["to"] + 1))
    # by word order, not by time: ASR times are the thing we do not trust
    json.dump([{"text": w["text"]} for i, w in enumerate(wr) if i not in gone], open(os.path.join(a.out, "intended.json"), "w"), indent=0)
    open(os.path.join(a.out, "review.md"), "w").write(review(info, th, floor, voice, wr, pauses, retakes, fillers, edl))
    print(json.dumps({"out": a.out, "source_s": info["duration"], "draft_s": edl["duration"], "segments": len(edl["segments"]),
                      "retakes": sum(1 for r in retakes if r["sure"]), "fillers": len(fillers),
                      "pauses_ge_0_4_audio": sum(1 for x in pauses if x["len"] >= 0.4),
                      "pauses_ge_0_4_word_gaps": sum(1 for i in range(1, len(wr)) if wr[i]["start"] - wr[i - 1]["end"] >= 0.4),
                      "vfr": info["vfr"]}))


if __name__ == "__main__":
    main()
