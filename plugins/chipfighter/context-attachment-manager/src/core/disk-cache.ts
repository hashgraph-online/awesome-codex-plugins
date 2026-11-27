import { lstatSync, utimesSync, type Stats } from "node:fs";
import { lstat, readdir, realpath, unlink } from "node:fs/promises";
import { join } from "node:path";
import { pixelCacheDirOf } from "./paths.ts";

export const PIXEL_CACHE_BUDGET_BYTES = 64 * 1024 ** 2;
export const CONTENT_DIGEST = /^[0-9a-f]{64}$/;

// Explicit recency works even on filesystems that do not update access times.
export function cachedFile(path: string, maxSize: number, touch = false): boolean {
  try {
    const file = lstatSync(path);
    if (!file.isFile() || file.size === 0 || file.size > maxSize) return false;
    const now = Date.now();
    if (touch && now - file.mtimeMs >= 60_000) {
      try { utimesSync(path, new Date(now), new Date(now)); } catch { /* a cache write or sweep raced us */ }
    }
    return true;
  } catch { return false; }
}

async function directories(path: string, names: RegExp): Promise<string[]> {
  try {
    if (!(await lstat(path)).isDirectory() || await realpath(path) !== path) return [];
    return (await readdir(path, { withFileTypes: true }))
      .filter(entry => entry.isDirectory() && names.test(entry.name))
      .map(entry => entry.name);
  } catch { return []; }
}

type CacheFolder = { path: string; digestPrefix?: string };
async function trim(folders: CacheFolder[], budget: number): Promise<void> {
  const entries: { path: string; folder: string; file: Stats; bytes: number }[] = [];
  let total = 0;
  for (const folder of folders) {
    try {
      if (!(await lstat(folder.path)).isDirectory() || await realpath(folder.path) !== folder.path) continue;
      for (const entry of await readdir(folder.path, { withFileTypes: true })) {
        if (!entry.isFile()) continue;
        const name = entry.name;
        const temp = /^(?<digest>[a-f0-9]{64})(?:\.(?:\d+|[a-f0-9-]{36}))?\.tmp$/.exec(name)?.groups?.digest;
        const digest = temp ?? name;
        if (!CONTENT_DIGEST.test(digest) || !digest.startsWith(folder.digestPrefix ?? "")) continue;
        try {
          const path = join(folder.path, name);
          const file = await lstat(path);
          if (!file.isFile() || file.nlink !== 1) continue;
          if (temp && Date.now() - file.mtimeMs < 60 * 60_000) continue;
          // Tiny fingerprint payloads still occupy a block on typical filesystems.
          const bytes = Math.max(Math.ceil(file.size / 4096) * 4096, (file.blocks ?? 0) * 512, 4096);
          entries.push({ path, folder: folder.path, file, bytes });
          total += bytes;
        } catch { /* another process removed the file */ }
      }
    } catch { /* a cache folder may disappear during update */ }
  }
  if (total <= budget) return;
  entries.sort((a, b) => a.file.mtimeMs - b.file.mtimeMs);
  for (const entry of entries) {
    if (total <= budget) break;
    try {
      if (await realpath(entry.folder) !== entry.folder) continue;
      const current = await lstat(entry.path);
      const old = entry.file;
      if (!current.isFile() || current.nlink !== 1 || current.dev !== old.dev || current.ino !== old.ino ||
          current.mtimeMs !== old.mtimeMs || current.ctimeMs !== old.ctimeMs || current.size !== old.size) continue;
      await unlink(entry.path);
      total -= entry.bytes;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") total -= entry.bytes;
    }
  }
}

// Only the long-lived proxy schedules this sweep. It is shared across the panel and platform processes via disk.
export async function pruneDiskCaches(root: string, pixelBudget = PIXEL_CACHE_BUDGET_BYTES): Promise<void> {
  try { root = await realpath(root); } catch { return; }
  if ((await directories(root, /^cache$/)).includes("cache")) {
    const pixels = pixelCacheDirOf(root);
    const shards = await directories(pixels, /^[a-f0-9]{2}$/);
    await trim(shards.map(shard => ({ path: join(pixels, shard), digestPrefix: shard })), pixelBudget);
  }
}
