#!/usr/bin/env node
// Prove a HyperFrames project draws the same pixels for the same time in any capture
// order: snapshot the times forwards, then backwards, in two separate browser runs,
// and compare the decoded pixels. Needs npx and ffmpeg (HyperFrames needs both anyway).
//
//   node scripts/check-determinism.mjs ./my-video
//   node scripts/check-determinism.mjs ./my-video --at 0.5,2,4.25
//   node scripts/check-determinism.mjs ./my-video --software   # SwiftShader instead of the GPU
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const HYPERFRAMES = "hyperframes@0.8.206";
const args = process.argv.slice(2);
const atIndex = args.indexOf("--at");
const dir = resolve(args.find((a, i) => !a.startsWith("--") && (atIndex < 0 || i !== atIndex + 1)) ?? ".");
const software = args.includes("--software");
const times = atIndex >= 0 ? args[atIndex + 1].split(",").map(Number) : defaultTimes();
if (times.some((t) => !Number.isFinite(t) || t < 0)) fail("--at takes comma-separated seconds, e.g. --at 0.5,2,4.25");

const work = mkdtempSync(join(tmpdir(), "paper-determinism-"));
try {
  const forward = snapshot(times, join(work, "forward"));
  const backward = snapshot([...times].reverse(), join(work, "backward"));
  let differ = 0;
  for (const t of times) {
    const a = pixels(forward, t);
    const b = pixels(backward, t);
    if (a !== b) differ++;
    console.log(`${a === b ? "same" : "DIFFERENT"}  t=${t}s  ${a}${a === b ? "" : ` vs ${b}`}`);
  }
  console.log(differ ? `${differ} of ${times.length} frames differ: something reads a clock, a random number or a late load` : `deterministic: ${times.length} frames identical across runs and orders`);
  process.exitCode = differ ? 1 : 0;
} finally {
  rmSync(work, { recursive: true, force: true });
}

function defaultTimes() {
  const html = readFileSync(join(dir, "index.html"), "utf8");
  const rootTag = html.match(/<[^>]*data-composition-id=[^>]*>/)?.[0] ?? "";
  const duration = Number(rootTag.match(/data-duration="([\d.]+)"/)?.[1]);
  if (!duration) fail("could not read the root data-duration; pass --at");
  return [0.2, 0.5, 0.8].map((k) => Number((k * duration).toFixed(2)));
}

function snapshot(at, out) {
  const run = spawnSync(
    "npx",
    ["--yes", HYPERFRAMES, "snapshot", dir, "--at", at.join(","), "--no-end", "-o", out, ...(software ? ["--no-browser-gpu"] : [])],
    { encoding: "utf8" },
  );
  if (run.status !== 0) fail(`hyperframes snapshot failed:\n${run.stdout}\n${run.stderr}`);
  return out;
}

function pixels(folder, t) {
  const file = readdirSync(folder).find((f) => f.endsWith(`-at-${t}s.png`));
  if (!file) fail(`no snapshot for t=${t}s in ${folder}`);
  const run = spawnSync("ffmpeg", ["-v", "error", "-i", join(folder, file), "-pix_fmt", "rgb24", "-f", "md5", "-"], { encoding: "utf8" });
  if (run.status !== 0) fail(`ffmpeg failed: ${run.stderr}`);
  return run.stdout.trim();
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
