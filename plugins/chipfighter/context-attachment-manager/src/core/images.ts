// Purpose: what the core knows of an image whatever the platform (v0.11: split from images.ts, docs/v0.11/plan.md):
// its kind and source, a content digest (sha256 of its base64, size from the header), the state our fetch tool writes
// before each image it returns, and a file's base name. Finding images in a request is the request format's business
// (adapters/protocols).
// Input: base64 image data. Output: digests and sizes (pure, no I/O).

import { createHash } from "node:crypto";

export type ImageKind = "upload" | "view" | "generated" | "tool";
// v0.2 — the source the panel filters by: the kind, except for the screenshots Codex desktop attaches to a comment on a
// PDF page or a web page.
export type ImageSource = ImageKind | "pdf" | "browser";
export type ImageDigest = { contentId: string; mime: string | null; base64Chars: number; width: number | null; height: number | null };

// v0.3 — the state our fetch tool (cam_view_image) writes in the line before each image it returns, in either
// language, so the image is known as a copy of that id. The rest of the line is the usual heading (words.ts).
export const FETCHED_STATE = { zh: "取回的原图", en: "fetched original" } as const;
const FETCHED_LINE = new RegExp(`^\\[(?:图片|Image) (IMG-\\d{3,}) (?:${FETCHED_STATE.zh}|${FETCHED_STATE.en})(?:｜| \\|)`);
// The id our fetch tool's line names, when `text` is one.
export const fetchedIdIn = (text: string): string | null => FETCHED_LINE.exec(text)?.[1] ?? null;

export function baseName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

// Width and height from the image header only, so large images are not decoded.
export function imageSize(bytes: Buffer): { width: number; height: number } | null {
  if (bytes.length >= 24 && bytes.readUInt32BE(0) === 0x89504e47) return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
  if (bytes.length >= 10 && bytes.toString("ascii", 0, 3) === "GIF") return { width: bytes.readUInt16LE(6), height: bytes.readUInt16LE(8) };
  if (bytes.length >= 30 && bytes.toString("ascii", 0, 4) === "RIFF" && bytes.toString("ascii", 8, 12) === "WEBP") {
    const chunk = bytes.toString("ascii", 12, 16);
    if (chunk === "VP8X") return { width: bytes.readUIntLE(24, 3) + 1, height: bytes.readUIntLE(27, 3) + 1 };
    if (chunk === "VP8 ") return { width: bytes.readUInt16LE(26) & 0x3fff, height: bytes.readUInt16LE(28) & 0x3fff };
    if (chunk === "VP8L") { const bits = bytes.readUInt32LE(21); return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 }; }
    return null;
  }
  if (bytes.length >= 4 && bytes[0] === 0xff && bytes[1] === 0xd8) {
    let offset = 2;
    while (offset + 9 < bytes.length) {
      if (bytes[offset] !== 0xff) return null;
      const marker = bytes[offset + 1];
      if (marker === 0xff) { offset++; continue; }
      const length = bytes.readUInt16BE(offset + 2);
      // SOF0–SOF15 carry the frame size, except DHT (C4), JPG (C8) and DAC (CC).
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) return { width: bytes.readUInt16BE(offset + 7), height: bytes.readUInt16BE(offset + 5) };
      offset += 2 + length;
    }
  }
  return null;
}

const digests = new WeakMap<object, ImageDigest>();

// Keyed by the object holding the image (a request part, a record's block), so re-reading the same cached records does
// not hash the same images again. `value` is raw base64, not a data URL.
export function imageDigest(owner: object, value: string, mime: string | null): ImageDigest {
  const known = digests.get(owner);
  if (known) return known;
  const header = Buffer.from(value.slice(0, 96 * 1024), "base64");
  const size = imageSize(header);
  const result = { contentId: createHash("sha256").update(value).digest("hex"), mime, base64Chars: value.length, width: size?.width ?? null, height: size?.height ?? null };
  digests.set(owner, result);
  return result;
}
