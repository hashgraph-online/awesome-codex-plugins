#!/usr/bin/env node
// Dependency-free PNG visual diff for the Superloopy frontend visual-QA gate.
// Turns "does it look right?" into measured evidence: a per-pixel diffRatio, a
// similarityScore, an alpha-intact flag, and an 8x8 grid of ranked hotspots that
// localize WHERE a render deviates from its reference. The JSON is evidence to AIM
// a review, never the verdict (a 99/100 score can still hide a faked or broken UI).
//
// Uses only node:zlib + node:fs so the loop can run in any sandbox with no install.
// Supports 8-bit non-interlaced PNGs, color types 0/2/4/6 (the shapes headless
// browsers and Playwright emit). Exports decode/diff/encode for tests; runs as a CLI.
//
// CLI:  node visual-diff.mjs <reference.png> <actual.png> [--json] [--tolerance N]

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { deflateSync, inflateSync } from "node:zlib";

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const GRID_SIZE = 8;
const MAX_PIXELS = 25_000_000;
const MAX_INFLATED_BYTES = 128 * 1024 * 1024;

const CRC_TABLE = (() => {
  const table = new Int32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c;
  }
  return table;
})();

function crc32(buffer) {
  let crc = 0xffffffff;
  for (let i = 0; i < buffer.length; i += 1) crc = CRC_TABLE[(crc ^ buffer[i]) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  return pb <= pc ? b : c;
}

const CHANNELS_BY_COLOR_TYPE = { 0: 1, 2: 3, 4: 2, 6: 4 };

// Decode an 8-bit non-interlaced PNG buffer to { width, height, rgba, hasTransparentPixels }.
export function decodePng(buffer) {
  if (buffer.length < 8 || !buffer.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error("Not a PNG file (bad signature).");
  }
  let offset = 8;
  let width = 0;
  let height = 0;
  let bitDepth = 0;
  let colorType = 0;
  let interlace = 0;
  const idat = [];
  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    const data = buffer.subarray(offset + 8, offset + 8 + length);
    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      interlace = data[12];
    } else if (type === "IDAT") {
      idat.push(Buffer.from(data));
    } else if (type === "IEND") {
      break;
    }
    offset += 12 + length;
  }
  if (bitDepth !== 8) throw new Error(`Unsupported PNG bit depth ${bitDepth} (need 8).`);
  if (interlace !== 0) throw new Error("Interlaced PNG is unsupported.");
  const channels = CHANNELS_BY_COLOR_TYPE[colorType];
  if (channels === undefined) throw new Error(`Unsupported PNG color type ${colorType}.`);
  if (width <= 0 || height <= 0) throw new Error("PNG dimensions must be positive.");
  const pixelsCount = width * height;
  const inflatedBytes = height * (width * channels + 1);
  if (!Number.isSafeInteger(pixelsCount) || pixelsCount > MAX_PIXELS || inflatedBytes > MAX_INFLATED_BYTES) {
    throw new Error(`PNG dimensions exceed safe decode limits (${width}x${height}).`);
  }

  const raw = inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  if (raw.length < inflatedBytes) throw new Error("PNG image data is truncated.");
  if (raw.length > MAX_INFLATED_BYTES) throw new Error("PNG image data exceeds safe decode limits.");
  const pixels = Buffer.alloc(height * stride);
  let prevRow = Buffer.alloc(stride);
  let src = 0;
  for (let y = 0; y < height; y += 1) {
    const filter = raw[src];
    src += 1;
    const row = pixels.subarray(y * stride, y * stride + stride);
    for (let i = 0; i < stride; i += 1) {
      const x = raw[src + i];
      const a = i >= channels ? row[i - channels] : 0;
      const b = prevRow[i];
      const c = i >= channels ? prevRow[i - channels] : 0;
      let value;
      if (filter === 0) value = x;
      else if (filter === 1) value = x + a;
      else if (filter === 2) value = x + b;
      else if (filter === 3) value = x + ((a + b) >> 1);
      else if (filter === 4) value = x + paeth(a, b, c);
      else throw new Error(`Unsupported PNG filter ${filter}.`);
      row[i] = value & 0xff;
    }
    src += stride;
    prevRow = row;
  }

  const rgba = new Uint8ClampedArray(width * height * 4);
  let hasTransparentPixels = false;
  for (let p = 0; p < width * height; p += 1) {
    const s = p * channels;
    let r;
    let g;
    let b;
    let a = 255;
    if (colorType === 0) { r = g = b = pixels[s]; }
    else if (colorType === 4) { r = g = b = pixels[s]; a = pixels[s + 1]; }
    else if (colorType === 2) { r = pixels[s]; g = pixels[s + 1]; b = pixels[s + 2]; }
    else { r = pixels[s]; g = pixels[s + 1]; b = pixels[s + 2]; a = pixels[s + 3]; }
    if (a < 255) hasTransparentPixels = true;
    const d = p * 4;
    rgba[d] = r; rgba[d + 1] = g; rgba[d + 2] = b; rgba[d + 3] = a;
  }
  return { width, height, rgba, hasTransparentPixels };
}

// Encode RGBA (Uint8/Array, length w*h*4) to a color-type-6 PNG buffer. Used by tests
// to synthesize fixtures so the diff can self-verify with no external image files.
export function encodePng(width, height, rgba) {
  const channels = 4;
  const stride = width * channels;
  const raw = Buffer.alloc(height * (stride + 1));
  for (let y = 0; y < height; y += 1) {
    raw[y * (stride + 1)] = 0; // filter: none
    for (let i = 0; i < stride; i += 1) raw[y * (stride + 1) + 1 + i] = rgba[y * stride + i] & 0xff;
  }
  const chunk = (type, data) => {
    const out = Buffer.alloc(12 + data.length);
    out.writeUInt32BE(data.length, 0);
    out.write(type, 4, "ascii");
    data.copy(out, 8);
    out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length);
    return out;
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([PNG_SIGNATURE, chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}

// Compare two decoded images. Returns measured fields + ranked grid hotspots.
export function diffImages(reference, actual, tolerance = 0) {
  const width = Math.min(reference.width, actual.width);
  const height = Math.min(reference.height, actual.height);
  const dimensionsMatch = reference.width === actual.width && reference.height === actual.height;
  const grid = Array.from({ length: GRID_SIZE * GRID_SIZE }, () => ({ diff: 0, total: 0 }));
  let diffPixels = 0;
  for (let y = 0; y < height; y += 1) {
    const gy = Math.min(GRID_SIZE - 1, Math.floor((y / height) * GRID_SIZE));
    for (let x = 0; x < width; x += 1) {
      const gx = Math.min(GRID_SIZE - 1, Math.floor((x / width) * GRID_SIZE));
      const cell = grid[gy * GRID_SIZE + gx];
      cell.total += 1;
      const ri = (y * reference.width + x) * 4;
      const ai = (y * actual.width + x) * 4;
      const differs =
        Math.abs(reference.rgba[ri] - actual.rgba[ai]) > tolerance ||
        Math.abs(reference.rgba[ri + 1] - actual.rgba[ai + 1]) > tolerance ||
        Math.abs(reference.rgba[ri + 2] - actual.rgba[ai + 2]) > tolerance ||
        Math.abs(reference.rgba[ri + 3] - actual.rgba[ai + 3]) > tolerance;
      if (differs) { diffPixels += 1; cell.diff += 1; }
    }
  }
  const total = width * height;
  const diffRatio = total === 0 ? 1 : diffPixels / total;
  const hotspots = [];
  for (let gy = 0; gy < GRID_SIZE; gy += 1) {
    for (let gx = 0; gx < GRID_SIZE; gx += 1) {
      const cell = grid[gy * GRID_SIZE + gx];
      if (cell.diff === 0 || cell.total === 0) continue;
      hotspots.push({
        gridX: gx,
        gridY: gy,
        x: Math.floor((gx / GRID_SIZE) * width),
        y: Math.floor((gy / GRID_SIZE) * height),
        width: Math.ceil(width / GRID_SIZE),
        height: Math.ceil(height / GRID_SIZE),
        diffRatio: cell.diff / cell.total
      });
    }
  }
  hotspots.sort((a, b) => b.diffRatio - a.diffRatio);
  return {
    dimensionsMatch,
    width,
    height,
    diffPixels,
    diffRatio,
    similarityScore: Math.round((1 - diffRatio) * 100),
    alphaChannelIntact: !(reference.hasTransparentPixels && !actual.hasTransparentPixels),
    hotspots
  };
}

export function diffPngFiles(referencePath, actualPath, tolerance = 0) {
  return diffImages(decodePng(readFileSync(referencePath)), decodePng(readFileSync(actualPath)), tolerance);
}

function main(argv) {
  const args = argv.filter((a) => a !== "--json");
  const tolFlag = args.indexOf("--tolerance");
  let tolerance = 0;
  if (tolFlag !== -1) { tolerance = Number.parseInt(args[tolFlag + 1], 10) || 0; args.splice(tolFlag, 2); }
  const [reference, actual] = args;
  if (!reference || !actual) {
    process.stderr.write("usage: visual-diff.mjs <reference.png> <actual.png> [--json] [--tolerance N]\n");
    process.exit(2);
  }
  const result = diffPngFiles(reference, actual, tolerance);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

// pathToFileURL (not `file://${argv[1]}`): on Windows argv[1] is `C:\...` while
// import.meta.url is `file:///C:/...`, so the string compare never matched and the
// gate silently exited 0 — a passing evidence artifact for an unchecked render.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  }
}
