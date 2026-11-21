// Purpose: v0.4 — the panel's data for a Claude Code session (v0.11: split from panel/panel-state.ts,
// docs/v0.11/plan.md): from its transcript (claude-index.ts) and the selection and statistics kept for Claude sessions
// (paths.ts).
// Input: session id, the tool's data directory. Output: PanelState; selection changes are written.

import { claudeRequestStatsDirOf, claudeSelectionDirOf, dataDir } from "../../core/paths.ts";
import { readRequestStats, type RequestStats } from "../../core/request-stats.ts";
import { stableIdTimes, writeSelection, type Selection } from "../../core/selection.ts";
import { askedIn, changedSelection, imageUrl, joinTurns, offKeys, panelStateOf, piece, type PanelState, type SelectionChange } from "../../panel/panel-state.ts";
import { claudeHome, claudeImageData, claudeStartedAt, isPrompt, loadClaudeIndex, type ClaudeIndex, type ClaudeRecord } from "./claude-index.ts";
import { claudeSelection } from "./selection.ts";

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

// kept for Claude sessions (paths.ts).
export type ClaudePanelOptions = { dataRoot?: string; home?: string };

function loadClaude(sessionId: string, options: ClaudePanelOptions) {
  const root = options.dataRoot ?? dataDir();
  const index = loadClaudeIndex(sessionId, options.home ?? claudeHome(), stableIdTimes(claudeSelectionDirOf(root)));
  const selection = claudeSelection(sessionId, claudeSelectionDirOf(root), claudeStartedAt(index), index.previous);
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
  const index = loadClaudeIndex(sessionId, options.home ?? claudeHome(), stableIdTimes(claudeSelectionDirOf(options.dataRoot ?? dataDir())));
  const image = index.images.find((candidate) => candidate.id === id);
  if (!image) throw new Error(`${id} is not an image of this session`);
  return { id, dataUrl: imageUrl(image, claudeImageData(index, image), maxSide) };
}
