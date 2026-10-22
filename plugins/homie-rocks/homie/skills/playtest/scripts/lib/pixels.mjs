/**
 * What a screenshot of a game shows, in numbers: brightness, contrast, colour, detail, flat dead
 * areas, black frames, motion between two frames, and how much of the screen the page's own UI
 * covers. ffmpeg decodes the PNG; plain JavaScript does the counting.
 *
 * Why these: a black or flat world is the most common way a game "works" in a test and fails on
 * a person's screen (a shader that did not compile, a camera inside a wall, a world that never
 * loaded for a late joiner). Edge density separates a finished-looking frame from a flat-shaded
 * placeholder better than brightness or a histogram does; a flat, featureless frame passes those.
 */
import { spawnSync } from 'node:child_process';

/**
 * How long one PNG decode may take. ffmpeg decodes a phone screenshot in well under a second; a decoder that is
 * still running after this is stuck (one sat for over five minutes with the game drawing fine behind it), and a
 * `spawnSync` with no bound holds the whole controller in it: no report, no closed browser. HOMIE_PLAYTEST_DECODE_MS
 * sets another bound (a very slow disk, or a test that wants it short).
 */
export const DECODE_TIMEOUT_MS = Math.max(200, Number(process.env.HOMIE_PLAYTEST_DECODE_MS) || 20_000);

/**
 * The instrument could not read its own picture: nothing about the game was measured. Callers report the row
 * BLOCKED (never FAIL, never PASS) and close their browser; `blocked` is how they tell it from a game fault.
 */
export class DecodeBlocked extends Error {
  constructor(message) { super(message); this.name = 'DecodeBlocked'; this.blocked = true; }
}

/**
 * Decode a PNG (a Buffer or a path) to RGB at `width` pixels wide. Returns { w, h, rgb }. Bounded: after
 * `timeoutMs` the decoder is killed and a DecodeBlocked is thrown. `bin` is the decoder (a test puts a stuck one here).
 */
export function decode(png, width = 480, { timeoutMs = DECODE_TIMEOUT_MS, bin = process.env.HOMIE_PLAYTEST_FFMPEG || 'ffmpeg' } = {}) {
  const input = Buffer.isBuffer(png) ? ['-f', 'png_pipe', '-i', '-'] : ['-i', png];
  const probe = spawnSync(bin, ['-hide_banner', '-loglevel', 'error', ...input, '-vf', `scale=${width}:-2:flags=area`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], { input: Buffer.isBuffer(png) ? png : undefined, maxBuffer: 256 * 1024 * 1024, timeout: timeoutMs, killSignal: 'SIGKILL' });
  // spawnSync reports its own timeout as error.code ETIMEDOUT (and the child killed by the signal above).
  if (probe.error?.code === 'ETIMEDOUT') throw new DecodeBlocked(`the screenshot decoder (ffmpeg) did not finish in ${Math.round(timeoutMs / 1000)} s and was stopped: the picture was not measured`);
  if (probe.error?.code === 'ENOENT') throw new DecodeBlocked('ffmpeg is not installed: screenshots cannot be measured on this computer');
  if (probe.status !== 0) throw new Error(`ffmpeg could not decode a screenshot: ${String(probe.stderr).trim().split('\n').pop()}`);
  const rgb = probe.stdout;
  const h = Math.round(rgb.length / 3 / width);
  return { w: width, h, rgb };
}

const lumaAt = (rgb, i) => 0.2126 * rgb[i] + 0.7152 * rgb[i + 1] + 0.0722 * rgb[i + 2];

/**
 * { mean, sd, saturation, edges, darkShare, flatDarkShare, black, flat }
 *   mean/sd       Rec.709 luma 0..255 and its spread (contrast)
 *   saturation    mean HSV saturation 0..1
 *   edges         share of pixels whose 3x3 luma range is over 24 (visible detail)
 *   darkShare     share of pixels under luma 16
 *   flatBlackShare share of 8x8 blocks that are perfectly flat (range <= 2) and black (mean < 5): a hole where
 *                 nothing drew (a shader that failed, a world that never loaded, the clear colour showing through)
 *   flatDarkShare  the same for dark (mean < 24): a plain dark backdrop, or an unlit world
 *   black         the frame is essentially black (mean < 8 and sd < 6); flat: sd < 4 (one colour)
 * `crop` { x, y, w, h } in fractions measures only part of the frame (the play area without the HUD).
 */
export function stats(img, { crop = null } = {}) {
  const { w, h, rgb } = img;
  const x0 = crop ? Math.floor(crop.x * w) : 0; const y0 = crop ? Math.floor(crop.y * h) : 0;
  const x1 = crop ? Math.min(w, Math.ceil((crop.x + crop.w) * w)) : w; const y1 = crop ? Math.min(h, Math.ceil((crop.y + crop.h) * h)) : h;
  const lum = new Float32Array(w * h);
  for (let i = 0, p = 0; i < w * h; i++, p += 3) lum[i] = lumaAt(rgb, p);
  let n = 0; let sum = 0; let sum2 = 0; let sat = 0; let dark = 0; let edges = 0;
  for (let y = y0; y < y1; y++) {
    for (let x = x0; x < x1; x++) {
      const i = y * w + x; const p = i * 3;
      const l = lum[i];
      n++; sum += l; sum2 += l * l;
      const mx = Math.max(rgb[p], rgb[p + 1], rgb[p + 2]); const mn = Math.min(rgb[p], rgb[p + 1], rgb[p + 2]);
      sat += mx > 0 ? (mx - mn) / mx : 0;
      if (l < 16) dark++;
      if (x > x0 && y > y0 && x < x1 - 1 && y < y1 - 1) {
        let lo = 255; let hi = 0;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const v = lum[i + dy * w + dx]; if (v < lo) lo = v; if (v > hi) hi = v; }
        if (hi - lo > 24) edges++;
      }
    }
  }
  let blocks = 0; let flatDark = 0; let flatBlack = 0;
  for (let by = y0; by + 8 <= y1; by += 8) {
    for (let bx = x0; bx + 8 <= x1; bx += 8) {
      let lo = 255; let hi = 0; let s = 0;
      for (let y = by; y < by + 8; y++) for (let x = bx; x < bx + 8; x++) { const v = lum[y * w + x]; s += v; if (v < lo) lo = v; if (v > hi) hi = v; }
      blocks++;
      if (hi - lo <= 2 && s / 64 < 24) flatDark++;
      if (hi - lo <= 2 && s / 64 < 5) flatBlack++;
    }
  }
  const mean = sum / Math.max(1, n);
  const sd = Math.sqrt(Math.max(0, sum2 / Math.max(1, n) - mean * mean));
  const r = (v, p = 3) => +v.toFixed(p);
  return { mean: r(mean, 1), sd: r(sd, 1), saturation: r(sat / Math.max(1, n)), edges: r(edges / Math.max(1, n)), darkShare: r(dark / Math.max(1, n)), flatDarkShare: r(flatDark / Math.max(1, blocks)), flatBlackShare: r(flatBlack / Math.max(1, blocks)), black: mean < 8 && sd < 6, flat: sd < 4 };
}

/** Share of pixels that changed by more than `threshold` luma between two frames of the same size. */
export function motion(a, b, threshold = 12) {
  if (a.w !== b.w || a.h !== b.h) return null;
  let changed = 0; const n = a.w * a.h;
  for (let i = 0, p = 0; i < n; i++, p += 3) if (Math.abs(lumaAt(a.rgb, p) - lumaAt(b.rgb, p)) > threshold) changed++;
  return +(changed / n).toFixed(4);
}

/**
 * How much of the screen the page's UI covers, from two screenshots taken with the world hidden and the
 * page's background black (a) and then white (b): a pixel the UI does not cover shows the background, so
 * it flips; a pixel under an opaque panel stays. alpha = 1 - |b - a| / 255.
 * Returns { cover (alpha > 0.25), opaque (alpha > 0.6), centreOpaque (opaque share of the middle third) }.
 */
export function uiCover(onBlack, onWhite) {
  if (onBlack.w !== onWhite.w || onBlack.h !== onWhite.h) throw new Error('the two UI screenshots differ in size');
  const { w, h } = onBlack;
  let cover = 0; let opaque = 0; let centre = 0; let centreOpaque = 0;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const p = (y * w + x) * 3;
      const d = Math.max(Math.abs(onWhite.rgb[p] - onBlack.rgb[p]), Math.abs(onWhite.rgb[p + 1] - onBlack.rgb[p + 1]), Math.abs(onWhite.rgb[p + 2] - onBlack.rgb[p + 2]));
      const alpha = 1 - d / 255;
      const inCentre = x >= w / 3 && x < (2 * w) / 3 && y >= h / 3 && y < (2 * h) / 3;
      if (alpha > 0.25) cover++;
      if (alpha > 0.6) { opaque++; if (inCentre) centreOpaque++; }
      if (inCentre) centre++;
    }
  }
  const n = w * h;
  return { cover: +(cover / n).toFixed(3), opaque: +(opaque / n).toFixed(3), centreOpaque: +(centreOpaque / Math.max(1, centre)).toFixed(3) };
}
