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
// v0.8 — what the model noted about the images in record lines at the end of its replies (notes.ts), by image id.
// 0.11.2 — and what it had noted by Codex's latest compaction, for the placeholders and the list of the images from
// before it: they stay as they are until the next compaction, so the prompt cache reads past them.
// Input: the sessions directory and a thread id. Output: ThreadIndex (in memory; files are parsed incrementally).

import { createHash } from "node:crypto";
import { closeSync, existsSync, openSync, readdirSync, readFileSync, readSync, statSync } from "node:fs";
import { basename, dirname, join, relative, toNamespacedPath } from "node:path";
import { zstdDecompressSync } from "node:zlib";
import { sqliteHome } from "./codexconfig.ts";
import { findImages, type ImageRef } from "../protocols/openai-responses/images.ts";
import { readLines, readRecord } from "../../core/jsonl.ts";
import { imageDigest, rememberImageDigest } from "../../core/images.ts";
import { LruCache } from "../../core/memory.ts";
import { addNotes, copyNotes, type Notes } from "../../core/notes.ts";
import { pixelHashOfData } from "../../core/pixels.ts";
import type { FetchedCopy, IndexedImage as SessionImage, SessionIndex } from "../../core/session.ts";

type Json = Record<string, any>;
// v0.11: the shape of the index and awaitingLine are the core's (core/session.ts); a Codex image also carries where it
// sits in its item (ImageRef).
export type IndexedImage = ImageRef & SessionImage;
// compaction (0.11.2): Codex's latest compaction: how many items of the history came before it, and the notes as they
// stood then.
export type ThreadIndex = SessionIndex<IndexedImage> & { compaction?: { before: number; notes: Map<string, Notes> } };
export type Parsed = { offset: number; type: string; payload: Json; timestamp: string | null };
type FileCache = { size: number; mtimeMs: number; parsedTo: number; weight: number; records: Parsed[] };

const SEGMENT_NAME = /^rollout-[0-9T:-]+-([0-9a-f-]{36})(?:_([0-9a-f-]{36}))?\.jsonl(?:\.zst)?$/;
// ponytail: uncompressed input bytes approximate retained objects and strings.
const files = new LruCache<FileCache>(128, (cache) => cache.weight);

function walk(directory: string): string[] {
  let entries;
  try { entries = readdirSync(directory, { withFileTypes: true }); } catch { return []; }
  return entries.flatMap((entry) => {
    const full = join(directory, entry.name);
    return entry.isDirectory() ? walk(full) : entry.isFile() ? [full] : [];
  });
}

// Index media while its bytes are available. A later explicit fetch reads just the owning line of a plain rollout.
const indexedPixels = new WeakMap<object, string | null>();

function parseRecord(line: Buffer, offset: number, file: string, cache: FileCache): void {
  let record: Json;
  try { record = JSON.parse(line.toString("utf8")); } catch { return; }
  if (!record || typeof record !== "object") return;
  let retained = line.length;
  if (line.length >= 4096 && record.payload && typeof record.payload === "object") {
    const length = line.length;
    const deferred: { path: string[]; digest?: ReturnType<typeof imageDigest>; pixels?: string | null }[] = [];
    function visit(value: Json, path: string[]): void {
      for (const [key, child] of Object.entries(value)) {
        if (child && typeof child === "object") { visit(child, [...path, key]); continue; }
        if (typeof child !== "string" || child.length < 4096) continue;
        const inline = key === "image_url" && (value.type === "input_image" || value.type === "output_image")
          ? /^data:([^;,]+);base64,/.exec(child) : null;
        const generated = key === "result" && value.type === "image_generation_call";
        // Event messages can contain additional copies that aren't used to build the timeline.
        if (!inline && !generated && !(record.type === "event_msg" && path.includes("images"))) continue;
        const data = inline ? child.slice(inline[0].length) : child;
        const digest = inline || generated ? imageDigest(value, data, inline?.[1] ?? "image/png") : undefined;
        deferred.push({ path: [...path, key], digest, pixels: digest ? pixelHashOfData(digest, data) : null });
        retained -= child.length;
        value[key] = "";
      }
    }
    visit(record.payload, []);
    if (deferred.length) {
      // Detach short parsed strings that V8 may represent as slices of a large JSON source.
      record = JSON.parse(JSON.stringify(record));
      for (const { path, digest, pixels } of deferred) {
        let owner = record.payload;
        for (const step of path.slice(0, -1)) owner = owner[step];
        if (digest) { rememberImageDigest(owner, digest); indexedPixels.set(owner, pixels ?? null); }
        Object.defineProperty(owner, path.at(-1)!, { enumerable: true, get: loadField(file, offset, length, path, digest?.contentId) });
      }
    }
  }
  cache.weight += Math.max(128, retained) * 4;
  cache.records.push({ offset, type: record.type, payload: record.payload ?? {}, timestamp: record.timestamp ?? null });
}

// A multi-image fetch from one archived page can share its decompression. The weak reference lets GC reclaim it.
let lastArchive: { file: string; size: number; mtimeMs: number; data: WeakRef<Buffer> } | undefined;
function archiveData(file: string): Buffer {
  const { size, mtimeMs } = statSync(file);
  if (lastArchive?.file === file && lastArchive.size === size && lastArchive.mtimeMs === mtimeMs) {
    const data = lastArchive.data.deref();
    if (data) return data;
  }
  const data = zstdDecompressSync(readFileSync(file));
  lastArchive = { file, size, mtimeMs, data: new WeakRef(data) };
  return data;
}

function loadField(file: string, offset: number, length: number, path: string[], contentId?: string) {
  return () => {
    const plain = file.replace(/\.zst$/, "");
    const current = existing(plain);
    if (!current) throw missing(plain);
    let value = current.endsWith(".zst")
      ? JSON.parse(archiveData(current).toString("utf8", offset, offset + length)).payload
      : readRecord(current, offset, length).payload;
    for (const step of path) value = value[step];
    if (contentId) {
      const data = path.at(-1) === "image_url" ? value.slice(value.indexOf(",") + 1) : value;
      if (createHash("sha256").update(data).digest("hex") !== contentId) throw new Error("rollout image changed");
    }
    return value;
  };
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
      cache = { size: stat.size, mtimeMs: stat.mtimeMs, parsedTo: 0, weight: 0, records: [] };
      const data = archiveData(file);
      let offset = 0;
      for (let end = data.indexOf(10); end >= 0; end = data.indexOf(10, offset)) {
        parseRecord(data.subarray(offset, end), offset, file, cache);
        offset = end + 1;
      }
      cache.parsedTo = offset;
      files.set(file, cache);
    }
    return cache.records;
  }
  if (!cache || stat.size < cache.size || (stat.size === cache.size && stat.mtimeMs !== cache.mtimeMs)) cache = { size: 0, mtimeMs: 0, parsedTo: 0, weight: 0, records: [] };
  if (stat.size !== cache.size || stat.mtimeMs !== cache.mtimeMs) {
    const target = cache;
    cache.parsedTo = readLines(file, cache.parsedTo, stat.size, (line, offset) => parseRecord(line, offset, file, target));
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
const trees = new LruCache<Tree>(4, (tree) => tree.segments.size * 1024);
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
  const previousSize = tree.segments.size;
  for (const folder of recentFolders(sessionsDir, now)) {
    let names: string[];
    try { names = readdirSync(folder); } catch { continue; }
    for (const name of names) addSegment(tree, join(folder, name));
  }
  if (tree.segments.size !== previousSize) trees.set(sessionsDir, tree);
  return tree;
}

// Reads that miss a file (moved or deleted since the last full walk) walk the tree again once.
function withSegments<T>(sessionsDir: string, read: (tree: Tree) => T): T {
  try { return read(allSegments(sessionsDir)); } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
    return read(allSegments(sessionsDir, true));
  }
}

const baseOf = (first?: Parsed): Json | null => first?.type === "session_meta" ? first.payload.history_base ?? null : null;

// With `missing` (the second look, after walking the tree again), a page the history starts in that is still not found
// is left out and its id added to `missing`; without it, the miss is thrown for the caller to look again.
function effective(segments: Map<string, string>, segmentId: string, endOffset = Number.POSITIVE_INFINITY, missing: string[] | null = null): Parsed[] {
  const file = segments.get(segmentId);
  // Not listed (yet): the caller walks the tree again once.
  if (!file) throw Object.assign(new Error(`rollout segment not found: ${segmentId}`), { code: "ENOENT" });
  const parsed = records(file);
  const base = baseOf(parsed[0]);
  let inherited: Parsed[] = [];
  if (base) {
    try { inherited = effective(segments, base.thread_id, base.end_byte_offset, missing); } catch (error) {
      if (!missing || (error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
      if (!missing.includes(base.thread_id)) missing.push(base.thread_id);
    }
  }
  return [...inherited, ...parsed.filter((record) => record.offset < endOffset)];
}

export function imageData(items: Json[], ref: ImageRef): string | null {
  try {
    const item = items[ref.item];
    if (ref.part === null) {
      const data = item?.result;
      return typeof data === "string" ? data : null;
    }
    const url = (item?.content ?? item?.output)?.[ref.part]?.image_url;
    return typeof url === "string" ? url.slice(url.indexOf(",") + 1) : null;
  } catch { return null; }
}

export function pixelHashOf(items: Json[], ref: ImageRef): string | null {
  const item = items[ref.item];
  const owner = ref.part === null ? item : (item?.content ?? item?.output)?.[ref.part];
  if (owner && indexedPixels.has(owner)) return indexedPixels.get(owner)!;
  const value = imageData(items, ref);
  return value === null ? null : pixelHashOfData(ref, value);
}

export function buildIndex(threadId: string, history: Parsed[]): ThreadIndex {
  const turnNumbers = new Map<string, number>();
  const items: Json[] = [];
  const activeTurn: Array<string | null> = [];
  const notes = new Map<string, Notes>();
  let current: string | null = null;
  // v0.10: the latest compaction of Codex: how many items came before it, and the images of the history it kept.
  let compaction: { before: number; kept: Set<string>; notes: Map<string, Notes> } | null = null;
  const interrupted = new Set<number>();
  for (const record of history) {
    if (record.type === "compacted" && Array.isArray(record.payload.replacement_history)) {
      compaction = { before: items.length, kept: new Set(findImages(record.payload.replacement_history).map((ref) => ref.key)), notes: copyNotes(notes) };
    }
    if (record.type === "event_msg" && record.payload.type === "task_started" && record.payload.turn_id) {
      current = record.payload.turn_id;
      if (!turnNumbers.has(current!)) turnNumbers.set(current!, turnNumbers.size + 1);
    }
    if (record.type === "event_msg" && record.payload.type === "turn_aborted" && current) interrupted.add(turnNumbers.get(current)!);
    if (record.type !== "response_item") continue;
    items.push(record.payload);
    activeTurn.push(current);
    // v0.8: only the model's own replies.
    const { type, role, content } = record.payload;
    if (type === "message" && role === "assistant" && Array.isArray(content)) {
      const turn = current ? turnNumbers.get(current) ?? null : null;
      for (const part of content) if (part?.type === "output_text" && typeof part.text === "string") addNotes(notes, part.text, turn);
    }
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
  if (compaction) for (const entry of images) if (entry.item < compaction.before && !compaction.kept.has(entry.key)) entry.compacted = true;
  return { threadId, images, byKey, turns: turnNumbers.size, turnNumbers, copies, notes, items, interrupted, ...(compaction ? { compaction: { before: compaction.before, notes: compaction.notes } } : {}) };
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

const origins = new LruCache<{ parent: string; at: string } | null>();

// A forked thread's session_meta names the thread it came from and when it was forked. Cached: it never changes.
export function forkOrigin(sessionsDir: string, threadId: string): { parent: string; at: string } | null {
  if (origins.has(threadId)) return origins.get(threadId)!;
  const meta = withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    return first ? { found: true, record: firstRecord(first) } : { found: false, record: null };
  });
  // No rollout yet: do not cache, it may appear once the thread starts. v0.7: nor while its first line is not written
  // yet: Codex creates the file a moment before, and a request can come in between.
  if (!meta.found || !meta.record) return null;
  const origin = meta.record.type === "session_meta" && meta.record.payload.forked_from_id ? { parent: meta.record.payload.forked_from_id, at: meta.record.payload.timestamp ?? "" } : null;
  origins.set(threadId, origin);
  return origin;
}

const spawners = new LruCache<string | null>();

// v0.7: the thread that started a subagent without history (session_meta source.subagent.thread_spawn); null for
// anything else: the user's tasks, forks (a subagent started with history is one), Codex's background tasks (review,
// compaction, memory). Cached once the rollout's first line is there (as forkOrigin): it never changes.
export function spawnParent(sessionsDir: string, threadId: string): string | null {
  const key = `${sessionsDir}\0${threadId}`;
  if (spawners.has(key)) return spawners.get(key)!;
  const meta = withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    return first ? { found: true, record: firstRecord(first) } : { found: false, record: null };
  });
  if (!meta.found || !meta.record) return null;
  const payload = meta.record.type === "session_meta" ? meta.record.payload : null;
  const spawn = payload?.source?.subagent?.thread_spawn;
  const parent = payload && !payload.forked_from_id && spawn ? spawn.parent_thread_id ?? payload.parent_thread_id : null;
  spawners.set(key, typeof parent === "string" ? parent : null);
  return spawners.get(key)!;
}

const starts = new LruCache<string | null>();

// v0.6: when a thread started, from its session_meta; a fork counts from the thread it came from (followed to the
// first one; the fork's own time when that one is gone). null while the thread has no rollout, or no first line yet.
// Cached once known.
export function threadStartedAt(sessionsDir: string, threadId: string, depth = 0): string | null {
  const origin = forkOrigin(sessionsDir, threadId);
  if (origin && depth < 16) return threadStartedAt(sessionsDir, origin.parent, depth + 1) ?? (origin.at || null);
  const key = `${sessionsDir}\0${threadId}`;
  if (starts.has(key)) return starts.get(key)!;
  const meta = withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    return first ? { found: true, record: firstRecord(first) } : { found: false, record: null };
  });
  if (!meta.found || !meta.record) return null;
  const at = (meta.record.type === "session_meta" ? meta.record.payload.timestamp : null) ?? meta.record.timestamp ?? null;
  starts.set(key, typeof at === "string" ? at : null);
  return starts.get(key)!;
}

// Whether the thread has a rollout at all: a thread Codex prepared for a new chat has none until its first message.
export function hasRollout(sessionsDir: string, threadId: string): boolean {
  return allSegments(sessionsDir).segments.has(threadId);
}

// v0.7: the task a side chat came from. Codex keeps a side chat in memory only: its requests and tool calls name the
// task it was forked from (forked_from_thread_id), and it has no rollout of its own (a fork the user made has one, and
// follows the fork rules). null for any other thread.
export function sideChatOrigin(threadId: string, forkedFrom: string | null | undefined, sessionsDir: string): string | null {
  return forkedFrom && forkedFrom !== threadId && !hasRollout(sessionsDir, threadId) ? forkedFrom : null;
}

// The thread's session_meta (where it came from: source, thread_source, forked_from_id, parent_thread_id), or null.
export function sessionMetaOf(sessionsDir: string, threadId: string): Json | null {
  return withSegments(sessionsDir, ({ segments }) => {
    const first = segments.get(threadId);
    const record = first ? firstRecord(first) : null;
    return record?.type === "session_meta" ? record.payload : null;
  });
}

const noteTakers = new LruCache<boolean>();

// v0.8: whether a thread's model writes feature lines (docs/v0.8/plan.md): the user's own tasks and their forks, not a
// subagent (started with history or without) or one of Codex's internal tasks. Without a first line yet, yes, and not
// cached: a subagent's first request can come before its rollout is written (v0.7); a user's task's rarely does.
export function writesNotes(sessionsDir: string, threadId: string): boolean {
  const key = `${sessionsDir}\0${threadId}`;
  if (noteTakers.has(key)) return noteTakers.get(key)!;
  const meta = sessionMetaOf(sessionsDir, threadId);
  if (!meta) return true;
  const source = meta.source;
  const own = !(source && typeof source === "object" && ("subagent" in source || "internal" in source));
  noteTakers.set(key, own);
  return own;
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

// Reverting a thread can leave several complete branches; Codex records its current rollout in the state database
function registeredHead(sessionsDir: string, threadId: string, heads: string[], segments: Map<string, string>): string | undefined {
  try {
    const home = dirname(sessionsDir);
    const config = join(home, "config.toml");
    const dir = sqliteHome(home, existsSync(config) ? readFileSync(config, "utf8") : "");
    const sqlite = process.getBuiltinModule("node:sqlite");
    if (!sqlite) return undefined;
    const db = new sqlite.DatabaseSync(join(dir, "state_5.sqlite"), { readOnly: true });
    try {
      const path = db.prepare("SELECT rollout_path FROM threads WHERE id = ?").get(threadId)?.rollout_path;
      if (typeof path !== "string") return undefined;
      const active = toNamespacedPath(path.replace(/\.zst$/, ""));
      return heads.find((id) => relative(active, toNamespacedPath(segments.get(id)!)) === "");
    } finally {
      db.close();
    }
  } catch {
    return undefined;
  }
}

// The thread's model-visible history records, following paginated segments back through history_base.
// A page the history starts in may be gone for good (its task deleted rather than archived): after walking the tree
// again, what is left is returned and the missing page ids are added to `missing`. The thread's own latest page must
// be there.
export function readThreadHistory(sessionsDir: string, threadId: string, missing: string[] = []): Parsed[] {
  const read = ({ segments, threadOf }: Tree, gaps: string[] | null) => {
    const own = [...segments.keys()].filter((id) => threadOf.get(id) === threadId);
    if (!own.length) throw new Error(`no rollout found for thread ${threadId}`);
    const bases = new Set(own.length > 1 ? own.map((id) => baseOf(firstRecord(segments.get(id)!) ?? undefined)?.thread_id).filter(Boolean) : []);
    const heads = own.filter((id) => !bases.has(id));
    const head = heads.length > 1 ? registeredHead(sessionsDir, threadId, heads, segments) : heads[0];
    if (!head) throw new Error(`expected one latest rollout segment for ${threadId}, found ${heads.length}`);
    return effective(segments, head, Number.POSITIVE_INFINITY, gaps);
  };
  try { return read(allSegments(sessionsDir), null); } catch (error) {
    if ((error as NodeJS.ErrnoException)?.code !== "ENOENT") throw error;
    return read(allSegments(sessionsDir, true), missing);
  }
}

export function loadThreadIndex(sessionsDir: string, threadId: string): ThreadIndex {
  return buildIndex(threadId, readThreadHistory(sessionsDir, threadId));
}
