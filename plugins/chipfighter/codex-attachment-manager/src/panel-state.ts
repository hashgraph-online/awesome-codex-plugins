// Purpose: P3-3 — what the panel shows for one thread: every image occurrence with its state, the ids the model asked
// for in its latest reply, and the engine's statistics of the latest request. Also applies check/uncheck actions.
// P4 — serves each image for the panel's thumbnails and previews, and the inputs of its "next message" estimate:
// the last full request as a size baseline, which images it carried, and whether the engine could not rewrite it.
// v0.1-9 — the task's name for the title (thread-names.ts). v0.1-13 — whether part of the history could not be found.
// v0.2 — each image's source, which the panel filters by.
// v0.3 — automatic selection: the switch, the checkboxes meaning "pinned" while it is on (kept apart from the manual
// checks), and the images the model fetched in the latest turn.
// v0.7 — a Codex task's subagents and side chats (children.ts), each with its last request. v0.8: always managed by
// automatic selection; the task's switch for them is gone.
// v0.8 — what the panel searches and groups by, and never shows (docs/v0.8/plan.md): each image's scene (its feature
// line's first part) and the feature line and ratings the model noted; and per turn, what was said in it.
// Input: thread id, the sessions directory (rollouts are only read) and the tool's data directory.
// Output: PanelState as plain JSON; selection changes are written to <data dir>/selection/.

import { readChildren } from "./children.ts";
import { claudeHome, claudeImageData, claudeStartedAt, isPrompt, loadClaudeIndex, type ClaudeIndex, type ClaudeRecord } from "./claude-index.ts";
import type { ImageSource } from "./images.ts";
import { sceneOf, withoutRecords } from "./notes.ts";
import { childrenDirOf, claudeRequestStatsDirOf, claudeSelectionDirOf, dataDir, requestStatsDirOf, selectionDirOf } from "./paths.ts";
import { readRequestStats, type RequestStats } from "./request-stats.ts";
import { claudeSelection, effectiveSelection, writeSelection, type Mark, type Selection } from "./selection.ts";
import { buildIndex, imageData, readThreadHistory, sessionMetaOf, type IndexedImage, type ThreadIndex } from "./thread-index.ts";
import { threadTitle } from "./thread-names.ts";
import { pngThumbnail } from "./thumbnail.ts";

type Json = Record<string, any>;
type Record_ = { type: string; payload: Json };
export type PanelImage = {
  id: string; kind: string; name: string | null; label: string | null; turn: number | null;
  // v0.2 — what the panel filters by; a PDF comment screenshot also says its page and the PDF's name when known.
  source: ImageSource; pdfPage: number | null; pdfName: string | null;
  width: number | null; height: number | null; bytes: number; base64Chars: number;
  // checked: the box is ticked: sent with automatic selection off, pinned with it on (v0.3). fetched: the model fetched
  // it in the latest turn.
  sameAs: string[]; checked: boolean; replaceable: boolean; requested: boolean; fetched: boolean;
  // Whether the last full request carried it (null: no such request recorded yet), and whether the next one will
  // (carried last time, or added since; images compacted out of the history will not come back).
  inLastRequest: boolean | null; inNextRequest: boolean;
  // v0.5: from before a Claude Code compaction: Claude Code no longer sends it, the engine sends it again if checked.
  compacted: boolean;
  // v0.8: the scene the model named in its feature line (null: none noted), and the line and ratings themselves, for
  // the search only.
  scene: string | null; search: string;
};
export type SendInfo = {
  // The last full HTTP request as Codex built it, before any rewrite: the baseline of the estimate.
  baseline: { at: string; bytes: number } | null;
  // What the engine sent for that request; resent: images from before a compaction it sent again (v0.5).
  last: { at: string; bytesBefore: number; bytesAfter: number; replaced: number; resent: number; skipped: boolean } | null;
  // v0.4: "fallback": Anthropic refused the rewritten history under its thinking, so the engine sent the original
  // (claude-rewrite.ts): what the user unchecked went out that time. "thinking": the account checks thinking, and the
  // engine left out `count` thinking records that no longer fit the history as sent (claude-thinking.ts); the model may
  // think again.
  notice: { kind: "skipped"; at: string; reason: SkipReason } | { kind: "websocket"; at: string } | { kind: "fallback"; at: string } | { kind: "thinking"; at: string; count: number } | null;
};
// started: the thread has a rollout. A panel opened on a new chat before its first message may be tied to a thread
// Codex prepared and then replaced (v0.1-8); that one never gets a rollout.
// historyMissing: an earlier part of the history is gone for good (e.g. the task a fork came from was deleted), so the
// images in it are not listed (v0.1-13).
// auto: automatic selection is on (v0.3); fetched: the ids the model fetched in the latest turn.
// children: the subagents and side chats the engine has seen (v0.7).
// turnTexts: v0.8, what each turn said, by turn number, for the search only (turnTexts below).
export type PanelState = {
  threadId: string; title: string | null; started: boolean; historyMissing: boolean; turns: number; images: PanelImage[]; requested: string[];
  auto: boolean; fetched: string[];
  totals: { images: number; unchecked: number; checkedBytes: number; allBytes: number };
  send: SendInfo;
  children: ChildInfo[];
  turnTexts: Record<string, string>;
};
// v0.7: a subagent (name: its nickname in Codex) or side chat, when it first sent a request, and its last full request
// (images: how many it carried, as Codex built it).
export type ChildInfo = { threadId: string; kind: "subagent" | "side"; name: string | null; startedAt: string; images: number | null; last: SendInfo["last"] };

// The engine's reasons for forwarding a request unchanged, as codes the panel says in its language (v0.1-14).
export type SkipReason = "undecodable" | "unparsable" | "format" | "integer" | "index" | "other";
const SKIP_REASONS: Array<[RegExp, SkipReason]> = [
  [/^undecodable body/, "undecodable"],
  [/^unparsable body/, "unparsable"],
  [/^no input array/, "format"],
  [/^integer beyond/, "integer"],
  [/^thread index/, "index"],
];

export function sendInfo(stats: RequestStats | null): SendInfo {
  const latest = stats?.latest ?? null;
  const http = stats?.lastHttp ?? null;
  const bytes = typeof http?.decodedBytes === "number" ? http.decodedBytes : null;
  const rewrite = http?.rewrite ?? null;
  let notice: SendInfo["notice"] = null;
  if (latest?.transport === "websocket" && (latest.event === "active-while-unchecked" || latest.activeWhileUnchecked)) notice = { kind: "websocket", at: latest.at };
  else if (latest?.transport === "http" && rewrite?.skipped) {
    notice = { kind: "skipped", at: http!.at, reason: SKIP_REASONS.find(([pattern]) => pattern.test(rewrite.skipped))?.[1] ?? "other" };
  } else if (latest?.transport === "http" && rewrite?.fallback) notice = { kind: "fallback", at: http!.at };
  else if (latest?.transport === "http" && rewrite?.thinking?.left > 0) notice = { kind: "thinking", at: http!.at, count: rewrite.thinking.left };
  return {
    baseline: http && bytes !== null && http.imageSizes ? { at: http.at, bytes } : null,
    last: http && bytes !== null ? {
      at: http.at, bytesBefore: bytes, bytesAfter: rewrite?.fallback ? bytes : rewrite?.decodedAfter ?? bytes,
      replaced: rewrite?.fallback ? 0 : rewrite?.replaced?.length ?? 0, resent: rewrite?.fallback ? 0 : rewrite?.compacted?.resent?.length ?? 0,
      skipped: !!rewrite?.skipped || !!rewrite?.fallback,
    } : null,
    notice,
  };
}
export type PanelOptions = { sessionsDir: string; dataRoot?: string };

// "需要 IMG-004" or a list right after it ("需要 IMG-004、IMG-002 和 IMG-007"); a full stop ends the list. The English
// wording (v0.1-14) asks for "need IMG-004", which the model may quote.
// v0.1-17 (self-test 2026-09-26): the model may also put the ids, or the whole list, in bold ("需要 **IMG-003**"), or ask
// the user to check them again in the note's own words ("请重新勾选 IMG-003 和 IMG-004", "please check IMG-004 back in",
// "please restore IMG-004"); "取消勾选" and a state ("已勾选", "没勾选", "was restored") are not asking.
const MARKS = "[“”\"'‘’「」*_`]*";
// v0.1-24: an id may carry a short note in brackets ("IMG-002 (v1 desktop)"), and several may be joined by "or".
const NOTE = "(?:\\s*[（(][^()（）]{0,40}[)）])?";
const item = (separators: string) => `(?:\\s*${MARKS}\\s*IMG-\\d{3,}\\s*${MARKS}${NOTE}\\s*(?:${separators})?)`;
const ZH_LIST = `(${item("[、，,/]|以及|和|与|及|或者|或")}+)`;
const EN_LIST = `(${item(",|and|or")}+)`;
// v0.1-24: models also ask the user to attach, send or share an image again (GPT-6 Luna: "Please reattach IMG-002").
const ZH_ASK = "(?:重新)?(?:勾选|附上|附加|上传|发送|提供)";
const EN_ASK = "needs?|restore|re-?enable|re-?check|re-?select|re-?attach|attach|re-?add|add back|re-?send|send|re-?share|share|re-?upload|upload|provide|re-?include|include";
const ASKED = [
  new RegExp(`(?:需要|(?<!取消|已|已经|没|没有|未)${ZH_ASK})${ZH_LIST}`, "g"),
  new RegExp(`\\b(?:${EN_ASK})(?:\\s+(?:me|us))?${EN_LIST}`, "gi"),
  new RegExp(`\\bcheck${EN_LIST}\\s*(?:back|again)\\b`, "gi"),
];

// The ids one reply asks for.
export function askedIn(text: string): string[] {
  const ids = new Set<string>();
  for (const pattern of ASKED) for (const match of text.matchAll(pattern)) for (const id of match[1].matchAll(/IMG-\d{3,}/gi)) ids.add(id[0].toUpperCase());
  return [...ids];
}

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

export function sameContent(index: ThreadIndex, image: IndexedImage): string[] {
  return index.images
    .filter((other) => other !== image && (other.contentId === image.contentId || (image.pixelSha256 !== null && other.pixelSha256 === image.pixelSha256)))
    .map((other) => other.id);
}

// v0.8: what each turn said, for the search only: the user's own words, the model's replies without their record
// lines, and what the tools were called with (a generation's prompt, a viewed path); each piece and each turn cut short,
// so a long task does not make every read of the panel large. The turns are numbered as in the index.
const PIECE = 200;
const TURN_TEXT = 600;
const joinTurns = (texts: Map<number, string[]>): Record<string, string> =>
  Object.fromEntries([...texts].map(([turn, pieces]) => [String(turn), pieces.join(" ").slice(0, TURN_TEXT)]));
const piece = (texts: Map<number, string[]>, turn: number, text: unknown) => {
  // Text the client adds (instructions, the environment, an image's tag) starts with a tag or the AGENTS.md heading.
  if (typeof text !== "string" || /^\s*(?:<|# AGENTS\.md)/.test(text)) return;
  const said = withoutRecords(text).replace(/\s+/g, " ").trim().slice(0, PIECE);
  if (said) texts.set(turn, [...(texts.get(turn) ?? []), said]);
};
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
export function claudeTurnTexts(chain: ClaudeRecord[]): Record<string, string> {
  const texts = new Map<number, string[]>();
  let turn = 0;
  for (const record of chain) {
    if (record.type === "user" && isPrompt(record)) turn++;
    const content = record.message?.content;
    if (!turn || (record.type !== "user" && record.type !== "assistant") || record.isMeta || record.isCompactSummary) continue;
    if (typeof content === "string") { piece(texts, turn, content); continue; }
    if (!Array.isArray(content)) continue;
    for (const block of content) {
      if (block?.type === "text") piece(texts, turn, block.text);
      else if (block?.type === "tool_use" && record.type === "assistant") piece(texts, turn, JSON.stringify(block.input ?? {}));
    }
  }
  return joinTurns(texts);
}

// `unchecked`: the keys whose box is not ticked (v0.3: with automatic selection on, every image not pinned).
export function panelState(threadId: string, history: Record_[], index: ThreadIndex, unchecked: Set<string>, stats: RequestStats | null, title: string | null = null, auto = false): PanelState {
  return panelStateOf(threadId, index, unchecked, stats, title, auto, requestedIds(history), history.length > 0, codexTurnTexts(history));
}

// v0.4: the same for any index: Codex's (from a rollout) or Claude Code's (claude-index.ts), with the ids the model's
// latest reply asked for and whether the conversation has started.
export function panelStateOf(threadId: string, index: ThreadIndex, unchecked: Set<string>, stats: RequestStats | null, title: string | null, auto: boolean, requested: string[], started: boolean, turnTexts: Record<string, string> = {}): PanelState {
  const fetched = [...new Set([...index.copies.values()].filter((copy) => copy.turn !== null && copy.turn === index.turns).map((copy) => copy.of))];
  const carried: Record<string, number> | null = stats?.lastHttp?.imageSizes ?? null;
  // Images after the last one that request carried, or from a later turn, were added since and go out next time.
  const lastCarried = carried ? index.images.reduce((last, image, position) => (image.key in carried ? position : last), -1) : -1;
  const lastTurn = stats?.lastHttp?.turnId ? index.turnNumbers.get(stats.lastHttp.turnId) ?? null : null;
  const images = index.images.map((image, position): PanelImage => {
    const inLast = carried ? image.key in carried : null;
    // v0.5: Claude Code's images from before a compaction (claude-index.ts) go out again from the engine when checked.
    const compacted = "compacted" in image && image.compacted === true;
    const notes = index.notes?.get(image.id);
    return {
      id: image.id, kind: image.kind, name: image.name, label: image.label, turn: image.turn,
      source: image.source, pdfPage: image.pdfPage, pdfName: image.pdfName,
      width: image.width, height: image.height, bytes: image.bytes, base64Chars: image.base64Chars,
      sameAs: sameContent(index, image),
      checked: !unchecked.has(image.key),
      replaceable: image.replaceable,
      requested: requested.includes(image.id),
      fetched: fetched.includes(image.id),
      inLastRequest: inLast,
      inNextRequest: compacted || inLast !== false || position > lastCarried || (lastTurn !== null && image.turn !== null && image.turn > lastTurn),
      compacted,
      scene: sceneOf(notes?.line ?? null),
      search: [notes?.line, ...(notes?.ratings ?? []).map((rating) => rating.text)].filter(Boolean).join(" "),
    };
  });
  return {
    threadId, title, started, historyMissing: false, turns: index.turns, images, requested, auto, fetched,
    totals: {
      images: images.length,
      unchecked: images.filter((image) => !image.checked).length,
      checkedBytes: images.filter((image) => image.checked).reduce((sum, image) => sum + image.bytes, 0),
      allBytes: images.reduce((sum, image) => sum + image.bytes, 0),
    },
    send: sendInfo(stats),
    children: [],
    turnTexts,
  };
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

// The keys whose box is not ticked: the unchecked ones; v0.3: with automatic selection on, every image that can be left
// out and is not pinned.
function offKeys(index: ThreadIndex, selection: Selection): Set<string> {
  if (!selection.auto) return new Set(Object.keys(selection.unchecked));
  const pinned = selection.pinned ?? {};
  return new Set(index.images.filter((image) => image.replaceable && !pinned[image.key]).map((image) => image.key));
}

export function loadPanelState(threadId: string, options: PanelOptions): PanelState {
  const { history, index, selection, stats, title, historyMissing } = load(threadId, options);
  return { ...panelState(threadId, history, index, offKeys(index, selection), stats, title, !!selection.auto), historyMissing, children: childrenOf(threadId, options) };
}

// v0.3: `auto` switches automatic selection; with `mode: "auto"` a tick pins an image instead of sending it, each kept
// in its own record, so switching back finds the manual checks as they were.
export type SelectionChange = { uncheck?: string[]; check?: string[]; checkAll?: boolean; auto?: boolean; mode?: "manual" | "auto" };
export function applySelection(threadId: string, change: SelectionChange, options: PanelOptions): PanelState {
  const { root, history, index, selection, stats, title, historyMissing } = load(threadId, options);
  const next = changedSelection(threadId, index, selection, change);
  writeSelection(next, selectionDirOf(root));
  return { ...panelState(threadId, history, index, offKeys(index, next), stats, title, !!next.auto), historyMissing, children: childrenOf(threadId, options) };
}

// The selection after a change; nothing is written.
export function changedSelection(threadId: string, index: ThreadIndex, selection: Selection, change: SelectionChange): Selection {
  const now = new Date().toISOString();
  let next: Selection = { ...selection, threadId };
  // Switched on for the first time, the thread is marked: from then on its history may hold copies the model fetched.
  if (typeof change.auto === "boolean" && change.auto !== !!selection.auto) next = { ...next, auto: change.auto, autoAt: now, autoSince: selection.autoSince ?? now };
  const pins = change.mode === "auto";
  const marks: Record<string, Mark> = pins ? { ...(next.pinned ?? {}) } : change.checkAll ? {} : { ...next.unchecked };
  const byId = new Map(index.images.map((image) => [image.id, image]));
  const imageOf = (id: string) => {
    const image = byId.get(id);
    if (!image) throw new Error(`${id} is not an image of this thread`);
    return image;
  };
  for (const id of change.uncheck ?? []) {
    const image = imageOf(id);
    if (!image.replaceable) throw new Error(`${id} cannot be unchecked (hosted image generation result)`);
    if (pins) delete marks[image.key]; else marks[image.key] = { id, at: now };
  }
  for (const id of change.check ?? []) {
    const image = imageOf(id);
    if (pins) marks[image.key] = { id, at: now }; else delete marks[image.key];
  }
  return pins ? { ...next, pinned: marks } : { ...next, unchecked: marks };
}

// One image for the panel: a PNG larger than maxSide is scaled down; smaller PNGs and other formats (which the
// browser scales itself) are passed through as they are.
export function imageFor(threadId: string, id: string, maxSide: number, options: PanelOptions): { id: string; dataUrl: string | null } {
  const { history } = historyOf(threadId, options.sessionsDir);
  const index = buildIndex(threadId, history);
  const image = index.images.find((candidate) => candidate.id === id);
  if (!image) throw new Error(`${id} is not an image of this thread`);
  const items = history.filter((record) => record.type === "response_item").map((record) => record.payload);
  const data = imageData(items, image);
  if (!data || !image.mime?.startsWith("image/")) return { id, dataUrl: null };
  const original = `data:${image.mime};base64,${data}`;
  const large = image.mime === "image/png" && Math.max(image.width ?? 0, image.height ?? 0) > maxSide;
  // A PNG our decoder cannot read (e.g. interlaced) is still shown, just not scaled down first.
  return { id, dataUrl: large ? pngThumbnail(data, maxSide) ?? original : original };
}

// v0.4: the same for a Claude Code session, from its transcript (claude-index.ts) and the selection and statistics
// kept for Claude sessions (paths.ts).
export type ClaudePanelOptions = { dataRoot?: string; home?: string };

function loadClaude(sessionId: string, options: ClaudePanelOptions) {
  const root = options.dataRoot ?? dataDir();
  const index = loadClaudeIndex(sessionId, options.home ?? claudeHome());
  const selection = claudeSelection(sessionId, claudeSelectionDirOf(root), claudeStartedAt(index));
  const stats = readRequestStats(sessionId, claudeRequestStatsDirOf(root));
  return { root, index, selection, stats };
}

const claudeState = (sessionId: string, index: ClaudeIndex, selection: Selection, stats: RequestStats | null): PanelState =>
  panelStateOf(sessionId, index, offKeys(index, selection), stats, index.title, !!selection.auto, [...new Set(index.replies.flatMap(askedIn))], index.chain.length > 0, claudeTurnTexts(index.chain));

export function loadClaudePanelState(sessionId: string, options: ClaudePanelOptions = {}): PanelState {
  const { index, selection, stats } = loadClaude(sessionId, options);
  return claudeState(sessionId, index, selection, stats);
}

export function applyClaudeSelection(sessionId: string, change: SelectionChange, options: ClaudePanelOptions = {}): PanelState {
  const { root, index, selection, stats } = loadClaude(sessionId, options);
  const next = changedSelection(sessionId, index, selection, change);
  writeSelection(next, claudeSelectionDirOf(root));
  return claudeState(sessionId, index, next, stats);
}

export function claudeImageFor(sessionId: string, id: string, maxSide: number, options: ClaudePanelOptions = {}): { id: string; dataUrl: string | null } {
  const index = loadClaudeIndex(sessionId, options.home ?? claudeHome());
  const image = index.images.find((candidate) => candidate.id === id);
  if (!image) throw new Error(`${id} is not an image of this session`);
  const data = claudeImageData(index, image);
  if (!data || !image.mime?.startsWith("image/")) return { id, dataUrl: null };
  const original = `data:${image.mime};base64,${data}`;
  const large = image.mime === "image/png" && Math.max(image.width ?? 0, image.height ?? 0) > maxSide;
  return { id, dataUrl: large ? pngThumbnail(data, maxSide) ?? original : original };
}
