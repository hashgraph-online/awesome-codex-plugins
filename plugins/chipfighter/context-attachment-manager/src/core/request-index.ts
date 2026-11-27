// Purpose: v0.11 — what the core keeps of a session on a platform that shows no panel (docs/v0.11/plan.md 3.8): an id
// for each image its requests carried, in the order they first appeared, and the image itself, so the model can fetch
// it back by id (cam_view_image). The platform's own records are never read: everything comes from its requests, which
// send their conversation in requests. Keep the only retrievable copy for as long as its index exists. Ids go by
// content, so the same picture keeps its id wherever it appears.
// Input/Output: under <data dir>/platforms/<platform>/: sessions/<key>.json, e.g. { "images": { "<content id>":
// { "id": "IMG-001", "mime": "image/png", "turn": 1, "kind": "upload", "width": 640, "height": 480 } } }; images/<content
// id>, the image as it was sent; latest.json, the session whose conversation went out last (the one a fetch is about).

import { randomUUID } from "node:crypto";
import { closeSync, lstatSync, mkdirSync, openSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { CONTENT_DIGEST } from "./disk-cache.ts";
import type { ImageKind } from "./images.ts";
import { PLATFORM_NAME } from "./routes.ts";
import { SESSION_KEY } from "./selection.ts";

export type Seen = { id: string; mime: string | null; turn: number; kind: ImageKind; width: number | null; height: number | null };
export type RequestIndex = { platform: string; key: string; images: Map<string, Seen>; changed: boolean };

export function platformDirOf(root: string, platform: string): string {
  if (!PLATFORM_NAME.test(platform)) throw new Error(`not a platform name: ${platform}`);
  return join(root, "platforms", platform);
}

const sessionFile = (root: string, platform: string, key: string) => {
  if (!SESSION_KEY.test(key)) throw new Error(`not a session key: ${key}`);
  return join(platformDirOf(root, platform), "sessions", `${key}.json`);
};

const writeWhole = (file: string, text: string) => {
  const staged = `${file}.${randomUUID()}.tmp`;
  const fd = openSync(staged, "wx");
  try {
    try { writeFileSync(fd, text); } finally { closeSync(fd); }
    renameSync(staged, file);
  } catch (error) {
    try { unlinkSync(staged); } catch { /* gone */ }
    throw error;
  }
};

const imagesDir = (root: string, platform: string) => join(platformDirOf(root, platform), "images");

export function hasStoredImage(root: string, platform: string, contentId: string): boolean {
  if (!CONTENT_DIGEST.test(contentId)) return false;
  try {
    const file = lstatSync(join(imagesDir(root, platform), contentId), { throwIfNoEntry: false });
    return !!file?.isFile() && file.size > 0;
  } catch { return false; }
}

export function openRequestIndex(platform: string, key: string, root: string): RequestIndex {
  const file = sessionFile(root, platform, key);
  let images = new Map<string, Seen>();
  try {
    const saved = JSON.parse(readFileSync(file, "utf8")).images;
    if (!saved || typeof saved !== "object" || Array.isArray(saved)) throw new Error("invalid image index");
    images = new Map(Object.entries(saved));
  } catch (error) {
    // Starting a new index over a damaged or unreadable one could reassign an existing image ID.
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  return { platform, key, images, changed: false };
}

// The image's id, given the first time its content is seen (with the turn it was seen in), and the image kept once.
// `data` is raw base64.
export function remember(index: RequestIndex, image: { contentId: string; mime: string | null; kind: ImageKind; width: number | null; height: number | null }, data: string, turn: number, root: string): Seen {
  if (CONTENT_DIGEST.test(image.contentId) && data.length && !hasStoredImage(root, index.platform, image.contentId)) {
    const dir = imagesDir(root, index.platform);
    try {
      mkdirSync(dir, { recursive: true });
      writeWhole(join(dir, image.contentId), data);
    } catch { /* an image without a stored copy is forwarded as-is */ }
  }
  const known = index.images.get(image.contentId);
  if (known) return known;
  const seen: Seen = { id: `IMG-${String(index.images.size + 1).padStart(3, "0")}`, mime: image.mime, turn, kind: image.kind, width: image.width, height: image.height };
  index.images.set(image.contentId, seen);
  index.changed = true;
  return seen;
}

export function saveRequestIndex(index: RequestIndex, root: string): void {
  if (!index.changed) return;
  const file = sessionFile(root, index.platform, index.key);
  mkdirSync(join(platformDirOf(root, index.platform), "sessions"), { recursive: true });
  writeWhole(file, JSON.stringify({ images: Object.fromEntries(index.images) }, null, 2));
  index.changed = false;
}

// An image by its id: what is known of it and its base64 data (null once its file is gone).
export function seenImage(index: RequestIndex, id: string, root: string): { seen: Seen; data: string | null } | null {
  for (const [contentId, seen] of index.images) {
    if (seen.id !== id) continue;
    let data: string | null = null;
    try {
      if (hasStoredImage(root, index.platform, contentId)) data = readFileSync(join(imagesDir(root, index.platform), contentId), "utf8");
    } catch { /* gone */ }
    return { seen, data };
  }
  return null;
}

// The session whose conversation request went out last, for the model's fetch (its call follows that request).
export function markLatest(platform: string, key: string, root: string, now = new Date()): void {
  const dir = platformDirOf(root, platform);
  mkdirSync(dir, { recursive: true });
  writeWhole(join(dir, "latest.json"), JSON.stringify({ key, at: now.toISOString() }));
}

export function latestSession(platform: string, root: string): string | null {
  try {
    const key = JSON.parse(readFileSync(join(platformDirOf(root, platform), "latest.json"), "utf8")).key;
    return typeof key === "string" && SESSION_KEY.test(key) ? key : null;
  } catch {
    return null;
  }
}
