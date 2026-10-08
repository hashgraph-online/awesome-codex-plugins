// Purpose: P2 — per-thread selection state: which image occurrences the user unchecked. Written by the CLI (later
// the panel), read by the proxy on every request of that thread.
// P3 — a forked thread starts with what its parent had unchecked when the fork was made (user decision 2026-09-24);
// from then on the two are independent.
// v0.3 — automatic selection: a switch per thread and the images pinned while it is on ("固定发送"), kept apart from
// the manual checks, which come back as they were when it is switched off. `autoAt` is when it was last switched,
// `autoSince` when it was first switched on: from then on the history may hold copies the model fetched, which the
// engine leaves out of later turns even with the switch off.
// Input/Output: <data dir>/selection/<thread id>.json, e.g. { "threadId": "…", "unchecked": { "<key>": { "id": "IMG-003", "at": "…" } } },
// plus "auto", "autoAt", "autoSince" and "pinned" (same shape as "unchecked") once automatic selection has been used.

import { existsSync, mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { selectionDirOf } from "./paths.ts";
import { forkOrigin } from "./thread-index.ts";

export type Mark = { id: string; at: string };
export type Selection = { threadId: string; unchecked: Record<string, Mark>; auto?: boolean; autoAt?: string; autoSince?: string; pinned?: Record<string, Mark>; inheritedFrom?: string };

export const selectionDir = selectionDirOf();
const THREAD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const cache = new Map<string, { mtimeMs: number; size: number; selection: Selection }>();

function fileFor(threadId: string, dir: string): string {
  if (!THREAD_ID.test(threadId)) throw new Error(`not a thread id: ${threadId}`);
  return join(dir, `${threadId}.json`);
}

export function readSelection(threadId: string, dir = selectionDir): Selection {
  const file = fileFor(threadId, dir);
  if (!existsSync(file)) return { threadId, unchecked: {} };
  const { mtimeMs, size } = statSync(file);
  const known = cache.get(file);
  if (known && known.mtimeMs === mtimeMs && known.size === size) return known.selection;
  const selection = JSON.parse(readFileSync(file, "utf8")) as Selection;
  cache.set(file, { mtimeMs, size, selection });
  return selection;
}

// Written to a temporary file first, so the proxy never reads a half-written selection.
export function writeSelection(selection: Selection, dir = selectionDir): void {
  const file = fileFor(selection.threadId, dir);
  mkdirSync(dir, { recursive: true });
  writeFileSync(`${file}.tmp`, JSON.stringify(selection, null, 2));
  renameSync(`${file}.tmp`, file);
}

// The thread's own selection; a fork without one takes the images its parent had unchecked by the time of the fork
// (a fork of a fork asks its own parent in turn) and keeps them as its own file from then on. v0.3: likewise the
// pinned images and the switch, when it was turned on before the fork.
export function effectiveSelection(threadId: string, sessionsDir: string, dir = selectionDir, depth = 0): Selection {
  if (existsSync(fileFor(threadId, dir)) || depth > 16) return readSelection(threadId, dir);
  const origin = forkOrigin(sessionsDir, threadId);
  if (!origin) return { threadId, unchecked: {} };
  const parent = effectiveSelection(origin.parent, sessionsDir, dir, depth + 1);
  const before = (entries: Record<string, Mark> = {}) => Object.fromEntries(Object.entries(entries).filter(([, entry]) => !origin.at || entry.at <= origin.at));
  const unchecked = before(parent.unchecked);
  const pinned = before(parent.pinned);
  const used = !!parent.autoSince && (!origin.at || parent.autoSince <= origin.at);
  // On at the fork if it is on now and was last switched before the fork.
  const auto = used && parent.auto === true && (!origin.at || !parent.autoAt || parent.autoAt <= origin.at);
  if (!Object.keys(unchecked).length && !Object.keys(pinned).length && !used) return { threadId, unchecked: {} };
  const switches = used ? { auto, autoSince: parent.autoSince, ...(auto ? { autoAt: parent.autoAt } : {}) } : {};
  const inherited: Selection = { threadId, unchecked, ...switches, ...(Object.keys(pinned).length ? { pinned } : {}), inheritedFrom: origin.parent };
  writeSelection(inherited, dir);
  return inherited;
}
