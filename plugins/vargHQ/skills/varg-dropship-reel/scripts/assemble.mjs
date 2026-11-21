#!/usr/bin/env node
// Cut a reel from an edit list: every shot is trimmed, filled to 1080x1920 at 30 fps (optionally
// punched in), the shots are joined back to back, the voiceover (and an optional quiet music bed)
// is laid under them and the .ass captions are burned in.
//
//   node assemble.mjs edit.json
//
// edit.json:
// {
//   "out": "reel.mp4",
//   "voiceover": "vo.mp3",
//   "captions": "captions.ass",          // optional, from captions.mjs
//   "fontsdir": "fonts",                 // folder with the caption font (Bangers-Regular.ttf)
//   "music": { "file": "bed.mp3", "volume": 0.08 },   // optional; without "voiceover" the music is the soundtrack
//   "overlays": [ { "file": "banner.png", "start": 0, "end": 4.5 } ],   // optional full-frame PNGs with alpha
//                                       // (on-screen text with emoji, a CCTV timestamp), shown under the captions
//   "shots": [
//     { "file": "hook.mp4",   "in": 0,   "dur": 5.6 },
//     { "file": "screen1.mp4","in": 0.2, "dur": 2.4 },
//     { "file": "screen1.mp4","in": 2.6, "dur": 2.2, "zoom": 1.08 },   // punch-in hides a reused clip
//     { "file": "skyline.mp4","in": 0,   "dur": 5.0, "speed": 0.85 }   // <1 slows a shot down
//   ]
// }
// A shot longer than what is left in its file holds the last frame. Runs with node 18+ or bun; needs ffmpeg.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const editPath = process.argv[2];
if (!editPath) {
  console.error("usage: node assemble.mjs edit.json");
  process.exit(1);
}
const base = dirname(resolve(editPath));
const p = (f) => resolve(base, f);
const edit = JSON.parse(readFileSync(editPath, "utf8"));
const W = edit.width ?? 1080, H = edit.height ?? 1920, FPS = edit.fps ?? 30;

const args = ["-y", "-hide_banner", "-loglevel", "error"];
edit.shots.forEach((s) => args.push("-i", p(s.file)));
let next = edit.shots.length;
const voIdx = edit.voiceover ? next++ : -1;
if (edit.voiceover) args.push("-i", p(edit.voiceover));
let musicIdx = -1;
if (edit.music) {
  args.push("-stream_loop", "-1", "-i", p(edit.music.file));
  musicIdx = next++;
}
if (voIdx < 0 && musicIdx < 0) {
  console.error("edit.json needs a voiceover, music, or both");
  process.exit(1);
}
const overlays = edit.overlays ?? [];
const ovIdx = overlays.map((o) => {
  args.push("-loop", "1", "-i", p(o.file));
  return next++;
});

const parts = [];
edit.shots.forEach((s, i) => {
  const speed = s.speed ?? 1;
  const zoom = s.zoom ?? 1;
  const srcDur = s.dur * speed; // seconds of source needed
  const zw = Math.round((W * zoom) / 2) * 2, zh = Math.round((H * zoom) / 2) * 2;
  parts.push(
    `[${i}:v]trim=start=${s.in ?? 0}:duration=${srcDur.toFixed(3)},setpts=(PTS-STARTPTS)/${speed},` +
      `scale=${zw}:${zh}:force_original_aspect_ratio=increase,crop=${W}:${H},fps=${FPS},setsar=1,format=yuv420p,` +
      `tpad=stop_mode=clone:stop_duration=${s.dur},trim=duration=${s.dur},setpts=PTS-STARTPTS[v${i}]`,
  );
});
const total = edit.shots.reduce((a, s) => a + s.dur, 0);
parts.push(`${edit.shots.map((_, i) => `[v${i}]`).join("")}concat=n=${edit.shots.length}:v=1:a=0[cut]`);

// ffmpeg runs inside the edit list's folder, so captions and fonts are plain relative paths
// (absolute paths would need filtergraph escaping).
const rel = (f) => f.replace(/\\/g, "/").replace(/([:,;'\[\]])/g, "\\$1");
// Overlays sit on the cut, under the captions; each is visible from start to end (seconds).
let video = "cut";
overlays.forEach((o, i) => {
  parts.push(`[${ovIdx[i]}:v]scale=${W}:${H},format=rgba[ov${i}]`);
  parts.push(`[${video}][ov${i}]overlay=0:0:enable='between(t,${o.start},${o.end})'[o${i}]`);
  video = `o${i}`;
});
if (edit.captions) {
  const fonts = edit.fontsdir ? `:fontsdir=${rel(edit.fontsdir)}` : "";
  parts.push(`[${video}]subtitles=filename=${rel(edit.captions)}${fonts}[vout]`);
} else {
  parts.push(`[${video}]null[vout]`);
}

if (voIdx < 0) {
  parts.push(`[${musicIdx}:a]volume=${edit.music.volume ?? 1},afade=t=out:st=${Math.max(0, total - 1).toFixed(2)}:d=1,atrim=duration=${total}[aout]`);
} else if (musicIdx >= 0) {
  parts.push(`[${voIdx}:a]apad[vo]`);
  parts.push(`[${musicIdx}:a]volume=${edit.music.volume ?? 0.08}[bed]`);
  parts.push(`[vo][bed]amix=inputs=2:duration=first:normalize=0,atrim=duration=${total}[aout]`);
} else {
  parts.push(`[${voIdx}:a]apad,atrim=duration=${total}[aout]`);
}

args.push(
  "-filter_complex", parts.join(";"),
  "-map", "[vout]", "-map", "[aout]",
  "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
  "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
  "-t", total.toFixed(3),
  p(edit.out ?? "reel.mp4"),
);
// Burning captions needs an ffmpeg built with libass. Homebrew's default `ffmpeg` no longer has it;
// the keg-only `ffmpeg-full` does and is picked up automatically. FFMPEG=/path/to/ffmpeg overrides.
const hasSubtitles = (bin) =>
  spawnSync(bin, ["-hide_banner", "-filters"], { encoding: "utf8" }).stdout?.includes(" subtitles ");
let ffmpeg = process.env.FFMPEG ?? "ffmpeg";
if (edit.captions && !process.env.FFMPEG && !hasSubtitles(ffmpeg)) {
  const full = ["/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/usr/local/opt/ffmpeg-full/bin/ffmpeg"].find(hasSubtitles);
  if (!full) {
    console.error("This ffmpeg can't burn captions (no libass). macOS: `brew install ffmpeg-full`. Linux: install your distro's ffmpeg. Or set FFMPEG=/path/to/ffmpeg.");
    process.exit(1);
  }
  ffmpeg = full;
}
const r = spawnSync(ffmpeg, args, { stdio: "inherit", cwd: base });
if (r.status !== 0) process.exit(r.status ?? 1);
console.error(`${edit.shots.length} shots, ${total.toFixed(2)} s -> ${edit.out ?? "reel.mp4"}`);
