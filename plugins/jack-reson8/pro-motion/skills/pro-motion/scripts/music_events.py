#!/usr/bin/env python3
"""Per-band event list for cutting picture to music (the edit list, not a summary).
usage: music_events.py music/mono.wav music/   → music/events.json + printed table
Finds, from the actual audio: kick / bass / mid / snare / hat onsets (band-limited spectral flux),
tonal mid stabs (horns, keys), 1 kHz-ish beeps, section
boundaries (spectral novelty), a beat grid from hat/kick inter-onset intervals cross-checked
at half and double time, and a per-frame level envelope (30 fps) for level-driven motion.
Shouts, lyrics and exact melody are not detected here: confirm them by ear or with ASR before mapping a brand moment."""
import json, sys
import numpy as np, scipy.io.wavfile as w, scipy.signal as s

src, out = sys.argv[1], sys.argv[2].rstrip('/')
sr, x = w.read(src); x = x.astype(float); x = x if x.ndim == 1 else x.mean(1); x /= np.abs(x).max() + 1e-9
hop = int(sr * .005); f, t, Z = s.stft(x, sr, nperseg=1024, noverlap=1024 - hop); P = np.abs(Z)
band = lambda a, b: P[(f >= a) & (f < b)]
def onsets(a, b, pct=97, gap=.09):
    e = np.log1p(band(a, b).sum(0) * 50); d = np.maximum(0, np.diff(e, prepend=e[0]))
    pk, _ = s.find_peaks(d, height=np.percentile(d, pct), distance=int(gap / .005)); return [round(float(t[i]), 3) for i in pk]
def spans(mask, minlen):
    out, on, st = [], False, 0
    for ti, m in zip(t, mask):
        if m and not on: st, on = ti, True
        if on and not m:
            if ti - st >= minlen: out.append([round(float(st), 2), round(float(ti - st), 2)])
            on = False
    return out
ev = {k: onsets(*r) for k, r in {'kick': (35, 120), 'bass': (120, 300), 'mid': (300, 1500), 'snare': (1500, 5000), 'hat': (6000, 11000)}.items()}
mid = band(250, 1600); peak = mid.max(0) ** 2 / ((mid ** 2).sum(0) + 1e-9); eng = mid.sum(0)
ev['tonal_mid'] = spans((peak > .12) & (eng > np.percentile(eng, 70)), .08)
k = np.argmin(abs(f - 1000)); tone = P[k - 1:k + 2].sum(0) ** 2 / ((P ** 2).sum(0) + 1e-12)
ev['beeps'] = spans(tone > .25, .05)
S = np.log1p(P[:200]); step = 20; win = 100
flux = np.array([np.abs(S[:, i:i + win].mean(1) - S[:, i - win:i].mean(1)).sum() if i > win else 0 for i in range(0, S.shape[1], step)])
pk, _ = s.find_peaks(flux, distance=10, prominence=np.percentile(flux, 80) * .3); ev['sections'] = [round(float(t[::step][i]), 2) for i in pk]
iois = np.diff(ev['hat'] + ev['kick']); iois = np.sort(np.abs(iois)); iois = iois[(iois > .25) & (iois < 1.2)]
beat = float(np.median(iois)) if len(iois) else None
ev['beat_s'] = beat; ev['bpm_candidates'] = [round(60 / beat * m, 1) for m in (.5, 1, 2)] if beat else []
fps = 30; n = int(len(x) / sr * fps); hp = sr // fps
lv = np.array([np.sqrt(np.mean(x[i * hp:(i + 2) * hp] ** 2)) for i in range(n)]); ev['level_30fps'] = [round(float(v), 3) for v in np.clip(lv / (np.percentile(lv, 98) + 1e-9), 0, 1)]
json.dump(ev, open(f'{out}/events.json', 'w'))
for key, v in ev.items():
    if key != 'level_30fps': print(f'{key:12s}', v if not isinstance(v, list) or len(v) < 24 else v[:24] + ['…'])
