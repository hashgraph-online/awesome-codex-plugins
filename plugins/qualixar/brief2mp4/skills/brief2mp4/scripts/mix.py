#!/usr/bin/env python3
"""mix.py: voice, music ducked under the voice, and sound effects pinned to their cues, mixed to -14 LUFS and -1.5 dBTP.

  python3 mix.py STORYBOARD.json TIMINGS.json --sfx-dir assets/sfx --music bed.mp3 --out audio/mix.wav

Reads the re-timed storyboard (retime.py): where each voice line starts and the film-time `t` of every sound cue.
Writes the mix, the stems (audio/stems/voice.wav, sfx.wav, music.wav: measure a mix claim on the stems, not on the
mix), cues.json (the one central table of time, file, volume and pinned start) and mix_report.json.

  Voice     each line WAV is placed sample-exact at its start time.
  Effects   pinned by their PEAK: start = cue time - the file's peak lag (sfx.json) - a lead (whooshes start 50 ms early,
            because the ear expects the sound just before the object). A start before 0 is trimmed so the peak still lands.
  Music     looped or trimmed to the film, faded 0.5 s in and 1.5 s out, 1-4 kHz carved by 3 dB where speech lives, and set
            7 dB below the voice's loudness. Under each voice line it ducks a further 8 dB (so 15 dB below the voice, inside
            the 12-18 dB range of references/sound.md), ramping down 0.12 s before the first word and back up over 0.5 s after the
            last, so a breath under 0.7 s between lines does not make the bed pump. The envelope comes from the known line times, so
            it is exact and repeatable (no compressor guessing).
  Loudness  the sum is measured and normalised in two passes to -14 LUFS integrated with a true peak under -1.5 dBTP, then
            measured again; mix_report.json records what the file really measures.

Needs ffmpeg. Everything else is the Python standard library.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_lib import FilmError, load_json, save_json  # noqa: E402

RATE = 48000
HOP = 0.01
CUE_VOLUME = {"whoosh": 0.35, "tick": 0.35, "thud": 0.55, "paper": 0.30, "typewriter": 0.30, "riser": 0.40, "hit": 0.60}
CUE_LEAD = {"whoosh": 0.05}                       # seconds early
BED_BELOW_VOICE = 7.0                             # LU below the voice's loudness when nobody speaks
DUCK_DB = -8.0                                    # extra reduction while someone speaks: 15 dB below the voice
ATTACK, RELEASE = 0.12, 0.5
HOLD_GAP = 0.7                                    # seconds: a gap between lines shorter than this keeps the bed ducked
TARGET_LUFS, TARGET_TP = -14.0, -1.5


def need_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FilmError("ffmpeg is not installed (macOS: brew install ffmpeg; Debian/Ubuntu: sudo apt-get install ffmpeg)")


def ff(*args) -> str:
    done = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *[str(a) for a in args]], capture_output=True, text=True)
    if done.returncode != 0:
        raise FilmError(f"ffmpeg failed: {done.stderr.strip()[-300:]}")
    return done.stderr


def read_mono(path: Path) -> array:
    with wave.open(str(path), "rb") as wf:
        if (wf.getframerate(), wf.getnchannels(), wf.getsampwidth()) != (RATE, 1, 2):
            raise FilmError(f"{Path(path).name} must be a 48 kHz mono 16-bit WAV (it is {wf.getframerate()} Hz, {wf.getnchannels()} channel(s)): "
                            "split_takes.py and the stand-in voice write that; convert others with ffmpeg -ar 48000 -ac 1")
        a = array("h")
        a.frombytes(wf.readframes(wf.getnframes()))
        return a


def write_wav(path: Path, samples: array, rate: int = RATE, channels: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(samples.tobytes())


def build_voice(sb: dict, timings: dict, base: Path, total: int) -> tuple[array, list[tuple[float, float]]]:
    """The voice track, and each line's speech window (start, end) in film seconds."""
    out = array("h", bytes(total * 2))
    windows = []
    for beat in sb["beats"]:
        for lid in beat.get("lines", []):
            line = timings["lines"][lid]
            samples = read_mono(base / line["file"])
            start = int(round(beat["line_starts"][lid] * RATE))
            end = min(total, start + len(samples))
            out[start:end] = samples[:end - start]
            windows.append((beat["line_starts"][lid] + line["speech_start"], beat["line_starts"][lid] + line["speech_end"]))
    return out, sorted(windows)


def cue_table(sb: dict, manifest: dict) -> list[dict]:
    rows = []
    effects = manifest.get("effects", {})
    for beat in sb["beats"]:
        for cue in beat.get("sound", []):
            name = cue["cue"]
            if name not in effects:
                raise FilmError(f"sound cue '{name}' in {beat['id']} is not an effect (sfx.json has: {', '.join(effects)})")
            lag = effects[name]["peak_lag"]
            rows.append({"t": round(cue["t"], 4), "cue": name, "file": effects[name]["file"], "volume": float(cue.get("volume", CUE_VOLUME.get(name, 0.4))),
                         "peak_lag": lag, "start": round(cue["t"] - lag - CUE_LEAD.get(name, 0.0), 4), "beat": beat["id"]})
    return sorted(rows, key=lambda r: (r["t"], r["cue"]))


def build_sfx(rows: list[dict], sfx_dir: Path, total: int) -> array:
    out = array("h", bytes(total * 2))
    for row in rows:
        samples = read_mono(sfx_dir / row["file"])
        first = int(round(row["start"] * RATE))
        skip = max(0, -first)                                           # the head that would fall before 0 is dropped, the peak still lands
        for j in range(skip, len(samples)):
            i = first + j
            if i >= total:
                break
            out[i] = max(-32768, min(32767, out[i] + int(samples[j] * row["volume"])))
    return out


def duck_gains(windows: list[tuple[float, float]], seconds: float, depth_db: float = DUCK_DB, attack: float = ATTACK, release: float = RELEASE, hop: float = HOP) -> list[float]:
    """Linear gain for the bed every `hop` seconds: 1.0 when nobody speaks, `depth_db` while someone does, smooth between."""
    smooth = lambda x: x * x * (3 - 2 * x)
    floor = 10 ** (depth_db / 20)
    merged: list[list[float]] = []
    for s, e in sorted(windows):                                        # a breath shorter than HOLD_GAP does not let the bed rise
        if merged and s - merged[-1][1] < HOLD_GAP:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    windows = [(s, e) for s, e in merged]
    out = []
    for i in range(int(math.ceil(seconds / hop)) + 1):
        t = i * hop
        act = 0.0
        for s, e in windows:
            if s - attack <= t <= e + release:
                a = smooth((t - (s - attack)) / attack) if t < s else (1.0 if t <= e else smooth(1 - (t - e) / release))
                act = max(act, min(1.0, max(0.0, a)))
        out.append(1.0 + (floor - 1.0) * act)
    return out


def measure(path: Path) -> tuple[float, float]:
    """(integrated LUFS, true peak dBTP) of a file; (-inf, -inf) for silence."""
    err = ff("-i", path, "-af", "ebur128=peak=true", "-f", "null", "-")
    tail = err[err.rfind("Summary:"):]
    i, p = re.search(r"I:\s+(-?[0-9.]+|-inf) LUFS", tail), re.search(r"Peak:\s+(-?[0-9.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else -math.inf), (float(p.group(1)) if p else -math.inf)


MAX_LOOPS = 200


def seconds_of(path: Path) -> float | None:
    done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(done.stdout.strip())
    except ValueError:
        return None


def loop_inputs(music: Path, seconds: float) -> tuple[list, str, int]:
    """(ffmpeg inputs, the filter that joins them, how many copies). A track shorter than the film is repeated with a
    crossfade at every join (never a hard seam): copies overlap by up to 2 s (a quarter of the track for short ones)."""
    dur = seconds_of(music)
    if dur is None or dur >= seconds:
        return ["-i", music], "[0:a]anull", 1
    xf = min(2.0, dur / 4)
    n = math.ceil((seconds - dur) / (dur - xf)) + 1
    if n > MAX_LOOPS:
        raise FilmError(f"the music is {dur:.1f} s long and would repeat {n} times under a {seconds:.0f} s film: use a longer track")
    chain = "[0:a]aresample=%d,aformat=channel_layouts=stereo[c0];" % RATE
    for i in range(1, n):
        chain += f"[{i}:a]aresample={RATE},aformat=channel_layouts=stereo[r{i}];[c{i - 1}][r{i}]acrossfade=d={xf:.3f}:c1=qsin:c2=qsin[c{i}];"
    return sum([["-i", music] for _ in range(n)], []), chain + f"[c{n - 1}]anull", n


def build_music(music: Path, seconds: float, voice_lufs: float, windows: list, tmp: Path, out: Path) -> tuple[float, int]:
    """The ducked bed at `out`; returns the gain applied before ducking (dB) and how many times the track plays."""
    base = tmp / "music_base.wav"
    fade = f"afade=t=in:d=0.5,afade=t=out:st={max(0.0, seconds - 1.5):.3f}:d=1.5"
    inputs, joined, copies = loop_inputs(music, seconds)
    ff(*inputs, "-filter_complex", f"{joined},atrim=0:{seconds:.4f},aresample={RATE},aformat=channel_layouts=stereo,{fade},equalizer=f=2200:t=h:w=3000:g=-3[o]",
       "-map", "[o]", "-c:a", "pcm_f32le", base)
    loud = measure(base)[0]
    if math.isinf(loud):
        raise FilmError(f"the music file {music} is silent")
    target = (voice_lufs if not math.isinf(voice_lufs) else -20.0) - BED_BELOW_VOICE
    gain = target - loud
    env = array("h", (int(round(g * 32767)) for g in duck_gains(windows, seconds)))
    write_wav(tmp / "env.wav", env, rate=int(1 / HOP))
    ff("-i", base, "-i", tmp / "env.wav", "-filter_complex",
       f"[0:a]volume={gain:.3f}dB,aformat=sample_fmts=fltp[m];[1:a]aresample={RATE},aformat=sample_fmts=fltp:channel_layouts=mono,pan=stereo|c0=c0|c1=c0[e];[m][e]amultiply,atrim=0:{seconds:.4f},asetpts=PTS-STARTPTS[o]",
       "-map", "[o]", "-c:a", "pcm_s16le", out)
    return gain, copies


def normalise(mixed: Path, out: Path) -> None:
    """Two-pass loudnorm to the target, then 48 kHz 16-bit stereo."""
    base = f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11"
    err = ff("-i", mixed, "-af", base + ":print_format=json", "-f", "null", "-")
    m = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    chain = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
             f":offset={m['target_offset']}:linear=true,aresample={RATE}")
    ff("-i", mixed, "-af", chain, "-ar", RATE, "-ac", 2, "-c:a", "pcm_s16le", out)


def mix(storyboard: Path, timings: Path, sfx_dir: Path, out: Path, music: Path | None = None) -> dict:
    need_ffmpeg()
    sb, tm = load_json(Path(storyboard), "STORYBOARD.json"), load_json(Path(timings), "TIMINGS.json")
    seconds = float(sb["duration"])
    total = int(round(seconds * RATE))
    base = Path(timings).parent
    manifest_path = Path(sfx_dir) / "sfx.json"
    rows = []
    if any(b.get("sound") for b in sb["beats"]):
        if not manifest_path.is_file():
            raise FilmError(f"no sound effects at {sfx_dir}: make them with `python3 sfx_synth.py all --out-dir {sfx_dir}`")
        rows = cue_table(sb, load_json(manifest_path))
    voice, windows = build_voice(sb, tm, base, total)
    if not windows and not rows and not music:
        raise FilmError("nothing to mix: the storyboard has no voice lines, no sound cues and no music")
    stems = Path(out).parent / "stems"
    write_wav(stems / "voice.wav", voice)
    write_wav(stems / "sfx.wav", build_sfx(rows, Path(sfx_dir), total))
    voice_lufs = measure(stems / "voice.wav")[0] if windows else -math.inf
    inputs = [stems / "voice.wav", stems / "sfx.wav"]
    gain, copies = None, 0
    music_stem = stems / "music.wav"
    if music_stem.exists():
        music_stem.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        if music:
            gain, copies = build_music(Path(music), seconds, voice_lufs, windows, Path(tmp), music_stem)
            inputs.append(music_stem)
        graph = "".join(f"[{i}:a]aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}];" if i else "[0:a]highpass=f=70,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];"
                        for i in range(len(inputs)))
        graph += "".join(f"[a{i}]" for i in range(len(inputs))) + f"amix=inputs={len(inputs)}:normalize=0,atrim=0:{seconds:.4f}[o]"
        summed = Path(tmp) / "sum.wav"
        ff(*sum([["-i", p] for p in inputs], []), "-filter_complex", graph, "-map", "[o]", "-c:a", "pcm_f32le", summed)
        if math.isinf(measure(summed)[0]):
            raise FilmError("the mix is silent: check the voice lines and cues")
        normalise(summed, Path(out))
    lufs, tp = measure(Path(out))
    report = {"duration": seconds, "voice_lufs": None if math.isinf(voice_lufs) else round(voice_lufs, 2), "music_gain_db": None if gain is None else round(gain, 2),
              "bed_below_voice_db": None if gain is None else BED_BELOW_VOICE - DUCK_DB, "cues": len(rows), "music_plays": copies, "lufs": round(lufs, 2), "true_peak": round(tp, 2),
              "target": {"lufs": TARGET_LUFS, "true_peak": TARGET_TP}}
    save_json(Path(out).parent / "cues.json", {"version": 1, "note": "start = time - peak lag - lead: the effect's loudest moment lands on the event", "cues": rows})
    save_json(Path(out).parent / "mix_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storyboard", help="the re-timed STORYBOARD.json")
    ap.add_argument("timings", help="TIMINGS.json")
    ap.add_argument("--sfx-dir", default="assets/sfx", help="folder with sfx.json from sfx_synth.py all")
    ap.add_argument("--music", help="a music file (any format ffmpeg reads); trimmed to the film, or repeated with a crossfade at each join")
    ap.add_argument("--out", default="audio/mix.wav")
    args = ap.parse_args(argv)
    try:
        r = mix(Path(args.storyboard), Path(args.timings), Path(args.sfx_dir), Path(args.out), Path(args.music) if args.music else None)
    except (FilmError, KeyError, OSError) as err:
        print(f"FAIL  mix: {err if isinstance(err, FilmError) else 'storyboard or timings are missing ' + str(err)}")
        return 1
    print(f"PASS  mixed {r['duration']:.1f} s to {args.out}: {r['lufs']} LUFS, {r['true_peak']} dBTP, {r['cues']} cue(s)"
          + (f", music {r['music_gain_db']:+.1f} dB, ducked under the voice" if r["music_gain_db"] is not None else ", no music"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
