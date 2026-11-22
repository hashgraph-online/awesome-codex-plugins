#!/usr/bin/env python3
"""standin_voice.py: a stand-in voice track made from word timestamps, to preview lip sync before there is a recording.

    python3 standin_voice.py words.json voice.wav               # words JSON in, WAV out
    python3 standin_voice.py words.json voice.wav --seconds 14  # pad or cut the file to the film's length
    python3 standin_voice.py words.json voice.wav --pitch 120   # a lower buzz

words.json is a list of {"text", "start", "end"} (what `npx hyperframes transcribe` writes). The WAV is a buzz that
swells with every word and follows the mouth shapes (open vowels loud, closed lips quiet), mono, 48 kHz, 16-bit. It is
NOT speech: use it to check timing, captions and loudness, then record or generate the real voice, run
`npx hyperframes transcribe` on it, and render again. `lipsync.py --wav` reads it back as open, half-open and
closed mouths, so it also exercises that fallback. Standard library only.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lipsync  # noqa: E402

RATE = 48000
LEVEL = {"rest": 0.0, "AI": 1.0, "O": 0.9, "E": 0.62, "U": 0.55, "L": 0.55, "FV": 0.45, "etc": 0.4, "MBP": 0.12}


def render(words: list[dict], seconds: float, pitch: float = 150.0, fps: float = 30.0) -> list[float]:
    """Samples in -1..1: a buzz at `pitch` Hz whose loudness follows the mouth shapes lip sync would draw."""
    track = lipsync.build_track(words, fps)
    n = int(seconds * RATE)
    level = [0.0] * n
    for a, b in zip(track, track[1:] + [{"t": seconds, "v": "rest"}]):
        for i in range(int(a["t"] * RATE), min(n, int(b["t"] * RATE))):
            level[i] = LEVEL.get(a["v"], 0.4)
    smooth, acc, k = [0.0] * n, 0.0, 1.0 / (0.006 * RATE)          # a 6 ms ramp so shapes do not click
    for i in range(n):
        acc += (level[i] - acc) * k
        smooth[i] = acc
    out = [0.0] * n
    for i, amp in enumerate(smooth):
        if amp < 1e-4:
            continue
        t = i / RATE
        f = pitch * (1 + 0.05 * math.sin(2 * math.pi * 5.2 * t))
        ph = 2 * math.pi * f * t
        out[i] = 0.3 * amp * (math.sin(ph) + 0.5 * math.sin(2 * ph) + 0.3 * math.sin(3 * ph + 1.0) + 0.15 * math.sin(7 * ph))
    return out


def write_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32000)) for v in samples))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("words", help="word timestamps JSON: a list of {text, start, end}")
    ap.add_argument("out", help="the WAV file to write")
    ap.add_argument("--seconds", type=float, help="length of the file (default: half a second after the last word)")
    ap.add_argument("--pitch", type=float, default=150.0, help="buzz pitch in Hz (default 150)")
    ap.add_argument("--fps", type=float, default=30.0, help="the video's frame rate, for the mouth timing (default 30)")
    args = ap.parse_args(argv)
    try:
        words = lipsync.load_words(Path(args.words))
    except (OSError, ValueError) as exc:
        print(f"standin_voice.py: {exc}", file=sys.stderr)
        return 2
    if not words:
        print("standin_voice.py: the words file is empty", file=sys.stderr)
        return 2
    seconds = args.seconds or max(w["end"] for w in words) + 0.5
    write_wav(Path(args.out), render(words, seconds, args.pitch, args.fps))
    print(f"wrote {args.out}: {seconds:.1f} s, mono 48 kHz (a buzz that follows the words, not speech)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
