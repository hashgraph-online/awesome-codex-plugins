// Purpose: decode the PNG variants in the phase 0 sample into canonical RGBA pixels.
// Input: PNG bytes; output: dimensions, RGBA pixels, and a dimension-aware pixel SHA-256.

import { createHash } from "node:crypto";
import { inflateSync } from "node:zlib";

export type DecodedPng = {
  width: number;
  height: number;
  pixels: Buffer;
  pixelSha256: string;
};

const PNG_SIGNATURE = Buffer.from("89504e470d0a1a0a", "hex");

function paeth(left: number, above: number, upperLeft: number): number {
  const predicted = left + above - upperLeft;
  const leftDistance = Math.abs(predicted - left);
  const aboveDistance = Math.abs(predicted - above);
  const upperLeftDistance = Math.abs(predicted - upperLeft);
  if (leftDistance <= aboveDistance && leftDistance <= upperLeftDistance) return left;
  if (aboveDistance <= upperLeftDistance) return above;
  return upperLeft;
}

export function decodePng(bytes: Buffer): DecodedPng {
  if (bytes.length < 33 || !bytes.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error("invalid PNG signature");
  }

  let offset = 8;
  let width = 0;
  let height = 0;
  let channels = 0;
  const imageData: Buffer[] = [];
  while (offset + 12 <= bytes.length) {
    const length = bytes.readUInt32BE(offset);
    const end = offset + 12 + length;
    if (end > bytes.length) throw new Error("truncated PNG chunk");
    const type = bytes.toString("ascii", offset + 4, offset + 8);
    const data = bytes.subarray(offset + 8, offset + 8 + length);
    if (type === "IHDR") {
      if (length !== 13) throw new Error("invalid PNG header");
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      if (data[8] !== 8 || (data[9] !== 2 && data[9] !== 6) || data[12] !== 0) {
        throw new Error(`unsupported PNG encoding: depth=${data[8]}, color=${data[9]}, interlace=${data[12]}`);
      }
      channels = data[9] === 2 ? 3 : 4;
    } else if (type === "IDAT") {
      imageData.push(data);
    } else if (type === "IEND") {
      break;
    }
    offset = end;
  }

  if (!width || !height || !channels || !imageData.length || width * height > 100_000_000) {
    throw new Error("invalid or oversized PNG image");
  }
  const rowBytes = width * channels;
  const inflated = inflateSync(Buffer.concat(imageData));
  if (inflated.length !== height * (rowBytes + 1)) throw new Error("invalid PNG scanline size");

  const pixels = Buffer.allocUnsafe(width * height * 4);
  let previous = Buffer.alloc(rowBytes);
  for (let y = 0; y < height; y++) {
    const rowStart = y * (rowBytes + 1);
    const filter = inflated[rowStart];
    const row = Buffer.allocUnsafe(rowBytes);
    for (let i = 0; i < rowBytes; i++) {
      const left = i >= channels ? row[i - channels] : 0;
      const above = previous[i];
      const upperLeft = i >= channels ? previous[i - channels] : 0;
      let predictor: number;
      switch (filter) {
        case 0: predictor = 0; break;
        case 1: predictor = left; break;
        case 2: predictor = above; break;
        case 3: predictor = Math.floor((left + above) / 2); break;
        case 4: predictor = paeth(left, above, upperLeft); break;
        default: throw new Error(`unsupported PNG filter: ${filter}`);
      }
      row[i] = (inflated[rowStart + 1 + i] + predictor) & 0xff;
    }
    for (let x = 0; x < width; x++) {
      const source = x * channels;
      const target = (y * width + x) * 4;
      pixels[target] = row[source];
      pixels[target + 1] = row[source + 1];
      pixels[target + 2] = row[source + 2];
      pixels[target + 3] = channels === 4 ? row[source + 3] : 255;
    }
    previous = row;
  }

  const dimensions = Buffer.alloc(8);
  dimensions.writeUInt32BE(width, 0);
  dimensions.writeUInt32BE(height, 4);
  return {
    width,
    height,
    pixels,
    pixelSha256: createHash("sha256").update(dimensions).update(pixels).digest("hex"),
  };
}
