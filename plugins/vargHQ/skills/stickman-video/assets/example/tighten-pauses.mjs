// Shorten every pause in a voiceover to KEEP seconds. Speech itself is never time-stretched.
// usage: bun tighten-pauses.mjs in.mp3 out.wav [keepSeconds=0.2] [minPause=0.25]
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

const [inp, outp, keepArg = "0.2", minArg = "0.25"] = process.argv.slice(2);
const KEEP = +keepArg, MIN = +minArg;
mkdirSync(dirname(outp), { recursive: true });
const sh = (cmd) => execFileSync("sh", ["-c", cmd]).toString();
const log = sh(`ffmpeg -hide_banner -i "${inp}" -af silencedetect=noise=-35dB:d=${MIN} -f null - 2>&1`);
const starts = [...log.matchAll(/silence_start: ([\d.]+)/g)].map((m) => +m[1]);
const ends = [...log.matchAll(/silence_end: ([\d.]+)/g)].map((m) => +m[1]);
const dur = +sh(`ffprobe -v error -show_entries format=duration -of csv=p=0 "${inp}"`).trim();

const segs = [];
let cur = 0;
starts.forEach((s, i) => {
  const e = ends[i] ?? dur;
  if (e - s <= KEEP) return;
  segs.push([cur, s + KEEP / 2]);
  cur = e - KEEP / 2;
});
segs.push([cur, dur]);
const parts = segs.map(([a, b], i) =>
  `[0:a]atrim=${a.toFixed(3)}:${b.toFixed(3)},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st=${(b - a - 0.012).toFixed(3)}:d=0.012[s${i}]`);
const filter = parts.join(";") + ";" + segs.map((_, i) => `[s${i}]`).join("") + `concat=n=${segs.length}:v=0:a=1[o]`;
execFileSync("ffmpeg", ["-hide_banner", "-y", "-loglevel", "error", "-i", inp, "-filter_complex", filter, "-map", "[o]", "-ar", "48000", "-ac", "1", outp], { stdio: "inherit" });
const total = segs.reduce((acc, [a, b]) => acc + (b - a), 0);
console.log(`${segs.length} segments, ${dur.toFixed(2)} s -> ${total.toFixed(2)} s`);
