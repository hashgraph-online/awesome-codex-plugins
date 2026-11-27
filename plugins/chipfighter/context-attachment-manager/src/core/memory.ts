// Rebuildable caches share one estimated byte budget per process.
export const CACHE_BUDGET_BYTES = 256 * 1024 ** 2;
export const CACHE_IDLE_MS = 15 * 60_000;

type Entry = { lastUsed: number; bytes: number; remove: () => void };
const retained = new Set<Entry>();
let retainedBytes = 0;

export class LruCache<V> {
  private readonly entries = new Map<string, Entry & { value: V }>();
  private readonly limit: number;
  private readonly sizeOf: (value: V) => number;

  constructor(limit = 1024, sizeOf: (value: V) => number = () => 512) {
    this.limit = limit;
    this.sizeOf = sizeOf;
  }

  private fresh(key: string) {
    const entry = this.entries.get(key);
    if (entry && performance.now() - entry.lastUsed >= CACHE_IDLE_MS) {
      this.delete(key);
      return undefined;
    }
    return entry;
  }

  has(key: string): boolean {
    return this.fresh(key) !== undefined;
  }

  get(key: string): V | undefined {
    const entry = this.fresh(key);
    if (!entry) return undefined;
    entry.lastUsed = performance.now();
    this.entries.delete(key);
    this.entries.set(key, entry);
    retained.delete(entry);
    retained.add(entry);
    return entry.value;
  }

  set(key: string, value: V): void {
    this.delete(key);
    const bytes = Math.max(0, Math.ceil(this.sizeOf(value))) + key.length * 2 + 128;
    if (!Number.isFinite(bytes) || bytes > CACHE_BUDGET_BYTES || this.limit < 1) return;
    const entry = { value, bytes, lastUsed: performance.now(), remove: () => this.delete(key) };
    this.entries.set(key, entry);
    retained.add(entry);
    retainedBytes += bytes;
    if (this.entries.size > this.limit) this.delete(this.entries.keys().next().value!);
    cleanupCaches();
  }

  delete(key: string): void {
    const entry = this.entries.get(key);
    if (!entry) return;
    retained.delete(entry);
    retainedBytes -= entry.bytes;
    this.entries.delete(key);
  }
}

export function cleanupCaches(now = performance.now()): void {
  for (const entry of retained) {
    if (retainedBytes <= CACHE_BUDGET_BYTES && now - entry.lastUsed < CACHE_IDLE_MS) break;
    entry.remove();
  }
}

export function clearCaches(): void {
  for (const entry of retained) entry.remove();
}

export function cacheMemory() {
  return { bytes: retainedBytes, entries: retained.size, budget: CACHE_BUDGET_BYTES, idleMs: CACHE_IDLE_MS };
}

setInterval(() => cleanupCaches(), 60_000).unref();
