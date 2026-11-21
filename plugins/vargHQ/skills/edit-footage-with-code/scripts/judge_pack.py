#!/usr/bin/env python3
"""Prepare blind evidence so a judge can compare cuts without knowing who made them.

  python3 judge_pack.py cut1.mp4 cut2.mp4 ... --out judge --seed 7 \
      --transcribe "npx hyperframes transcribe {video} -d {dir} --model small.en --json"

Writes judge/pack/<ID>/ for each cut: transcript.md, numbers.md, sheet.jpg, joins.jpg.
File names, authors and order are gone. judge/key.json maps IDs back: never show it to a judge.
Reference text for the judge goes in judge/pack/SOURCE.md (--source-text intended.json).
"""
import argparse, array, hashlib, json, math, os, random, re, shlex, shutil, statistics, subprocess, sys


def run(*c):
    return subprocess.run(c, capture_output=True, text=True)


def frame_diffs(video):
    """Mean absolute difference between neighbouring frames at 64x36."""
    info = json.loads(run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "json", video).stdout)
    n, _, m = info["streams"][0]["r_frame_rate"].partition("/")
    fps = float(n) / float(m or 1)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    size = 64 * 36
    frames = [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]
    return fps, frames, [sum(abs(a - b) for a, b in zip(frames[i - 1], frames[i])) / size for i in range(1, len(frames))]


def joins_from(diffs, fps, floor=0.8, ratio=3.0):
    """A join is a frame that changes far more than the frames around it do."""
    out = []
    for i, d in enumerate(diffs):
        if d < floor:
            continue
        near = diffs[max(0, i - 6):i] + diffs[i + 1:i + 7]
        if near and d / max(statistics.median(near), 0.15) >= ratio and (not out or (i + 1) / fps - out[-1] > 0.1):
            out.append(round((i + 1) / fps, 3))
    return out


def abrupt_edges(video):
    """Speech that stops or starts within 10 ms, as a hard cut through a word does."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    pcm = array.array("h"); pcm.frombytes(raw[: len(raw) - len(raw) % 2])
    db = []
    for i in range(0, len(pcm) - 79, 80):
        r = math.sqrt(sum(x * x for x in pcm[i:i + 80]) / 80) / 32768
        db.append(20 * math.log10(r) if r > 0 else -120.0)
    live = sorted(d for d in db if d > -80)
    if not live:
        return 0, 0
    voice = live[int(len(live) * 0.9)]
    return (sum(1 for i in range(2, len(db)) if db[i - 2] > voice - 10 and db[i] < db[i - 2] - 25),
            sum(1 for i in range(2, len(db)) if db[i] > voice - 10 and db[i - 2] < db[i] - 25))


def measure(video, words):
    dur = float(json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", video).stdout)["format"]["duration"])
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", video, "-af", "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-").stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    gaps = [(round(a, 2), round(b - a, 2)) for a, b in zip(st, en)]
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", video, "-af", "loudnorm=print_format=json", "-f", "null", "-").stderr
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", err, re.S)
    ld = json.loads(m.group(0)) if m else {}
    fps, frames, diffs = frame_diffs(video)
    js = joins_from(diffs, fps)
    err = run("ffmpeg", "-hide_banner", "-nostats", "-i", video, "-vf", "blackdetect=d=0.05:pix_th=0.1", "-an", "-f", "null", "-").stderr
    black = [(round(float(a), 2), round(float(b) - float(a), 2)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    shots = [b - a for a, b in zip([0] + js, js + [dur])]
    off, on = abrupt_edges(video)
    wc = len(words)
    speech = max(1e-3, dur - sum(g[1] for g in gaps))
    toks = [re.sub(r"[^a-z0-9]", "", w["text"].lower()) for w in words]
    reps = []
    for n in range(7, 3, -1):
        for k in range(len(toks) - 2 * n + 1):
            if toks[k:k + n] == toks[k + n:k + 2 * n]:
                reps.append(" ".join(toks[k:k + n]))
    return {"duration_s": round(dur, 2), "fps": round(fps, 2), "lufs": float(ld.get("input_i", 0)), "true_peak_dbtp": float(ld.get("input_tp", 0)),
            "words_heard": wc, "words_per_minute_of_speech": round(60 * wc / speech), "pauses": gaps, "pauses_over_0_6_s": [g for g in gaps if g[1] > 0.6],
            "longest_pause_s": max([g[1] for g in gaps] or [0]), "starts_with_silence_s": gaps[0][1] if gaps and gaps[0][0] < 0.05 else 0,
            "picture_jumps_at_s": js, "picture_jumps_per_minute": round(60 * len(js) / max(dur, 1), 1), "longest_shot_s": round(max(shots), 2) if shots else 0,
            "speech_stops_within_10_ms": off, "speech_starts_within_10_ms": on, "black_stretches": black, "phrase_said_twice_in_a_row": reps[:5]}


def transcript_md(words, gaps):
    gaps = sorted(gaps); L = []; line = []; g = 0
    for w in words:
        while g < len(gaps) and gaps[g][0] <= float(w["start"]):
            if line:
                L.append(line); line = []
            L.append("[%.2f s: silence %.2f s]" % gaps[g]); g += 1
        if not line:
            line.append("[%.2f] " % float(w["start"]))
        line.append(w["text"].strip() + " ")
        if len(line) > 14 or re.search(r"[.?!]$", w["text"].strip()):
            L.append(line); line = []
    if line:
        L.append(line)
    return "\n".join("".join(x) if isinstance(x, list) else x for x in L) + "\n"


def sheets(video, dur, joins, d):
    run("ffmpeg", "-y", "-v", "error", "-i", video, "-vf", "fps=%f,scale=320:-2,tile=6x4" % (24 / max(dur, 1)), "-frames:v", "1", os.path.join(d, "sheet.jpg"))
    # the frames either side of each jump: at most 18, spread across the whole film so the sheet stays readable
    fps = float(eval(run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", video).stdout.strip()))
    picks = joins if len(joins) <= 18 else [joins[round(i * (len(joins) - 1) / 17)] for i in range(18)]
    json.dump({"joins_shown_at_s": picks, "tiles_per_join": "2 or 3"}, open(os.path.join(d, "joins_index.json"), "w"))
    if picks:
        expr = "+".join("between(t,%.3f,%.3f)" % (t - 1.2 / fps, t + 0.7 / fps) for t in picks)
        run("ffmpeg", "-y", "-v", "error", "-i", video, "-vf", "select='%s',scale=240:-2,tile=6x%d" % (expr, max(1, math.ceil(len(picks) * 3 / 6))),
            "-fps_mode", "vfr", "-frames:v", "1", os.path.join(d, "joins.jpg"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("videos", nargs="+"); p.add_argument("--out", default="judge"); p.add_argument("--seed", type=int, default=7)
    p.add_argument("--transcribe", required=True, help="command that writes {dir}/transcript.json")
    p.add_argument("--source-text", help="JSON word list of what the source says, as reference")
    a = p.parse_args()
    pack = os.path.join(a.out, "pack"); os.makedirs(pack, exist_ok=True)
    rnd = random.Random(a.seed); key = {}
    ids = ["".join(rnd.choice("BCDFGHJKLMNPQRSTVWXZ") for _ in range(2)) + str(rnd.randint(10, 99)) for _ in a.videos]
    order = list(a.videos); rnd.shuffle(order)
    for cid, v in zip(ids, order):
        d = os.path.join(pack, cid); os.makedirs(d, exist_ok=True)
        tmp = os.path.join(a.out, "work", hashlib.sha1(v.encode()).hexdigest()[:10]); os.makedirs(tmp, exist_ok=True)
        wav = os.path.join(tmp, "audio.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", v, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
        if not os.path.exists(os.path.join(tmp, "transcript.json")):
            subprocess.run(a.transcribe.format(video=shlex.quote(wav), dir=shlex.quote(tmp)), shell=True, capture_output=True, text=True)
        words = json.load(open(os.path.join(tmp, "transcript.json")))
        m = measure(v, words)
        open(os.path.join(d, "transcript.md"), "w").write(transcript_md(words, m["pauses"]))
        json.dump(m, open(os.path.join(d, "numbers.json"), "w"), indent=1)
        sheets(v, m["duration_s"], m["picture_jumps_at_s"], d)
        key[cid] = v
    if a.source_text:
        w = json.load(open(a.source_text))
        open(os.path.join(pack, "SOURCE.md"), "w").write("What the speaker says in the raw take, once, for reference:\n\n" + " ".join(x["text"].strip() for x in w) + "\n")
    json.dump(key, open(os.path.join(a.out, "key.json"), "w"), indent=1)
    print(json.dumps({"pack": pack, "candidates": ids, "key": os.path.join(a.out, "key.json")}))


if __name__ == "__main__":
    main()
