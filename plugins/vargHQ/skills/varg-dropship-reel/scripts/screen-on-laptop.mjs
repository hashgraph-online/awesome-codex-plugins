#!/usr/bin/env node
// Put real screenshots onto the green screen of one laptop photo, in perspective, so every
// laptop shot shows the exact same app UI (pixel for pixel) on the exact same desk.
//
//   node screen-on-laptop.mjs plate.png out/ shot1.png shot2.png …
//
// plate.png: a 9:16 photo of a laptop whose screen is flat chroma green (#00FF00), no hand
// (make it once with gpt_image_2_5, see references/screen-demo.md). Each screenshot (any size,
// 16:10 is best) is warped onto the green quad; the frame comes out at 2x the plate size as
// out/<screenshot name>.jpg, ready for image-to-video, where the model only adds the hand.
// Runs with node 18+ or bun; needs ffmpeg + ffprobe.
import { mkdirSync } from "node:fs";
import { basename, join } from "node:path";
import { spawnSync } from "node:child_process";

const [plate, outDir, ...shots] = process.argv.slice(2);
if (!plate || !outDir || !shots.length) {
  console.error("usage: node screen-on-laptop.mjs plate.png out/ shot1.png [shot2.png …]");
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });
const run = (cmd, args, opts = {}) => {
  const r = spawnSync(cmd, args, { maxBuffer: 1 << 30, ...opts });
  if (r.status !== 0) throw new Error(`${cmd} failed: ${r.stderr?.toString().slice(-400)}`);
  return r.stdout;
};

// Plate at 2x, so small UI text survives the warp; the video model downsizes later anyway.
const [pw, ph] = run("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", plate])
  .toString().trim().split(",").map(Number);
const W = pw * 2, H = ph * 2;
const rgb = run("ffmpeg", ["-v", "error", "-i", plate, "-vf", `scale=${W}:${H}:flags=lanczos`, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]);

// The four corners of the green screen: extremes of x+y and x−y over the green pixels.
let tl, tr, br, bl, sMin = Infinity, sMax = -Infinity, dMin = Infinity, dMax = -Infinity, n = 0;
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  const i = (y * W + x) * 3, r = rgb[i], g = rgb[i + 1], b = rgb[i + 2];
  if (!(g > 140 && g > r + 60 && g > b + 60)) continue;
  n++;
  const s = x + y, d = x - y;
  if (s < sMin) { sMin = s; tl = [x, y]; }
  if (s > sMax) { sMax = s; br = [x, y]; }
  if (d > dMax) { dMax = d; tr = [x, y]; }
  if (d < dMin) { dMin = d; bl = [x, y]; }
}
if (n < W * H * 0.02) throw new Error("no green screen found in the plate (needs a flat #00FF00 screen)");
console.error(`screen corners: TL ${tl} TR ${tr} BR ${br} BL ${bl}`);

for (const shot of shots) {
  const out = join(outDir, basename(shot).replace(/\.[^.]+$/, "") + ".jpg");
  // Screenshot → full-frame canvas → perspective onto the quad; a touch darker and softer, like a
  // photographed screen. The plate goes on top with its green keyed out (a 2 px choke hides the fringe).
  const fc = [
    `[1:v]scale=${W}:${H},format=rgba,perspective=0:0:${W}:0:0:${H}:${W}:${H}:sense=source,` +
      `perspective=${tl[0]}:${tl[1]}:${tr[0]}:${tr[1]}:${bl[0]}:${bl[1]}:${br[0]}:${br[1]}:sense=destination,` +
      `eq=brightness=-0.015:saturation=0.97,gblur=sigma=0.5[screen]`,
    `[0:v]scale=${W}:${H}:flags=lanczos,format=rgba,colorkey=0x00FF00:0.32:0.08,erosion=threshold0=0:threshold1=0:threshold2=0:threshold3=255[plate]`,
    `[screen][plate]overlay=0:0,format=yuvj420p[v]`,
  ].join(";");
  run("ffmpeg", ["-v", "error", "-y", "-i", plate, "-i", shot, "-filter_complex", fc, "-map", "[v]", "-frames:v", "1", "-q:v", "3", out]);
  console.log(out);
}
