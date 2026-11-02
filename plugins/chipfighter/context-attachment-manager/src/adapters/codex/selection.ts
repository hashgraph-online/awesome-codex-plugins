// Purpose: P3 — a forked Codex task starts with what its parent had unchecked when the fork was made (user decision
// 2026-09-24); from then on the two are independent. v0.7 — a task's subagents (started without history) and side
// chats get automatic selection. (v0.11: split from selection.ts, docs/v0.11/plan.md.)

import { existsSync } from "node:fs";
import { autoDefaultSince, fileFor, readSelection, selectionDir, withAutoDefault, writeSelection, type Mark, type Selection } from "../../core/selection.ts";
import { forkOrigin, spawnParent, threadStartedAt } from "./thread-index.ts";

// The thread's own selection; a fork without one takes the images its parent had unchecked by the time of the fork
// (a fork of a fork asks its own parent in turn) and keeps them as its own file from then on. v0.3: likewise the
// pinned images and the switch, when it was turned on before the fork. v0.6: then the default applies, a fork
// counting from the thread it came from.
// v0.7: a subagent without a switch of its own has automatic selection instead.
export function effectiveSelection(threadId: string, sessionsDir: string, dir = selectionDir, depth = 0): Selection {
  const own = ownSelection(threadId, sessionsDir, dir, depth);
  const subagent = typeof own.auto === "boolean" || depth > 16 ? false : mainTaskOf(sessionsDir, threadId) !== null;
  if (subagent) return childSelection(own, threadStartedAt(sessionsDir, threadId));
  return withAutoDefault(own, threadStartedAt(sessionsDir, threadId), autoDefaultSince(dir));
}

// v0.7: the task a subagent started without history belongs to: its parent, followed up while that is such a subagent
// too. null for any other thread.
export function mainTaskOf(sessionsDir: string, threadId: string, depth = 0): string | null {
  const parent = spawnParent(sessionsDir, threadId);
  if (!parent) return null;
  return (depth < 16 ? mainTaskOf(sessionsDir, parent, depth + 1) : null) ?? parent;
}

// v0.7: automatic selection from the subagent's start.
export function childSelection(own: Selection, startedAt: string | null): Selection {
  return { ...own, auto: true, autoSince: own.autoSince ?? startedAt ?? new Date().toISOString() };
}

// v0.7: what a side chat forked from `origin` is sent with: the images of that task, every one of its turns counting as
// earlier, so all of them are left out but the ones pinned there.
export function sideChatSelection(origin: string, sessionsDir: string, dir = selectionDir): Selection {
  const from = effectiveSelection(origin, sessionsDir, dir);
  return { threadId: origin, unchecked: {}, auto: true, autoSince: from.autoSince ?? new Date().toISOString(), ...(from.pinned ? { pinned: from.pinned } : {}) };
}

function ownSelection(threadId: string, sessionsDir: string, dir: string, depth: number): Selection {
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
