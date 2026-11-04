#!/usr/bin/env python3
"""Measure, build and check the soundtrack of a video. An agent cannot hear, so every step prints numbers.

Commands (ffmpeg on PATH; Python 3.9+ stdlib only, `beats` and `fit` also need librosa):

  sound.py measure FILE                   loudness (LUFS, true peak, LRA), length, silences, as JSON
  sound.py beats MUSIC [-o beats.json]    BPM, beats, estimated downbeats, strongest hits, quiet spans
  sound.py fit MUSIC --to SECONDS -o OUT  cut a track to length on a downbeat so it keeps its real ending
  sound.py mix CUES.json [-o mix.wav]     place every voice, sfx, ambience and music cue, duck music under
                                          voice, normalise to the platform target; writes stems + report
  sound.py check MIX --cues CUES.json     pass/fail: loudness, peaks, voice above music, sfx on their
                                          moments, cuts on beats, no dead air
  sound.py sheet FILE --cues CUES.json    waveform + spectrogram PNG with cue marks, to look at the sound
  sound.py preview FILE [--cues C] -o P.mp4  the sheet as a video with a playhead and the sound, to share
  sound.py mux VIDEO MIX -o OUT.mp4       put the mix on the picture (video stream copied, AAC 320k)

librosa without installing anything:  uv run --with librosa python3 sound.py beats track.wav

The cue sheet format is in references/cue-sheet.md. Times are seconds from the first frame.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile
from array import array

TARGETS = {  # integrated LUFS, true peak dBTP. Sources: references/mix.md
    "youtube": (-14.0, -1.0), "tiktok": (-14.0, -1.0), "reels": (-14.0, -1.0), "x": (-14.0, -1.0),
    "web": (-16.0, -1.0), "podcast": (-16.0, -1.0), "broadcast": (-23.0, -1.0),
}
SR_AN = 8000  # analysis sample rate (mono float), enough for RMS and onsets


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def need_ffmpeg():
    if not shutil.which("ffmpeg"):
        die("ffmpeg is not on PATH (brew install ffmpeg / apt install ffmpeg)")


def run(cmd, capture=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        die(f"{' '.join(cmd[:6])}... failed:\n{p.stderr[-2000:]}")
    return p.stderr if capture else ""


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         stdout=subprocess.PIPE, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        die(f"cannot read the length of {path}")


def loudness(path, af_prefix=""):
    """Integrated loudness, true peak and LRA via loudnorm's measuring pass."""
    af = (af_prefix + "," if af_prefix else "") + "loudnorm=I=-14:TP=-1:LRA=11:print_format=json"
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", af, "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if not m:
        die(f"no loudness reading for {path}")
    j = json.loads(m.group(0))
    return {"lufs": float(j["input_i"]), "true_peak": float(j["input_tp"]), "lra": float(j["input_lra"]),
            "thresh": float(j["input_thresh"]), "_raw": j}


def silences(path, noise_db=-50, min_s=0.3):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
               f"silencedetect=noise={noise_db}dB:d={min_s}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration(path)
        out.append({"start": round(max(0.0, s), 3), "end": round(e, 3), "len": round(e - max(0.0, s), 3)})
    return out


def pcm(path, sr=SR_AN, af=None):
    """Mono float32 samples at sr, for RMS and onset maths in plain Python."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, *(["-af", af] if af else []), "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], stdout=subprocess.PIPE)
    a = array("f")
    a.frombytes(p.stdout[: len(p.stdout) // 4 * 4])
    return a


def rms_db(a, t0, t1, sr=SR_AN):
    i0, i1 = max(0, int(t0 * sr)), min(len(a), int(t1 * sr))
    if i1 <= i0:
        return -120.0
    s = 0.0
    for v in a[i0:i1]:
        s += v * v
    r = math.sqrt(s / (i1 - i0))
    return 20 * math.log10(r) if r > 1e-9 else -120.0


def onset(a, sr=SR_AN, rel_db=-30.0):
    """First moment the clip rises within rel_db of its own peak: where a sound effect really starts."""
    peak = max((abs(v) for v in a), default=0.0)
    if peak <= 0:
        return 0.0
    thr = peak * 10 ** (rel_db / 20)
    for i, v in enumerate(a):
        if abs(v) >= thr:
            return i / sr
    return 0.0


def peak_time(a, sr=SR_AN, win=0.02):
    """Time of the loudest 20 ms in a clip: where a whoosh or riser should meet its event."""
    w = max(1, int(win * sr))
    best, at = -1.0, 0.0
    for i in range(0, max(1, len(a) - w), w // 2 or 1):
        e = 0.0
        for v in a[i:i + w]:
            e += v * v
        if e > best:
            best, at = e, i / sr
    return at


# ---------------------------------------------------------------- measure

def cmd_measure(args):
    need_ffmpeg()
    L = loudness(args.file)
    L.pop("_raw")
    out = {"file": args.file, "duration": round(duration(args.file), 3), **L,
           "silences": silences(args.file, args.noise, args.min_silence)}
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- beats / fit

def _librosa():
    try:
        import librosa, numpy  # noqa
        return librosa, numpy
    except ImportError:
        die("librosa is missing. Run:  uv run --with librosa python3 sound.py ...  (or pip install librosa)")


def analyse_beats(path):
    librosa, np = _librosa()
    y, sr = librosa.load(path, sr=22050, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beats = librosa.frames_to_time(beat_frames, sr=sr)
    env = librosa.onset.onset_strength(y=y, sr=sr)
    # downbeat phase: the beat phase (mod 4) with the most low-end energy. An estimate; check it by ear or plot.
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    low = S[: int(150 / (sr / 2048)) + 1].sum(axis=0)
    scores = []
    for ph in range(4):
        idx = beat_frames[ph::4]
        idx = idx[idx < len(low)]
        scores.append(float(low[idx].mean()) if len(idx) else 0.0)
    phase = int(np.argmax(scores))
    downbeats = beats[phase::4]
    # strongest hits: top onset peaks, at least 1 s apart
    peaks = librosa.util.peak_pick(env, pre_max=10, post_max=10, pre_avg=20, post_avg=20, delta=0.5, wait=40)
    order = sorted(peaks, key=lambda f: -env[f])[:12]
    hits = sorted(round(float(librosa.frames_to_time(f, sr=sr)), 3) for f in order)
    # quiet spans: RMS 12 dB or more under the track median for at least 0.4 s (stops, breakdowns, the "quiet part")
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    med = float(np.median(db))
    t = librosa.frames_to_time(np.arange(len(db)), sr=sr, hop_length=512)
    quiet, start = [], None
    for ti, d in zip(t, db):
        if d < med - 12 and start is None:
            start = ti
        elif d >= med - 12 and start is not None:
            if ti - start >= 0.4:
                quiet.append({"start": round(float(start), 2), "end": round(float(ti), 2)})
            start = None
    # librosa's tempo comes from coarse bins (120 BPM often reads 117.45); the average beat gap is closer
    bpm = float(60 * (len(beats) - 1) / (beats[-1] - beats[0])) if len(beats) > 4 else float(np.atleast_1d(tempo)[0])
    # the tracker often stops early when the groove thins out: carry the grid on to the end of the track
    tracked = len(beats)
    beats = list(beats)
    if bpm and beats:
        step = 60 / bpm
        while beats[-1] + step < len(y) / sr - 0.05:
            beats.append(beats[-1] + step)
    downbeats = beats[phase::4]
    return {"track": path, "duration": round(len(y) / sr, 3), "bpm": round(bpm, 2),
            "beats_tracked": tracked, "beats_after_that": "extrapolated at the measured tempo",
            "bar_seconds": round(4 * 60 / bpm, 3) if bpm else None,
            "beats": [round(float(b), 3) for b in beats],
            "downbeats": [round(float(b), 3) for b in downbeats], "downbeats_estimated": True,
            "hits": hits, "quiet": quiet}


def cmd_beats(args):
    r = analyse_beats(args.music)
    txt = json.dumps(r, indent=1)
    if args.o:
        open(args.o, "w").write(txt)
        print(f"wrote {args.o}: {r['bpm']} BPM, {len(r['beats'])} beats, {len(r['downbeats'])} bars, "
              f"{len(r['quiet'])} quiet spans")
    else:
        print(txt)


def cmd_fit(args):
    """Music-editor move: keep the opening, keep the real ending, cut out the middle on matching downbeats."""
    need_ffmpeg()
    r = analyse_beats(args.music)
    db, total, target = r["downbeats"], r["duration"], args.to
    if total <= target + 0.05:
        die(f"track is {total:.2f}s, not longer than {target}s: generate a longer one or loop a section")
    tail_needed = total - target  # seconds to remove
    best = None  # (error, a, b): cut out [a, b), both downbeats, b - a ~= tail_needed
    for a in db:
        if a < args.keep_intro:
            continue
        for b in db:
            if b <= a or b > total - args.keep_outro:
                continue
            err = abs((b - a) - tail_needed)
            if best is None or err < best[0]:
                best = (err, a, b)
    if best is None:
        die("no downbeat pair found; lower --keep-intro or check `beats` output")
    err, a, b = best
    xf = args.crossfade
    fc = (f"[0:a]atrim=0:{a + xf / 2:.4f},asetpts=PTS-STARTPTS[h];"
          f"[0:a]atrim={b - xf / 2:.4f},asetpts=PTS-STARTPTS[t];"
          f"[h][t]acrossfade=d={xf}:c1=tri:c2=tri,atrim=0:{target:.4f},afade=t=out:st={max(0, target - 0.05):.4f}:d=0.05[o]")
    run(["ffmpeg", "-y", "-hide_banner", "-i", args.music, "-filter_complex", fc, "-map", "[o]",
         "-ar", "48000", args.o])
    print(json.dumps({"out": args.o, "bpm": r["bpm"], "cut_from": a, "cut_to": b, "removed": round(b - a, 3),
                      "length_error_s": round(err, 3), "new_length": round(duration(args.o), 3),
                      "note": "listen at the cut; if it jumps, try --keep-intro to move it"}, indent=1))


# ---------------------------------------------------------------- mix

def load_cues(path):
    c = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    for t in c.get("tracks", []):
        if not os.path.isabs(t["file"]):
            t["file"] = os.path.join(base, t["file"])
        if not os.path.exists(t["file"]):
            die(f"cue {t.get('id')}: file not found: {t['file']}")
        t.setdefault("role", "sfx")
        t.setdefault("gain_db", 0.0)
        if t.get("align") == "peak":
            t["trim_lead"] = False
            t["_peak"] = peak_time(pcm(t["file"]))
            if "start" not in t and "at" in t:
                t["start"] = round(t["at"] - t["_peak"], 3)
        if "start" not in t:
            t["start"] = t.get("at", 0.0)
    if "duration" not in c:
        die("cue sheet needs \"duration\" (seconds, = the video length)")
    return c


def voice_windows(cues, merge_gap=0.6):
    """Where someone is speaking: [start, start + clip length], merged across gaps under 0.6 s so the bed doesn't
    pump between lines (HyperFrames' duck script bridges the same gap)."""
    w = []
    for t in cues["tracks"]:
        if t["role"] == "voice":
            d = t.get("length") or (duration(t["file"]) - t.get("trim_start", 0.0))
            w.append([t["start"], t["start"] + d])
    w.sort()
    out = []
    for s, e in w:
        if out and s - out[-1][1] <= merge_gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def duck_expr(windows, depth_db, down, up):
    """Volume curve for the music: -depth_db while anyone speaks. Fast down before the line (`down` s, trailer
    editor Derek Lieu uses ~4 frames), slow back up after it (`up` s, he uses 20-30 frames)."""
    if not windows or depth_db <= 0:
        return "1"
    terms = []
    for s, e in windows:
        terms.append(f"clip((t-{s - down:.3f})/{down},0,1)*clip(({e + up:.3f}-t)/{up},0,1)")
    m = terms[0]
    for x in terms[1:]:
        m = f"max({m},{x})"
    return f"pow(10,-{depth_db}*({m})/20)"


def build_chain(t, total):
    """Filters for one cue: trim, optional loop, lead-silence trim for sfx, gain, fades, place in time."""
    f = []
    if t.get("trim_start") or t.get("length"):
        a = t.get("trim_start", 0.0)
        f.append(f"atrim=start={a}" + (f":duration={t['length']}" if t.get("length") else ""))
        f.append("asetpts=PTS-STARTPTS")
    if t["role"] == "sfx" and t.get("trim_lead", True):
        f.append("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.005")
    f.append("aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo")
    if t.get("loop"):
        f.append("aloop=loop=-1:size=2147483647")
        f.append(f"atrim=duration={max(0.0, total - t['start']):.3f}")
    if t.get("gain_db"):
        f.append(f"volume={t['gain_db']}dB")
    # no clip starts or ends on a hard cut: a few ms on effects (keeps the transient), 30 ms on everything else
    edge = 0.005 if t["role"] == "sfx" else 0.03
    t.setdefault("fade_in", edge)
    t.setdefault("fade_out", 0.03)
    if t.get("fade_in"):
        f.append(f"afade=t=in:st=0:d={t['fade_in']}")
    if t.get("fade_out"):
        d = t.get("length") or (total - t["start"] if t.get("loop") else None)
        if d is None:
            d = duration(t["file"]) - t.get("trim_start", 0.0)
        f.append(f"afade=t=out:st={max(0.0, d - t['fade_out']):.3f}:d={t['fade_out']}")
    if t["start"] < 0:
        die(f"cue {t.get('id')} starts before 0 s; trim its head with trim_start instead")
    ms = int(round(t["start"] * 1000))
    if ms > 0:
        f.append(f"adelay={ms}:all=1")
    return ",".join(f)


def bus_graph(tracks, total, label, extra=""):
    """Sum a list of cues into one labelled bus, padded to the video length."""
    if not tracks:
        return f"anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[{label}]", []
    parts, ins = [], []
    for i, t in enumerate(tracks):
        parts.append(f"[{t['_in']}:a]{build_chain(t, total)}[{label}c{i}]")
        ins.append(f"[{label}c{i}]")
    mix = "".join(ins) + (f"amix=inputs={len(ins)}:normalize=0:dropout_transition=0," if len(ins) > 1 else "anull,")
    parts.append(f"{mix}apad=whole_dur={total:.3f},atrim=duration={total:.3f}{extra}[{label}]")
    return ";".join(parts), ins


def cmd_mix(args):
    need_ffmpeg()
    cues = load_cues(args.cues)
    total = float(cues["duration"])
    plat = cues.get("platform", "youtube")
    lufs, tp = TARGETS.get(plat, TARGETS["youtube"])
    lufs = cues.get("target", {}).get("lufs", lufs)
    tp = cues.get("target", {}).get("true_peak", tp)
    duck = cues.get("duck", {})
    fps = float(cues.get("fps", 30))
    depth = float(duck.get("depth_db", 10))
    down = float(duck.get("down", duck.get("ramp", 4 / fps)))
    up = float(duck.get("up", duck.get("ramp", 24 / fps)))
    out = args.o or os.path.join(os.path.dirname(os.path.abspath(args.cues)), "mix.wav")
    stem_dir = os.path.splitext(out)[0] + "_stems"
    os.makedirs(stem_dir, exist_ok=True)

    inputs = []
    for t in cues["tracks"]:
        t["_in"] = len(inputs) // 2
        inputs += ["-i", t["file"]]
    roles = {r: [t for t in cues["tracks"] if t["role"] == r] for r in ("voice", "music", "sfx", "ambience")}
    unknown = [t.get("id") for t in cues["tracks"] if t["role"] not in roles]
    if unknown:
        die(f"unknown role on {unknown}; use voice, music, sfx or ambience")
    win = voice_windows(cues)
    vo_hp = ",highpass=f=80" if cues.get("voice_highpass", True) else ""
    g = []
    carve = duck.get("carve", True) and bool(win) and depth > 0
    for role, label, extra in (("voice", "V", vo_hp), ("music", "M", ""), ("sfx", "S", ""), ("ambience", "A", "")):
        if role == "music" and roles["music"] and not carve:
            extra = f",asetnsamples=n=256,volume='{duck_expr(win, depth, down, up)}':eval=frame"
        s, _ = bus_graph(roles[role], total, label + ("raw" if role == "music" and carve and roles["music"] else ""), extra)
        g.append(s)
    if carve and roles["music"]:
        # duck the voice's band hardest: split the bed at 300 Hz and 4 kHz (crossover bands sum back flat) and
        # pull lows 30%, mids 100%, highs 55% of the depth, so the bed stays full but leaves the words alone
        lo, hi = depth * 0.35, depth * 0.65
        g.append("[Mraw]acrossover=split=300 4000:order=4th[mlo][mmid][mhi];"
                 f"[mlo]asetnsamples=n=256,volume='{duck_expr(win, lo, down, up)}':eval=frame[mlo2];"
                 f"[mmid]asetnsamples=n=256,volume='{duck_expr(win, depth, down, up)}':eval=frame[mmid2];"
                 f"[mhi]asetnsamples=n=256,volume='{duck_expr(win, hi, down, up)}':eval=frame[mhi2];"
                 "[mlo2][mmid2][mhi2]amix=inputs=3:normalize=0:dropout_transition=0[M]")
    g.append("[V]asplit=2[V1][Vs];[M]asplit=2[M1][Ms];[S]asplit=2[S1][Ss];[A]asplit=2[A1][As]")
    g.append("[V1][M1][S1][A1]amix=inputs=4:normalize=0:dropout_transition=0[pre]")
    graph = ";".join(g)

    with tempfile.TemporaryDirectory() as td:
        pre = os.path.join(td, "pre.wav")
        cmd = ["ffmpeg", "-y", "-hide_banner", *inputs, "-filter_complex", graph,
               "-map", "[pre]", "-c:a", "pcm_f32le", "-ar", "48000", pre]
        for lab, name in (("Vs", "voice"), ("Ms", "music"), ("Ss", "sfx"), ("As", "ambience")):
            cmd += ["-map", f"[{lab}]", "-c:a", "pcm_f32le", "-ar", "48000", os.path.join(stem_dir, f"{name}.wav")]
        run(cmd)
        m = loudness(pre)
        # master: one static gain to the target, then a peak limiter at 4x oversampling (so it catches
        # inter-sample peaks) 0.5 dB under the true-peak ceiling; re-measure and correct
        ceiling = 10 ** ((tp - 0.5) / 20)
        gain = lufs - m["lufs"]
        for _ in range(3):
            run(["ffmpeg", "-y", "-hide_banner", "-i", pre, "-af",
                 f"volume={gain:.2f}dB,aresample=192000,alimiter=limit={ceiling:.4f}:attack=2:release=60:level=disabled,"
                 f"aresample=48000",
                 "-c:a", "pcm_s24le", out])
            f = loudness(out)
            if abs(f["lufs"] - lufs) <= 0.3 or gain > 30:
                break
            gain += lufs - f["lufs"]
    report = {"out": out, "stems": stem_dir, "platform": plat, "target_lufs": lufs, "target_tp": tp,
              "pre_master": {"lufs": m["lufs"], "true_peak": m["true_peak"]},
              "master_gain_db": round(gain, 2),
              "final": {"lufs": f["lufs"], "true_peak": f["true_peak"], "lra": f["lra"]},
              "voice_windows": [[round(a, 3), round(b, 3)] for a, b in win],
              "duck": {"depth_db": depth, "down_s": round(down, 3), "up_s": round(up, 3),
                       "carve": "lows 35%, 300 Hz-4 kHz 100%, highs 65% of the depth" if carve else False},
              "note": "stems are pre-master; apply master_gain_db to compare them with the mix"}
    json.dump(report, open(os.path.splitext(out)[0] + "_report.json", "w"), indent=1)
    print(json.dumps(report, indent=1))


# ---------------------------------------------------------------- check

def cmd_check(args):
    need_ffmpeg()
    cues = load_cues(args.cues)
    total = float(cues["duration"])
    plat = cues.get("platform", "youtube")
    lufs, tp = TARGETS.get(plat, TARGETS["youtube"])
    lufs = cues.get("target", {}).get("lufs", lufs)
    tp = cues.get("target", {}).get("true_peak", tp)
    fps = float(cues.get("fps", 30))
    rows = []

    def row(name, ok, value, target, note=""):
        rows.append({"check": name, "pass": bool(ok), "value": value, "target": target, "note": note})

    L = loudness(args.mix)
    row("loudness", abs(L["lufs"] - lufs) <= 1.0, f"{L['lufs']:.1f} LUFS", f"{lufs} ±1 LUFS ({plat})")
    row("true peak", L["true_peak"] <= tp + 0.1, f"{L['true_peak']:.1f} dBTP", f"<= {tp} dBTP")
    d = duration(args.mix)
    row("length", abs(d - total) <= 1 / fps, f"{d:.3f} s", f"{total} s ±1 frame")

    stems = args.stems or os.path.splitext(args.mix)[0] + "_stems"
    win = voice_windows(cues)
    min_gap = float(cues.get("checks", {}).get("voice_over_music_db", 10))
    if os.path.isdir(stems) and win:
        band = "highpass=f=300,lowpass=f=4000"  # the band where words are understood
        v = pcm(os.path.join(stems, "voice.wav"), af=band)
        m = pcm(os.path.join(stems, "music.wav"), af=band)
        worst = None
        for s, e in win:
            gap = rms_db(v, s, e) - rms_db(m, s, e)
            if worst is None or gap < worst[0]:
                worst = (gap, s, e)
        if worst:
            row("voice above music", worst[0] >= min_gap,
                f"{worst[0]:.1f} dB in 300 Hz-4 kHz (worst line {worst[1]:.2f}-{worst[2]:.2f}s)",
                f">= {min_gap} dB during every line (WCAG AAA asks 20)",
                "raise duck depth_db or lower the music gain_db" if worst[0] < min_gap else "")
    elif win:
        row("voice above music", False, "no stems", "stems folder from `mix`", "run mix first or pass --stems")

    # sfx land on their moments: real onset (after the clip's own lead silence) vs the moment they belong to
    late = []
    for t in cues["tracks"]:
        if t["role"] != "sfx":
            continue
        at = t.get("at", t["start"])
        if t.get("align") == "peak":
            lead = t["_peak"]
        else:
            lead = 0.0 if t.get("trim_lead", True) else onset(pcm(t["file"]))
        real = t["start"] + lead
        late.append((abs(real - at), t.get("id", os.path.basename(t["file"])), real, at))
    if late:
        bad = [x for x in late if x[0] > 1 / fps]
        row("sfx on their moments", not bad, f"{len(late) - len(bad)}/{len(late)} within 1 frame",
            f"<= {1000 / fps:.0f} ms", "; ".join(f"{i}: {r:.3f}s vs {a:.3f}s" for _, i, r, a in bad[:6]))

    beats = cues.get("beats")
    if isinstance(beats, str):
        beats = json.load(open(os.path.join(os.path.dirname(os.path.abspath(args.cues)), beats)))
    grid = (beats or {}).get("downbeats" if cues.get("cut_on") == "downbeats" else "beats") if beats else None
    if grid and cues.get("cuts"):
        off = [min(abs(c - b) for b in grid) for c in cues["cuts"]]
        bad = [(c, o) for c, o in zip(cues["cuts"], off) if o > 1 / fps]
        row("cuts on the beat", not bad, f"{len(off) - len(bad)}/{len(off)} within 1 frame", f"<= {1000 / fps:.0f} ms",
            "; ".join(f"cut {c:.3f}s is {o * 1000:.0f} ms off" for c, o in bad[:6]))

    # dead air: the full mix falling to near digital silence where no silence was planned
    planned = [(s["start"], s["end"]) for s in cues.get("silences", [])]
    dead = [s for s in silences(args.mix, -60, 0.3)
            if not any(a - 0.05 <= s["start"] and s["end"] <= b + 0.05 for a, b in planned)]
    row("no dead air", not dead, f"{len(dead)} unplanned gaps under -60 dBFS", "0 (room tone under everything)",
        "; ".join(f"{s['start']}-{s['end']}s" for s in dead[:6]))

    # mono fold-down: phones often play one speaker
    mono = loudness(args.mix, "pan=mono|c0=0.5*c0+0.5*c1")
    drop = L["lufs"] - mono["lufs"]
    row("mono safe", drop <= 6.5, f"mono is {drop:.1f} dB quieter", "<= 6.5 dB",
        "3 dB = same in both speakers, 6 dB = fully wide, more = phase cancelling: check stereo widening")

    ok = all(r["pass"] for r in rows)
    out = {"mix": args.mix, "pass": ok, "checks": rows}
    print(json.dumps(out, indent=1))
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- sheet / mux

def cmd_sheet(args):
    need_ffmpeg()
    cues = load_cues(args.cues) if args.cues else {"tracks": [], "duration": duration(args.file)}
    total = float(cues["duration"])
    W = 1920
    out = args.o or os.path.splitext(args.file)[0] + "_sheet.png"
    marks = []
    for s, e in (voice_windows(cues) if cues["tracks"] else []):
        marks.append(f"drawbox=x={int(s / total * W)}:y=0:w={max(2, int((e - s) / total * W))}:h=28:color=0x2f80ed@0.9:t=fill")
    for t in cues["tracks"]:
        if t["role"] == "sfx":
            marks.append(f"drawbox=x={int(t.get('at', t['start']) / total * W)}:y=0:w=5:h=ih:color=0xeb5757@0.9:t=fill")
    for c in cues.get("cuts", []):
        marks.append(f"drawbox=x={int(c / total * W)}:y=0:w=2:h=ih:color=0xffffff@0.7:t=fill")
    fc = (f"color=c=0x16181d:s={W}x300:d=1[bg];"
          f"[0:a]asplit=2[a][b];[a]showwavespic=s={W}x300:split_channels=0:colors=0xb8bcc4[w0];"
          f"[bg][w0]overlay=format=auto,format=rgb24[w];"
          f"[b]showspectrumpic=s={W}x400:legend=0:scale=log:color=intensity,format=rgb24[s];"
          f"[w][s]vstack=inputs=2" + ("," + ",".join(marks) if marks else "") + "[o]")
    run(["ffmpeg", "-y", "-hide_banner", "-i", args.file, "-filter_complex", fc, "-map", "[o]", "-frames:v", "1", out])
    labels = []  # (seconds, text): --labels "0=bare;7=punctuation" plus every cue id
    for part in (getattr(args, "labels", None) or "").split(";"):
        if "=" in part:
            t, txt = part.split("=", 1)
            labels.append((float(t), txt.strip()))
    for t in cues["tracks"]:
        if t["role"] in ("voice", "sfx") and t.get("id"):
            labels.append((t.get("at", t["start"]), t["id"]))
    if labels:
        try:
            from PIL import Image, ImageDraw, ImageFont
            im = Image.open(out).convert("RGB")
            dr = ImageDraw.Draw(im)
            font = None
            for fp in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial Unicode.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                if os.path.exists(fp):
                    font = ImageFont.truetype(fp, 26)
                    break
            for i, (t, txt) in enumerate(sorted(labels)):
                x = int(t / total * W) + 6
                dr.text((min(x, W - 200), 40 + 34 * (i % 3)), txt, fill=(236, 234, 228), font=font)
            im.save(out)
        except ImportError:
            pass  # labels need Pillow; the marks are still drawn
    print(json.dumps({"sheet": out, "legend": "blue bars = voice lines, red = sfx moments, white = cuts; "
                      "top = waveform, bottom = spectrogram (low notes at the bottom)"}, indent=1))


def cmd_preview(args):
    """The sheet as a video with a moving playhead and the sound: look and listen at the same time."""
    need_ffmpeg()
    sheet = os.path.splitext(args.o)[0] + "_sheet.png"
    ns = argparse.Namespace(file=args.file, cues=args.cues, o=sheet, labels=args.labels)
    cmd_sheet(ns)
    d = duration(args.file)
    fc = (f"[0:v]scale=1280:-2,format=yuv420p[bg];color=c=white:s=4x720:r=30[ph];"
          f"[bg][ph]overlay=x='t/{d:.3f}*W':y=0:shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-hide_banner", "-loop", "1", "-framerate", "30", "-i", sheet, "-i", args.file,
         "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-tune", "stillimage",
         "-crf", "28", "-c:a", "aac", "-b:a", "192k", "-t", f"{d:.3f}", "-movflags", "+faststart", args.o])
    print(json.dumps({"preview": args.o, "duration": round(d, 3)}))


def cmd_mux(args):
    need_ffmpeg()
    run(["ffmpeg", "-y", "-hide_banner", "-i", args.video, "-i", args.mix, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", args.o])
    print(json.dumps({"out": args.o, "duration": round(duration(args.o), 3)}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("measure"); a.add_argument("file"); a.add_argument("--noise", type=float, default=-50)
    a.add_argument("--min-silence", type=float, default=0.3); a.set_defaults(fn=cmd_measure)
    a = sp.add_parser("beats"); a.add_argument("music"); a.add_argument("-o"); a.set_defaults(fn=cmd_beats)
    a = sp.add_parser("fit"); a.add_argument("music"); a.add_argument("--to", type=float, required=True)
    a.add_argument("-o", required=True); a.add_argument("--keep-intro", type=float, default=4.0)
    a.add_argument("--keep-outro", type=float, default=6.0, help="seconds of the real ending that must survive")
    a.add_argument("--crossfade", type=float, default=0.06); a.set_defaults(fn=cmd_fit)
    a = sp.add_parser("mix"); a.add_argument("cues"); a.add_argument("-o"); a.set_defaults(fn=cmd_mix)
    a = sp.add_parser("check"); a.add_argument("mix"); a.add_argument("--cues", required=True)
    a.add_argument("--stems"); a.set_defaults(fn=cmd_check)
    a = sp.add_parser("sheet"); a.add_argument("file"); a.add_argument("--cues"); a.add_argument("-o")
    a.add_argument("--labels", help='text at times, e.g. "0=bare;7=with pauses"')
    a.set_defaults(fn=cmd_sheet)
    a = sp.add_parser("preview"); a.add_argument("file"); a.add_argument("--cues"); a.add_argument("-o", required=True)
    a.add_argument("--labels", help='text at times, e.g. "0=bare;7=with pauses"')
    a.set_defaults(fn=cmd_preview)
    a = sp.add_parser("mux"); a.add_argument("video"); a.add_argument("mix"); a.add_argument("-o", required=True)
    a.set_defaults(fn=cmd_mux)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
