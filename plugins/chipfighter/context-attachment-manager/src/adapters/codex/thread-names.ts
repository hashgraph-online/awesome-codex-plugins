// Purpose: v0.1-9 — the task's name for the panel's title, as Codex shows it. Codex keeps names in
// <CODEX_HOME>/session_index.jsonl, one {id, thread_name, updated_at} per line, append-only: a rename appends a line
// and the last non-empty name of a thread wins; removing a thread's names rewrites the file. A task without a name is
// shown by the start of the first message the user sent.
// Input: the sessions directory (the index sits next to it) and a thread's history records. Output: strings; read-only.

import { closeSync, openSync, readSync, statSync } from "node:fs";
import { dirname, join } from "node:path";

type Json = Record<string, any>;
type IndexCache = { ino: number; size: number; mtimeMs: number; parsedTo: number; names: Map<string, string> };
const indexes = new Map<string, IndexCache>();
const TITLE_CHARS = 40;

export const sessionIndexOf = (sessionsDir: string) => join(dirname(sessionsDir), "session_index.jsonl");

// Parsed incrementally like a rollout; a rewritten file (another file id, or shorter) is read again from the start.
function names(file: string): Map<string, string> {
  let stat;
  try { stat = statSync(file); } catch { return new Map(); }
  let cache = indexes.get(file);
  if (!cache || cache.ino !== stat.ino || stat.size < cache.parsedTo) cache = { ino: stat.ino, size: 0, mtimeMs: 0, parsedTo: 0, names: new Map() };
  if (stat.size !== cache.size || stat.mtimeMs !== cache.mtimeMs) {
    const length = stat.size - cache.parsedTo;
    const buffer = Buffer.alloc(length);
    const fd = openSync(file, "r");
    try { readSync(fd, buffer, 0, length, cache.parsedTo); } finally { closeSync(fd); }
    let start = 0;
    for (let end = buffer.indexOf(0x0a); end >= 0; end = buffer.indexOf(0x0a, start)) {
      try {
        const entry = JSON.parse(buffer.toString("utf8", start, end));
        const name = typeof entry?.thread_name === "string" ? entry.thread_name.trim() : "";
        if (typeof entry?.id === "string" && name) cache.names.set(entry.id, name);
      } catch { /* a damaged line is skipped, as Codex does */ }
      start = end + 1;
    }
    cache.parsedTo += start;
    cache.size = stat.size;
    cache.mtimeMs = stat.mtimeMs;
    indexes.set(file, cache);
  }
  return cache.names;
}

export function threadName(sessionsDir: string, threadId: string): string | null {
  return names(sessionIndexOf(sessionsDir)).get(threadId) ?? null;
}

// The first message the user sent (Codex records it as an event_msg user_message), on one line.
export function firstMessage(history: Array<{ type: string; payload: Json }>): string | null {
  for (const record of history) {
    if (record.type !== "event_msg" || record.payload.type !== "user_message" || typeof record.payload.message !== "string") continue;
    const text = record.payload.message.replace(/\s+/g, " ").trim();
    if (text) return text;
  }
  return null;
}

export function threadTitle(sessionsDir: string, threadId: string, history: Array<{ type: string; payload: Json }>): string | null {
  const name = threadName(sessionsDir, threadId);
  if (name) return name;
  const message = firstMessage(history);
  if (!message) return null;
  const chars = [...message];
  return chars.length > TITLE_CHARS ? `${chars.slice(0, TITLE_CHARS).join("")}…` : message;
}
