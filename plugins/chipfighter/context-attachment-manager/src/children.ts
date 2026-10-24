// Purpose: v0.7 — a task's subagents (started without history) and side chats, as the engine sees their requests, so
// the task's panel can list them. A side chat leaves no rollout: its requests are the only trace of it.
// Input: request identities (proxy.ts) and the sessions directory (read-only).
// Output: <data dir>/state/children/<task id>.json, e.g.
// { "<thread id>": { "kind": "side", "from": "<the thread it came from>", "at": "<its first request>" } }.

import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { childrenDirOf } from "./paths.ts";
import { mainTaskOf } from "./selection.ts";
import { sideChatOrigin, spawnParent } from "./thread-index.ts";

export type Child = { kind: "subagent" | "side"; from: string; at: string };
const THREAD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
// Recorded once each: later requests do not touch the file.
const known = new Set<string>();

export function readChildren(taskId: string, dir = childrenDirOf()): Record<string, Child> {
  if (!THREAD_ID.test(taskId)) return {};
  try { return JSON.parse(readFileSync(join(dir, `${taskId}.json`), "utf8")); } catch { return {}; }
}

// Whether the child was new. Written to a temporary file first, so the panel never reads a half-written list.
export function recordChild(taskId: string, childId: string, child: Child, dir = childrenDirOf()): boolean {
  const key = `${dir}\0${taskId}\0${childId}`;
  if (known.has(key) || !THREAD_ID.test(taskId) || !THREAD_ID.test(childId)) return false;
  const children = readChildren(taskId, dir);
  if (children[childId]) { known.add(key); return false; }
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `${taskId}.json`);
  writeFileSync(`${file}.tmp`, JSON.stringify({ ...children, [childId]: child }, null, 2));
  renameSync(`${file}.tmp`, file);
  known.add(key);
  return true;
}

// The task a request's thread belongs to as a side chat or as a subagent started without history, or null. A
// subagent's first request can come before Codex writes its rollout; it is found at the next one.
export function childOf(identity: { threadId: string | null; forkedFrom: string | null; turnTrigger?: string | null }, sessionsDir: string, at: string): { task: string; id: string; child: Child } | null {
  // Codex also forks an ephemeral thread for its suggested next message. Keep rewriting those requests, but do not
  // present an app-generated composer prediction as a side chat the user opened (HTTP and WebSocket share this path).
  if (identity.turnTrigger === "composer_predictions") return null;
  const id = identity.threadId;
  if (!id) return null;
  const origin = sideChatOrigin(id, identity.forkedFrom, sessionsDir);
  if (origin) return { task: mainTaskOf(sessionsDir, origin) ?? origin, id, child: { kind: "side", from: origin, at } };
  const parent = spawnParent(sessionsDir, id);
  return parent ? { task: mainTaskOf(sessionsDir, id) ?? parent, id, child: { kind: "subagent", from: parent, at } } : null;
}
