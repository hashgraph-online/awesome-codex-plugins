#!/usr/bin/env node
// Put new openers in front of a winning ad: one MP4 per hook, same body.
//
//   node hook-swap.mjs --body master.mp4 --cut 7.34 --out variants/ hookA.mp4 hookB.mp4+lineB.mp3 …
//
// --body   the winner WITHOUT burned captions (re-caption every variant afterwards)
// --cut    seconds where the body starts: the first word after the old hook (take it from word timings)
// hooks    a clip, or "clip.mp4+line.mp3" to lay a new spoken line over the clip; the hook lasts as long as
//          the line + 0.3 s (or the clip, or --hook-dur), at most the clip length (the last frame holds)
// Every part is normalised to 1080x1920, 30 fps, 48 kHz before the join, with a 20 ms fade at the cut so
// there is no click. Writes variants/v1.mp4 … and variants/manifest.json. Runs with node 18+ or bun; needs ffmpeg.
import { mkdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { spawnSync } from "node:child_process";

const argv = process.argv.slice(2);
const opt = (n) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv.splice(i, 2)[1] : undefined; };
const body = opt("body"), cut = Number(opt("cut")), out = opt("out") ?? "variants", fixedDur = opt("hook-dur");
const hooks = argv;
if (!body || Number.isNaN(cut) || !hooks.length) {
  console.error("usage: node hook-swap.mjs --body master.mp4 --cut <seconds> [--out dir] [--hook-dur s] hook.mp4[+line.mp3] …");
  process.exit(1);
}
mkdirSync(out, { recursive: true });
const dur = (f) => Number(spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).stdout.toString());
const hasAudio = (f) => spawnSync("ffprobe", ["-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", f]).stdout.toString().trim() !== "";
const V = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p";
const A = "aresample=48000,aformat=channel_layouts=stereo";

const manifest = { body, cut, variants: [] };
hooks.forEach((h, i) => {
  const [clip, line] = h.split("+");
  const clipLen = dur(clip);
  const hd = +(fixedDur ? Number(fixedDur) : line ? Math.min(dur(line) + 0.3, clipLen + 2) : clipLen).toFixed(3);
  const file = join(out, `v${i + 1}.mp4`);
  const args = ["-v", "error", "-y", "-i", clip, "-i", body];
  let hookAudio;
  if (line) { args.push("-i", line); hookAudio = `[2:a]${A},apad,atrim=0:${hd}`; }
  else if (hasAudio(clip)) hookAudio = `[0:a]${A},apad,atrim=0:${hd}`;
  else { args.push("-f", "lavfi", "-t", String(hd), "-i", "anullsrc=r=48000:cl=stereo"); hookAudio = `[2:a]${A}`; }
  const fc = [
    `[0:v]${V},tpad=stop_mode=clone:stop_duration=${hd},trim=duration=${hd},setpts=PTS-STARTPTS[hv]`,
    `${hookAudio},afade=t=out:st=${Math.max(0, hd - 0.02)}:d=0.02,asetpts=PTS-STARTPTS[ha]`,
    `[1:v]trim=start=${cut},setpts=PTS-STARTPTS,${V}[bv]`,
    `[1:a]atrim=start=${cut},asetpts=PTS-STARTPTS,${A},afade=t=in:d=0.02[ba]`,
    `[hv][ha][bv][ba]concat=n=2:v=1:a=1[v][a]`,
  ].join(";");
  args.push("-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", file);
  const r = spawnSync("ffmpeg", args, { stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status ?? 1);
  manifest.variants.push({ file, hook: basename(clip), line: line ? basename(line) : null, hookSeconds: hd, totalSeconds: +dur(file).toFixed(2) });
  console.log(file);
});
writeFileSync(join(out, "manifest.json"), JSON.stringify(manifest, null, 2));
console.error(`${hooks.length} variants -> ${out}/ (manifest.json)`);
