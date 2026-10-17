#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

function usage() {
  console.error([
    'Usage: node visual-diff.mjs --expected source.png --actual actual.png --out diff.json',
    'Options: --diff diff.png --threshold 0.1',
  ].join('\n'));
}

function parseArgs(argv) {
  const args = { threshold: 0.1, diff: null };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith('--')) throw new Error(`Unknown argument: ${key}`);
    args[key.slice(2)] = argv[++i];
  }
  for (const required of ['expected', 'actual', 'out']) {
    if (!args[required]) {
      usage();
      process.exit(2);
    }
  }
  args.threshold = Number(args.threshold);
  if (!Number.isFinite(args.threshold)) throw new Error('--threshold must be a number.');
  return args;
}

function requireFromCandidates(packageName) {
  const require = createRequire(import.meta.url);
  const bundledNodeModules = process.env.HOME
    ? path.join(process.env.HOME, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    : null;
  const candidates = [
    null,
    process.env.CODEX_NODE_MODULES,
    bundledNodeModules,
  ];
  const failures = [];
  for (const modulesDir of candidates) {
    try {
      return modulesDir ? require(path.join(modulesDir, packageName)) : require(packageName);
    } catch (error) {
      failures.push(error.message);
    }
  }
  throw new Error(`Cannot load ${packageName}. Install it in the target project or set CODEX_NODE_MODULES. Last error: ${failures.at(-1)}`);
}

async function importFromCandidates(packageName) {
  const bundledNodeModules = process.env.HOME
    ? path.join(process.env.HOME, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    : null;
  const candidates = [
    packageName,
    process.env.CODEX_NODE_MODULES && path.join(process.env.CODEX_NODE_MODULES, packageName, 'index.js'),
    bundledNodeModules && path.join(bundledNodeModules, packageName, 'index.js'),
  ].filter(Boolean);
  const failures = [];
  for (const specifier of candidates) {
    try {
      const resolved = specifier.startsWith('/') ? `file://${specifier}` : specifier;
      return await import(resolved);
    } catch (error) {
      failures.push(error.message);
    }
  }
  throw new Error(`Cannot import ${packageName}. Install it in the target project or set CODEX_NODE_MODULES. Last error: ${failures.at(-1)}`);
}

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(path.resolve(filePath)), { recursive: true });
}

async function imageToRaw(sharp, filePath, width, height) {
  const image = sharp(filePath).ensureAlpha();
  const metadata = await image.metadata();
  const canvasWidth = width ?? metadata.width;
  const canvasHeight = height ?? metadata.height;
  if (!canvasWidth || !canvasHeight) {
    throw new Error(`Cannot determine dimensions for ${filePath}`);
  }
  const buffer = await image
    .extend({
      top: 0,
      bottom: Math.max(0, canvasHeight - metadata.height),
      left: 0,
      right: Math.max(0, canvasWidth - metadata.width),
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    })
    .extract({ left: 0, top: 0, width: canvasWidth, height: canvasHeight })
    .raw()
    .toBuffer();
  return {
    width: metadata.width,
    height: metadata.height,
    canvasWidth,
    canvasHeight,
    buffer,
  };
}

const args = parseArgs(process.argv.slice(2));
const sharp = requireFromCandidates('sharp');
const pixelmatchModule = await importFromCandidates('pixelmatch');
const pixelmatch = pixelmatchModule.default ?? pixelmatchModule;

const expectedMetadata = await sharp(args.expected).metadata();
const actualMetadata = await sharp(args.actual).metadata();
const canvasWidth = Math.max(expectedMetadata.width ?? 0, actualMetadata.width ?? 0);
const canvasHeight = Math.max(expectedMetadata.height ?? 0, actualMetadata.height ?? 0);
if (!canvasWidth || !canvasHeight) {
  throw new Error('Cannot compare images with missing dimensions.');
}

const expected = await imageToRaw(sharp, args.expected, canvasWidth, canvasHeight);
const actual = await imageToRaw(sharp, args.actual, canvasWidth, canvasHeight);
const diffBuffer = Buffer.alloc(canvasWidth * canvasHeight * 4);

const mismatchPixels = pixelmatch(
  expected.buffer,
  actual.buffer,
  diffBuffer,
  canvasWidth,
  canvasHeight,
  { threshold: args.threshold },
);

let totalDelta = 0;
let maxDelta = 0;
for (let i = 0; i < expected.buffer.length; i += 4) {
  const delta =
    Math.abs(expected.buffer[i] - actual.buffer[i]) +
    Math.abs(expected.buffer[i + 1] - actual.buffer[i + 1]) +
    Math.abs(expected.buffer[i + 2] - actual.buffer[i + 2]) +
    Math.abs(expected.buffer[i + 3] - actual.buffer[i + 3]);
  totalDelta += delta;
  maxDelta = Math.max(maxDelta, delta);
}

const totalPixels = canvasWidth * canvasHeight;
const report = {
  expected: { width: expected.width, height: expected.height },
  actual: { width: actual.width, height: actual.height },
  canvas: { width: canvasWidth, height: canvasHeight },
  threshold: args.threshold,
  mismatchPixels,
  totalPixels,
  mismatchRatio: totalPixels === 0 ? 0 : mismatchPixels / totalPixels,
  averageDelta: totalPixels === 0 ? 0 : totalDelta / totalPixels,
  maxDelta,
};

ensureDir(args.out);
fs.writeFileSync(args.out, `${JSON.stringify(report, null, 2)}\n`);

if (args.diff) {
  ensureDir(args.diff);
  await sharp(diffBuffer, {
    raw: { width: canvasWidth, height: canvasHeight, channels: 4 },
  })
    .png()
    .toFile(args.diff);
}

process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
