// Purpose: P3-3 — scaled-down PNGs for the panel, made from the inline images in the rollout. Only PNG is decoded;
// other formats go to the panel as they are and the browser scales them.
// Input: base64 image data and a maximum side length. Output: a PNG data URL, cached per content and size.

import { createHash } from "node:crypto";
import zlib from "node:zlib";
import { decodePng } from "./png.ts";

const cache = new Map<string, string | null>();

// Box filter: every target pixel is the average of the source block it covers.
export function shrink(width: number, height: number, rgba: Buffer, maxSide: number): { width: number; height: number; pixels: Buffer } {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  const tw = Math.max(1, Math.round(width * scale));
  const th = Math.max(1, Math.round(height * scale));
  const out = Buffer.alloc(tw * th * 4);
  for (let ty = 0; ty < th; ty++) {
    const y0 = Math.floor((ty * height) / th);
    const y1 = Math.max(y0 + 1, Math.floor(((ty + 1) * height) / th));
    for (let tx = 0; tx < tw; tx++) {
      const x0 = Math.floor((tx * width) / tw);
      const x1 = Math.max(x0 + 1, Math.floor(((tx + 1) * width) / tw));
      const sum = [0, 0, 0, 0];
      for (let y = y0; y < y1; y++) {
        for (let x = x0; x < x1; x++) {
          const source = (y * width + x) * 4;
          for (let c = 0; c < 4; c++) sum[c] += rgba[source + c];
        }
      }
      const count = (y1 - y0) * (x1 - x0);
      for (let c = 0; c < 4; c++) out[(ty * tw + tx) * 4 + c] = Math.round(sum[c] / count);
    }
  }
  return { width: tw, height: th, pixels: out };
}

export function encodePngRgba(width: number, height: number, rgba: Buffer): Buffer {
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) rgba.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  const chunk = (type: string, data: Buffer) => {
    const length = Buffer.alloc(4);
    length.writeUInt32BE(data.length);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(zlib.crc32(Buffer.concat([Buffer.from(type, "ascii"), data])));
    return Buffer.concat([length, Buffer.from(type, "ascii"), data, crc]);
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 6;
  return Buffer.concat([Buffer.from("89504e470d0a1a0a", "hex"), chunk("IHDR", header), chunk("IDAT", zlib.deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}

export function pngThumbnail(base64: string, maxSide = 96): string | null {
  const key = `${createHash("sha256").update(base64).digest("hex")}:${maxSide}`;
  if (cache.has(key)) return cache.get(key)!;
  let result: string | null = null;
  try {
    const png = decodePng(Buffer.from(base64, "base64"));
    const small = shrink(png.width, png.height, png.pixels, maxSide);
    result = `data:image/png;base64,${encodePngRgba(small.width, small.height, small.pixels).toString("base64")}`;
  } catch {
    result = null;
  }
  cache.set(key, result);
  return result;
}
