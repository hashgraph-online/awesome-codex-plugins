# Signed offset of the sound at each cut, plus a shift test: does the edit follow the sound more than chance?
# usage: sound_vs_cuts.py clip.mp4 cut1 cut2 cut3 ...
import subprocess
import sys
import numpy as np

path = sys.argv[1]
cuts = np.array([float(c) for c in sys.argv[2:]])
sr, hop, n = 22050, 256, 1024
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
y = np.frombuffer(raw, np.float32)
win = np.hanning(n)
frames = np.stack([y[i:i + n] * win for i in range(0, len(y) - n, hop)])
mag = np.log1p(40 * np.abs(np.fft.rfft(frames, axis=1)))
flux = np.maximum(np.diff(mag, axis=0), 0).mean(axis=1)
avg = np.convolve(flux, np.ones(43) / 43, "same")
peaks = [i for i in range(1, len(flux) - 1)
         if flux[i] > flux[i - 1] and flux[i] > flux[i + 1] and flux[i] > 1.5 * avg[i] + 0.2 * np.percentile(flux, 99.5)]
onsets = (np.array(peaks) + 1) * hop / sr + (n / 2) / sr

for c in cuts:
    near = onsets[np.abs(onsets - c) <= 0.4]
    if len(near):
        off = (near[np.argmin(np.abs(near - c))] - c) * 1000
        print(f"cut {c:6.2f}s: sound {off:+6.0f} ms" + ("  LATE" if off > 125 else "  EARLY" if off < -45 else ""))
    else:
        print(f"cut {c:6.2f}s: no sound within 400 ms")

dur = len(y) / sr
hit = lambda cs: np.mean([np.min(np.abs(onsets - c)) <= 0.05 for c in cs])
rng = np.random.default_rng(7)
sims = [hit((cuts + rng.uniform(0, dur)) % dur) for _ in range(400)]
print(f"on the cut: {hit(cuts):.0%}, by chance {np.mean(sims):.0%}, z {(hit(cuts) - np.mean(sims)) / (np.std(sims) or 1e-6):+.1f}")
