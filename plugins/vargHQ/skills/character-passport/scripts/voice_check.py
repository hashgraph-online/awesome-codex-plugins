#!/usr/bin/env python3
"""Measure a TTS take against the voice line: pace (words per minute) and pauses. Needs ffmpeg + ffprobe.

  python3 voice_check.py take.wav --text "Mm. It's late, no? ..." --target-wpm 130 [--tolerance 15]

Two paces are reported. Overall wpm counts pauses (what the viewer feels). Articulation wpm counts only
speech (how fast the words themselves are said). Conversational English is usually quoted at roughly
120-160 overall; check your target against the voice line, not against this script.
"""
import argparse, re, subprocess, sys

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("audio"); ap.add_argument("--text", required=True)
ap.add_argument("--target-wpm", type=float); ap.add_argument("--tolerance", type=float, default=15.0, help="percent")
ap.add_argument("--noise", default="-35dB"); ap.add_argument("--min-pause", type=float, default=0.25)
a = ap.parse_args()

dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.audio]).stdout.strip())
log = run(["ffmpeg", "-hide_banner", "-i", a.audio, "-af", f"silencedetect=noise={a.noise}:d={a.min_pause}", "-f", "null", "-"]).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
lengths = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", log)]
# ignore leading/trailing silence when counting pauses between words
inner = [(s, l) for s, l in zip(starts, lengths) if s > 0.05 and s + l < dur - 0.05]
lead = sum(l for s, l in zip(starts, lengths) if s <= 0.05)
tail = sum(l for s, l in zip(starts, lengths) if s + l >= dur - 0.05)
words = len(re.findall(r"[A-Za-zÀ-ɏ']+", a.text))
spoken = dur - lead - tail
pause_total = sum(l for _, l in inner)
overall = words / spoken * 60 if spoken > 0 else 0
artic = words / (spoken - pause_total) * 60 if spoken - pause_total > 0 else 0
print(f"words {words} · length {dur:.2f}s (speech span {spoken:.2f}s)")
print(f"pace overall {overall:.0f} wpm · articulation {artic:.0f} wpm")
print(f"pauses {len(inner)} · total {pause_total:.2f}s · longest {max([l for _, l in inner], default=0):.2f}s")
if a.target_wpm:
    lo, hi = a.target_wpm * (1 - a.tolerance / 100), a.target_wpm * (1 + a.tolerance / 100)
    ok = lo <= overall <= hi
    print(("PASS" if ok else "FAIL") + f" target {a.target_wpm:.0f} wpm ±{a.tolerance:.0f}% ({lo:.0f}-{hi:.0f})")
    if not ok:
        print("fix: " + ("fewer or shorter pauses in the text/tags, or say 'brisker'" if overall < lo
                         else "add pauses (… or [pause]) and say 'slower, unhurried'") + ", then re-measure")
    sys.exit(0 if ok else 1)
