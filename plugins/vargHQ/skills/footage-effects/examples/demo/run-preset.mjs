#!/usr/bin/env node
// Apply one footage-effects preset to a clip with ffmpeg, exactly as the preset JSON says.
//   node run-preset.mjs <clip.mp4> <template> <variant> <out.mp4> [seconds]
//   node run-preset.mjs c1.mp4 glow-bloom film-halation fx1.mp4 3.6
// The clip should be 1920x1080 at 30 fps (the presets' pixel values assume 1080p).
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const [clip, template, variant, out, seconds = "4"] = process.argv.slice(2);
if (!clip || !template || !variant || !out) {
  console.error("usage: node run-preset.mjs <clip> <template> <variant> <out.mp4> [seconds]");
  process.exit(2);
}
const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const file = JSON.parse(readFileSync(join(root, "assets", "presets", `${template}.json`), "utf8"));
const preset = file.presets.find((p) => p.id === `${template}.${variant}`);
if (!preset) {
  console.error(`no preset ${template}.${variant}; have: ${file.presets.map((p) => p.id).join(", ")}`);
  process.exit(2);
}
const ff = preset.params.ffmpeg;
const args = ["-v", "error", "-y", "-i", clip];
for (const input of ff.inputs) {
  const prefix = "-f lavfi -i ";
  if (!input.startsWith(prefix)) throw new Error(`unexpected input: ${input}`);
  args.push("-f", "lavfi", "-i", input.slice(prefix.length));
}
// Generated inputs never end: -t caps the output (see the skill's gates).
args.push("-filter_complex", ff.filter_complex, "-map", "[v]", "-t", seconds, "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "14", out);
const r = spawnSync("ffmpeg", args, { stdio: "inherit" });
process.exit(r.status ?? 1);
