#!/usr/bin/env python3
"""sfx_synth.py: sound effects made in code, so there is nothing to license.

  python3 sfx_synth.py all --out-dir assets/sfx [--seed 7]        # every effect + sfx.json (length and peak lag of each)
  python3 sfx_synth.py make whoosh --out whoosh.wav [--seed 3]
  python3 sfx_synth.py make riser --out riser.wav --seconds 3
  python3 sfx_synth.py list

Effects: whoosh, tick, thud, paper, typewriter, riser, hit. Every one is built from sine partials, decaying resonances
and seeded random timing: the same seed always gives the same bytes, a different seed a slightly different effect, and
no global random state is touched. There is no white noise anywhere (a noise whoosh reads as static under a voice):
the whoosh is a gliding cluster of detuned partials, the paper rustle is a spray of tiny resonant clicks. Each file is
mono, 48 kHz, 16-bit, scaled so its true peak (4x oversampled) is -1.3 dBTP, safely under -1 dBTP.

sfx.json records each effect's length and its peak lag (seconds from the file start to its loudest sample), which
mix.py uses to land the peak, not the start, on the visual event. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import struct
import sys
import wave
from pathlib import Path

RATE = 48000
TARGET_DBTP = -1.3
TWO_PI = 2 * math.pi


class SfxError(ValueError):
    pass


def peak_linear() -> float:
    return 10 ** (TARGET_DBTP / 20)


def _sinc_taps(a: int = 6, phases: int = 4) -> list[list[float]]:
    taps = []
    for k in range(1, phases):
        frac = k / phases
        row = []
        for n in range(-a + 1, a + 1):
            x = n - frac
            sinc = 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)
            row.append(sinc * (0.5 + 0.5 * math.cos(math.pi * x / a)))
        taps.append(row)
    return taps


_TAPS = _sinc_taps()


def true_peak(samples: list[float]) -> float:
    """Highest absolute value of the waveform 4x oversampled (windowed sinc), found only around the loud samples."""
    base = max((abs(v) for v in samples), default=0.0)
    best, n = base, len(samples)
    for i in range(n):
        if abs(samples[i]) < base * 0.5:
            continue
        for row in _TAPS:
            acc = 0.0
            for j, c in enumerate(row):
                k = i + j - 5
                if 0 <= k < n:
                    acc += c * samples[k]
            best = max(best, abs(acc))
    return best


def peak_lag(samples: list[float], rate: int = RATE) -> float:
    """Seconds from the file start to its loudest sample."""
    return max(range(len(samples)), key=lambda i: abs(samples[i])) / rate if samples else 0.0


def normalise(samples: list[float]) -> list[float]:
    tp = true_peak(samples)
    if tp <= 0:
        raise SfxError("the effect came out silent")
    gain = peak_linear() / tp
    return [v * gain for v in samples]


def _env(t: float, attack: float, decay: float) -> float:
    return (1 - math.exp(-t / attack)) * math.exp(-t / decay) if attack > 0 else math.exp(-t / decay)


def _glide(n: int, f0: float, f1: float, curve: float = 1.0):
    """Phase of a tone gliding exponentially from f0 to f1 over n samples."""
    phase, out = 0.0, []
    for i in range(n):
        p = (i / n) ** curve
        phase += TWO_PI * f0 * math.exp(math.log(f1 / f0) * p) / RATE
        out.append(phase)
    return out


def whoosh(rng: random.Random, seconds: float = 0.7, rising: bool = True) -> list[float]:
    n = int(seconds * RATE)
    lo, hi = 260 * rng.uniform(0.9, 1.1), 2400 * rng.uniform(0.9, 1.1)
    parts = []
    for k in range(9):                                   # a cluster of detuned partials: the beating is the air
        spread = 1 + rng.uniform(-0.09, 0.09)
        parts.append((_glide(n, lo * spread * (1 + 0.31 * k), hi * spread * (1 + 0.17 * k)) if rising else _glide(n, hi * spread, lo * spread), 1 / (1 + 0.5 * k), rng.uniform(0, TWO_PI)))
    out = []
    for i in range(n):
        x = i / n
        bell = math.sin(math.pi * x ** 0.8) ** 2
        out.append(bell * sum(a * math.sin(ph[i] + p0) for ph, a, p0 in parts) * (1 + 0.15 * math.sin(TWO_PI * 31 * i / RATE)))
    return out


def tick(rng: random.Random, seconds: float = 0.08) -> list[float]:
    f = 2800 * rng.uniform(0.95, 1.05)
    return [(_env(i / RATE, 0.0002, 0.011) * math.sin(TWO_PI * f * i / RATE) + 0.3 * _env(i / RATE, 0.0001, 0.006) * math.sin(TWO_PI * 2.02 * f * i / RATE))
            for i in range(int(seconds * RATE))]


def thud(rng: random.Random, seconds: float = 0.6) -> list[float]:
    f0, f1 = 120 * rng.uniform(0.95, 1.05), 46 * rng.uniform(0.95, 1.05)
    phase, out = 0.0, []
    for i in range(int(seconds * RATE)):
        t = i / RATE
        phase += TWO_PI * (f1 + (f0 - f1) * math.exp(-t / 0.045)) / RATE
        out.append(_env(t, 0.0015, 0.16) * math.sin(phase))
    return out


def paper(rng: random.Random, seconds: float = 0.5) -> list[float]:
    """A rustle: a few hundred tiny resonant clicks at seeded times, denser in the middle, never a continuous hiss."""
    n = int(seconds * RATE)
    out = [0.0] * n
    for _ in range(int(seconds * 700)):
        at = int(n * (0.5 + 0.5 * math.sin(rng.uniform(-1.5, 1.5)) * 0.9 + 0.05) * 0.95)
        f, amp, dec = rng.uniform(1400, 6200), rng.uniform(0.15, 1.0) * rng.choice((1, -1)), rng.uniform(0.0008, 0.003)
        for j in range(min(int(dec * 6 * RATE), n - at)):
            out[at + j] += amp * math.exp(-j / (dec * RATE)) * math.sin(TWO_PI * f * j / RATE)
    return [v * math.sin(math.pi * i / n) ** 0.5 for i, v in enumerate(out)]


def typewriter(rng: random.Random, seconds: float = 1.6) -> list[float]:
    n = int(seconds * RATE)
    out = [0.0] * n
    t = 0.05
    while t < seconds - 0.35:
        at, f = int(t * RATE), 1700 * rng.uniform(0.85, 1.2)
        amp = rng.uniform(0.6, 1.0)
        for j in range(min(int(0.04 * RATE), n - at)):
            s = j / RATE
            out[at + j] += amp * (_env(s, 0.0001, 0.006) * math.sin(TWO_PI * f * s) + 0.7 * _env(s, 0.0004, 0.014) * math.sin(TWO_PI * 150 * s))
        t += rng.uniform(0.07, 0.12)
    at = int((seconds - 0.3) * RATE)                      # carriage return: a low knock and a small bell
    for j in range(n - at):
        s = j / RATE
        out[at + j] += 1.1 * _env(s, 0.001, 0.07) * math.sin(TWO_PI * 90 * s) + 0.5 * _env(s, 0.0005, 0.18) * math.sin(TWO_PI * 2350 * s)
    return out


def riser(rng: random.Random, seconds: float = 2.0) -> list[float]:
    n = int(seconds * RATE)
    f0 = 200 * rng.uniform(0.95, 1.05)
    parts = [(_glide(n, f0 * m, f0 * m * 8, 1.4), 1 / m, rng.uniform(0, TWO_PI)) for m in (1, 1.5, 2, 3, 4.02, 5.01)]
    out = []
    for i in range(n):
        x = i / n
        trem = 1 + 0.3 * math.sin(TWO_PI * (4 + 14 * x) * i / RATE)
        fade = min(1.0, (n - i) / (0.006 * RATE))
        out.append(fade * x ** 2.2 * trem * sum(a * math.sin(ph[i] + p0) for ph, a, p0 in parts))
    return out


def hit(rng: random.Random, seconds: float = 1.2) -> list[float]:
    f0 = 52 * rng.uniform(0.95, 1.05)
    out = []
    for i in range(int(seconds * RATE)):
        t = i / RATE
        low = _env(t, 0.002, 0.42) * math.sin(TWO_PI * (f0 + 70 * math.exp(-t / 0.05)) * t)
        knock = 0.6 * _env(t, 0.001, 0.09) * math.sin(TWO_PI * 190 * t)
        ping = 0.25 * _env(t, 0.0008, 0.35) * (math.sin(TWO_PI * 1120 * t) + 0.5 * math.sin(TWO_PI * 2210 * t))
        out.append(1.4 * low + knock + ping)
    return out


EFFECTS = {"whoosh": whoosh, "tick": tick, "thud": thud, "paper": paper, "typewriter": typewriter, "riser": riser, "hit": hit}
PURPOSE = {"whoosh": "a transition, a map route starting", "tick": "a counter step, a label landing", "thud": "a hard cut, a weight",
           "paper": "a still laid down on the desk", "typewriter": "a date or caption being typed", "riser": "tension before the hero moment (peaks at its end)",
           "hit": "the hero moment"}


def synth(name: str, seed: int = 0, seconds: float | None = None) -> list[float]:
    if name not in EFFECTS:
        raise SfxError(f"unknown effect '{name}': choose one of {', '.join(EFFECTS)}")
    rng = random.Random(f"{name}:{seed}")                # a private generator: nothing global is touched
    raw = EFFECTS[name](rng, seconds) if seconds else EFFECTS[name](rng)
    return normalise(raw)


def write_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(struct.pack("<h", max(-32768, min(32767, round(v * 32767)))) for v in samples))


def write_effect(name: str, path: Path, seed: int = 0, seconds: float | None = None) -> dict:
    samples = synth(name, seed, seconds)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_wav(Path(path), samples)
    return {"file": Path(path).name, "seconds": round(len(samples) / RATE, 4), "peak_lag": round(peak_lag(samples), 4), "seed": seed, "use": PURPOSE[name]}


def write_all(out_dir: Path, seed: int = 0) -> dict:
    out_dir = Path(out_dir)
    manifest = {"version": 1, "rate": RATE, "effects": {}, "note": "Synthesised by sfx_synth.py from sine partials and seeded timing: no samples, no licence to clear."}
    for name in EFFECTS:
        manifest["effects"][name] = write_effect(name, out_dir / f"{name}.wav", seed)
    (out_dir / "sfx.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("all", help="write every effect and sfx.json")
    a.add_argument("--out-dir", default="assets/sfx")
    a.add_argument("--seed", type=int, default=0)
    m = sub.add_parser("make", help="write one effect")
    m.add_argument("name")
    m.add_argument("--out", required=True)
    m.add_argument("--seed", type=int, default=0)
    m.add_argument("--seconds", type=float, help="length (whoosh, riser, paper, typewriter and so on)")
    sub.add_parser("list", help="the effects and what each is for")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            print("\n".join(f"{k:11s} {v}" for k, v in PURPOSE.items()))
        elif args.cmd == "all":
            manifest = write_all(Path(args.out_dir), args.seed)
            print(f"PASS  {len(manifest['effects'])} effects and sfx.json written to {args.out_dir} (seed {args.seed}, true peak {TARGET_DBTP} dBTP)")
        else:
            info = write_effect(args.name, Path(args.out), args.seed, args.seconds)
            print(f"PASS  {args.out}: {info['seconds']} s, peak at {info['peak_lag']} s")
    except SfxError as err:
        print(f"FAIL  sfx_synth: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
