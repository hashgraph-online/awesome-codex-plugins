#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Smallest Star: score, ambience and sound effects.

Every sample written by this script is computed here from sines, noise and
arithmetic. No audio files, no soundfonts, no models, no network.
Python 3 + numpy only (own oscillators, filters, reverb, limiter, loudness meter, WAV writer).

    python3 score.py            render score.wav + three stems, print the checks
    python3 score.py --notes    print the composition bar by bar and exit

All timing comes from ../timeline.json: tempo and meter, shot starts and
lengths (sections follow the shot ids), and the cue times in `events`.
Edit the timeline, run again, and the music follows.
"""
import json
import os
import sys
import wave
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
SEED = 52

with open(os.path.join(HERE, '..', 'timeline.json')) as fh:
    TL = json.load(fh)

TOTAL = float(TL['total_seconds'])
BPM = float(TL['bpm'])
BEATS = int(str(TL.get('meter', '3/4')).split('/')[0])
BEAT = 60.0 / BPM
BAR = BEAT * BEATS
if 'bar_seconds' in TL and abs(float(TL['bar_seconds']) - BAR) > 1e-3:
    BAR = float(TL['bar_seconds'])
    BEAT = BAR / BEATS
SHOT_LIST = TL['shots']
SHOTS = {s['id']: s for s in SHOT_LIST}
EVENTS = sorted(TL.get('events', []), key=lambda e: e['t'])

N = int(round(TOTAL * SR))          # exact output length
TAIL = 5.0                          # extra render room for reverb tails
NT = int(round((TOTAL + TAIL) * SR))

# Linear gains before the final loudness normalization.
LV = dict(
    box=0.50, key=0.20, pad=0.080, bass=0.24, glass=0.045, twinkle=0.050,
    crickets=0.0225, trill=0.0042, air=0.017,
    wings=0.058, hop=0.085, drip=0.072, glow=0.014, bloom=0.050,
    fall=0.026, home=0.030, takeoff=0.028, rise=0.016,
)
SEND = dict(box=0.34, key=0.30, pad=0.24, bass=0.0, glass=0.55, twinkle=0.9,
            sfx=0.40, crickets=0.30)
TARGET_LUFS = -16.0
CEILING_DB = -1.6                   # sample-peak ceiling; true peak is checked after


# ----------------------------------------------------------------------------
# timeline helpers
def ev(kind, lo=None, hi=None):
    for e in EVENTS:
        if e['type'] == kind and (lo is None or e['t'] >= lo - 1e-6) and (hi is None or e['t'] < hi - 1e-6):
            return e
    return None


def evs(kind):
    return [e for e in EVENTS if e['type'] == kind]


def shot_at(t):
    for s in SHOT_LIST:
        if s['start'] - 1e-6 <= t < s['start'] + s['dur'] - 1e-6:
            return s
    return None


def nbars(s):
    return max(1, int(round(s['dur'] / BAR)))


def bt(s, bar, beat):
    return s['start'] + bar * BAR + beat * BEAT


def rng_for(name):
    return np.random.default_rng(zlib.crc32(name.encode()) + SEED)


# ----------------------------------------------------------------------------
# DSP helpers
def m2f(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def ramp_in(n):
    return 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / max(n, 1))


def ramp_out(n):
    return 0.5 + 0.5 * np.cos(np.pi * np.arange(n) / max(n, 1))


def edges(x, a, r):
    """Raised-cosine attack and release (seconds) so no voice ever clicks."""
    n = x.shape[0]
    na = min(int(a * SR), n)
    nr = min(int(r * SR), n)
    env = np.ones(n)
    if na > 0:
        env[:na] *= ramp_in(na)
    if nr > 0:
        env[n - nr:] *= ramp_out(nr)
    return x * (env[:, None] if x.ndim == 2 else env)


def lp(fc, order=2):
    return lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order))


def hp(fc, order=2):
    return lambda f: 1.0 / np.sqrt(1.0 + (fc / np.maximum(f, 1e-9)) ** (2 * order))


def band(lo, hi, order=2):
    a, b = hp(lo, order), lp(hi, order)
    return lambda f: a(f) * b(f)


def fftfilt(x, gain):
    """Zero-phase filter: multiply the spectrum by a real gain curve."""
    n = x.shape[0]
    g = gain(np.fft.rfftfreq(n, 1.0 / SR))
    if x.ndim == 1:
        return np.fft.irfft(np.fft.rfft(x) * g, n)
    return np.stack([np.fft.irfft(np.fft.rfft(x[:, c]) * g, n) for c in range(x.shape[1])], axis=1)


def smoothnoise(n, rate, rng):
    """Band-limited random LFO: random points at `rate` Hz, cosine-interpolated."""
    m = int(n / SR * rate) + 3
    pts = rng.standard_normal(m)
    x = np.arange(n) / SR * rate
    i = x.astype(int)
    fr = 0.5 - 0.5 * np.cos(np.pi * (x - i))
    return pts[i] * (1 - fr) + pts[i + 1] * fr


TSIZE = 2048


def wavetable(amps, phases):
    spec = np.zeros(TSIZE // 2 + 1, complex)
    k = np.arange(1, len(amps) + 1)
    spec[k] = np.asarray(amps) * np.exp(1j * (np.asarray(phases) - np.pi / 2)) * (TSIZE / 2)
    tab = np.fft.irfft(spec, TSIZE)
    return np.append(tab, tab[0])


def osc(tab, freq, n, phase0=0.0):
    if np.isscalar(freq):
        ph = phase0 + freq * np.arange(n) / SR
    else:
        ph = phase0 + np.cumsum(freq) / SR
    return np.interp((ph % 1.0) * TSIZE, np.arange(TSIZE + 1), tab)


def pan2(x, p):
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


class Bus:
    def __init__(self):
        self.dry = np.zeros((NT, 2))
        self.send = np.zeros((NT, 2))

    def put(self, t, x, gain=1.0, pan=0.0, send=0.0):
        if x.ndim == 1:
            x = pan2(x, pan)
        i = int(round(t * SR))
        if i < 0:
            x = x[-i:]
            i = 0
        n = min(x.shape[0], NT - i)
        if n <= 0:
            return
        self.dry[i:i + n] += gain * x[:n]
        if send:
            self.send[i:i + n] += gain * send * x[:n]


# ----------------------------------------------------------------------------
# reverb: a synthesized hall impulse response (decaying noise, each octave band
# with its own decay time so highs die first), applied by FFT convolution
def make_ir(seed, length=3.6, predelay=0.024):
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    f = np.fft.rfftfreq(n, 1.0 / SR)
    centers = np.array([125.0, 250, 500, 1000, 2000, 4000, 8000, 16000])
    rt60 = np.array([2.7, 2.8, 2.7, 2.4, 1.9, 1.35, 0.8, 0.45])
    lf = np.log2(np.maximum(f, 1.0))
    lc = np.log2(centers)
    ir = np.zeros((n, 2))
    for ch in range(2):
        S = np.fft.rfft(rng.standard_normal(n))
        acc = np.zeros(n)
        for b in range(len(centers)):
            w = np.clip(1.0 - np.abs(lf - lc[b]), 0.0, 1.0)
            if b == 0:
                w = np.where(lf < lc[0], 1.0, w)
            if b == len(centers) - 1:
                w = np.where(lf > lc[-1], 1.0, w)
            acc += np.fft.irfft(S * w, n) * np.exp(-6.908 * t / rt60[b])
        acc *= (1.0 - np.exp(-t / 0.015))          # diffuse build-up, no slap
        for _ in range(7):                          # a few early reflections
            d = int(rng.uniform(0.007, 0.055) * SR)
            acc[d] += rng.choice([-1.0, 1.0]) * rng.uniform(4.0, 9.0) * np.std(acc[:SR // 10])
        pd = int(predelay * SR)
        acc = np.concatenate([np.zeros(pd), acc[:n - pd]])
        ir[:, ch] = acc
    ir = fftfilt(ir, hp(140.0, 2))                 # keep the low end dry and clean
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True))
    return ir


def convolve(x, ir):
    n = x.shape[0]
    size = 1
    while size < n + ir.shape[0]:
        size *= 2
    out = np.zeros_like(x)
    for c in range(2):
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], size) * np.fft.rfft(ir[:, c], size), size)[:n]
    return out


# ----------------------------------------------------------------------------
# instruments
MB_PARTIALS = [  # (frequency ratio, amplitude, decay scale): a struck steel tine
    (1.0, 1.00, 1.00), (2.0, 0.30, 0.60), (3.0, 0.07, 0.40),
    (4.2, 0.03, 0.30), (6.27, 0.15, 0.17), (9.8, 0.03, 0.10),
]


def musicbox(midi, vel, rng, tau_scale=1.0):
    f = m2f(midi)
    tau = float(np.clip(1.7 * (880.0 / f) ** 0.5, 0.45, 3.0)) * tau_scale
    n = int(min(6.5 * tau, 6.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    dl, dr = 2.0 ** (-2.6 / 1200.0), 2.0 ** (2.6 / 1200.0)
    for r, a, ts in MB_PARTIALS:
        fp = f * r
        if fp > 7500.0:
            continue
        if r > 2.5:
            a = a * (0.5 + 0.7 * vel)              # harder strike, brighter tine
        if fp > 4500.0:
            a = a * (4500.0 / fp) ** 1.5           # soften the top of the ting
        env = a * np.exp(-t / (tau * ts))
        main = np.sin(2 * np.pi * fp * t)
        if r <= 2.0:                               # centre tone plus quieter detuned sides (mono-safe width)
            out[:, 0] += env * (main + 0.36 * np.sin(2 * np.pi * fp * dl * t)) / 1.36
            out[:, 1] += env * (main + 0.36 * np.sin(2 * np.pi * fp * dr * t)) / 1.36
        else:
            out += (env * main)[:, None]
    tick = fftfilt(rng.standard_normal(256), band(1500.0, 6000.0, 1)) * np.exp(-np.arange(256) / 40.0)
    out[:256] += (0.035 * vel) * tick[:, None]
    out = edges(out, 0.0015, 0.06)
    return out * (vel ** 1.25) * min(1.0, (1000.0 / f) ** 0.35)


def softkey(midi, vel, rng):
    """Mellow celesta-like key for the waltz chords, arpeggios and rolled chords."""
    f = m2f(midi)
    tau = float(np.clip(0.95 * (330.0 / f) ** 0.4, 0.35, 1.7))
    n = int(6.0 * tau * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    dl, dr = 2.0 ** (-3.0 / 1200.0), 2.0 ** (3.0 / 1200.0)
    for r, a, ts in ((1, 1.0, 1.0), (2, 0.34, 0.7), (3, 0.11, 0.5), (4, 0.04, 0.4)):
        env = a * np.exp(-t / (tau * ts))
        main = np.sin(2 * np.pi * f * r * t)
        out[:, 0] += env * (main + 0.36 * np.sin(2 * np.pi * f * r * dl * t)) / 1.36
        out[:, 1] += env * (main + 0.36 * np.sin(2 * np.pi * f * r * dr * t)) / 1.36
    out = edges(out, 0.005, 0.08)
    return out * (vel ** 1.2) * min(1.0, (700.0 / f) ** 0.3)


def pad_tone(midi, dur, att, rel, cutoff, rng, width=0.7):
    """Three detuned low-passed saws (additive, band-limited) with slow drift."""
    f = m2f(midi)
    n = int((dur + rel) * SR)
    tt = np.arange(n) / SR
    out = np.zeros((n, 2))
    for cents, p in ((-7.0, -width), (6.0, width), (0.6, 0.0)):
        fv = f * 2.0 ** (cents / 1200.0)
        K = int(max(1, min(40, min(2.6 * cutoff, 9000.0) / fv)))
        k = np.arange(1, K + 1)
        a = (1.0 / k) / np.sqrt(1.0 + (k * fv / cutoff) ** 4)
        tab = wavetable(a, rng.uniform(0, 2 * np.pi, K))
        fm = fv * (1.0 + 0.0016 * np.sin(2 * np.pi * rng.uniform(0.12, 0.3) * tt + rng.uniform(0, 6.28)))
        x = osc(tab, fm, n, rng.uniform())
        x *= 1.0 + 0.08 * np.sin(2 * np.pi * rng.uniform(0.08, 0.22) * tt + rng.uniform(0, 6.28))
        out += pan2(x / np.sqrt(np.sum(a ** 2) / 2.0), p)
    return edges(out, att, rel) / np.sqrt(3.0)


def bass_tone(midi, beats, vel):
    f = m2f(midi)
    dur = beats * BEAT
    n = int((dur + 0.35) * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.36 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    x *= np.exp(-t / 1.25)
    return edges(x, 0.03, 0.35) * vel


def glass_tone(midi, dur, vel, att, rel, rng):
    """Bowed-glass / pure tone with a slow shimmer."""
    f = m2f(midi)
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    vib = 1.0 + 0.0012 * np.sin(2 * np.pi * 4.6 * t + rng.uniform(0, 6.28))
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    main = np.sin(ph) + 0.10 * np.sin(2 * ph) + 0.03 * np.sin(3 * ph)
    for ch, cents in ((0, -3.0), (1, 3.0)):         # centre tone plus quieter detuned sides
        side = np.sin(ph * 2.0 ** (cents / 1200.0) + rng.uniform(0, 6.28))
        out[:, ch] = (main + 0.36 * side) / 1.36 * (1.0 + 0.16 * smoothnoise(n, 5.0, rng))
    return edges(out, att, rel) * vel * min(1.0, (500.0 / f) ** 0.5)


def twinkle(midi, vel, rng):
    f = m2f(midi)
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.30)
    if f * 2.76 < 7000.0:
        x += 0.18 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.09)
    return edges(x, 0.004, 0.05) * vel * min(1.0, (1500.0 / f) ** 0.6)


# ----------------------------------------------------------------------------
# harmony: B minor for the lonely half, D major once the light finds a purpose
CH = {
    'Bm':      dict(pcs={11, 2, 6},    pad=[47, 54, 59, 62, 66], bass=47, comp=[66, 71]),
    'Bm_thin': dict(pcs={11, 2, 6},    pad=[54, 59, 62, 66],     bass=47, comp=[66, 71]),
    'B5':      dict(pcs={11, 6},       pad=[47, 54, 59],         bass=35, comp=[]),
    'G':       dict(pcs={7, 11, 2},    pad=[43, 55, 59, 62, 67], bass=43, comp=[67, 71]),
    'Gn5':     dict(pcs={7, 11},       pad=[43, 55, 59, 67],     bass=43, comp=[67, 71]),
    'Gmaj7':   dict(pcs={7, 11, 2, 6}, pad=[55, 59, 62, 66],     bass=43, comp=[66, 71]),
    'Gadd9':   dict(pcs={7, 11, 2, 9}, pad=[43, 55, 59, 62, 69], bass=43, comp=[67, 71]),
    'Gadd9n5': dict(pcs={7, 11, 9},    pad=[43, 55, 59, 67, 69], bass=43, comp=[67, 71]),
    'F#m7':    dict(pcs={6, 9, 1, 4},  pad=[42, 54, 57, 61, 64], bass=42, comp=[64, 69]),
    'F#7sus4': dict(pcs={6, 11, 1, 4}, pad=[54, 59, 61, 64],     bass=42, comp=[]),
    'A':       dict(pcs={9, 1, 4},     pad=[45, 57, 61, 64, 69], bass=45, comp=[69, 73]),
    'A7':      dict(pcs={9, 1, 4, 7},  pad=[45, 57, 61, 64, 67], bass=45, comp=[67, 73]),
    'A7sus4':  dict(pcs={9, 2, 4, 7},  pad=[45, 57, 62, 64, 67], bass=45, comp=[67, 74]),
    'D':       dict(pcs={2, 6, 9},     pad=[38, 50, 57, 62, 66], bass=38, comp=[66, 69]),
    'D/F#':    dict(pcs={2, 6, 9},     pad=[42, 57, 62, 66, 69], bass=42, comp=[69, 74]),
    'Em7':     dict(pcs={4, 7, 11, 2}, pad=[40, 52, 55, 59, 62], bass=40, comp=[67, 71]),
}
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def nn(m):
    return '%s%d' % (NAMES[m % 12], m // 12 - 1)


melody, chords, bassn, keysn, glassn, tw_zones = [], [], [], [], [], []


def M(t, midi, beats, vel, strong=False, tag='', double=(), warm=False, tau=1.0):
    melody.append(dict(t=t, midi=midi, beats=beats, vel=vel, strong=strong, tag=tag,
                       double=tuple(double), warm=warm, tau=tau))


def C(t0, t1, name, level=1.0, att=0.7, rel=1.6, cutoff=1400.0, up=0.0):
    if t1 - t0 > 0.02:
        chords.append(dict(t0=t0, t1=t1, name=name, level=level, att=att, rel=rel, cutoff=cutoff, up=up))


def B(t, midi, beats, vel):
    bassn.append(dict(t=t, midi=midi, beats=beats, vel=vel))


def K(t, midis, vel):
    for m in midis:
        keysn.append(dict(t=t, midi=m, vel=vel))


def G(t, midi, dur, vel, att=0.8, rel=1.5):
    glassn.append(dict(t=t, midi=midi, dur=dur, vel=vel, att=att, rel=rel))


def TW(t0, t1, density, level):
    if t1 > t0:
        tw_zones.append(dict(t0=t0, t1=t1, density=density, level=level))


def fit_bars(material, n):
    """Stretch or trim a list of composed bars to the bar count the shot really has."""
    m = len(material)
    if n == m:
        return list(material)
    if n < m:
        return (list(material[:n - 1]) + [material[-1]]) if n > 1 else [material[-1]]
    body = material[:-1] or material
    return [body[i % len(body)] for i in range(n - 1)] + [material[-1]]


def play_bars(s, material, warm=False):
    for i, b in enumerate(fit_bars(material, nbars(s))):
        t0 = bt(s, i, 0)
        pause = ev('look_back', t0, t0 + BAR) is not None   # a held breath: no waltz chords
        for b0, b1, name in b['ch']:
            C(t0 + b0 * BEAT, t0 + b1 * BEAT, name, level=b.get('lvl', 1.0), cutoff=b.get('cut', 1400.0),
              att=b.get('att', 0.7), up=b.get('up', 0.0))
        for beat, beats, midi, vel in b.get('mel', []):
            M(t0 + beat * BEAT, midi, beats, vel, strong=(beat == 0), double=b.get('dbl', ()), warm=warm)
        for beat, midi, beats, vel in b.get('bass', []):
            B(t0 + beat * BEAT, midi, beats, vel)
        if not pause:
            for beat, vel in b.get('comp', []):
                name = [c for c in b['ch'] if c[0] <= beat < c[1]][0][2]
                K(t0 + beat * BEAT, CH[name]['comp'], vel)
        for beat, midi, vel in b.get('keys', []):
            K(t0 + beat * BEAT, [midi], vel)
        for j, m in enumerate(b.get('roll', [])):
            K(t0 + j * 0.075, [m], 0.26 + 0.02 * j)
        for beat, midi, beats, vel in b.get('glass', []):
            G(t0 + beat * BEAT, midi, beats * BEAT, vel)


def compose():
    # The theme (D major, 3/4), stated whole across s08-s10 and echoed everywhere else:
    #   | F#5 .  A5 | D6 .  B5 | A5 G5 E5 | F#5 . A5 | D6 . E6 | B5 . C#6 | D6 . . |
    # Its head, F#-A-D, is a reach upward that lands on the tonic.

    # s01: stillness. The pad fades in; the head is only hinted, in B minor.
    s = SHOTS.get('s01')
    if s:
        nb = nbars(s)
        t0, t1 = s['start'], s['start'] + nb * BAR
        C(t0, t1, 'Bm', level=0.55, att=min(3.2, s['dur'] * 0.7), rel=2.0, cutoff=900.0)
        tn = bt(s, nb - 1, 0)
        gp = ev('glow_pulse')
        if gp and abs(gp['t'] - tn) <= BEAT:
            tn = gp['t']                         # the first note is the first glow
        M(tn, 78, 2, 0.40, strong=True, tag='theme head, hinted')
        M(bt(s, nb - 1, 2), 81, 1, 0.34)
        TW(t0 + 0.4, t1, 0.9, 0.50)

    # s02: longing. The reach arrives on D6 but over G major 7, then sinks.
    s = SHOTS.get('s02')
    if s:
        play_bars(s, [
            dict(ch=[(0, 3, 'Gmaj7')], lvl=0.70, cut=1000.0, mel=[(0, 3, 86, 0.46)]),
            dict(ch=[(0, 3, 'F#m7')], lvl=0.70, cut=1000.0, mel=[(0, 2, 85, 0.40), (2, 1, 83, 0.34)]),
        ])
        TW(s['start'], s['start'] + s['dur'], 0.5, 0.40)

    # s03: hope. A rising line over rising arpeggios; the pad lifts.
    s = SHOTS.get('s03')
    if s:
        play_bars(s, [
            dict(ch=[(0, 3, 'Gn5')], lvl=0.72, cut=1300.0,
                 mel=[(0, 1, 83, 0.44), (1, 1, 85, 0.48), (2, 1, 86, 0.52)],
                 keys=[(0, 55, 0.30), (0.5, 59, 0.31), (1, 67, 0.33), (1.5, 71, 0.35), (2, 74, 0.37), (2.5, 79, 0.39)]),
            dict(ch=[(0, 3, 'A')], lvl=0.85, cut=1700.0, up=0.5,
                 mel=[(0, 2, 88, 0.56), (2, 1, 90, 0.60)],
                 keys=[(0, 57, 0.34), (0.5, 61, 0.36), (1, 64, 0.38), (1.5, 69, 0.40), (2, 73, 0.42), (2.5, 76, 0.44)]),
        ])
        TW(s['start'], s['start'] + s['dur'], 0.6, 0.45)

    # s04: vast and thin. The top note hangs over a major seventh; at `falter` it weakens, unresolved.
    s = SHOTS.get('s04')
    if s:
        nb = nbars(s)
        t0, t1 = s['start'], s['start'] + s['dur']
        fa = ev('falter', t0 + 0.2, t1)
        tf = fa['t'] if fa else (bt(s, nb - 1, 0) if nb > 1 else t0 + s['dur'] / 2)
        C(t0, tf, 'Gmaj7', level=0.50, att=0.9, rel=2.2, cutoff=1100.0)
        C(tf, t1, 'F#7sus4', level=0.30, att=1.2, rel=2.0, cutoff=800.0)
        M(t0, 90, 3, 0.50, strong=True, tag='the top note hangs')
        G(t0 + 0.15, 78, (t1 - t0) - 0.9, 0.8, att=1.2, rel=1.8)
        M(tf, 88, 1, 0.30, strong=True, tag='falter')
        if tf + 1.6 * BEAT < t1 - 0.2:
            M(tf + 1.6 * BEAT, 85, 1.4, 0.20, tag='late, unresolved')
        TW(t0, tf, 1.3, 0.60)
        TW(tf, t1, 0.5, 0.35)

    # s05: the fall. A B minor arpeggio drops, slowing, into near silence.
    s = SHOTS.get('s05')
    if s:
        t0, t1 = s['start'], s['start'] + s['dur']
        fl = ev('fall', t0, t1)
        tfall = fl['t'] if fl else t0
        C(t0, t0 + s['dur'] * 0.6, 'Bm_thin', level=0.30, att=0.5, rel=2.2, cutoff=700.0)
        notes = [90, 86, 83, 78, 74, 71]
        step = min(BEAT / 2, (t1 - tfall - 0.1) / (len(notes) - 1 + 0.03 * (len(notes) - 1) ** 2))
        for i, m in enumerate(notes):
            M(tfall + step * (i + 0.03 * i * i), m, 0.5, 0.40 * 0.78 ** i, strong=(i == 0), tag='falling')

    # s06: dark and still. A bare fifth drone; one faint note when the glow drifts in.
    s = SHOTS.get('s06')
    if s:
        t0, t1 = s['start'], s['start'] + s['dur']
        C(t0, t1, 'B5', level=0.26, att=1.5, rel=2.5, cutoff=320.0)
        G(t0, 35, s['dur'], 0.60, att=1.6, rel=2.5)
        G(t0, 42, s['dur'], 0.36, att=1.8, rel=2.5)
        ge = ev('glow_enters', t0, t1)
        if ge:
            M(ge['t'], 78, 2, 0.20, tag="the firefly's note")

    # s07: the turn. Bare fifth, then at `glow_bloom` the bass drops B -> G and G major opens
    # (filter and all), a harp-like run climbs with the light, A7sus4 leads home to D.
    s = SHOTS.get('s07')
    if s:
        t0, t1 = s['start'], s['start'] + nbars(s) * BAR
        bl = ev('glow_bloom', t0, t1)
        tb = bl['t'] if bl else t0 + 2 * BEAT
        bd = float(bl.get('dur', 1.5)) if bl else 1.5
        t_dom = t1 - BEAT
        if tb > t0 + 0.05:
            C(t0, tb, 'B5', level=0.36, att=0.6, rel=1.4, cutoff=420.0)
            G(t0, 35, tb - t0, 0.75, att=0.6, rel=1.4)
        C(tb, t_dom, 'Gadd9', level=0.82, att=bd, rel=1.5, cutoff=750.0)
        C(tb, t_dom, 'Gadd9', level=0.70, att=bd * 1.7, rel=1.5, cutoff=2300.0, up=0.6)
        C(t_dom, t1, 'A7sus4', level=1.0, att=0.35, rel=1.3, cutoff=1700.0)
        B(tb, 43, (t_dom - tb) / BEAT, 0.55)
        B(t_dom, 45, 1, 0.50)
        run = [67, 71, 74, 79, 81, 83, 86]
        span = max(0.3, min(bd * 0.9, t_dom - tb - 0.4 * BEAT))
        for i, m in enumerate(run):
            M(tb + span * i / (len(run) - 1), m, 0.5, 0.30 + 0.28 * i / (len(run) - 1),
              strong=(i == 0), tag='bloom run' if i == 0 else '')
        ta = t_dom - BEAT
        if ta > tb + span + 0.15:
            M(ta, 81, 1, 0.46)
        M(t_dom, 76, 1, 0.46, strong=True)
        TW(tb, t1, 1.2, 0.55)

    # s08: the journey. Theme, first phrase: bass on one, soft chords on two and three.
    s = SHOTS.get('s08')
    if s:
        play_bars(s, [
            dict(ch=[(0, 3, 'D')], lvl=0.95, cut=1500.0, mel=[(0, 2, 78, 0.56), (2, 1, 81, 0.52)],
                 bass=[(0, 38, 2.6, 0.75)], comp=[(1, 0.26), (2, 0.24)]),
            dict(ch=[(0, 3, 'G')], lvl=0.95, cut=1500.0, mel=[(0, 2, 86, 0.62), (2, 1, 83, 0.52)],
                 bass=[(0, 43, 2.6, 0.75)], comp=[(1, 0.30), (2, 0.28)]),
            dict(ch=[(0, 3, 'A7')], lvl=0.95, cut=1500.0, mel=[(0, 1, 81, 0.56), (1, 1, 79, 0.50), (2, 1, 76, 0.50)],
                 bass=[(0, 45, 2.6, 0.75)], comp=[(1, 0.30), (2, 0.28)]),
        ], warm=True)

    # s09: the pond. Second phrase begins, hushed: music box and glass, no pulse.
    s = SHOTS.get('s09')
    if s:
        play_bars(s, [
            dict(ch=[(0, 3, 'Bm_thin')], lvl=0.50, cut=1000.0, mel=[(0, 2, 78, 0.40), (2, 1, 81, 0.38)],
                 dbl=[(12, 0.30)], glass=[(0, 71, 3, 0.60), (0, 78, 3, 0.40)]),
            dict(ch=[(0, 3, 'Em7')], lvl=0.55, cut=1000.0, mel=[(0, 2, 86, 0.44), (2, 1, 88, 0.42)],
                 dbl=[(12, 0.28)], glass=[(0, 67, 3, 0.60), (0, 76, 3, 0.40)], bass=[(0, 40, 2.4, 0.35)]),
        ])
        TW(s['start'], s['start'] + s['dur'], 0.5, 0.35)

    # s10: home. The phrase climbs B - C# - D and resolves; a breath where the mouse looks back.
    s = SHOTS.get('s10')
    if s:
        play_bars(s, [
            dict(ch=[(0, 2, 'G'), (2, 3, 'A7')], lvl=1.0, cut=1600.0, mel=[(0, 2, 83, 0.56), (2, 1, 85, 0.56)],
                 bass=[(0, 43, 1.7, 0.75), (2, 45, 0.9, 0.70)], comp=[(1, 0.30), (2, 0.32)]),
            dict(ch=[(0, 3, 'D')], lvl=1.0, cut=1600.0, mel=[(0, 3, 86, 0.62)],
                 bass=[(0, 38, 2.8, 0.80)], comp=[(1, 0.20), (2, 0.20)], roll=[62, 66, 69, 74]),
        ], warm=True)

    # s11: the camera rises. The s03 climb returns and this time it arrives: B C# D E F# G over
    # G - A - A7, the seventh hangs, and at `moral` it falls to F#: the head of the theme, alone.
    s = SHOTS.get('s11')
    if s:
        t0, t1 = s['start'], s['start'] + s['dur']
        mo = ev('moral', t0, t1)
        tm = float(s.get('moral_at', mo['t'] if mo else t0 + 0.6 * s['dur']))
        nsw = max(1, int((tm - t0) / BAR + 1e-6))
        swell = ['Bm', 'D/F#'] * nsw
        swell = swell[:max(0, nsw - 2)] + (['Gadd9n5', 'A'] if nsw >= 2 else ['Gadd9n5'])
        for i, name in enumerate(swell):
            b0 = t0 + i * BAR
            last, prev = i == nsw - 1, i == nsw - 2
            C(b0, b0 + BAR, name, level=1.10 + 0.15 * (i / max(1, nsw - 1)), att=0.6, rel=1.4, cutoff=2000.0, up=0.8)
            B(b0, CH[name]['bass'], 2.7, 0.85)
            dbl = [(-12, 0.55), (12, 0.22)]
            if nsw >= 2 and prev:
                for j, m in enumerate((83, 85, 86)):
                    M(b0 + j * BEAT, m, 1, 0.62 + 0.03 * j, strong=(j == 0), double=dbl, warm=True)
                for beat, m in ((0, 55), (0.5, 59), (1, 67), (1.5, 69), (2, 74), (2.5, 79)):
                    K(b0 + beat * BEAT, [m], 0.36 + 0.02 * beat)
            elif last and nsw >= 2:
                M(b0, 88, 2, 0.72, strong=True, double=dbl, warm=True)
                M(b0 + 2 * BEAT, 90, 1, 0.74, double=dbl, warm=True)
                for beat, m in ((0, 57), (0.5, 61), (1, 64), (1.5, 69), (2, 73), (2.5, 76)):
                    K(b0 + beat * BEAT, [m], 0.40 + 0.02 * beat)
            elif last:
                for j, m in enumerate((83, 85, 86)):
                    M(b0 + j * BEAT, m, 1, 0.64, strong=(j == 0), double=dbl, warm=True)
            else:
                M(b0, 78, 2, 0.56, strong=True, warm=True)
                M(b0 + 2 * BEAT, 81, 1, 0.52, warm=True)
        th = t0 + nsw * BAR
        if tm - th > 0.25:                         # the held breath before the resolution
            C(th, tm, 'A7', level=1.30, att=0.4, rel=0.6, cutoff=2100.0, up=0.8)
            B(th, 45, (tm - th) / BEAT, 0.85)
            M(th, 91 if nsw >= 2 else 88, (tm - th) / BEAT, 0.72, strong=True, tag='the seventh hangs',
              double=[(-12, 0.5)], tau=0.55)
        TW(t0, tm, 1.5, 0.60)
        # the moral: music box nearly alone
        C(tm, t1, 'D', level=0.55, att=0.45, rel=2.4, cutoff=1300.0)
        B(tm, 38, 3, 0.55)
        for j, m in enumerate((78, 81, 86)):
            tj = tm + j * BEAT
            if tj < t1 - 0.5 * BEAT:
                M(tj, m, 1 if j < 2 else 3, (0.60, 0.56, 0.64)[j], strong=(j == 0),
                  tag='theme head, alone' if j == 0 else '')
        TW(tm + BEAT, t1, 0.7, 0.45)

    # coda: afterglow. The answering phrase, softly: D E | B C# |
    s = SHOTS.get('coda')
    if s:
        play_bars(s, [
            dict(ch=[(0, 3, 'Gadd9')], lvl=0.50, cut=1100.0, mel=[(0, 2, 86, 0.36), (2, 1, 88, 0.34)],
                 glass=[(0, 71, 3, 0.40)]),
            dict(ch=[(0, 2, 'G'), (2, 3, 'A7')], lvl=0.50, cut=1100.0, mel=[(0, 2, 83, 0.34), (2, 1, 85, 0.34)]),
        ])
        TW(s['start'], s['start'] + s['dur'], 0.6, 0.40)

    # end: | D |. A rolled chord lands on the tonic and rings out; one last small star.
    s = SHOTS.get('end')
    if s:
        t0 = s['start']
        C(t0, max(t0 + 1.0, TOTAL - 2.6), 'D', level=0.60, att=0.5, rel=2.2, cutoff=1200.0)
        roll = [50, 57, 62, 66, 69, 74, 78, 81]
        for i, m in enumerate(roll):
            K(t0 + i * 0.07, [m], 0.20 + 0.02 * i)
        M(t0, 86, 3, 0.52, strong=True, tag='home')
        B(t0, 38, 3, 0.60)
        if nbars(s) >= 2:
            M(bt(s, 1, 0), 93, 2, 0.17, tag='last small star')
        TW(t0, TOTAL - 3.0, 0.5, 0.35)

    melody.sort(key=lambda m: m['t'])
    chords.sort(key=lambda c: (c['t0'], c['cutoff']))


def chord_at(t):
    best = None
    for c in chords:
        if c['t0'] - 1e-6 <= t < c['t1'] - 1e-6:
            best = c
    return best


def check_composition(verbose=True):
    """Print the score bar by bar; verify chord tones on strong beats and no minor-ninth rubs."""
    problems, passing = [], []
    for s in SHOT_LIST:
        t0, t1 = s['start'], s['start'] + s['dur']
        bars = max(1, int(np.ceil(s['dur'] / BAR - 1e-6)))
        for b in range(bars):
            a, z = t0 + b * BAR, min(t0 + (b + 1) * BAR, t1)
            cs = []
            for c in chords:
                if c['t0'] < z - 1e-6 and c['t1'] > a + 1e-6 and (not cs or cs[-1] != c['name']):
                    cs.append(c['name'])
            ms = ['%s@%.2f(%.2fs)' % (nn(m['midi']), (m['t'] - a) / BEAT + 1, m['t']) for m in melody if a - 1e-6 <= m['t'] < z - 1e-6]
            if verbose:
                print('  %-5s bar %2d  %6.2f s  %-18s %s' % (s['id'], int(round(a / BAR)) + 1, a, ' > '.join(cs) or '-', '  '.join(ms) or '.'))
    for m in melody:
        c = chord_at(m['t'] + 1e-3)
        if c is None:
            continue
        pcs = CH[c['name']]['pcs']
        padpcs = {p % 12 for p in CH[c['name']]['pad']}
        pc = m['midi'] % 12
        if m['strong'] and pc not in pcs:
            problems.append('strong-beat %s at %.2f s is not in %s' % (nn(m['midi']), m['t'], c['name']))
        for p in padpcs:
            if (pc - p) % 12 == 1:
                msg = '%s at %.2f s sits a minor ninth over %s in %s' % (nn(m['midi']), m['t'], NAMES[p], c['name'])
                (problems if m['beats'] > 1 or m['strong'] else passing).append(msg)
    if verbose:
        print('  strong-beat chord tones: %d checked, %d problems' % (sum(1 for m in melody if m['strong']), len(problems)))
        for p in problems:
            print('  PROBLEM ' + p)
        for p in passing:
            print('  passing ' + p)
    return problems


# ----------------------------------------------------------------------------
# rendering the music
def synth_music():
    parts = {k: Bus() for k in ('pad', 'box', 'keys', 'bass', 'glass', 'stars')}
    rng = rng_for('music')
    for c in chords:
        v = CH[c['name']]['pad']
        dur = c['t1'] - c['t0']
        g = LV['pad'] * c['level'] / np.sqrt(len(v) / 4.0)
        for m in v:
            w = 0.55 if m < 45 else (0.8 if m < 52 else 1.0)
            parts['pad'].put(c['t0'], pad_tone(m, dur, c['att'], c['rel'], c['cutoff'], rng), gain=g * w, send=SEND['pad'])
        if c['up'] > 0:
            for m in v[-3:]:
                parts['pad'].put(c['t0'], pad_tone(m + 12, dur, c['att'] * 1.3, c['rel'], c['cutoff'], rng),
                        gain=g * 0.45 * c['up'], send=SEND['pad'] * 1.4)
    for m in melody:
        t = m['t'] + rng.uniform(-0.006, 0.006)
        vel = m['vel'] * rng.uniform(0.95, 1.05)
        parts['box'].put(t, musicbox(m['midi'], vel, rng, m['tau']), gain=LV['box'], send=SEND['box'])
        for semi, vs in m['double']:
            if 55 <= m['midi'] + semi <= 98:
                parts['box'].put(t + rng.uniform(0.0, 0.008), musicbox(m['midi'] + semi, vel * vs, rng, m['tau']),
                        gain=LV['box'], send=SEND['box'])
        if m['warm']:
            parts['keys'].put(t, softkey(m['midi'], vel * 0.7, rng), gain=LV['key'], send=SEND['key'])
    for k in keysn:
        parts['keys'].put(k['t'] + rng.uniform(-0.007, 0.007), softkey(k['midi'], k['vel'] * rng.uniform(0.92, 1.08), rng),
                gain=LV['key'], send=SEND['key'])
    for b in bassn:
        parts['bass'].put(b['t'], bass_tone(b['midi'], b['beats'], b['vel']), gain=LV['bass'], send=SEND['bass'])
    for g in glassn:
        parts['glass'].put(g['t'], glass_tone(g['midi'], g['dur'], g['vel'], g['att'], g['rel'], rng), gain=LV['glass'], send=SEND['glass'])
    for z in tw_zones:                              # stars: sparse high chord tones
        n = rng.poisson(z['density'] * (z['t1'] - z['t0']))
        for t in np.sort(rng.uniform(z['t0'], z['t1'], n)):
            c = chord_at(t)
            if c is None or len(CH[c['name']]['pcs']) < 3:
                continue
            cands = [m for m in range(86, 101) if m % 12 in CH[c['name']]['pcs']]
            parts['stars'].put(t, twinkle(int(rng.choice(cands)), rng.uniform(0.5, 1.0), rng), gain=LV['twinkle'] * z['level'],
                    pan=rng.uniform(-0.8, 0.8), send=SEND['twinkle'])
    bus = Bus()
    for b in parts.values():
        bus.dry += b.dry
        bus.send += b.send
    return bus, {k: b.dry for k, b in parts.items()}


# ----------------------------------------------------------------------------
# ambience: crickets and night air
def smooth_gate(points, default=1.0, glide=1.2):
    """Piecewise gain automation from (time, value) points, then smoothed."""
    if not points:
        return np.full(NT, default)
    points = sorted(points)
    cr = 200.0                                      # smooth at control rate, then interpolate up
    tc = np.arange(int((TOTAL + TAIL) * cr) + 2) / cr
    g = np.interp(tc, [p[0] for p in points], [p[1] for p in points])
    k = max(3, int(glide * cr))
    win = np.hanning(k)
    win /= win.sum()
    pad = np.concatenate([np.full(k // 2, g[0]), g, np.full(k - k // 2, g[-1])])
    g = np.convolve(pad, win, mode='valid')[:len(tc)]
    return np.interp(np.arange(NT) / SR, tc, g)


def synth_ambience():
    rng = rng_for('ambience')
    tt = np.arange(NT) / SR
    cr = np.zeros((NT, 2))
    voices = [  # carrier Hz, chirp period s, syllables per chirp, pan, gain
        (4650.0, 0.83, 3, -0.60, 1.00), (4950.0, 1.09, 4, 0.50, 0.80), (4320.0, 0.66, 2, 0.15, 0.62),
        (5180.0, 1.33, 3, -0.20, 0.50), (4480.0, 0.95, 3, 0.78, 0.45),
    ]
    for fc, period, syl, p, gain in voices:
        env = np.zeros(NT)
        t = rng.uniform(0.0, period)
        sing_until = t + rng.uniform(5.0, 11.0)
        while t < TOTAL + 1.0:
            if t > sing_until:                      # crickets rest, then start again
                t += rng.uniform(1.0, 2.8)
                sing_until = t + rng.uniform(5.0, 11.0)
            a = rng.uniform(0.75, 1.0)
            for k in range(syl):
                i = int((t + k * 0.034 + rng.normal(0, 0.0012)) * SR)
                w = int(0.019 * SR)
                if 0 <= i and i + w < NT:
                    env[i:i + w] += a * (0.7 if k == 0 else 1.0) * np.hanning(w)
            t += period * (1.0 + rng.normal(0, 0.035))
        car = np.sin(2 * np.pi * fc * tt + 1.2 * np.sin(2 * np.pi * 0.23 * tt + rng.uniform(0, 6.28)))
        cr += pan2(env * car * gain, p)
    trill = fftfilt(rng.standard_normal((NT, 2)), band(5200.0, 6400.0, 4))
    trill *= (0.5 + 0.5 * np.sin(2 * np.pi * 46.0 * tt))[:, None] ** 2
    trill *= (0.7 + 0.3 * smoothnoise(NT, 0.2, rng))[:, None]
    cr = cr * LV['crickets'] + trill * (LV['trill'] / np.sqrt(np.mean(trill ** 2)) * 0.5)

    air = rng.standard_normal((NT, 2))
    air = fftfilt(air, lambda f: hp(110.0, 2)(f) * lp(950.0, 2)(f) * np.minimum(1.0, (220.0 / np.maximum(f, 1.0)) ** 0.5))
    air /= np.sqrt(np.mean(air ** 2))
    air *= (0.75 + 0.25 * smoothnoise(NT, 0.13, rng))[:, None]

    # automation, all from events: fade in, thin out while the firefly is high, muffle in the dark
    pts = [(0.0, 0.0)]
    ai = ev('ambience_in')
    ta = ai['t'] if ai else 0.0
    pts += [(ta, 0.0), (ta + 3.0, 1.0)]
    to, fl = ev('takeoff'), ev('fall')
    if to and fl and fl['t'] > to['t']:
        pts += [(to['t'], 1.0), (to['t'] + 3.0, 0.5), (fl['t'], 0.5), (fl['t'] + 1.5, 0.8)]
    muffle = [(0.0, 0.0)]
    dk = ev('dark')
    if dk:
        s = shot_at(dk['t'])
        end = s['start'] + s['dur'] if s else dk['t'] + BAR * 2
        bl = ev('glow_bloom', end)
        back = bl['t'] + 2.0 if bl else end + BAR
        pts += [(dk['t'] - 0.8, 0.8), (dk['t'] + 0.6, 0.30), (end, 0.36), (back, 1.0)]
        muffle += [(dk['t'] - 0.8, 0.0), (dk['t'] + 0.6, 1.0), (end, 1.0), (back, 0.0)]
    pts.append((TOTAL + TAIL, 1.0))
    muffle.append((TOTAL + TAIL, 0.0))
    g = smooth_gate(pts)[:, None]
    mu = smooth_gate(muffle)[:, None]
    cr_dark = fftfilt(cr, lp(2400.0, 2))
    cr = (cr * (1 - mu) + cr_dark * mu) * g
    air = air * LV['air'] * (0.55 + 0.45 * g)
    return cr, air


# ----------------------------------------------------------------------------
# sound effects, each placed by an event in the timeline
def wings_fx(e, rng):
    t0 = e['t']
    t1 = float(e.get('until', t0 + 2.0))
    n = int((t1 - t0 + 0.4) * SR)
    t = t0 + np.arange(n) / SR
    takeoff = ev('takeoff', t0 - 0.6, t0 + 0.6)
    fa = ev('falter', t0, t1)
    fl = ev('fall', t0, t1)
    if takeoff:                                     # strong, then faltering, then sputtering
        I = np.ones(n)
        if fa:
            tend = fl['t'] if fl else t1
            I = np.where(t > fa['t'], np.interp(t, [fa['t'], tend], [0.78, 0.42]), np.interp(t, [t0, fa['t']], [1.0, 0.78]))
            tremor = np.clip((t - fa['t']) / max(tend - fa['t'], 0.1), 0, 1)
            I = I * (1.0 - 0.45 * tremor * np.clip(smoothnoise(n, 5.5, rng), 0, 1.4))
        if fl:
            after = np.clip((t - fl['t']) / max(t1 - fl['t'], 0.1), 0, 1)
            gate = (smoothnoise(n, 11.0, rng) > (-0.4 + 1.5 * after)).astype(float)
            k = int(0.012 * SR)
            gate = np.convolve(gate, np.hanning(k) / np.hanning(k).sum(), mode='same')
            depth = np.clip((t - fl['t']) / 0.25, 0, 1)
            I = I * (1 - after) ** 0.7 * (1.0 - depth * (1.0 - gate))
    else:                                           # light steady flight
        I = np.full(n, 0.40)
        pd = ev('pond', t0, t1)
        if pd:
            s = shot_at(pd['t'])
            if s:
                I = I * np.interp(t, [s['start'] - 0.5, s['start'] + 0.3, s['start'] + s['dur'] - 0.3, s['start'] + s['dur'] + 0.5],
                                  [1.0, 0.6, 0.6, 1.0])
        I = I * (1.0 + 0.18 * smoothnoise(n, 0.7, rng))
    I = np.clip(I, 0.0, 1.2)
    fade_in = 0.55 if takeoff else 0.3
    I *= np.clip((t - t0) / fade_in, 0, 1) ** 1.5 * np.clip((t1 + 0.3 - t) / 0.45, 0, 1)
    f0 = 92.0 + 42.0 * I + 3.5 * smoothnoise(n, 1.6, rng)
    if takeoff:
        f0 -= 26.0 * np.exp(-(t - t0) / 0.35)       # the buzz rises as it lifts off
    ph = np.cumsum(f0) / SR
    tab = wavetable([1.0, 0.50, 0.28, 0.15, 0.08, 0.04], rng.uniform(0, 6.28, 6))
    harm = np.interp((ph % 1.0) * TSIZE, np.arange(TSIZE + 1), tab)
    flutter = 1.0 - 0.30 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(13.0 + 3.0 * smoothnoise(n, 2.0, rng)) / SR))
    breath = fftfilt(rng.standard_normal(n), band(320.0, 2100.0, 4))
    breath = breath / np.sqrt(np.mean(breath ** 2)) * (0.5 + 0.5 * np.sin(2 * np.pi * ph)) ** 2
    x = I ** 1.15 * (0.85 * harm * flutter + 0.42 * breath)
    x = fftfilt(x, lp(2600.0, 4))
    p = 0.25 * smoothnoise(n, 0.35, rng)
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return t0, np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def glow_fx(dur, midis, rng, air=0.0, warm=None):
    """A soft shimmering swell: high partials, each trembling at its own rate."""
    n = int((dur * 2.6) * SR)
    t = np.arange(n) / SR
    env = np.where(t < dur, (0.5 - 0.5 * np.cos(np.pi * t / dur)) ** 1.5, np.exp(-(t - dur) / (0.55 * dur)))
    out = np.zeros((n, 2))
    for m in midis:
        f = m2f(m)
        for ch in range(2):
            trem = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(4.5, 9.0) * t + rng.uniform(0, 6.28))
            out[:, ch] += np.sin(2 * np.pi * f * 2.0 ** (rng.uniform(-4, 4) / 1200.0) * t + rng.uniform(0, 6.28)) * trem \
                * min(1.0, (1200.0 / f) ** 0.7)
    out /= max(1, len(midis)) ** 0.5
    if air:
        a = fftfilt(rng.standard_normal((n, 2)), band(1800.0, 5200.0, 2))
        out += air * a / np.sqrt(np.mean(a ** 2))
    if warm:
        for m in warm:
            out += (0.9 * np.sin(2 * np.pi * m2f(m) * t))[:, None]
    return edges(out * env[:, None], 0.01, 0.2)


def hop_fx(rng, wood=False):
    n = int(0.17 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(72.0 + 150.0 * np.exp(-t / 0.028)) / SR
    x = np.sin(ph) * np.exp(-t / 0.034)
    pat = fftfilt(rng.standard_normal(n), band(250.0, 1900.0, 2))
    x += 1.1 * pat / np.sqrt(np.mean(pat ** 2)) * np.exp(-t / 0.009) * 0.5
    if wood:                                        # a small hollow knock for the twig
        f = rng.uniform(560.0, 690.0)
        x += 0.75 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.024) + 0.25 * np.sin(2 * np.pi * f * 2.4 * t) * np.exp(-t / 0.012)
    return edges(x, 0.0015, 0.03)


def drip_fx(f0, rng):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = f0 * (0.82 + 0.18 * np.exp(-t / 0.10)) * (1.0 - 0.42 * np.exp(-t / 0.011))  # bubble up, then a falling ring
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.085) + 0.2 * np.sin(2.4 * ph) * np.exp(-t / 0.035)
    return edges(x, 0.002, 0.05)


def fall_fx(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = m2f(78) * (m2f(59) / m2f(78)) ** (t / dur) ** 0.8
    wob = 1.0 + 0.012 * (t / dur) * np.sin(2 * np.pi * 9.0 * t)
    ph = 2 * np.pi * np.cumsum(f * wob) / SR
    x = (np.sin(ph) + 0.15 * np.sin(2 * ph)) * (1.0 - t / dur) ** 1.4
    return edges(x, 0.15, 0.3)


def synth_sfx():
    bus = Bus()
    rng = rng_for('sfx')
    for e in evs('wings'):
        t0, x = wings_fx(e, rng)
        bus.put(t0, x, gain=LV['wings'], send=SEND['sfx'] * 0.5)
    to = ev('takeoff')
    if to:                                          # a short airy lift
        n = int(0.8 * SR)
        t = np.arange(n) / SR
        a = fftfilt(rng.standard_normal(n), band(450.0, 2600.0, 4))
        a = a / np.sqrt(np.mean(a ** 2)) * np.sin(np.pi * t / 0.8) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(70.0 + 60.0 * t / 0.8) / SR))
        bus.put(to['t'], a, gain=LV['takeoff'], send=SEND['sfx'])
    for e in evs('glow_pulse'):                     # the weak pulse of a firefly that feels small
        until = float(e.get('until', (to['t'] if to and to['t'] > e['t'] else e['t'] + 4.0)))
        every = float(e.get('every', 1.0))
        k = 0
        while e['t'] + k * every < until - 0.4:
            bus.put(e['t'] + k * every, glow_fx(0.42, [78, 90], rng), gain=LV['glow'] * rng.uniform(0.75, 1.0),
                    pan=0.0, send=SEND['sfx'] * 1.5)
            k += 1
    ge = ev('glow_enters')
    if ge:
        bus.put(ge['t'] - 0.3, glow_fx(0.9, [78, 90, 97], rng), gain=LV['glow'] * 0.9, send=SEND['sfx'] * 1.8)
    bl = ev('glow_bloom')
    if bl:                                          # the turn: light opening
        bd = float(bl.get('dur', 1.5))
        bus.put(bl['t'], glow_fx(bd, [79, 83, 86, 93, 98], rng, air=0.10, warm=[55, 62]), gain=LV['bloom'], send=SEND['sfx'] * 1.6)
    fl = ev('fall')
    if fl:
        s = shot_at(fl['t'])
        dur = min(2.0, (s['start'] + s['dur'] - fl['t']) if s else 2.0)
        bus.put(fl['t'], fall_fx(max(0.6, dur - 0.2), rng), gain=LV['fall'], pan=-0.1, send=SEND['sfx'] * 1.5)
    pd = ev('pond')
    pond_shot = shot_at(pd['t']) if pd else None
    for e in evs('hops'):
        every = float(e.get('every', BEAT / 2))
        until = float(e.get('until', e['t'] + BAR))
        k = 0
        while e['t'] + k * every <= until + 1e-6:
            th = e['t'] + k * every
            wood = bool(pond_shot and pond_shot['start'] <= th < pond_shot['start'] + pond_shot['dur'])
            g = LV['hop'] * rng.uniform(0.72, 1.0) * (0.85 if wood else 1.0) * (1.0 if k % 2 == 0 else 0.86)
            bus.put(th, hop_fx(rng, wood), gain=g, pan=rng.uniform(-0.18, 0.18), send=SEND['sfx'] * (0.9 if wood else 0.5))
            k += 1
    if pd:                                          # glassy drips between the careful steps
        for off, m in ((0.42, 86), (2.46, 95), (4.44, 88)):
            th = pd['t'] + off * BEAT
            if pond_shot is None or th < pond_shot['start'] + pond_shot['dur'] - 0.2:
                bus.put(th, drip_fx(m2f(m), rng), gain=LV['drip'] * rng.uniform(0.8, 1.0), pan=rng.uniform(-0.5, 0.5),
                        send=SEND['sfx'] * 2.2)
    ho = ev('home')
    if ho:                                          # the window's warmth
        bus.put(ho['t'], glow_fx(1.3, [74, 81], rng, warm=[50, 57, 66]), gain=LV['home'], send=SEND['sfx'])
    ri = ev('rise')
    if ri:
        mo = ev('moral', ri['t'])
        dur = (mo['t'] - ri['t']) if mo else 5.0
        bus.put(ri['t'], glow_fx(max(1.0, dur * 0.9), [86, 90, 93, 98], rng, air=0.22), gain=LV['rise'], send=SEND['sfx'] * 1.5)
    return bus


# ----------------------------------------------------------------------------
# metering and mastering
def k_weight(x):
    n = x.shape[0]
    z = np.exp(-1j * 2 * np.pi * np.fft.rfftfreq(n, 1.0 / SR) / SR)
    h1 = (1.53512485958697 - 2.69169618940638 * z + 1.19839281085285 * z * z) / (1 - 1.69065929318241 * z + 0.73248077421585 * z * z)
    h2 = (1 - 2 * z + z * z) / (1 - 1.99004745483398 * z + 0.99007225036621 * z * z)
    return np.stack([np.fft.irfft(np.fft.rfft(x[:, c]) * h1 * h2, n) for c in range(2)], axis=1)


def lufs(x, kw=None):
    """Integrated loudness, ITU-R BS.1770-4: K-weighting, 400 ms blocks, both gates."""
    y = k_weight(x) if kw is None else kw
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if y.shape[0] < blk:
        return -120.0
    cs = np.concatenate([np.zeros((1, 2)), np.cumsum(y ** 2, axis=0)])
    idx = np.arange(0, y.shape[0] - blk + 1, hop)
    z = ((cs[idx + blk] - cs[idx]) / blk).sum(axis=1)
    l = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    keep = l > -70.0
    if not keep.any():
        return -120.0
    gate = -0.691 + 10 * np.log10(z[keep].mean()) - 10.0
    keep &= l > gate
    return float(-0.691 + 10 * np.log10(z[keep].mean()))


def true_peak_db(x):
    pk = 0.0
    n = x.shape[0]
    for c in range(2):
        X = np.fft.rfft(x[:, c])
        Y = np.zeros(2 * n + 1, complex)
        Y[:len(X)] = X
        pk = max(pk, float(np.max(np.abs(np.fft.irfft(Y, 4 * n) * 4))))
    return 20 * np.log10(max(pk, 1e-12))


def sliding_min(x, w):
    out = x.copy()
    span = 1
    while span < w:
        step = min(span, w - span)
        out = np.minimum(out, np.concatenate([out[step:], np.ones(step)]))
        span += step
    c = w // 2
    return np.concatenate([np.ones(c), out[:-c]])


def limiter_gain(x, ceiling):
    need = np.minimum(1.0, ceiling / np.maximum(np.max(np.abs(x), axis=1), 1e-9))
    w = int(0.010 * SR) | 1
    g = sliding_min(need, w)
    cs = np.concatenate([[0.0], np.cumsum(np.concatenate([np.ones(w // 2), g, np.ones(w // 2)]))])
    return (cs[w:] - cs[:-w]) / w


def db(v):
    return 20 * np.log10(max(float(v), 1e-12))


def write_wav(path, x, seed):
    rng = np.random.default_rng(seed)
    d = (rng.random(x.shape) - rng.random(x.shape)) * (x != 0)       # TPDF dither, none on true silence
    y = np.clip(np.round(x * 32767.0 + d), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def main():
    compose()
    print('The Smallest Star: %.0f bpm, %d/4, bar %.3f s, %d bars, %.1f s' % (BPM, BEATS, BAR, round(TOTAL / BAR), TOTAL))
    print('Composition (bar, time, chords, melody as note@beat(time)):')
    problems = check_composition()
    if '--notes' in sys.argv:
        return 1 if problems else 0

    ir = make_ir(SEED)
    mus, parts = synth_music()
    music = mus.dry + convolve(fftfilt(mus.send, lp(7500.0, 1)), ir)
    cr, air = synth_ambience()
    amb = cr + convolve(cr, ir) * SEND['crickets'] + air
    fx = synth_sfx()
    sfx = fx.dry + convolve(fftfilt(fx.send, lp(6500.0, 1)), ir)

    tone = lambda f: hp(32.0, 2)(f) * lp(11500.0, 1)(f)               # no rumble, soft top
    stems = dict(music=fftfilt(music, tone), ambience=fftfilt(amb, tone), sfx=fftfilt(sfx, tone))

    # ring out to silence half a second before the end
    silent_at = TOTAL - 0.5
    t = np.arange(NT) / SR
    fade = np.clip((silent_at - t) / 3.0, 0.0, 1.0)
    fade = (0.5 - 0.5 * np.cos(np.pi * fade))[:, None]
    for k in stems:
        stems[k] = (stems[k] * fade)[:N]
        stems[k] -= stems[k].mean(axis=0, keepdims=True) * (np.arange(N) / SR < silent_at)[:, None]
    mix = stems['music'] + stems['ambience'] + stems['sfx']

    # loudness: gain to target, limit the rare peak, repeat once so the target holds
    deepest, touched = 1.0, 0.0
    for _ in range(3):
        g = 10 ** ((TARGET_LUFS - lufs(mix)) / 20.0)
        lim = limiter_gain(mix * g, 10 ** (CEILING_DB / 20.0))
        deepest, touched = min(deepest, float(lim.min())), max(touched, float(np.mean(lim < 0.999)))
        lg = lim[:, None] * g
        for k in stems:
            stems[k] = stems[k] * lg
        mix = stems['music'] + stems['ambience'] + stems['sfx']

    # ---- checks -------------------------------------------------------------
    assert mix.shape == (N, 2), mix.shape
    assert np.isfinite(mix).all(), 'NaN or inf in the mix'
    kw = k_weight(mix)
    L = lufs(mix, kw)
    tp = true_peak_db(mix)
    print('\nMix: %.2f LUFS integrated (own BS.1770 meter), sample peak %.2f dBFS, true peak %.2f dBTP (4x)' % (L, db(np.max(np.abs(mix))), tp))
    print('     DC %.1e / %.1e, L/R correlation %.2f, mono fold-down %.2f dB vs stereo power, energy above 8 kHz %.1f dB' % (
        mix[:, 0].mean(), mix[:, 1].mean(), float(np.corrcoef(mix[:, 0], mix[:, 1])[0, 1]),
        10 * np.log10(np.mean(((mix[:, 0] + mix[:, 1]) / 2) ** 2) / np.mean((mix ** 2).sum(axis=1) / 2)),
        10 * np.log10(np.mean(fftfilt(mix, hp(8000.0, 6)) ** 2) / np.mean(mix ** 2))))
    print('     limiter touched %.3f%% of samples, deepest %.2f dB; stems LUFS: music %.1f, ambience %.1f, sfx %.1f' % (
        100 * touched, db(deepest), lufs(stems['music']), lufs(stems['ambience']), lufs(stems['sfx'])))
    print('\n  section   start    dur   LUFS    RMS dB  peak dB  centroid Hz   music/amb/sfx RMS dB   sfx peak')
    for s in SHOT_LIST:
        a, z = int(s['start'] * SR), min(N, int((s['start'] + s['dur']) * SR))
        seg = mix[a:z]
        mono = seg.mean(axis=1)
        mag = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
        fr = np.fft.rfftfreq(len(mono), 1.0 / SR)
        print('  %-7s %6.2f %6.2f %7.1f %8.1f %8.1f %10.0f      %6.1f %6.1f %6.1f   %6.1f' % (
            s['id'], s['start'], s['dur'], lufs(seg, kw[a:z]), db(np.sqrt(np.mean(seg ** 2))), db(np.max(np.abs(seg))),
            float((fr * mag).sum() / max(mag.sum(), 1e-12)),
            db(np.sqrt(np.mean(stems['music'][a:z] ** 2))), db(np.sqrt(np.mean(stems['ambience'][a:z] ** 2))),
            db(np.sqrt(np.mean(stems['sfx'][a:z] ** 2))), db(np.max(np.abs(stems['sfx'][a:z])))))
    print('\n  dry instrument RMS dB before mastering (relative balance)   pad    box   keys   bass  glass  stars')
    for s in SHOT_LIST:
        a, z = int(s['start'] * SR), min(N, int((s['start'] + s['dur']) * SR))
        print('  %-7s' % s['id'] + ' ' * 52 + ' '.join('%6.1f' % db(np.sqrt(np.mean(parts[k][a:z] ** 2))) for k in ('pad', 'box', 'keys', 'bass', 'glass', 'stars')))
    print('\n  loudness per bar (LUFS, 400 ms blocks inside each bar):')
    row = []
    for b in range(int(round(TOTAL / BAR))):
        a, z = int(b * BAR * SR), min(N, int((b + 1) * BAR * SR))
        row.append('%5.1f' % lufs(mix[a:z], kw[a:z]))
    for i in range(0, len(row), 14):
        print('   bars %2d-%2d: ' % (i + 1, min(i + 14, len(row))) + ' '.join(row[i:i + 14]))
    tail = mix[int(silent_at * SR):]
    print('  after %.1f s: peak %.1f dBFS (silence)' % (silent_at, db(np.max(np.abs(tail))) if len(tail) else -240))

    write_wav(os.path.join(HERE, 'score.wav'), mix, 1)
    write_wav(os.path.join(HERE, 'stem_music.wav'), stems['music'], 2)
    write_wav(os.path.join(HERE, 'stem_ambience.wav'), stems['ambience'], 3)
    write_wav(os.path.join(HERE, 'stem_sfx.wav'), stems['sfx'], 4)
    print('\nwrote score.wav, stem_music.wav, stem_ambience.wav, stem_sfx.wav (%d samples, %.3f s, 48 kHz stereo 16-bit)' % (N, N / SR))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
