// Purpose: P2 — per-session selection state (a Codex task, a Claude Code session): which image occurrences the user
// unchecked. Written by the panel, read by the engine on every request of that session.
// v0.3 — automatic selection: a switch per thread and the images pinned while it is on ("固定发送"), kept apart from
// the manual checks, which come back as they were when it is switched off. `autoAt` is when it was last switched,
// `autoSince` when it was first switched on: from then on the history may hold copies the model fetched, which the
// engine leaves out of later turns even with the switch off.
// v0.6 — automatic selection is on by default in a thread started after this version first ran here (user
// 2026-10-13: every new task and session, in Codex and Claude Code; the ones from before keep what they had). That
// time is written once next to the selections (auto-default.json); a thread's own switch always wins, and the default
// itself is never written down.
// v0.11: the platform's own rules (a Codex fork or subagent, a resumed Claude session) are in its adapter's
// selection.ts (docs/v0.11/plan.md).
// Input/Output: <data dir>/selection/<thread id>.json, e.g. { "threadId": "…", "unchecked": { "<key>": { "id": "IMG-003", "at": "…" } } },
// plus "auto", "autoAt", "autoSince" and "pinned" (same shape as "unchecked") once automatic selection has been used.

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { selectionDirOf } from "./paths.ts";

export type Mark = { id: string; at: string };
export type Selection = { threadId: string; unchecked: Record<string, Mark>; auto?: boolean; autoAt?: string; autoSince?: string; pinned?: Record<string, Mark>; inheritedFrom?: string };

export const selectionDir = selectionDirOf();
// Codex and Claude Code name their sessions with UUIDs.
export const THREAD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
// v0.11: the name of a session's files, whatever the platform calls it: a UUID as it is, any other id as 32 hex
// characters of its hash, which can be neither a path nor one of the files kept next to the selections.
export const SESSION_KEY = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{32})$/;
export const sessionKeyOf = (id: string): string => (THREAD_ID.test(id) ? id : createHash("sha256").update(id).digest("hex").slice(0, 32));
const cache = new Map<string, { mtimeMs: number; size: number; selection: Selection }>();

export function fileFor(threadId: string, dir: string): string {
  if (!SESSION_KEY.test(threadId)) throw new Error(`not a thread id: ${threadId}`);
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

// v0.6: written by the engine and the plugin service when they start; the first one wins.
const AUTO_DEFAULT = "auto-default.json";
// v0.10: when this version first ran here. Before it, a Claude session resumed after a compaction was numbered from
// its transcript's own start; claude-index.ts translates what was written then (docs/v0.10/plan.md).
const STABLE_IDS = "stable-ids.json";
const sinceOf = new Map<string, string>();
function ensureSince(name: string, dir: string, now: Date): void {
  mkdirSync(dir, { recursive: true });
  try {
    writeFileSync(join(dir, name), JSON.stringify({ since: now.toISOString() }, null, 2), { flag: "wx" });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
  }
}
function sinceIn(name: string, dir: string): string | null {
  const key = join(dir, name);
  const known = sinceOf.get(key);
  if (known) return known;
  try {
    const since = JSON.parse(readFileSync(key, "utf8")).since;
    if (typeof since === "string") sinceOf.set(key, since);
    return typeof since === "string" ? since : null;
  } catch {
    return null;
  }
}
export const ensureAutoDefault = (dir = selectionDir, now = new Date()): void => ensureSince(AUTO_DEFAULT, dir, now);
// null until this version has run here: then nothing is on by default.
export const autoDefaultSince = (dir = selectionDir): string | null => sinceIn(AUTO_DEFAULT, dir);
// The numbering rules the ids follow. 2: the calls of a reply found off the chain, when their results came back out of
// order, get ids too (claude-index.ts). Under newer rules the start time starts again, so what was written under the
// earlier ones is translated.
const ID_RULES = 2;
// When the calls that hang off another call's result (Claude Code 2.1.317 and 2.1.321) first got ids here, written once:
// what was written between the two times is translated (claude-index.ts). A file of its own, since a copy of v0.10 or
// v0.11 still running beside this one (a Claude plugin not updated yet) writes stable-ids.json again under any rules but
// its own.
const CHAINED_IDS = "chained-ids.json";
export function ensureStableIds(dir = selectionDir, now = new Date()): void {
  const file = join(dir, STABLE_IDS);
  let rules: unknown;
  try {
    rules = JSON.parse(readFileSync(file, "utf8")).rules;
  } catch {
    mkdirSync(dir, { recursive: true });
    try { writeFileSync(file, JSON.stringify({ since: now.toISOString(), rules: ID_RULES }, null, 2), { flag: "wx" }); } catch (error) { if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error; }
    ensureSince(CHAINED_IDS, dir, now);
    return;
  }
  ensureSince(CHAINED_IDS, dir, now);
  if (rules === ID_RULES) return;
  writeFileSync(file, JSON.stringify({ since: now.toISOString(), rules: ID_RULES }, null, 2));
  sinceOf.delete(file);
}
// null until this version has run here: then nothing is translated. chained: null until then too.
export type IdTimes = { since: string; chained: string | null };
export function stableIdTimes(dir = selectionDir): IdTimes | null {
  const since = sinceIn(STABLE_IDS, dir);
  return since === null ? null : { since, chained: sinceIn(CHAINED_IDS, dir) };
}

// A thread with no switch of its own that started at or after `since` has automatic selection on, from its start;
// one with no history yet (startedAt null) is just starting.
export function withAutoDefault(selection: Selection, startedAt: string | null, since: string | null): Selection {
  if (typeof selection.auto === "boolean" || !since) return selection;
  const started = startedAt ?? new Date().toISOString();
  if (Date.parse(started) < Date.parse(since)) return selection;
  return { ...selection, auto: true, autoSince: selection.autoSince ?? started };
}
