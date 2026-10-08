/**
 * Honest frames and the page's own sound, shared by capture-game.mjs (a game's big screen) and record-page.mjs
 * (any page, driven by a script):
 *
 *   startScreencast   the compositor's own frame stream (CDP Page.startScreencast): every frame kept as a JPEG
 *                     with the time Chrome presented it.
 *   constantRate      those frames onto a constant frame rate: output frame k shows the newest frame presented by
 *                     t0 + k/fps. A frame the page did not paint in time is HELD (and counted), never invented: no
 *                     interpolation, no blending.
 *   TapReader         tap.js's copy of what a frame sends to its speaker (WebAudio), stamped with the audio clock.
 *   fitAudio          that sound laid onto the picture's clock (a straight-line fit of the audio clock to the page's).
 *   encodeMp4         H.264 (+ AAC when there was sound), limited-range BT.709 (converted and tagged), faststart.
 *   BT709_TAIL        the end of a filter chain that makes a picture limited-range BT.709 yuv420p, and says so
 *   BT709_FLAGS       the encoder flags that carry those tags into the file
 *   frameSegments     an edit's segments as whole frames, each cut on the frame nearest its time
 */
import { spawnSync } from 'node:child_process';
import { closeSync, openSync, readFileSync, rmSync, writeFileSync, writeSync } from 'node:fs';
import { join } from 'node:path';

/** Start keeping every frame the compositor presents; `stop()` ends it. `frames` fills as they arrive. */
export async function startScreencast(page, { dir, width, height, quality = 88 }) {
  const frames = [];
  const cdp = await page.createCDPSession();
  cdp.on('Page.screencastFrame', (e) => {
    const file = join(dir, `${String(frames.length).padStart(6, '0')}.jpg`);
    writeFileSync(file, Buffer.from(e.data, 'base64'));
    frames.push({ file, t: e.metadata.timestamp });
    cdp.send('Page.screencastFrameAck', { sessionId: e.sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality, maxWidth: width, maxHeight: height, everyNthFrame: 1 });
  return { frames, stop: () => cdp.send('Page.stopScreencast').catch(() => {}) };
}

/**
 * Frames (each `{ file, t }`, t in epoch seconds) onto a constant frame rate. `until` (epoch seconds) holds the last
 * frame to that time: a page that did not change at the end still lasts as long as it was recorded.
 */
export function constantRate(frames, fps, { until = null } = {}) {
  const sorted = [...frames].sort((a, b) => a.t - b.t);
  const t0 = sorted[0].t;
  const end = Math.max(sorted.at(-1).t, until ?? 0);
  const total = Math.floor((end - t0) * fps);
  const list = [];
  let j = 0; let held = 0; let last = -1;
  for (let k = 0; k < total; k++) {
    const t = t0 + k / fps;
    while (j + 1 < sorted.length && sorted[j + 1].t <= t + 1e-4) j++;
    if (j === last) held++;
    last = j;
    list.push(sorted[j].file);
  }
  return { t0, total, list, held, distinct: new Set(list).size, frames: sorted };
}

/** An ffconcat list: each output frame for exactly 1/fps. */
export function writeConcat(file, list, fps) {
  writeFileSync(file, `ffconcat version 1.0\n${list.map((f) => `file '${f}'\nduration ${(1 / fps).toFixed(6)}`).join('\n')}\nfile '${list.at(-1)}'\n`);
  return file;
}

/** Drains tap.js in one frame (window.__homieTap) into a raw 16-bit stereo file, with the audio clock's samples. */
export class TapReader {
  constructor(pcmFile) {
    this.pcmFile = pcmFile;
    this.fd = openSync(pcmFile, 'w');
    this.pulls = []; this.clock = []; this.frames = 0; this.rate = null;
  }

  async poll(frame) {
    const got = await frame.evaluate(() => ({ runs: window.__homieTap ? window.__homieTap.take() : [], c: window.__homieTap ? window.__homieTap.clock() : null }));
    if (got.c) { this.clock.push(got.c); this.rate = got.c.rate ?? this.rate; }
    for (const r of got.runs) {
      this.pulls.push({ ctxFrame: r.f, fileFrame: this.frames, frames: r.frames });
      writeSync(this.fd, Buffer.from(r.b64, 'base64'));
      this.frames += r.frames;
    }
  }

  close() { try { closeSync(this.fd); } catch { /* closed */ } }
}

/**
 * The tap's sound onto the picture's clock, written as raw s16le stereo at the context's rate (`out`). Fits
 * epoch(ms) = a + b * contextTime from the output timestamps (or the context clock against the wall when there are
 * too few). Returns null when there was no sound to fit.
 */
export function fitAudio(tap, { t0, total, fps, out }) {
  if (!(tap.frames > 0 && tap.rate)) return null;
  const pts = tap.clock.filter((c) => c.ot && c.state === 'running').map((c) => c.ot);
  const use = pts.length >= 8 ? pts : tap.clock.filter((c) => c.now != null).map((c) => [c.now, c.wall]);
  const n = use.length; const mx = use.reduce((s, p) => s + p[0], 0) / n; const my = use.reduce((s, p) => s + p[1], 0) / n;
  let sxy = 0; let sxx = 0; for (const [x, y] of use) { sxy += (x - mx) * (y - my); sxx += (x - mx) ** 2; }
  // The audio clock runs at real time (a sound card drifts by parts per million). A straight line fitted over a short
  // span of jittery timestamps can be percents off (measured: 1037.9 ms per second from 14 samples over 3.5 s), which
  // walks the sound away from the picture; then only the offset is fitted (the median, which ignores outliers).
  const span = use.length ? Math.max(...use.map((p) => p[0])) - Math.min(...use.map((p) => p[0])) : 0;
  const line = sxx ? sxy / sxx : null;
  const trust = line !== null && span >= 20 && Math.abs(line - 1000) < 2;
  const b = trust ? line : 1000;
  const offsets = use.map(([x, y]) => y - b * x).sort((p, q) => p - q);
  const a = trust ? my - b * mx : offsets[Math.floor(offsets.length / 2)];
  const raw = readFileSync(tap.pcmFile);
  const src = new Int16Array(raw.buffer, raw.byteOffset, Math.floor(raw.byteLength / 2));
  const outFrames = Math.round((total / fps) * tap.rate);
  const dst = new Int16Array(outFrames * 2);
  let filled = 0;
  const pulls = [...tap.pulls].sort((x, y) => x.ctxFrame - y.ctxFrame);
  let q = -1;
  for (let i = 0; i < outFrames; i++) {
    const epochMs = (t0 + i / tap.rate) * 1000;
    const ctxT = (epochMs - a) / b;
    const F = Math.round(ctxT * tap.rate);
    while (q + 1 < pulls.length && pulls[q + 1].ctxFrame <= F) q++;
    const p = q >= 0 ? pulls[q] : null;
    if (!p || F - p.ctxFrame >= p.frames) continue;
    const at = p.fileFrame + (F - p.ctxFrame);
    dst[i * 2] = src[at * 2]; dst[i * 2 + 1] = src[at * 2 + 1]; filled++;
  }
  let peak = 0; for (let i = 0; i < dst.length; i++) peak = Math.max(peak, Math.abs(dst[i]));
  writeFileSync(out, Buffer.from(dst.buffer));
  const audio = { rate: tap.rate, seconds: +(outFrames / tap.rate).toFixed(3), covered: +(filled / Math.max(1, outFrames)).toFixed(3), peakDb: peak ? +(20 * Math.log10(peak / 32767)).toFixed(1) : null, fitMsPerS: +b.toFixed(3), fit: trust ? 'line' : 'offset', samples: use.length, raw: out };
  if (!peak) audio.note = 'the page made no sound while it was recorded';
  return audio;
}

/**
 * The last filters of every picture this skill encodes: limited-range ("tv") BT.709 in yuv420p, with the frames
 * tagged so. A frame that comes from a JPEG (every captured frame does) is FULL range with BT.601 coefficients.
 * `format=yuv420p` alone changes neither: the encoder then writes a full-range file that ffprobe calls yuvj420p,
 * with no primaries and no transfer tag, and a phone that assumes limited range shows it washed out or crushed.
 * `-colorspace bt709` on the encoder only relabels the matrix without converting it. So: scale converts the
 * range and the matrix from what the frame says it is, format picks the layout, setparams writes the tags.
 */
export const BT709_TAIL = 'scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709';
export const BT709_FLAGS = ['-pix_fmt', 'yuv420p', '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709'];

/**
 * An edit's segments as whole frames. Each cut is put on the frame nearest its time in the music, and a segment
 * is the frames between two cuts: 1.875 s at 30 fps is 56.25 frames, so the segments run 56, 56, 57, 56 … and
 * no cut is ever more than half a frame from its beat.
 *
 * Trimming each segment by its duration instead (what this did before) rounds every segment by itself: nine
 * 1.875 s segments came out a quarter of a frame short each, and the cuts walked away from a bed that plays at
 * its own speed, up to five frames by the end of a trailer.
 */
export function frameSegments(segments, fps) {
  let t = 0; let done = 0;
  return segments.map((s) => {
    t += s.dur;
    const end = Math.round(t * fps + 1e-6);
    const frames = Math.max(1, end - done);
    const out = { startFrame: done, frames, at: t - s.dur };
    done += frames;
    return out;
  });
}

/** The film: the concat list's frames at `fps`, scaled to w x h, with the fitted sound when it had any. */
export function encodeMp4({ concat, audio, fps, width, height, seconds, out, crf = 16 }) {
  const sound = audio?.peakDb != null;
  const args = ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', concat];
  if (sound) args.push('-f', 's16le', '-ar', String(audio.rate), '-ac', '2', '-i', audio.raw);
  args.push('-map', '0:v', ...(sound ? ['-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000'] : []),
    '-vf', `fps=${fps},scale=${width}:${height}:flags=lanczos,${BT709_TAIL}`, '-c:v', 'libx264', '-preset', 'medium', '-crf', String(crf), '-r', String(fps),
    ...BT709_FLAGS, '-movflags', '+faststart', '-t', seconds.toFixed(3), out);
  const r = spawnSync('ffmpeg', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (audio?.raw) rmSync(audio.raw, { force: true });
  return { ok: r.status === 0, why: r.status === 0 ? null : (r.stderr ?? '').trim().split('\n').pop() };
}
