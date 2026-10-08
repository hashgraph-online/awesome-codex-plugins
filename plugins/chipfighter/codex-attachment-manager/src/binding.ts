// Purpose: v0.1-10 — a panel opened on a new chat before its first message is tied to a thread Codex prepared, which
// Codex may drop for a new one when the message is sent; the panel keeps asking about the prepared one (v0.1-8).
// Here: which threads the user just started (for the panel to switch to), and which thread such a panel was switched
// to, so every later call from that tab is about the new thread.
// v0.1-16 — Codex hands such a panel a freshly prepared thread every few minutes, so the panel is offered its task again
// each time: only the newest thread started while it was on screen counts (and any started within 20 s of it, which
// the user picks from), and binding records older than a week are dropped.
// Input: the sessions directory (read-only) and the tool's data directory.
// Output: <data dir>/bindings/<the panel's thread id>.json = { "threadId": "<the thread it shows>", "at": "…" }.

import { mkdirSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { bindingsDirOf } from "./paths.ts";
import { hasRollout, threadsStartedSince } from "./thread-index.ts";

type Json = Record<string, any>;
const THREAD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
// Bindings never change once written, so they are remembered; a missing one is looked up again.
const known = new Map<string, string>();

// A thread the user started in a chat. Not: a sub-agent, an internal task (memory, guardian), a fork, a `codex exec`
// run, a call through Codex's own MCP server, or a thread some feature started (e.g. an automation).
export function isUserThread(meta: Json | null): boolean {
  if (!meta || meta.forked_from_id || meta.parent_thread_id) return false;
  const source = meta.source;
  if (source && typeof source === "object" && ("subagent" in source || "internal" in source)) return false;
  if (source === "exec" || source === "mcp") return false;
  return meta.thread_source === undefined || meta.thread_source === null || meta.thread_source === "user";
}

// When the panel page was on screen, as it reports it: [from, to] in ms, newest last. The user sends the first message
// on the page the panel is on, so a thread started while the page was on screen is this page's; one started while the
// page was hidden (the user on another chat) is not, however late the user comes back. The page notes itself every few
// seconds, so a thread started up to 5 s after the last note still counts (the user sent and left at once).
export type Shown = Array<[number, number]>;
export const LEFT_AT_ONCE_MS = 5_000;
// Threads that started this close to the newest one started "at once" (e.g. two windows): the user picks.
export const SAME_MOMENT_MS = 20_000;
const MAX_PERIODS = 20;
const KEEP_BINDINGS_MS = 7 * 86_400_000;

export function newThreads(sessionsDir: string, shown: unknown): Array<{ threadId: string; startedAt: number }> {
  const periods = (Array.isArray(shown) ? shown : [])
    .filter((period): period is [number, number] => Array.isArray(period) && Number.isFinite(period[0]) && Number.isFinite(period[1]) && period[0] <= period[1])
    .slice(-MAX_PERIODS);
  if (!periods.length) return [];
  const since = Math.min(...periods.map(([from]) => from));
  const started = threadsStartedSince(sessionsDir, since)
    .filter((entry) => isUserThread(entry.meta) && periods.some(([from, to]) => entry.startedAt >= from && entry.startedAt <= to + LEFT_AT_ONCE_MS));
  // Oldest first: the newest is last. A task started earlier on this page is not offered once a newer one exists.
  const newest = started.at(-1)?.startedAt ?? 0;
  return started.filter((entry) => newest - entry.startedAt <= SAME_MOMENT_MS).map(({ threadId, startedAt }) => ({ threadId, startedAt }));
}

export function boundThread(threadId: string, dir = bindingsDirOf()): string | null {
  const key = `${dir}|${threadId}`;
  if (known.has(key)) return known.get(key)!;
  if (!THREAD_ID.test(threadId)) return null;
  try {
    const target = JSON.parse(readFileSync(join(dir, `${threadId}.json`), "utf8"))?.threadId;
    if (typeof target !== "string" || !THREAD_ID.test(target)) return null;
    known.set(key, target);
    return target;
  } catch { return null; }
}

export function bindThread(threadId: string, target: string, dir = bindingsDirOf()): void {
  if (!THREAD_ID.test(threadId) || !THREAD_ID.test(target)) throw new Error("not a thread id");
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `${threadId}.json`);
  writeFileSync(`${file}.tmp`, JSON.stringify({ threadId: target, at: new Date().toISOString() }));
  renameSync(`${file}.tmp`, file);
  known.set(`${dir}|${threadId}`, target);
  // One record is written each time Codex hands the panel a new prepared thread; a week is plenty.
  for (const name of readdirSync(dir)) {
    const old = join(dir, name);
    try { if (name.endsWith(".json") && Date.now() - statSync(old).mtimeMs > KEEP_BINDINGS_MS) rmSync(old, { force: true }); } catch { /* gone meanwhile */ }
  }
}

// The thread a panel's call is about: the panel's own once that has a rollout, otherwise the one it was switched to.
export function resolveThread(threadId: string, sessionsDir: string, dir = bindingsDirOf()): string {
  if (!THREAD_ID.test(threadId) || hasRollout(sessionsDir, threadId)) return threadId;
  return boundThread(threadId, dir) ?? threadId;
}
