#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function usage() {
  console.error('Usage: node image-metadata.mjs <image-path> [--out metadata.json]');
}

function parseArgs(argv) {
  const args = { image: null, out: null };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === '--out') {
      args.out = argv[++i];
    } else if (!args.image) {
      args.image = value;
    } else {
      throw new Error(`Unknown argument: ${value}`);
    }
  }
  if (!args.image) {
    usage();
    process.exit(2);
  }
  return args;
}

function readPng(buffer) {
  if (buffer.length < 24) return null;
  const signature = '89504e470d0a1a0a';
  if (buffer.subarray(0, 8).toString('hex') !== signature) return null;
  return {
    format: 'png',
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}

function readGif(buffer) {
  if (buffer.length < 10) return null;
  const header = buffer.subarray(0, 6).toString('ascii');
  if (header !== 'GIF87a' && header !== 'GIF89a') return null;
  return {
    format: 'gif',
    width: buffer.readUInt16LE(6),
    height: buffer.readUInt16LE(8),
  };
}

function readJpeg(buffer) {
  if (buffer.length < 4 || buffer[0] !== 0xff || buffer[1] !== 0xd8) return null;
  let offset = 2;
  const sofMarkers = new Set([
    0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf,
  ]);
  while (offset < buffer.length) {
    while (offset < buffer.length && buffer[offset] !== 0xff) offset += 1;
    while (offset < buffer.length && buffer[offset] === 0xff) offset += 1;
    if (offset >= buffer.length) break;
    const marker = buffer[offset];
    offset += 1;
    if (marker === 0xd9 || marker === 0xda) break;
    if (offset + 2 > buffer.length) break;
    const length = buffer.readUInt16BE(offset);
    if (length < 2 || offset + length > buffer.length) break;
    if (sofMarkers.has(marker)) {
      return {
        format: 'jpeg',
        width: buffer.readUInt16BE(offset + 6),
        height: buffer.readUInt16BE(offset + 4),
      };
    }
    offset += length;
  }
  return null;
}

function readWebp(buffer) {
  if (buffer.length < 30) return null;
  if (buffer.subarray(0, 4).toString('ascii') !== 'RIFF') return null;
  if (buffer.subarray(8, 12).toString('ascii') !== 'WEBP') return null;
  const chunk = buffer.subarray(12, 16).toString('ascii');
  if (chunk === 'VP8X' && buffer.length >= 30) {
    return {
      format: 'webp',
      width: 1 + buffer.readUIntLE(24, 3),
      height: 1 + buffer.readUIntLE(27, 3),
    };
  }
  if (chunk === 'VP8L' && buffer.length >= 25) {
    const b0 = buffer[21];
    const b1 = buffer[22];
    const b2 = buffer[23];
    const b3 = buffer[24];
    return {
      format: 'webp',
      width: 1 + (((b1 & 0x3f) << 8) | b0),
      height: 1 + (((b3 & 0x0f) << 10) | (b2 << 2) | ((b1 & 0xc0) >> 6)),
    };
  }
  if (chunk === 'VP8 ' && buffer.length >= 30) {
    const start = 20;
    const keyFrame = buffer.subarray(start + 3, start + 6).toString('hex') === '9d012a';
    if (keyFrame) {
      return {
        format: 'webp',
        width: buffer.readUInt16LE(start + 6) & 0x3fff,
        height: buffer.readUInt16LE(start + 8) & 0x3fff,
      };
    }
  }
  return null;
}

function readImageMetadata(filePath) {
  const buffer = fs.readFileSync(filePath);
  const parsed = readPng(buffer) || readJpeg(buffer) || readGif(buffer) || readWebp(buffer);
  if (!parsed) {
    throw new Error('Unsupported image format. Supported: png, jpeg, gif, webp.');
  }
  const absolutePath = path.resolve(filePath);
  return {
    path: absolutePath,
    fileName: path.basename(filePath),
    format: parsed.format,
    width: parsed.width,
    height: parsed.height,
    designSize: `${parsed.width}x${parsed.height}`,
    designSizeSource: 'inferred-from-image-pixels',
  };
}

const args = parseArgs(process.argv.slice(2));
const metadata = readImageMetadata(args.image);
const output = `${JSON.stringify(metadata, null, 2)}\n`;
if (args.out) {
  fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
  fs.writeFileSync(args.out, output);
} else {
  process.stdout.write(output);
}
