// Purpose: v0.6 — a Claude Code session's selection with the default applied; v0.10: a resumed or forked session
// starts with the selection of the one it continues (v0.11: split from selection.ts, docs/v0.11/plan.md).

import { autoDefaultSince, fileFor, readSelection, THREAD_ID, withAutoDefault, writeSelection, type Mark, type Selection } from "../../core/selection.ts";
import { existsSync } from "node:fs";

// v0.6: a Claude Code session's selection with the default applied, given when it started (claudeStartedAt).
// v0.10: `previous`, the sessions it continues (ClaudeIndex.previous), for one without a selection of its own.
export function claudeSelection(sessionId: string, dir: string, startedAt: string | null, previous: Array<{ sessionId: string; at: string | null }> = []): Selection {
  return withAutoDefault(claudeOwnSelection(sessionId, dir, previous), startedAt, autoDefaultSince(dir));
}

// v0.10: Claude Desktop resumes a session as a new one, and a fork is one too: without a selection of its own, it
// starts with that of the latest session it continues that has one — the marks made by the time it took over, and
// the switch if it was last switched by then — kept as its own file from then on, as a Codex fork (ownSelection).
function claudeOwnSelection(sessionId: string, dir: string, previous: Array<{ sessionId: string; at: string | null }>): Selection {
  if (!previous.length || existsSync(fileFor(sessionId, dir))) return readSelection(sessionId, dir);
  for (const { sessionId: other, at } of previous) {
    if (!THREAD_ID.test(other) || other === sessionId || !existsSync(fileFor(other, dir))) continue;
    const from = readSelection(other, dir);
    const before = (entries: Record<string, Mark> = {}) => Object.fromEntries(Object.entries(entries).filter(([, entry]) => !at || entry.at <= at));
    const unchecked = before(from.unchecked);
    const pinned = before(from.pinned);
    const switched = typeof from.auto === "boolean" && (!at || !from.autoAt || from.autoAt <= at);
    const switches = switched ? { auto: from.auto, ...(from.autoAt ? { autoAt: from.autoAt } : {}), ...(from.autoSince ? { autoSince: from.autoSince } : {}) } : {};
    const inherited: Selection = { threadId: sessionId, unchecked, ...switches, ...(Object.keys(pinned).length ? { pinned } : {}), inheritedFrom: other };
    writeSelection(inherited, dir);
    return inherited;
  }
  return readSelection(sessionId, dir);
}
