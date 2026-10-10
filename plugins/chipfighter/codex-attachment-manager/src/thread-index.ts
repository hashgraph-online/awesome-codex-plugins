// Purpose: P2 — the image timeline of one thread, read from its rollout (read-only): every image occurrence in
// history order with a stable id (IMG-001…), turn number, name, size and content hashes. The CLI and the proxy both
// derive it from the same files, so they agree on ids without sharing state.
// v0.1-11 — a panel read on a new process used to walk every rollout folder on each call and decode every PNG for its
// pixel fingerprint (1.2 s for 12 screenshots). Now the tree is walked in full once a minute and only the folders of
// today and yesterday in between; fingerprints can be shared between processes through a cache folder. Rollouts
// Codex compressed after a week without activity (.jsonl.zst) are read as well.
// v0.1-10 — the first line of recent rollouts, so a panel opened on a new chat can find the thread that started there.
// v0.1-12 — archived tasks (<CODEX_HOME>/archived_sessions) are looked up too: a fork's history may start in a page of
// a task the user has archived since. v0.1-13 — if that page is gone for good (its task deleted), the rest is read and
// the gap reported, instead of failing.
// v0.3 — an image the model fetched with our tool (cam_view_image) is kept apart as a copy of the original: no id.
// Input: the sessions directory and a thread id. Output: ThreadIndex (in memory; files are parsed incrementally).

import { closeSync, existsSync, mkdirSync, openSync, readdirSync, readFileSync, readSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { zstdDecompressSync } from "node:zlib";
import { findImages, type ImageRef } from "./images.ts";
import { decodePng } from "./png.ts";

type Json = Record<string, any>;
export type IndexedImage = ImageRef & { id: string; turn: number | null; bytes: number; pixelSha256: string | null };
// v0.3: an image the model fetched with our tool, a copy of `of` sent in its own turn only (spec: automatic selection).
export type FetchedCopy = { key: string; of: string; turn: number | null };
export type ThreadIndex = { threadId: string; images: IndexedImage[]; byKey: Map<string, IndexedImage>; turns: number; turnNumbers: Map<string, number>; copies: Map<string, FetchedCopy> };
export type Parsed = { offset: number; type: string; payload: Json; timestamp: string | null };
type FileCache = { size: number; mtimeMs: number; parsedTo: number; records: Parsed[] };

const SEGMENT_NAME = /^rollout-[0-9T:-]+-([0-9a-f-]{36})(?:_([0-9a-f-]{36}))?\.jsonl(?:\.zst)?$/;
const files = new Map<string, FileCache>();
const pixelHashes = new Map<string, string | null>();

function walk(directory: string): string[] {
  let entries;
  try { entries = readdirSync(directory, { withFileTypes: true }); } catch { return []; }
  return entries.flatMap((entry) => {
    const full = join(directory, entry.name);
    return entry.isDirectory() ? walk(full) : entry.isFile() ? [full] : [];
  });
}

function parseLines(buffer: Buffer, base: number, cache: FileCache): number {
  let start = 0;
  for (let end = buffer.indexOf(0x0a); end >= 0; end = buffer.indexOf(0x0a, start)) {
    const text = buffer.toString("utf8", start, end).replace(/\r$/, "");
    // A damaged line is skipped rather than failing the whole index; unknown images are sent unchanged anyway.
    let record: Json | null = null;
    if (text.trim()) { try { record = JSON.parse(text); } catch { record = null; } }
    if (record) cache.records.push({ offset: base + start, type: record.type, payload: record.payload ?? {}, timestamp: typeof record.timestamp === "string" ? record.timestamp : null });
    start = end + 1;
  }
  return start;
}

const missing = (plain: string) => Object.assign(new Error(`rollout missing: ${basename(plain)}`), { code: "ENOENT" });

// A rollout is kept under its plain name; Codex may have compressed it (.jsonl.zst), or turned a compressed one back
// into plain text to append to it.
function existing(plain: string): string | null {
  return existsSync(plain) ? plain : existsSync(`${plain}.zst`) ? `${plain}.zst` : null;
}

// Rollouts are append-only: parse only the complete lines added since the last read. A compressed one does not change
// until Codex turns it back into plain text, so it is read whole once.
function records(plain: string): Parsed[] {
  const file = existing(plain);
  if (!file) throw missing(plain);
  const stat = statSync(file);
  let cache = files.get(file);
  if (file.endsWith(".zst")) {
    if (!cache || cache.size !== stat.size || cache.mtimeMs !== stat.mtimeMs) {
      cache = { size: stat.size, mtimeMs: stat.mtimeMs, parsedTo: 0, records: [] };
      cache.parsedTo = parseLines(zstdDecompressSync(readFileSync(file)), 0, cache);
      files.set(file, cache);
    }
    return cache.records;
  }
  if (!cache || stat.size < cache.parsedTo) cache = { size: 0, mtimeMs: 0, parsedTo: 0, records: [] };
  if (stat.size !== cache.size || stat.mtimeMs !== cache.mtimeMs) {
    const length = stat.size - cache.parsedTo;
    const buffer = Buffer.alloc(length);
    const fd = openSync(file, "r");
    try { readSync(fd, buffer, 0, length, cache.parsedTo); } finally { closeSync(fd); }
    cache.parsedTo += parseLines(buffer, cache.parsedTo, cache);
    cache.size = stat.size;
    cache.mtimeMs = stat.mtimeMs;
    files.set(file, cache);
  }
  return cache.records;
}

// Every rollout segment by id: a thread's first segment uses the thread id itself, later pages are named
// <thread>_<segment>. A fork's history_base points into its parent's segments, so bases are looked up globally.
// Codex files each rollout under <sessions>/YYYY/MM/DD of the day it was created (local time), so new threads, forks
// and later pages all land in today's folder: between full walks only today's and yesterday's folders (local and UTC)
// are listed again. Archived tasks move to <CODEX_HOME>/archived_sessions, which full walks include (a task's own
// folder wins). A file moved elsewhere is found by the next full walk, or at once when a read misses it (at most one
// such extra walk every 5 s, so a history whose page was deleted does not walk the tree on every poll).
type Tree = { walkedAt: number; missedAt: number; segments: Map<string, string>; threadOf: Map<string, string> };
const FULL_WALK_MS = 60_000;
const MISSED_WALK_MS = 5_000;
const trees = new Map<string, Tree>();
const archivedOf = (sessionsDir: string) => join(dirname(sessionsDir), "archived_sessions");

export function recentFolders(sessionsDir: string, now = Date.now()): string[] {
  const pad = (n: number) => String(n).padStart(2, "0");
  const folders = new Set<string>();
  for (const at of [now, now - 86_400_000]) {
    const day = new Date(at);
    folders.add(join(sessionsDir, String(day.getFullYear()), pad(day.getMonth() + 1), pad(day.getDate())));
    folders.add(join(sessionsDir, String(day.getUTCFullYear()), pad(day.getUTCMonth() + 1), pad(day.getUTCDate())));
  }
  return [...folders];
}

function addSegment(tree: Tree, file: string): void {
  const match = SEGMENT_NAME.exec(basename(file));
  if (!match) return;
  tree.segments.set(match[2] ?? match[1], file.replace(/\.zst$/, ""));
  tree.threadOf.set(match[2] ?? match[1], match[1]);
}

function allSegments(sessionsDir: string, missed = false): Tree {
  const now = Date.now();
  let tree = trees.get(sessionsDir);
  const again = missed && (!tree || now - tree.missedAt >= MISSED_WALK_MS);
  if (!tree || again || now - tree.walkedAt > FULL_WALK_MS) {
    tree = { walkedAt: now, missedAt: again ? now : tree?.missedAt ?? 0, segments: new Map(), threadOf: new Map() };
    for (const file of [...walk(archivedOf(sessionsDir)), ...walk(sessionsDir)]) addSegment(tree, file);
    trees.set(sessionsDir, tree);
    return tree;
  }
  for (const folder of recentFolders(sessionsDir, now)) {
    let names: string[];
    try { names = readdirSync(folder); } catch { continue; }
    for (const name of names) addSegment(tree, join(folder, name));
  }
  return tree;
}

// Reads that miss a file (moved or deleted since the last full walk) walk the tree again once.
function withSegments<T>(sessionsDir: string, read: (tree: Tree) => T): T {
  try { return read(allSegments(sessionsDir)); } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
    return read(allSegments(sessionsDir, true));
  }
}

const baseOf = (file: string): Json | null => (records(file)[0]?.type === "session_meta" ? records(file)[0].payload.history_base ?? null : null);

// With `missing` (the second look, after walking the tree again), a page the history starts in that is still not found
// is left out and its id added to `missing`; without it, the miss is thrown for the caller to look again.
function effective(segments: Map<string, string>, segmentId: string, endOffset = Number.POSITIVE_INFINITY, missing: string[] | null = null): Parsed[] {
  const file = segments.get(segmentId);
  // Not listed (yet): the caller walks the tree again once.
  if (!file) throw Object.assign(new Error(`rollout segment not found: ${segmentId}`), { code: "ENOENT" });
  const base = baseOf(file);
  let inherited: Parsed[] = [];
  if (base) {
    try { inherited = effective(segments, base.thread_id, base.end_byte_offset, missing); } catch (error) {
      if (!missing || (error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
      if (!missing.includes(base.thread_id)) missing.push(base.thread_id);
    }
  }
  return [...inherited, ...records(file).filter((record) => record.offset < endOffset)];
}

// The engine and the plugin services (Codex starts one per task) share pixel fingerprints through this folder, so a
// new process does not decode every PNG again. Only fingerprints are stored, never image content. Unset: memory only
// (tests). "-" marks a PNG our decoder cannot read.
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

function pixelHash(ref: ImageRef, value: string): string | null {
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

// v0.4: the same fingerprint for an image held elsewhere (a Claude Code transcript), by its digest and base64.
export function pixelHashOfData(ref: Pick<ImageRef, "contentId" | "mime">, value: string): string | null {
  return pixelHash(ref as ImageRef, value);
}

export function imageData(items: Json[], ref: ImageRef): string | null {
  const item = items[ref.item];
  if (ref.part === null) return typeof item?.result === "string" ? item.result : null;
  const url = (item?.content ?? item?.output)?.[ref.part]?.image_url;
  return typeof url === "string" ? url.slice(url.indexOf(",") + 1) : null;
}

export function pixelHashOf(items: Json[], ref: ImageRef): string | null {
  const value = imageData(items, ref);
  return value === null ? null : pixelHash(ref, value);
}

export function buildIndex(threadId: string, history: Parsed[]): ThreadIndex {
  const turnNumbers = new Map<string, number>();
  const items: Json[] = [];
  const activeTurn: Array<string | null> = [];
  let current: string | null = null;
  for (const record of history) {
    if (record.type === "event_msg" && record.payload.type === "task_started" && record.payload.turn_id) {
      current = record.payload.turn_id;
      if (!turnNumbers.has(current!)) turnNumbers.set(current!, turnNumbers.size + 1);
    }
    if (record.type === "response_item") { items.push(record.payload); activeTurn.push(current); }
  }
  const images: IndexedImage[] = [];
  const byKey = new Map<string, IndexedImage>();
  const copies = new Map<string, FetchedCopy>();
  for (const ref of findImages(items)) {
    if (byKey.has(ref.key) || copies.has(ref.key)) continue;
    const turnId = ref.turnId ?? activeTurn[ref.item];
    const turn = turnId ? turnNumbers.get(turnId) ?? null : null;
    const pixelSha256 = pixelHashOf(items, ref);
    // v0.3: what our fetch tool brought back is the same image again, not a new occurrence, so it takes no id (the ids
    // after it stay as they were) and the panel lists it on the original's row. Its content must match that id's.
    const original = ref.fetchedId ? images.find((image) => image.id === ref.fetchedId) : undefined;
    if (original && (original.contentId === ref.contentId || (pixelSha256 !== null && original.pixelSha256 === pixelSha256))) {
      copies.set(ref.key, { key: ref.key, of: original.id, turn });
      continue;
    }
    const entry: IndexedImage = { ...ref, id: `IMG-${String(images.length + 1).padStart(3, "0")}`, turn, bytes: Math.floor((ref.base64Chars * 3) / 4), pixelSha256 };
    images.push(entry);
    byKey.set(ref.key, entry);
  }
  // An image whose own name is unknown (e.g. viewed through a variable path) takes the name of an identical one.
  for (const entry of images) {
    if (entry.name) continue;
    const twin = images.find((other) => other.name && (other.contentId === entry.contentId || (entry.pixelSha256 !== null && other.pixelSha256 === entry.pixelSha256)));
    if (twin) entry.name = twin.name;
  }
  return { threadId, images, byKey, turns: turnNumbers.size, turnNumbers, copies };
}

// The first line alone (session_meta can be long), read in chunks without parsing the rest of the file.
function firstLine(file: string): string {
  const fd = openSync(file, "r");
  try {
    const chunks: Buffer[] = [];
    const chunk = Buffer.alloc(64 * 1024);
    for (let position = 0; ; position += chunk.length) {
      const read = readSync(fd, chunk, 0, chunk.length, position);
      if (read <= 0) break;
      const end = chunk.subarray(0, read).indexOf(0x0a);
      chunks.push(Buffer.from(chunk.subarray(0, end >= 0 ? end : read)));
      if (end >= 0 || read < chunk.length) break;
    }
    return Buffer.concat(chunks).toString("utf8");
  } finally {
    closeSync(fd);
  }
}

// The first record of a rollout: read from a plain file without parsing the rest; a compressed one is read whole.
function firstRecord(plain: string): Parsed | null {
  if (!existsSync(plain)) return records(plain)[0] ?? null;
  try {
    const raw = JSON.parse(firstLine(plain));
    return { offset: 0, type: raw.type, payload: raw.payload ?? {}, timestamp: typeof raw.timestamp === "string" ? raw.timestamp : null };
  } catch { return null; }
}

const origins = new Map<string, { parent: string; at: string } | null>();

// A forked thread's session_meta names the thread it came from and when it was forked. Cached: it never changes.
export function forkOrigin(sessionsDir: string, threadId: string): { parent: string; at: string } | null {
  if (origins.has(threadId)) return origins.get(threadId)!;
  const meta = withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    return first ? { found: true, record: firstRecord(first) } : { found: false, record: null };
  });
  // No rollout yet: do not cache, it may appear once the thread starts.
  if (!meta.found) return null;
  const origin = meta.record?.type === "session_meta" && meta.record.payload.forked_from_id ? { parent: meta.record.payload.forked_from_id, at: meta.record.payload.timestamp ?? "" } : null;
  origins.set(threadId, origin);
  return origin;
}

// Whether the thread has a rollout at all: a thread Codex prepared for a new chat has none until its first message.
export function hasRollout(sessionsDir: string, threadId: string): boolean {
  return allSegments(sessionsDir).segments.has(threadId);
}

// The thread's session_meta (where it came from: source, thread_source, forked_from_id, parent_thread_id), or null.
export function sessionMetaOf(sessionsDir: string, threadId: string): Json | null {
  return withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    const record = first ? firstRecord(first) : null;
    return record?.type === "session_meta" ? record.payload : null;
  });
}

// Threads whose rollout was first written at or after `since` (ms), with their session_meta, newest last. Only
// today's and yesterday's folders are looked at. For a thread started by a message, the first line is written when
// that message is sent (Codex writes rollouts lazily), so its timestamp tells when the thread started.
export function threadsStartedSince(sessionsDir: string, since: number): Array<{ threadId: string; startedAt: number; meta: Json }> {
  const found: Array<{ threadId: string; startedAt: number; meta: Json }> = [];
  for (const folder of recentFolders(sessionsDir)) {
    let names: string[];
    try { names = readdirSync(folder); } catch { continue; }
    for (const name of names) {
      const match = SEGMENT_NAME.exec(name);
      // First segments only (named after the thread); plain text, since a compressed rollout is a week old.
      if (!match || match[2] || name.endsWith(".zst")) continue;
      const file = join(folder, name);
      try { if (statSync(file).mtimeMs < since) continue; } catch { continue; }
      const record = firstRecord(file);
      if (record?.type !== "session_meta") continue;
      const startedAt = Date.parse(record.timestamp ?? record.payload.timestamp ?? "");
      if (Number.isFinite(startedAt) && startedAt >= since && !found.some((entry) => entry.threadId === match[1])) found.push({ threadId: match[1], startedAt, meta: record.payload });
    }
  }
  return found.sort((a, b) => a.startedAt - b.startedAt);
}

// The thread's model-visible history records, following paginated segments back through history_base.
// A page the history starts in may be gone for good (its task deleted rather than archived): after walking the tree
// again, what is left is returned and the missing page ids are added to `missing`. The thread's own latest page must
// be there.
export function readThreadHistory(sessionsDir: string, threadId: string, missing: string[] = []): Parsed[] {
  const read = ({ segments, threadOf }: Tree, gaps: string[] | null) => {
    const own = [...segments.keys()].filter((id) => threadOf.get(id) === threadId);
    if (!own.length) throw new Error(`no rollout found for thread ${threadId}`);
    const bases = new Set(own.map((id) => baseOf(segments.get(id)!)?.thread_id).filter(Boolean));
    const heads = own.filter((id) => !bases.has(id));
    if (heads.length !== 1) throw new Error(`expected one latest rollout segment for ${threadId}, found ${heads.length}`);
    return effective(segments, heads[0], Number.POSITIVE_INFINITY, gaps);
  };
  try { return read(allSegments(sessionsDir), null); } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
    return read(allSegments(sessionsDir, true), missing);
  }
}

export function loadThreadIndex(sessionsDir: string, threadId: string): ThreadIndex {
  return buildIndex(threadId, readThreadHistory(sessionsDir, threadId));
}
