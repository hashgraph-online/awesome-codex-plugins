import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export async function getOrRefreshCatalog({
  cacheDir,
  cacheKey,
  ttlSeconds,
  refresh = false,
  now = () => Math.floor(Date.now() / 1000),
  loader
}) {
  const cachePath = path.join(cacheDir, `${cacheKey}.json`);
  const currentTime = now();

  if (!refresh) {
    const cached = await readCache(cachePath);
    if (cached && currentTime - cached.fetchedAtEpoch < ttlSeconds) {
      return cached;
    }
  }

  const items = await loader();
  const record = {
    fetchedAtEpoch: currentTime,
    items
  };

  await mkdir(cacheDir, { recursive: true });
  await writeFile(cachePath, JSON.stringify(record, null, 2), "utf8");
  return record;
}

async function readCache(cachePath) {
  try {
    const raw = await readFile(cachePath, "utf8");
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed.items) || typeof parsed.fetchedAtEpoch !== "number") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}
