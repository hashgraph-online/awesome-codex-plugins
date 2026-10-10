// Purpose: v0.4 — the image timeline of one Claude Code session, read from its transcript (read-only), the way
// thread-index.ts reads a Codex rollout: every image occurrence in conversation order with a stable id (IMG-001…),
// its turn, name, size and content hashes. The engine and the plugin service each derive it from the same file, so
// they agree on ids without sharing state.
// A transcript is <Claude config dir>/projects/<project>/<session id>.jsonl, appended to as the session goes on. Its
// records form a tree (parentUuid): a rewind or an edited prompt starts a branch, and the conversation is the path
// from the newest message back to the start, across compaction boundaries (logicalParentUuid). Images are in user
// records: pasted ones as image blocks, a tool's inside its tool_result. A resumed or forked session copies the
// records it continues from, with their uuids, so keys built on them stay the same in the new session.
// Keys: "<record uuid>#<n>" for a pasted image, "tool:<tool_use_id>#<n>" for one in a tool result. A request carries
// tool_use_id but not record uuids: claude-rewrite.ts matches pasted images to records by their content.
// Input: the session id (and optionally the Claude config dir). Output: ClaudeIndex (in memory; files are parsed
// incrementally).

import { closeSync, existsSync, openSync, readdirSync, readSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { baseName, FETCHED_STATE, imageDigest, type ImageKind, type ImageRef } from "./images.ts";
import { pixelHashOfData, type FetchedCopy, type IndexedImage, type ThreadIndex } from "./thread-index.ts";

type Json = Record<string, any>;
export type ClaudeRecord = Json & { type: string; uuid?: string; parentUuid?: string | null; logicalParentUuid?: string | null };
// Where an image sits: the record (its position in the conversation) and block, and for a tool result the image's
// position within that result's content.
export type ClaudeImage = IndexedImage & { recordUuid: string; toolUseId: string | null; sub: number | null; compacted: boolean };
// The records with pasted images, in conversation order, with the digests of their images: what a request's user
// messages are matched against. compacted: before the latest compaction, so no longer in requests.
export type UploadRecord = { uuid: string; contentIds: string[]; compacted: boolean };
export type ClaudeIndex = ThreadIndex & {
  images: ClaudeImage[];
  byKey: Map<string, ClaudeImage>;
  uploads: UploadRecord[];
  // The conversation, oldest first: what image positions point into.
  chain: ClaudeRecord[];
  title: string | null;
  // The text of the latest finished assistant reply (its turn), for the ids the model asked for.
  replies: string[];
  transcript: string | null;
};

const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const FETCHED_LINE = new RegExp(`^\\[(?:图片|Image) (IMG-\\d{3,}) (?:${FETCHED_STATE.zh}|${FETCHED_STATE.en})(?:｜| \\|)`);

export function claudeHome(env: NodeJS.ProcessEnv = process.env): string {
  return env.CLAUDE_CONFIG_DIR?.trim() || join(homedir(), ".claude");
}

// Where each session's transcript is: <home>/projects/<project>/<id>.jsonl. Looked up again when a session is not
// found (at most every 5 s), since a new session's file appears with its first message.
const located = new Map<string, string>();
const missedAt = new Map<string, number>();
export function transcriptOf(sessionId: string, home = claudeHome()): string | null {
  if (!SESSION_ID.test(sessionId)) return null;
  const key = `${home}\0${sessionId}`;
  const known = located.get(key);
  if (known && existsSync(known)) return known;
  if (Date.now() - (missedAt.get(key) ?? 0) < 5000) return null;
  missedAt.set(key, Date.now());
  let projects: string[];
  try { projects = readdirSync(join(home, "projects")); } catch { return null; }
  for (const project of projects) {
    const file = join(home, "projects", project, `${sessionId}.jsonl`);
    if (existsSync(file)) { located.set(key, file); missedAt.delete(key); return file; }
  }
  return null;
}

type FileCache = { size: number; mtimeMs: number; parsedTo: number; records: ClaudeRecord[] };
const files = new Map<string, FileCache>();

// Append-only: only the complete lines added since the last read are parsed. A damaged line is skipped.
export function readTranscript(file: string): ClaudeRecord[] {
  const stat = statSync(file);
  let cache = files.get(file);
  if (!cache || stat.size < cache.parsedTo) cache = { size: 0, mtimeMs: 0, parsedTo: 0, records: [] };
  if (stat.size !== cache.size || stat.mtimeMs !== cache.mtimeMs) {
    const length = stat.size - cache.parsedTo;
    const buffer = Buffer.alloc(length);
    const fd = openSync(file, "r");
    try { readSync(fd, buffer, 0, length, cache.parsedTo); } finally { closeSync(fd); }
    let start = 0;
    for (let end = buffer.indexOf(0x0a); end >= 0; end = buffer.indexOf(0x0a, start)) {
      const text = buffer.toString("utf8", start, end).trim();
      if (text) { try { cache.records.push(JSON.parse(text)); } catch { /* damaged line */ } }
      start = end + 1;
    }
    cache.parsedTo += start;
    cache.size = stat.size;
    cache.mtimeMs = stat.mtimeMs;
    files.set(file, cache);
  }
  return cache.records;
}

const isMessage = (record: ClaudeRecord) => (record.type === "user" || record.type === "assistant") && typeof record.uuid === "string";
const isBoundary = (record: ClaudeRecord) => record.type === "system" && (record.subtype === "compact_boundary" || !!record.compactMetadata);

const blocksOf = (record: ClaudeRecord): Json[] => (Array.isArray(record.message?.content) ? record.message.content : []);

// The conversation as it stands: from the newest message (not a subagent's sidechain) back to the start.
export function activeChain(records: ClaudeRecord[]): ClaudeRecord[] {
  const byUuid = new Map<string, ClaudeRecord>();
  for (const record of records) if (typeof record.uuid === "string") byUuid.set(record.uuid, record);
  let leaf: ClaudeRecord | undefined;
  for (let i = records.length - 1; i >= 0; i--) if (isMessage(records[i]) && !records[i].isSidechain) { leaf = records[i]; break; }
  const chain: ClaudeRecord[] = [];
  const seen = new Set<string>();
  for (let record = leaf; record && !seen.has(record.uuid!); ) {
    seen.add(record.uuid!);
    chain.push(record);
    const parent = record.parentUuid ?? (isBoundary(record) ? record.logicalParentUuid : null);
    record = parent ? byUuid.get(parent) : undefined;
  }
  chain.reverse();
  // Parallel tool calls (Claude Code 2.1.293): each result hangs off its own call's record and the conversation goes
  // on from the last result, so the others sit off this chain though Claude Code sends them with it. Each result whose
  // call is on the chain and has no result there joins it right after its call; a result on an abandoned branch
  // answers a call that is not on the chain and stays out.
  const calls = new Set<string>();
  const answered = new Set<string>();
  for (const record of chain) {
    for (const block of blocksOf(record)) {
      if (block?.type === "tool_use") calls.add(String(block.id));
      if (block?.type === "tool_result") answered.add(String(block.tool_use_id));
    }
  }
  const after = new Map<string, ClaudeRecord[]>();
  for (const record of records) {
    if (record.type !== "user" || record.isSidechain || seen.has(record.uuid!) || !record.parentUuid || !seen.has(record.parentUuid)) continue;
    const results = blocksOf(record).filter((block) => block?.type === "tool_result");
    if (results.length === 0 || !results.every((block) => calls.has(String(block.tool_use_id)) && !answered.has(String(block.tool_use_id)))) continue;
    for (const block of results) answered.add(String(block.tool_use_id));
    after.set(record.parentUuid, [...(after.get(record.parentUuid) ?? []), record]);
  }
  return after.size === 0 ? chain : chain.flatMap((record) => [record, ...(after.get(record.uuid!) ?? [])]);
}

// A prompt the user sent (or a delivery queued as one): not a tool result, not Claude Code's own meta message or a
// compaction summary. Claude Code 2.1.293 marks the record that starts a turn with turnPosition, also for a message
// another session delivered (a meta record, origin "peer"); without that mark, a meta record starts none.
export function isPrompt(record: ClaudeRecord): boolean {
  if (record.type !== "user" || record.isCompactSummary || record.toolUseResult !== undefined) return false;
  if (record.turnPosition && typeof record.turnPosition === "object") return true;
  if (record.isMeta) return false;
  const content = record.message?.content;
  if (typeof content === "string") return true;
  return Array.isArray(content) && content.some((block: Json) => block?.type !== "tool_result");
}

const textOf = (block: Json | undefined) => (block?.type === "text" && typeof block.text === "string" ? block.text : null);

// Every image block of a user record, in order: pasted ones, then those inside each tool result.
export type BlockImage = { part: number; sub: number | null; block: Json; toolUseId: string | null; before: string | null };
export function imageBlocks(content: unknown): BlockImage[] {
  if (!Array.isArray(content)) return [];
  const found: BlockImage[] = [];
  content.forEach((block: Json, part: number) => {
    if (block?.type === "image" && typeof block.source?.data === "string") found.push({ part, sub: null, block, toolUseId: null, before: textOf(content[part - 1]) });
    if (block?.type === "tool_result" && Array.isArray(block.content)) {
      block.content.forEach((inner: Json, sub: number) => {
        if (inner?.type === "image" && typeof inner.source?.data === "string") found.push({ part, sub, block: inner, toolUseId: String(block.tool_use_id ?? ""), before: textOf(block.content[sub - 1]) });
      });
    }
  });
  return found;
}

export function buildClaudeIndex(sessionId: string, records: ClaudeRecord[], transcript: string | null = null): ClaudeIndex {
  const chain = activeChain(records);
  let lastBoundary = -1;
  chain.forEach((record, position) => { if (isBoundary(record)) lastBoundary = position; });
  const tools = new Map<string, { name: string; input: Json }>();
  const turnNumbers = new Map<string, number>();
  const images: ClaudeImage[] = [];
  const byKey = new Map<string, ClaudeImage>();
  const copies = new Map<string, FetchedCopy>();
  const uploads: UploadRecord[] = [];
  let turn = 0;
  // The assistant's text in the current turn and in the one before (Codex: requestedIds in panel-state.ts).
  let current: string[] = [];
  let previous: string[] = [];
  chain.forEach((record, position) => {
    const content = record.message?.content;
    if (record.type === "assistant" && Array.isArray(content)) {
      for (const block of content as Json[]) {
        if (block?.type === "tool_use" && block.id) tools.set(String(block.id), { name: String(block.name ?? ""), input: block.input ?? {} });
        const text = textOf(block);
        if (text) current.push(text);
      }
      return;
    }
    if (record.type !== "user") return;
    if (isPrompt(record)) {
      turn++;
      turnNumbers.set(record.uuid!, turn);
      if (current.length) previous = current;
      current = [];
    }
    const compacted = position < lastBoundary;
    const pasted: string[] = [];
    let n = 0;
    const perTool = new Map<string, number>();
    for (const found of imageBlocks(content)) {
      const mime = typeof found.block.source.media_type === "string" ? found.block.source.media_type : null;
      const digest = imageDigest(found.block, found.block.source.data, mime);
      const tool = found.toolUseId ? tools.get(found.toolUseId) : undefined;
      let key: string;
      let kind: ImageKind;
      let name: string | null = null;
      if (found.toolUseId === null) {
        key = `${record.uuid}#${n++}`;
        kind = "upload";
        pasted.push(digest.contentId);
      } else {
        const m = perTool.get(found.toolUseId) ?? 0;
        perTool.set(found.toolUseId, m + 1);
        key = `tool:${found.toolUseId}#${m}`;
        kind = tool?.name === "Read" ? "view" : "tool";
        if (tool?.name === "Read" && typeof tool.input.file_path === "string") name = baseName(tool.input.file_path);
      }
      if (byKey.has(key) || copies.has(key)) continue;
      const pixelSha256 = pixelHashOfData(digest, found.block.source.data);
      // What our fetch tool brought back is a copy of an image already listed: no id of its own (thread-index.ts).
      const fetchedId = found.toolUseId && found.before ? FETCHED_LINE.exec(found.before)?.[1] ?? null : null;
      const original = fetchedId ? images.find((image) => image.id === fetchedId) : undefined;
      if (original && (original.contentId === digest.contentId || (pixelSha256 !== null && original.pixelSha256 === pixelSha256))) {
        copies.set(key, { key, of: original.id, turn: turn || null });
        continue;
      }
      const ref: ImageRef = {
        ...digest, key, item: position, part: found.part, openTag: null, closeTag: null, kind, replaceable: true, name, label: null,
        turnId: null, source: kind, pdfPage: null, pdfName: null, fetchedId,
      };
      const entry: ClaudeImage = {
        ...ref, id: `IMG-${String(images.length + 1).padStart(3, "0")}`, turn: turn || null, bytes: Math.floor((digest.base64Chars * 3) / 4), pixelSha256,
        recordUuid: record.uuid!, toolUseId: found.toolUseId, sub: found.sub, compacted,
      };
      images.push(entry);
      byKey.set(key, entry);
    }
    if (pasted.length) uploads.push({ uuid: record.uuid!, contentIds: pasted, compacted });
  });
  // A turn with no reply yet falls back to the one before.
  const replies = current.length ? current : previous;
  for (const entry of images) {
    if (entry.name) continue;
    const twin = images.find((other) => other.name && (other.contentId === entry.contentId || (entry.pixelSha256 !== null && other.pixelSha256 === entry.pixelSha256)));
    if (twin) entry.name = twin.name;
  }
  return { threadId: sessionId, images, byKey, turns: turn, turnNumbers, copies, uploads, chain, title: titleOf(records, chain), replies, transcript };
}

// The session's name as Claude Code shows it: the latest custom title, else the start of the first prompt.
export function titleOf(records: ClaudeRecord[], chain: ClaudeRecord[]): string | null {
  for (let i = records.length - 1; i >= 0; i--) {
    const title = records[i].type === "custom-title" ? records[i].customTitle : null;
    if (typeof title === "string" && title.trim()) return title.trim();
  }
  const first = chain.find(isPrompt);
  const content = first?.message?.content;
  const text = typeof content === "string" ? content : Array.isArray(content) ? content.map(textOf).filter(Boolean).join(" ") : "";
  const line = text.replace(/<[^>]+>[^]*?<\/[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  return line ? (line.length > 40 ? `${line.slice(0, 40)}…` : line) : null;
}

// The base64 of one indexed image, from the record it sits in.
export function claudeImageData(index: ClaudeIndex, image: ClaudeImage): string | null {
  const block = index.chain[image.item]?.message?.content?.[image.part!];
  const inner = image.sub === null ? block : block?.content?.[image.sub];
  return typeof inner?.source?.data === "string" ? inner.source.data : null;
}

// An empty index for a session without a transcript yet.
export function emptyClaudeIndex(sessionId: string): ClaudeIndex {
  return buildClaudeIndex(sessionId, []);
}

export function loadClaudeIndex(sessionId: string, home = claudeHome()): ClaudeIndex {
  const file = transcriptOf(sessionId, home);
  if (!file) return emptyClaudeIndex(sessionId);
  return buildClaudeIndex(sessionId, readTranscript(file), file);
}
