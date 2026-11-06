"""Item 10 plus voice and music: loudness, clipping, drop-outs, sound against cuts, beats, script match."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from mj_common import check, not_run, run, th

SR = 22050
HOP = 256
N_FFT = 1024


def decode(path: str, sr: int = SR, mono: bool = True) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:a:0", "-f", "f32le", "-ar", str(sr)]
    cmd += ["-ac", "1"] if mono else []
    cmd += ["-"]
    proc = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(proc.stdout, np.float32).copy()


def stft_mag(y: np.ndarray) -> np.ndarray:
    if len(y) < N_FFT:
        return np.zeros((1, N_FFT // 2 + 1))
    win = np.hanning(N_FFT)
    n = 1 + (len(y) - N_FFT) // HOP
    out = np.empty((n, N_FFT // 2 + 1), np.float32)
    for i in range(0, n, 2048):
        idx = np.arange(i, min(i + 2048, n))
        frames = np.stack([y[j * HOP:j * HOP + N_FFT] for j in idx]) * win
        out[idx] = np.abs(np.fft.rfft(frames, axis=1))
    return out


def onset_envelope(mag: np.ndarray) -> np.ndarray:
    # 24 log-spaced bands, log compressed, half-wave rectified flux
    bins = mag.shape[1]
    edges = np.unique(np.geomspace(2, bins - 1, 25).astype(int))
    bands = np.stack([mag[:, a:b].mean(axis=1) for a, b in zip(edges, edges[1:])], axis=1)
    log = np.log1p(40 * bands)
    flux = np.maximum(np.diff(log, axis=0), 0).mean(axis=1)
    return np.r_[0.0, flux]


def pick_onsets(env: np.ndarray, delta: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Peaks above a moving average, at least 50 ms apart. Times are the sound's rise."""
    if len(env) < 8:
        return np.zeros(0), np.zeros(0)
    hop_s = HOP / SR
    w = int(0.25 / hop_s)
    avg = np.convolve(env, np.ones(2 * w + 1) / (2 * w + 1), "same")
    # Scale the floor on the strongest events, or a steady pad beating against itself counts as a stream of hits.
    level = avg * 1.5 + (delta if delta is not None else 0.2 * float(np.percentile(env, 99.5)))
    peaks = []
    gap = int(0.05 / hop_s)
    for i in range(1, len(env) - 1):
        if env[i] >= env[i - 1] and env[i] > env[i + 1] and env[i] > level[i]:
            if not peaks or i - peaks[-1] >= gap:
                peaks.append(i)
            elif env[i] > env[peaks[-1]]:
                peaks[-1] = i
    idx = np.array(peaks, int)
    # n_fft window centre: a frame at index i covers samples i*HOP .. i*HOP+N_FFT
    times = idx * hop_s + (N_FFT / 2) / SR if len(idx) else np.zeros(0)
    return times, env[idx] if len(idx) else np.zeros(0)


def loudness(path: str) -> dict:
    proc = run(["ffmpeg", "-nostats", "-nostdin", "-hide_banner", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"], check=False)
    txt = proc.stderr
    out = {}
    for key, pat in (("integrated_lufs", r"I:\s+(-?[\d.]+) LUFS"), ("range_lu", r"LRA:\s+(-?[\d.]+) LU"), ("true_peak_dbtp", r"Peak:\s+(-?[\d.]+) dBFS")):
        ms = re.findall(pat, txt)
        if ms:
            out[key] = float(ms[-1])
    return out


def _edit_offsets(cut_times: np.ndarray, onset_times: np.ndarray, strengths: np.ndarray, window: float) -> list[dict]:
    out = []
    for c in cut_times:
        if not len(onset_times):
            continue
        d = onset_times - c
        near = np.where(np.abs(d) <= window)[0]
        if len(near) == 0:
            out.append({"cut": round(float(c), 3), "offset_ms": None})
            continue
        # The nearest sound of real strength: a big hit 300 ms away must not hide a smaller one on the cut.
        real = near[strengths[near] >= 0.35 * strengths[near].max()]
        i = real[np.argmin(np.abs(d[real]))]
        out.append({"cut": round(float(c), 3), "offset_ms": round(float(d[i]) * 1000, 1), "strength": round(float(strengths[i]), 3)})
    return out


def _chance(cut_times: np.ndarray, targets: np.ndarray, tol: float, dur: float, rng: np.random.Generator, trials: int = 400) -> dict:
    if not len(cut_times) or not len(targets) or dur <= 0:
        return {"hit_share": 0.0, "chance_share": 0.0, "z": 0.0}
    def share(cs):
        return float(np.mean([np.min(np.abs(targets - c)) <= tol for c in cs]))
    real = share(cut_times)
    sims = [share((cut_times + rng.uniform(0, dur)) % dur) for _ in range(trials)]
    mu, sd = float(np.mean(sims)), float(np.std(sims)) or 1e-6
    return {"hit_share": round(real, 3), "chance_share": round(mu, 3), "z": round((real - mu) / sd, 2)}


def track_beats(env: np.ndarray) -> tuple[float, np.ndarray, float]:
    """Tempo by autocorrelation, then beats by dynamic programming (Ellis 2007)."""
    if len(env) < 200:
        return 0.0, np.zeros(0), 0.0
    hop_s = HOP / SR
    e = env - env.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(e, 2 * len(e))) ** 2)[: len(e)]
    lo, hi = int(60 / 200 / hop_s), int(60 / 60 / hop_s)
    lags = np.arange(lo, min(hi, len(ac)))
    weight = np.exp(-0.5 * (np.log2((60 / (lags * hop_s)) / 110) / 0.9) ** 2)
    best = lags[np.argmax(ac[lags] * weight)]
    tempo = 60 / (best * hop_s)
    clarity = float(ac[best] / max(ac[0], 1e-9))
    period = best
    norm = env / max(env.std(), 1e-9)  # Ellis's tightness of 100 assumes this scale. Too weak a pull and beats stop matching the tempo.
    score = norm.copy().astype(float)
    back = -np.ones(len(env), int)
    span = np.arange(int(0.5 * period), int(2 * period))
    pen = -100.0 * (np.log(span / period) ** 2)
    for i in range(int(2 * period), len(env)):
        cand = score[i - span] + pen
        j = int(np.argmax(cand))
        score[i] = norm[i] + cand[j]
        back[i] = i - span[j]
    i = int(np.argmax(score[-int(period):])) + len(score) - int(period)
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    times = np.array(beats[::-1]) * hop_s + (N_FFT / 2) / SR
    return float(tempo), times, clarity


def _cutoff_full_rate(y: np.ndarray, sr: int = 48000) -> float:
    """Where the spectrum falls away. A hard wall low down means a low-bitrate or generated source."""
    if len(y) < 8192:
        return 0.0
    n = 4096
    win = np.hanning(n)
    idx = np.linspace(0, len(y) - n, min(200, max(1, len(y) // n))).astype(int)
    m = np.mean([np.abs(np.fft.rfft(y[i:i + n] * win)) ** 2 for i in idx], axis=0)
    db = 10 * np.log10(m + 1e-12)
    above = np.where(db > float(np.max(db)) - 70)[0]
    return round(float(np.linspace(0, sr / 2, len(m))[above[-1]]), 0) if len(above) else 0.0


def audio_checks(path: str, probe, shots: list[dict], script_text: str | None, music_only: bool, ev: Path) -> tuple[list[dict], np.ndarray | None]:
    res: list[dict] = []
    if not probe.has_audio:
        return [not_run("audio", "10 sound after the cut", "This file has no audio stream.")], None

    y = decode(path)
    if not len(y):
        return [not_run("audio", "10 sound after the cut", "Audio stream did not decode.")], None
    dur = len(y) / SR
    offset = probe.a_start - probe.v_start
    mag = stft_mag(y)
    env = onset_envelope(mag)
    onsets, strength = pick_onsets(env)
    onsets = onsets + offset

    # level
    lv = loudness(path)
    res.append(check("loudness", "voice and music", "flagged" if _loud_off(lv) else "clear", lv, thresholds=["lufs_low", "lufs_high", "true_peak"]))

    # clipping counted on full-rate samples
    y48 = decode(path, 48000, mono=False)
    clipped = 0
    y48_mono = y48
    if len(y48):
        hit = np.abs(y48) >= 0.999
        runs = np.diff(np.flatnonzero(np.diff(np.r_[0, hit.astype(int), 0])))[::2] if hit.any() else np.zeros(0)
        clipped = int((runs >= 3).sum())
    res.append(check("clipping", "voice and music", "flagged" if clipped > th("clip_runs") else "clear",
                     {"clipped_runs": clipped, "seconds_of_audio": round(len(y48) / (48000 * max(probe.channels, 1)), 2)}, thresholds=["clip_runs"]))

    # drop-outs: digital silence inside sound
    rms = np.sqrt((mag ** 2).mean(axis=1))
    level = 20 * np.log10(rms + 1e-9)
    loud = np.percentile(level, 90)
    silent = level < loud - th("dropout_db")
    hop_s = HOP / SR
    drops, i, n = [], 0, len(silent)
    while i < n:
        if silent[i]:
            j = i
            while j + 1 < n and silent[j + 1]:
                j += 1
            d = (j - i + 1) * hop_s
            edge = th("dropout_edge_db")
            hard_in = i >= 2 and level[i - 2] - level[i] >= edge
            hard_out = j + 2 < n and level[j + 2] - level[j] >= edge
            if th("dropout_min_s") <= d <= th("dropout_max_s") and hard_in and hard_out:
                drops.append({"t": round(i * hop_s + offset, 3), "duration_s": round(d, 3)})
            i = j + 1
        else:
            i += 1
    res.append(check("audio_dropouts", "voice and music", "flagged" if drops else "clear", {"count": len(drops)}, drops[:12], ["dropout_db", "dropout_edge_db", "dropout_min_s"],
                     note="Counts gaps with a hard edge on both sides. A pause in speech fades, so it does not count."))

    end_gap = (probe.duration - (dur + offset))
    res.append(check("audio_length", "voice and music", "flagged" if abs(end_gap) > th("av_length_s") else "clear",
                     {"audio_seconds": round(dur, 3), "video_seconds": round(probe.duration, 3), "audio_start_offset_s": round(offset, 3), "video_minus_audio_s": round(end_gap, 3)},
                     thresholds=["av_length_s"]))

    # sound against cuts
    cuts = np.array([s["start"] for s in shots[1:]], float)
    rng = np.random.default_rng(7)
    covers = "10 a sound that lands after the cut instead of on it"
    if len(cuts) == 0:
        res.append(check("sound_on_cut", covers, "info", {"cuts": 0}, note="No cuts to test."))
    else:
        window = th("sync_window_s")
        rows = _edit_offsets(cuts, onsets, strength, window)
        matched = [r for r in rows if r.get("offset_ms") is not None]
        offs = np.array([r["offset_ms"] for r in matched], float) if matched else np.zeros(0)
        strong = 0.3 * float(np.percentile(strength, 95)) if len(strength) else 0
        strong_rows = [r for r in matched if r["strength"] >= strong]
        s_offs = np.array([r["offset_ms"] for r in strong_rows], float) if strong_rows else np.zeros(0)
        late = [r for r in strong_rows if r["offset_ms"] > th("late_ms")]
        early = [r for r in strong_rows if r["offset_ms"] < -th("early_ms")]
        tol = th("on_cut_tol_s")
        chance = _chance(cuts, onsets, tol, dur, rng)
        related = chance["z"] >= 2.0
        systematic = float(np.median(s_offs)) if len(s_offs) >= 3 else None
        sys_late = systematic is not None and systematic > th("late_ms") and np.mean(s_offs > 0) >= 0.7
        # One cut with an unrelated sound nearby proves nothing. A habit across the edit does.
        on_time = sum(1 for r in strong_rows if abs(r["offset_ms"]) <= th("on_cut_tol_s") * 1000)
        habit = len(strong_rows) >= 3 and (len(late) + len(early)) >= 0.5 * len(strong_rows) and on_time < 0.5 * len(strong_rows)
        state = "flagged" if (habit or sys_late) else "clear"
        res.append(check("sound_on_cut", covers, state,
                         {"cuts": len(cuts), "cuts_with_a_sound_near": len(matched), "cuts_with_strong_sound_near": len(strong_rows),
                          "median_offset_ms": round(float(np.median(offs)), 1) if len(offs) else None,
                          "median_offset_strong_ms": round(systematic, 1) if systematic is not None else None,
                          "late_cuts": len(late), "early_cuts": len(early), "on_time_cuts": on_time, "sound_on_cut_vs_chance": chance,
                          "edit_follows_sound": bool(related), "per_cut": rows[:40]},
                         (late + early)[:12], ["late_ms", "early_ms", "on_cut_tol_s"],
                         note="Positive offset means the sound comes after the cut. If the edit does not follow the sound, chance decides most matches and this says less."))

    # music: tempo, cuts on beats against chance, end, cutoff
    tempo, beats, clarity = track_beats(env)
    beat_rows = {"beat_clarity": round(clarity, 3)}
    # On calm music the tracker invents a metronome, so no beat test without a clear pulse.
    if len(beats) >= 8 and clarity >= th("beat_clarity_min"):
        beats = beats + offset
        beat_rows.update({"tempo_bpm": round(tempo, 1), "beats": len(beats)})
        if len(cuts):
            beat_rows["cuts_on_beat"] = _chance(cuts, beats, th("on_beat_tol_s"), dur, rng)
            # Whether cuts sit on a regular grid at this tempo. Unlike the above, a tracker's phase error can't hide it.
            per = 60 / tempo
            lock = float(np.abs(np.exp(2j * np.pi * cuts / per).mean()))
            sims = [float(np.abs(np.exp(2j * np.pi * rng.uniform(0, dur, len(cuts)) / per).mean())) for _ in range(400)]
            beat_rows["cut_grid_lock"] = {"lock": round(lock, 3), "chance": round(float(np.mean(sims)), 3), "chance_p95": round(float(np.percentile(sims, 95)), 3)}
    else:
        beat_rows["no_beat_test"] = "No clear pulse, so a beat grid would be invented."
    tail = rms[-int(0.25 / hop_s):] if len(rms) > int(0.3 / hop_s) else rms
    tail_db = 20 * np.log10(float(np.mean(tail)) + 1e-9) - 20 * np.log10(float(np.percentile(rms, 90)) + 1e-9)
    beat_rows["end_level_db_vs_body"] = round(tail_db, 1)
    beat_rows["abrupt_end"] = bool(tail_db > th("abrupt_end_db"))
    beat_rows["spectral_cutoff_hz"] = _cutoff_full_rate(y48_mono)
    state = "flagged" if beat_rows["abrupt_end"] else "info"
    res.append(check("music_facts", "voice and music", state, beat_rows, thresholds=["abrupt_end_db", "on_beat_tol_s"], note="The tempo is a fact. Whether the edit should follow it is a choice."))

    # level per shot: an end card far under the dialogue, or a jump at a cut, is a mix error
    rows = []
    for sh in shots:
        a, b = int((sh["start"] - offset) * SR), int((sh["end"] - offset) * SR)
        seg = y[max(a, 0):max(b, 0)]
        if len(seg) > SR * 0.2:
            rows.append({"shot": sh["index"], "t": sh["start"], "rms_db": round(20 * np.log10(float(np.sqrt((seg ** 2).mean())) + 1e-9), 1)})
    jumps = [dict(t=b["t"], from_db=a["rms_db"], to_db=b["rms_db"]) for a, b in zip(rows, rows[1:]) if abs(a["rms_db"] - b["rms_db"]) > th("level_jump_db") and min(a["rms_db"], b["rms_db"]) > -55]
    if rows:
        res.append(check("level_jumps", "voice and music", "flagged" if jumps else "clear", {"shots": len(rows)}, jumps[:10], ["level_jump_db"]))

    # voice
    res += voice_checks(path, y, script_text, music_only, shots)
    return res, onsets


def _loud_off(lv: dict) -> bool:
    i, tp = lv.get("integrated_lufs"), lv.get("true_peak_dbtp")
    if i is not None and (i < th("lufs_low") or i > th("lufs_high")):
        return True
    return tp is not None and tp > th("true_peak")


def f0_track(y: np.ndarray) -> np.ndarray:
    """Pitch by normalized autocorrelation in the speech range."""
    frame, hop = int(0.04 * SR), int(0.02 * SR)
    lo, hi = int(SR / 350), int(SR / 70)
    out = []
    for i in range(0, len(y) - frame, hop):
        x = y[i:i + frame]
        if np.sqrt((x ** 2).mean()) < 0.01:
            out.append(0.0)
            continue
        x = x - x.mean()
        ac = np.correlate(x, x, "full")[frame - 1:]
        if ac[0] <= 0:
            out.append(0.0)
            continue
        ac = ac / ac[0]
        seg = ac[lo:hi]
        if len(seg) == 0:
            out.append(0.0)
            continue
        k = int(np.argmax(seg))
        out.append(SR / (lo + k) if seg[k] > 0.5 else 0.0)
    return np.array(out)


def voice_checks(path: str, y: np.ndarray, script_text: str | None, music_only: bool, shots: list[dict]) -> list[dict]:
    out = []
    if music_only:
        return [check("voice", "voice and music", "info", {}, note="Skipped: --music-only.")]
    words = None
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        # Hand over samples we decoded with ffmpeg, so a PyAV version clash can't take this check down.
        segs, _info = model.transcribe(decode(path, 16000), word_timestamps=True, vad_filter=True)
        words = [{"w": w.word.strip(), "t": round(w.start, 2), "t_end": round(w.end, 2), "p": round(w.probability, 3)} for s in segs for w in (s.words or [])]
    except Exception as err:
        out.append(not_run("speech_to_text", "voice", f"faster-whisper did not run ({type(err).__name__}: {str(err)[:120]}). Add it with: uv run --with faster-whisper"))
    f0 = f0_track(y[: SR * 180])
    voiced = f0[f0 > 0]
    if len(voiced) > 25:
        st = 12 * np.log2(voiced / np.median(voiced))
        spread = float(np.std(st))
        out.append(check("voice_pitch", "voice", "info", {"median_f0_hz": round(float(np.median(voiced)), 1), "pitch_spread_semitones": round(spread, 2), "voiced_seconds": round(len(voiced) * 0.02, 1)},
                         note="A spread under about 1.5 semitones reads as flat. Mixed music raises this number, so use it on a dry voice."))
    if words is not None:
        spoken = " ".join(w["w"] for w in words)
        dur = (words[-1]["t_end"] - words[0]["t"]) if words else 0
        facts = {"words": len(words), "spoken": spoken[:1500], "words_per_minute": round(len(words) / dur * 60, 1) if dur else 0, "low_confidence_words": [w for w in words if w["p"] < 0.5][:20]}
        evs = []
        state = "info"
        if script_text:
            wer, subs = _wer(script_text, spoken)
            facts["word_error_rate"] = round(wer, 3)
            facts["differences"] = subs[:30]
            state = "flagged" if wer > th("script_wer") else "clear"
            evs = [{"t": None, "difference": s} for s in subs[:12]]
        out.append(check("voice_script", "voice", state, facts, evs, ["script_wer"], note="Whisper can hear what it expects, so it misses some mispronunciations. Listen to low-confidence words."))
    return out


def _norm_words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def _wer(ref: str, hyp: str) -> tuple[float, list[str]]:
    r, h = _norm_words(ref), _norm_words(hyp)
    dp = np.zeros((len(r) + 1, len(h) + 1), int)
    dp[:, 0] = np.arange(len(r) + 1)
    dp[0, :] = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    diffs = []
    i, j = len(r), len(h)
    while i > 0 or j > 0:
        if i and j and dp[i, j] == dp[i - 1, j - 1] and r[i - 1] == h[j - 1]:
            i, j = i - 1, j - 1
        elif i and j and dp[i, j] == dp[i - 1, j - 1] + 1:
            diffs.append(f"script '{r[i - 1]}' heard '{h[j - 1]}'")
            i, j = i - 1, j - 1
        elif i and dp[i, j] == dp[i - 1, j] + 1:
            diffs.append(f"script '{r[i - 1]}' not heard")
            i -= 1
        else:
            diffs.append(f"extra word '{h[j - 1]}'")
            j -= 1
    return float(dp[len(r), len(h)]) / max(len(r), 1), diffs[::-1]
