#!/usr/bin/env python3
"""Lay the narration over the synthesized score: place each line from timeline.json, duck the music under
speech, add a little room, and bring the mix to -16 LUFS. Writes audio/mix_narrated.wav."""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); SR = 48000
TL = json.load(open(os.path.join(HERE, '..', 'timeline.json')))
N = int(round(TL['total_seconds'] * SR))


def read(path):
    w = wave.open(path, 'rb'); assert w.getframerate() == SR, path
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return x.reshape(-1, w.getnchannels())


def smooth(x, ms):
    # Hann window by FFT: a direct convolution with a 25,000-tap kernel takes minutes
    n = max(1, int(SR * ms / 1000)); k = np.hanning(n * 2 + 1); k /= k.sum()
    M = 1 << int(np.ceil(np.log2(len(x) + len(k))))
    y = np.fft.irfft(np.fft.rfft(x, M) * np.fft.rfft(k, M), M)
    return y[n:n + len(x)]


def hp(x, fc=85.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (f ** 2 / (f ** 2 + fc ** 2)), len(x))


music, amb, sfx = (read(os.path.join(HERE, f'stem_{k}.wav'))[:N] for k in ('music', 'ambience', 'sfx'))
vo = np.zeros(N)
for ln in TL['narration']['lines']:
    x = hp(read(os.path.join(HERE, 'vo', ln['file']))[:, 0])
    act = np.abs(x) > 10 ** (-40 / 20)
    rms = np.sqrt(np.mean(x[act] ** 2)); x *= 10 ** (-21.0 / 20) / rms          # every line at the same speech level
    f = int(SR * 0.012); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    i = int(round(ln['t'] * SR)); j = min(N, i + len(x)); vo[i:j] += x[:j - i]
    ln['end'] = round(ln['t'] + len(x) / SR, 2)

# a short, dark room so the voice sits in the same space as the score
rng = np.random.default_rng(7); L = int(SR * 0.9); tt = np.arange(L) / SR
ir = rng.standard_normal(L) * np.exp(-tt / 0.22); ir[:int(SR * 0.012)] = 0
IR = np.fft.rfft(ir, 2 * L); fr = np.fft.rfftfreq(2 * L, 1 / SR); ir = np.fft.irfft(IR / (1 + (fr / 3500.0) ** 2), 2 * L)[:L]
ir /= np.sqrt(np.sum(ir ** 2))
M = 1 << int(np.ceil(np.log2(N + L)))
wet = np.fft.irfft(np.fft.rfft(vo, M) * np.fft.rfft(ir, M), M)[:N]
voice = np.stack([vo + 0.10 * wet, vo + 0.10 * np.roll(wet, int(SR * 0.007))], axis=1)

# duck the music 9.5 dB under speech: quick down, slow back
env = smooth((np.abs(vo) > 10 ** (-38 / 20)).astype(float), 40)
gate = np.clip(smooth(np.maximum.reduce([np.roll(env, -int(SR * 0.10)), env, np.roll(env, int(SR * 0.25))]), 260) * 1.6, 0, 1)
duck = 10 ** (-9.5 * gate / 20)
mix = music * duck[:, None] + amb + sfx + voice * 10 ** (5.5 / 20)


def measure(x):
    tmp = os.path.join(HERE, '_tmp_mix.wav'); write(tmp, x)
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', tmp, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    os.remove(tmp)
    I = float([l for l in out.split('\n') if l.strip().startswith('I:')][-1].split()[1])
    P = float([l for l in out.split('\n') if l.strip().startswith('Peak:')][-1].split()[1])
    return I, P


def write(path, x):
    w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767.0).astype(np.int16).tobytes()); w.close()


I, P = measure(mix)
mix *= 10 ** ((-16.0 - I) / 20)
I, P = measure(mix)
if P > -1.2:                                   # round the few highest peaks, then trim what is left
    th = 10 ** (-4.0 / 20); a = np.abs(mix); over = a > th
    mix[over] = np.sign(mix[over]) * (th + (1 - th) * np.tanh((a[over] - th) / (1 - th)) * 0.7)
    I, P = measure(mix)
    if P > -1.2:
        mix *= 10 ** ((-1.3 - P) / 20); I, P = measure(mix)
write(os.path.join(HERE, 'mix_narrated.wav'), mix)
sp = gate > 0.5
r = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
print(f'mix_narrated.wav: {I:.1f} LUFS integrated, true peak {P:.1f} dBTP, {N / SR:.3f} s')
print(f'while speaking, before the final gain: voice {r(voice[sp] * 10 ** (5.5 / 20)):.1f} dB, music under it {r((music * duck[:, None])[sp]):.1f} dB (unducked {r(music[sp]):.1f} dB)')
for ln in TL['narration']['lines']:
    i, j = int(ln['t'] * SR), int(ln['end'] * SR)
    v = r(voice[i:j] * 10 ** (5.5 / 20)); m = r((music * duck[:, None])[i:j])
    print(f"  {ln['t']:6.2f}-{ln['end']:6.2f}  voice {v:6.1f}  bed {m:6.1f}  margin {v - m:5.1f} dB  {ln['text'][:48]}")
