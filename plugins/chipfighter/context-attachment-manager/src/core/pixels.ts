// Purpose: v0.1-11 — pixel fingerprints of PNG images, so the same picture saved with different bytes counts as the same
// content (v0.11: moved here from thread-index.ts, docs/v0.11/plan.md). The engine and the plugin services (Codex
// starts one per task) share them through a folder in the data directory, so a new process does not decode every PNG
// again. Only fingerprints are stored, never image content. Unset: memory only (tests). "-" marks a PNG our decoder
// cannot read.
// Input: an image's digest and base64. Output: the sha256 of its decoded pixels, or null.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { ImageDigest } from "./images.ts";
import { decodePng } from "./png.ts";

const pixelHashes = new Map<string, string | null>();
let pixelCacheDir: string | null = null;
export function setPixelCache(dir: string | null): void { pixelCacheDir = dir; }
const SHA256 = /^[0-9a-f]{64}$/;

function storedPixelHash(contentId: string): string | null | undefined {
  if (!pixelCacheDir || !SHA256.test(contentId)) return undefined;
  try {
    const text = readFileSync(join(pixelCacheDir, contentId.slice(0, 2), contentId), "utf8").trim();
    return text === "-" ? null : SHA256.test(text) ? text : undefined;
  } catch { return undefined; }
}

function storePixelHash(contentId: string, hash: string | null): void {
  if (!pixelCacheDir || !SHA256.test(contentId)) return;
  try {
    const folder = join(pixelCacheDir, contentId.slice(0, 2));
    mkdirSync(folder, { recursive: true });
    writeFileSync(join(folder, contentId), hash ?? "-", { flag: "wx" });
  } catch { /* best effort; another process may have written it first */ }
}

export function pixelHashOfData(ref: Pick<ImageDigest, "contentId" | "mime">, value: string): string | null {
  if (ref.mime !== "image/png") return null;
  if (!pixelHashes.has(ref.contentId)) {
    let hash = storedPixelHash(ref.contentId);
    if (hash === undefined) {
      try { hash = decodePng(Buffer.from(value, "base64")).pixelSha256; } catch { hash = null; }
      storePixelHash(ref.contentId, hash);
    }
    pixelHashes.set(ref.contentId, hash);
  }
  return pixelHashes.get(ref.contentId) ?? null;
}
