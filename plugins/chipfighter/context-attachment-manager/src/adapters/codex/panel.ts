// Purpose: the panel's data for a Codex task (v0.11: split from panel/panel-state.ts, docs/v0.11/plan.md): the task's
// rollout, selection, statistics, name, subagents and side chats, and the ids the model's latest reply asked for.
// v0.1-9 — the task's name (thread-names.ts). v0.1-13 — whether part of the history could not be found. v0.7 — the
// task's subagents and side chats (children.ts), each with its last request.
// Input: thread id, the sessions directory (rollouts are only read) and the tool's data directory.
// Output: PanelState; selection changes are written to <data dir>/selection/.

import { childrenDirOf, dataDir, requestStatsDirOf, selectionDirOf } from "../../core/paths.ts";
import { readRequestStats, type RequestStats } from "../../core/request-stats.ts";
import { writeSelection } from "../../core/selection.ts";
import { askedIn, changedSelection, imageUrl, joinTurns, offKeys, panelStateOf, piece, sendInfo, type ChildInfo, type PanelState, type SelectionChange } from "../../panel/panel-state.ts";
import { readChildren } from "./children.ts";
import { effectiveSelection } from "./selection.ts";
import { buildIndex, imageData, readThreadHistory, sessionMetaOf, type ThreadIndex } from "./thread-index.ts";
import { threadTitle } from "./thread-names.ts";

type Json = Record<string, any>;
type Record_ = { type: string; payload: Json };
export type PanelOptions = { sessionsDir: string; dataRoot?: string };

// Ids the model asked for ("需要 IMG-003") in its latest reply; a turn still running falls back to the one before.
export function requestedIds(history: Record_[]): string[] {
  let current: string[] = [];
  let previous: string[] = [];
  for (const record of history) {
    if (record.type === "event_msg" && record.payload.type === "task_started") {
      if (current.length) previous = current;
      current = [];
    }
    if (record.type === "response_item" && record.payload.type === "message" && record.payload.role === "assistant") {
      for (const part of record.payload.content ?? []) if (typeof part?.text === "string") current.push(part.text);
    }
  }
  return [...new Set((current.length ? current : previous).flatMap(askedIn))];
}

export function codexTurnTexts(history: Record_[]): Record<string, string> {
  const numbers = new Map<string, number>();
  const texts = new Map<number, string[]>();
  let turn: number | null = null;
  for (const record of history) {
    if (record.type === "event_msg" && record.payload.type === "task_started" && record.payload.turn_id) {
      if (!numbers.has(record.payload.turn_id)) numbers.set(record.payload.turn_id, numbers.size + 1);
      turn = numbers.get(record.payload.turn_id)!;
    }
    if (turn === null || record.type !== "response_item") continue;
    const item = record.payload;
    if (item.type === "message" && (item.role === "user" || item.role === "assistant") && Array.isArray(item.content)) for (const part of item.content) piece(texts, turn, part?.text);
    else if (item.type === "function_call") piece(texts, turn, item.arguments);
    else if (item.type === "custom_tool_call") piece(texts, turn, item.input);
    else if (item.type === "image_generation_call") piece(texts, turn, item.revised_prompt);
  }
  return joinTurns(texts);
}

// `unchecked`: the keys whose box is not ticked (v0.3: with automatic selection on, every image not pinned).
export function panelState(threadId: string, history: Record_[], index: ThreadIndex, unchecked: Set<string>, stats: RequestStats | null, title: string | null = null, auto = false): PanelState {
  return panelStateOf(threadId, index, unchecked, stats, title, auto, requestedIds(history), history.length > 0, codexTurnTexts(history));
}

// v0.7: oldest first, as the engine first saw each one.
function childrenOf(taskId: string, options: PanelOptions): ChildInfo[] {
  const root = options.dataRoot ?? dataDir();
  return Object.entries(readChildren(taskId, childrenDirOf(root)))
    .sort(([, a], [, b]) => a.at.localeCompare(b.at))
    .map(([threadId, child]): ChildInfo => {
      const stats = readRequestStats(threadId, requestStatsDirOf(root));
      const spawn = child.kind === "subagent" ? sessionMetaOf(options.sessionsDir, threadId)?.source?.subagent?.thread_spawn : null;
      const images = stats?.lastHttp?.images;
      return { threadId, kind: child.kind, name: spawn?.agent_nickname ?? spawn?.agent_path?.split("/").pop() ?? null, startedAt: child.at, images: typeof images === "number" ? images : null, last: sendInfo(stats).last };
    });
}

// A thread with no rollout yet (new, or the panel opened outside a thread) simply has no images. An earlier part of
// the history that is gone for good is left out and reported.
function historyOf(threadId: string, sessionsDir: string): { history: Record_[]; missing: string[] } {
  const missing: string[] = [];
  try {
    return { history: readThreadHistory(sessionsDir, threadId, missing), missing };
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("no rollout found")) return { history: [], missing };
    throw error;
  }
}

function load(threadId: string, options: PanelOptions) {
  const root = options.dataRoot ?? dataDir();
  const { history, missing } = historyOf(threadId, options.sessionsDir);
  const index = buildIndex(threadId, history);
  const selection = effectiveSelection(threadId, options.sessionsDir, selectionDirOf(root));
  const stats = readRequestStats(threadId, requestStatsDirOf(root));
  const title = threadTitle(options.sessionsDir, threadId, history);
  return { root, history, index, selection, stats, title, historyMissing: missing.length > 0 };
}

export function loadPanelState(threadId: string, options: PanelOptions): PanelState {
  const { history, index, selection, stats, title, historyMissing } = load(threadId, options);
  return { ...panelState(threadId, history, index, offKeys(index, selection), stats, title, !!selection.auto), historyMissing, children: childrenOf(threadId, options) };
}

export function applySelection(threadId: string, change: SelectionChange, options: PanelOptions): PanelState {
  const { root, history, index, selection, stats, title, historyMissing } = load(threadId, options);
  const next = changedSelection(threadId, index, selection, change);
  writeSelection(next, selectionDirOf(root));
  return { ...panelState(threadId, history, index, offKeys(index, next), stats, title, !!next.auto), historyMissing, children: childrenOf(threadId, options) };
}

export function imageFor(threadId: string, id: string, maxSide: number, options: PanelOptions): { id: string; dataUrl: string | null } {
  const { history } = historyOf(threadId, options.sessionsDir);
  const index = buildIndex(threadId, history);
  const image = index.images.find((candidate) => candidate.id === id);
  if (!image) throw new Error(`${id} is not an image of this thread`);
  const items = history.filter((record) => record.type === "response_item").map((record) => record.payload);
  return { id, dataUrl: imageUrl(image, imageData(items, image), maxSide) };
}
