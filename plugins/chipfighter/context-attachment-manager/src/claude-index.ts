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
// v0.10 (docs/v0.10/plan.md) — since 2.1.304 a compaction keeps the last messages verbatim (compactMetadata
// preservedSegment / preservedMessages). Claude Code reads such a transcript by putting them after the summary and
// dropping what came before the boundary; the file keeps them where they were, so the chain is relinked the same way
// here, keeping the history before the boundary. Claude Desktop resumes a session as a new one, whose transcript
// starts at the latest compaction: the history is followed back into the transcript where that compaction happened,
// so ids stay what they were and the images from before it can be put back. Record lines and fetch labels written
// while the plugin numbered such a transcript from its own start are translated back.
// Input: the session id (and optionally the Claude config dir). Output: ClaudeIndex (in memory; files are parsed
// incrementally).

import { closeSync, existsSync, openSync, readdirSync, readFileSync, readSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join, resolve, sep } from "node:path";
import { baseName, FETCHED_STATE, imageDigest, type ImageKind, type ImageRef } from "./images.ts";
import { addNotes, copyNotes, type Notes } from "./notes.ts";
import { pixelHashOfData, type FetchedCopy, type IndexedImage, type ThreadIndex } from "./thread-index.ts";

type Json = Record<string, any>;
export type ClaudeRecord = Json & { type: string; uuid?: string; parentUuid?: string | null; logicalParentUuid?: string | null };
// Where an image sits: the record (its position in the conversation) and block, and for a tool result the image's
// position within that result's content.
export type ClaudeImage = IndexedImage & { recordUuid: string; toolUseId: string | null; sub: number | null; compacted: boolean };
// The records with pasted images, in conversation order, with the digests of their images: what a request's user
// messages are matched against. compacted: before the latest compaction, so no longer in requests.
export type UploadRecord = { uuid: string; contentIds: string[]; compacted: boolean };
// v0.10: the session's transcripts (this one, the ones it was resumed or forked from), each with the record it starts
// at and when it was started, oldest first.
export type FamilyFile = { sessionId: string; start: string; created: string; forkedFrom: string | null };
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
  // v0.5: the latest compaction summary's text: Claude Code starts each request after the compaction with it.
  summary: string | null;
  // v0.10: the sessions this one continues, most recent first (for its selection, selection.ts).
  previous: Array<{ sessionId: string; at: string | null }>;
  // v0.10: the notes as they stood at the latest compaction, for the list put back after it (proxy.ts): one noted
  // later is in the model's reply after the summary, and changing the list would rewrite the whole prompt cache.
  compactedNotes: Map<string, Notes>;
};

const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
// v0.10: the text Claude Code records as a prompt when the user stops a turn.
const INTERRUPTED = /^\[Request interrupted by user/;
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

// v0.10: the messages a compaction kept, oldest first, as Claude Code 2.1.309 finds them: the list it wrote
// (preservedMessages), else the walk from the tail up the parent links to the head (preservedSegment).
function preservedOf(boundary: ClaudeRecord, byUuid: Map<string, ClaudeRecord>): { anchor: string; uuids: string[] } | null {
  const meta = boundary.compactMetadata;
  const list = meta?.preservedMessages;
  if (list && typeof list.anchorUuid === "string" && Array.isArray(list.uuids)) return { anchor: list.anchorUuid, uuids: list.uuids.map(String) };
  const segment = meta?.preservedSegment;
  if (!segment || typeof segment.anchorUuid !== "string") return null;
  const walk: string[] = [];
  for (let uuid: string | null | undefined = segment.tailUuid; uuid && !walk.includes(uuid); uuid = byUuid.get(uuid)?.parentUuid) {
    walk.push(uuid);
    if (uuid === segment.headUuid) return { anchor: segment.anchorUuid, uuids: walk.reverse() };
  }
  return null;
}

// v0.10: the record a boundary's history goes on from, among `records`: the one the first kept message came after,
// unless Claude Code already put that message after the summary (a resumed transcript); without kept messages, the
// last message before the compaction (logicalParentUuid).
function historyStart(records: ClaudeRecord[], boundary: ClaudeRecord, known?: Map<string, ClaudeRecord>): string | null {
  const byUuid = known ?? new Map(records.filter((record) => typeof record.uuid === "string").map((record) => [record.uuid!, record]));
  const preserved = preservedOf(boundary, byUuid);
  if (preserved?.uuids.length) {
    const parent = byUuid.get(preserved.uuids[0])?.parentUuid ?? null;
    return parent && parent !== preserved.anchor && byUuid.has(parent) ? parent : null;
  }
  const logical = boundary.logicalParentUuid ?? null;
  return logical && byUuid.has(logical) ? logical : null;
}

// v0.10: what Claude Code 2.1.309 does when it reads a transcript (its relink after the latest boundary, when that one
// kept messages): the kept messages follow the summary; records that followed the summary, or a record it drops (one
// before the boundary that was not kept), follow the last kept message. It then drops those records; here they stay
// as the history the boundary leads back to, so the images there count as compacted. Parents to use, by uuid.
function relinked(records: ClaudeRecord[], byUuid: Map<string, ClaudeRecord>): Map<string, string | null> {
  const parents = new Map<string, string | null>();
  let last = -1;
  records.forEach((record, at) => { if (isBoundary(record)) last = at; });
  if (last < 0) return parents;
  const boundary = records[last];
  const preserved = preservedOf(boundary, byUuid);
  if (!preserved || !preserved.uuids.length || preserved.uuids.some((uuid) => !byUuid.has(uuid))) return parents;
  const { anchor, uuids } = preserved;
  const head = uuids[0];
  const tail = uuids[uuids.length - 1];
  const kept = new Set(uuids);
  const position = new Map<string, number>();
  records.forEach((record, at) => { if (typeof record.uuid === "string") position.set(record.uuid, at); });
  const dropped = (uuid: string) => { const at = position.get(uuid); return at !== undefined && at < last && !kept.has(uuid); };
  const history = historyStart(records, boundary, byUuid);
  let previous = anchor;
  for (const uuid of uuids) { parents.set(uuid, previous); previous = uuid; }
  for (const record of records) {
    if (typeof record.uuid !== "string" || kept.has(record.uuid) || dropped(record.uuid)) continue;
    if (record.parentUuid === anchor) parents.set(record.uuid, tail);
    else if ((record.type === "user" || record.type === "assistant") && record.parentUuid && dropped(record.parentUuid)) parents.set(record.uuid, tail);
  }
  if (typeof boundary.uuid === "string" && history && history !== head) parents.set(boundary.uuid, history);
  return parents;
}

// v0.10: the calls activeChain found off the chain (out-of-order parallel results) and their results.
const offChain = new WeakSet<ClaudeRecord>();

// The conversation as it stands: from the newest message (not a subagent's sidechain) back to the start. v0.10:
// `links` are where boundaries whose history sits in an earlier transcript lead (withHistory).
export function activeChain(records: ClaudeRecord[], links: Map<string, string> = new Map()): ClaudeRecord[] {
  const byUuid = new Map<string, ClaudeRecord>();
  for (const record of records) if (typeof record.uuid === "string") byUuid.set(record.uuid, record);
  const parents = relinked(records, byUuid);
  const parentOf = (record: ClaudeRecord): string | null | undefined => {
    if (parents.has(record.uuid!)) return parents.get(record.uuid!);
    return record.parentUuid ?? (isBoundary(record) ? links.get(record.uuid!) ?? record.logicalParentUuid : null);
  };
  let leaf: ClaudeRecord | undefined;
  for (let i = records.length - 1; i >= 0; i--) if (isMessage(records[i]) && !records[i].isSidechain) { leaf = records[i]; break; }
  // A record the newer transcript holds wins over the same one read from an earlier transcript.
  if (leaf) leaf = byUuid.get(leaf.uuid!) ?? leaf;
  const chain: ClaudeRecord[] = [];
  const seen = new Set<string>();
  for (let record = leaf; record && !seen.has(record.uuid!); ) {
    seen.add(record.uuid!);
    chain.push(record);
    const parent = parentOf(record);
    record = parent ? byUuid.get(parent) : undefined;
  }
  chain.reverse();
  // v0.10: the results can come back out of order (Claude Code 2.1.309, 2026-10-31). When the conversation goes on from
  // a result that is not the last call's, the calls made after that one hang off the chain too. Claude Code gives all
  // the calls of one reply its message id and sends them together, so they join the chain after that reply's records
  // and the result the conversation went on from, in the order they were made; their results join below like the
  // others. Their images were left out before: what was written then is translated (offChain, oldNumbering).
  const replyOf = (record: ClaudeRecord): string | null => (record.type === "assistant" && typeof record.message?.id === "string" ? record.message.id : null);
  const replies = new Set(chain.map(replyOf).filter((id): id is string => id !== null));
  const strays = new Map<string, ClaudeRecord[]>();
  for (const record of byUuid.values()) {
    const reply = replyOf(record);
    if (reply === null || !replies.has(reply) || seen.has(record.uuid!) || record.isSidechain || !blocksOf(record).some((block) => block?.type === "tool_use")) continue;
    const group = strays.get(reply) ?? [];
    if (!record.parentUuid || !(seen.has(record.parentUuid) || group.some((other) => other.uuid === record.parentUuid))) continue;
    strays.set(reply, [...group, record]);
  }
  for (const [reply, group] of strays) {
    let at = chain.length - 1;
    while (at >= 0 && replyOf(chain[at]) !== reply) at--;
    while (at + 1 < chain.length && chain[at + 1].type === "user" && blocksOf(chain[at + 1]).length > 0 && blocksOf(chain[at + 1]).every((block) => block?.type === "tool_result")) at++;
    chain.splice(at + 1, 0, ...group);
    for (const record of group) { seen.add(record.uuid!); offChain.add(record); }
  }
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
  for (const record of byUuid.values()) {
    if (record.type !== "user" || record.isSidechain || seen.has(record.uuid!) || !record.parentUuid || !seen.has(record.parentUuid)) continue;
    const results = blocksOf(record).filter((block) => block?.type === "tool_result");
    if (results.length === 0 || !results.every((block) => calls.has(String(block.tool_use_id)) && !answered.has(String(block.tool_use_id)))) continue;
    for (const block of results) answered.add(String(block.tool_use_id));
    if (offChain.has(byUuid.get(record.parentUuid)!)) offChain.add(record);
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

// The key each image of a user record gets, in order (what buildClaudeIndex and the old numberings share).
function keysOf(record: ClaudeRecord): Array<BlockImage & { key: string }> {
  let n = 0;
  const perTool = new Map<string, number>();
  return imageBlocks(record.message?.content).map((found) => {
    if (found.toolUseId === null) return { ...found, key: `${record.uuid}#${n++}` };
    const m = perTool.get(found.toolUseId) ?? 0;
    perTool.set(found.toolUseId, m + 1);
    return { ...found, key: `tool:${found.toolUseId}#${m}` };
  });
}

const mimeOf = (block: Json) => (typeof block.source?.media_type === "string" ? block.source.media_type : null);

// v0.10: when record lines and fetch labels were written under another numbering. `family`: the session's transcripts
// (FamilyFile); a line written at a time belongs to the newest one started by then. One that starts at a compaction
// was numbered, until `since` (when this version first ran here), from that compaction on.
export type Eras = { family: FamilyFile[]; since: string | null };
// chain: activeChain(records, links), when the caller has it already.
export type ClaudeIndexOptions = { links?: Map<string, string>; eras?: Eras; chain?: ClaudeRecord[] };

// The ids a transcript started at chain position `from` gave its images, as the plugin numbered it then: one by one
// from there, a copy our fetch tool returned (its label naming an id of this numbering, same content) taking none, and
// the calls found off the chain (offChain) taking none either: the plugin did not see them then.
// Only up to `until` (nothing written later is translated), so it stays the same as the session goes on: kept.
const numberings = new Map<string, Map<string, string>>();
function oldNumbering(chain: ClaudeRecord[], from: number, until: string): Map<string, string> {
  let end = from;
  while (end < chain.length && !(typeof chain[end].timestamp === "string" && chain[end].timestamp >= until)) end++;
  const cacheKey = `${chain[from].uuid}\0${chain[end - 1]?.uuid}\0${end - from}`;
  const known = numberings.get(cacheKey);
  if (known) return known;
  const keys = new Map<string, string>();
  const seen = new Set<string>();
  const content = new Map<string, { contentId: string; pixels: string | null }>();
  for (let position = from; position < end; position++) {
    const record = chain[position];
    if (record.type !== "user" || offChain.has(record)) continue;
    for (const found of keysOf(record)) {
      if (seen.has(found.key)) continue;
      seen.add(found.key);
      const digest = imageDigest(found.block, found.block.source.data, mimeOf(found.block));
      const pixels = pixelHashOfData(digest, found.block.source.data);
      const fetched = found.toolUseId && found.before ? FETCHED_LINE.exec(found.before)?.[1] ?? null : null;
      const original = fetched ? content.get(keys.get(fetched) ?? "") : undefined;
      if (original && (original.contentId === digest.contentId || (pixels !== null && original.pixels === pixels))) continue;
      keys.set(`IMG-${String(keys.size + 1).padStart(3, "0")}`, found.key);
      content.set(found.key, { contentId: digest.contentId, pixels });
    }
  }
  if (numberings.size > 64) numberings.clear();
  numberings.set(cacheKey, keys);
  return keys;
}

// v0.10: for a record written at `timestamp`, the numbering its ids were in: null when they are this index's own.
function translator(chain: ClaudeRecord[], eras: Eras | undefined): (timestamp: unknown) => Map<string, string> | null {
  if (!eras || eras.since === null || !chain.length) return () => null;
  const positions = new Map<string, number>();
  chain.forEach((record, at) => { if (typeof record.uuid === "string") positions.set(record.uuid, at); });
  const family = eras.family.filter((file) => positions.has(file.start)).sort((a, b) => a.created.localeCompare(b.created));
  // Calls found off the chain shift every id after theirs, in the session's first transcript too.
  const hidden = chain.some((record) => offChain.has(record));
  if (!hidden && !family.some((file) => file.start !== chain[0].uuid)) return () => null;
  const used = new Map<string, Map<string, string>>();
  return (timestamp) => {
    if (typeof timestamp !== "string" || timestamp >= eras.since!) return null;
    let start: string | null = null;
    for (const file of family) if (file.created <= timestamp) start = file.start;
    if (start === null || start === chain[0].uuid) {
      if (!hidden) return null;
      start = chain[0].uuid!;
    }
    if (!used.has(start)) used.set(start, oldNumbering(chain, positions.get(start)!, eras.since!));
    return used.get(start)!;
  };
}

export function buildClaudeIndex(sessionId: string, records: ClaudeRecord[], transcript: string | null = null, options: ClaudeIndexOptions = {}): ClaudeIndex {
  const chain = options.chain ?? activeChain(records, options.links);
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
  // v0.8: what the model noted in record lines at the end of its replies (notes.ts), by image id.
  const notes = new Map<string, Notes>();
  let compactedNotes = notes;
  const interrupted = new Set<number>();
  const skipped = new Set<number>();
  // v0.10: ids written under another numbering, back to this one's (through the image they named).
  const numberingAt = translator(chain, options.eras);
  const ownId = (numbering: Map<string, string> | null) => (id: string) => (numbering ? byKey.get(numbering.get(id) ?? "")?.id ?? null : id);
  chain.forEach((record, position) => {
    if (position === lastBoundary) compactedNotes = copyNotes(notes);
    const content = record.message?.content;
    if (record.type === "assistant" && Array.isArray(content)) {
      const idOf = ownId(numberingAt(record.timestamp));
      for (const block of content as Json[]) {
        if (block?.type === "tool_use" && block.id) tools.set(String(block.id), { name: String(block.name ?? ""), input: block.input ?? {} });
        const text = textOf(block);
        if (!text) continue;
        current.push(text);
        addNotes(notes, text, turn || null, idOf);
      }
      return;
    }
    if (record.type !== "user") return;
    if (isPrompt(record)) {
      turn++;
      turnNumbers.set(record.uuid!, turn);
      if (current.length) previous = current;
      current = [];
      // v0.10: Claude Code's mark that the user stopped the turn before: that turn was interrupted, this one is no turn.
      const said = typeof content === "string" ? content : Array.isArray(content) ? content.map(textOf).filter(Boolean).join("\n") : "";
      if (INTERRUPTED.test(said)) { if (turn > 1) interrupted.add(turn - 1); skipped.add(turn); }
    }
    const compacted = position < lastBoundary;
    const pasted: string[] = [];
    const idOf = ownId(numberingAt(record.timestamp));
    for (const found of keysOf(record)) {
      const { key } = found;
      const mime = mimeOf(found.block);
      const digest = imageDigest(found.block, found.block.source.data, mime);
      const tool = found.toolUseId ? tools.get(found.toolUseId) : undefined;
      let kind: ImageKind;
      let name: string | null = null;
      if (found.toolUseId === null) {
        kind = "upload";
        pasted.push(digest.contentId);
      } else {
        kind = tool?.name === "Read" ? "view" : "tool";
        if (tool?.name === "Read" && typeof tool.input.file_path === "string") name = baseName(tool.input.file_path);
      }
      if (byKey.has(key) || copies.has(key)) continue;
      const pixelSha256 = pixelHashOfData(digest, found.block.source.data);
      // What our fetch tool brought back is a copy of an image already listed: no id of its own (thread-index.ts).
      const labelled = found.toolUseId && found.before ? FETCHED_LINE.exec(found.before)?.[1] ?? null : null;
      const fetchedId = labelled ? idOf(labelled) : null;
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
  const summaryRecord = lastBoundary < 0 ? undefined : chain.slice(lastBoundary + 1).find((record) => record.type === "user" && record.isCompactSummary);
  const summaryContent = summaryRecord?.message?.content;
  const summary = typeof summaryContent === "string" ? summaryContent : Array.isArray(summaryContent) ? summaryContent.map(textOf).filter((text) => text !== null).join("\n") || null : null;
  for (const entry of images) {
    if (entry.name) continue;
    const twin = images.find((other) => other.name && (other.contentId === entry.contentId || (entry.pixelSha256 !== null && other.pixelSha256 === entry.pixelSha256)));
    if (twin) entry.name = twin.name;
  }
  return { threadId: sessionId, images, byKey, turns: turn, turnNumbers, copies, notes, uploads, chain, title: titleOf(records, chain), replies, transcript, summary, previous: previousOf(sessionId, options.eras?.family ?? []), interrupted, skipped, compactedNotes };
}

// v0.10: the sessions this one continues, most recent first, each with the time this one took over: the one it was
// forked from (the copied records keep that session's id), then the transcripts started before it.
function previousOf(sessionId: string, family: FamilyFile[]): Array<{ sessionId: string; at: string | null }> {
  const own = family.find((file) => file.sessionId === sessionId);
  if (!own) return [];
  const earlier = family.filter((file) => file.sessionId !== sessionId && file.created <= own.created).sort((a, b) => b.created.localeCompare(a.created));
  const ids = [...(own.forkedFrom ? [own.forkedFrom] : []), ...earlier.map((file) => file.sessionId)];
  return [...new Set(ids)].map((id) => ({ sessionId: id, at: own.created }));
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

// v0.6: when the session started: Claude Code stamps its records, and the conversation's first one is the oldest.
// null before its first message.
export function claudeStartedAt(index: ClaudeIndex): string | null {
  const first = index.chain.find((record) => typeof record.timestamp === "string");
  return first ? first.timestamp : null;
}

// v0.10: an image read from an earlier transcript keeps its data on disk: where to read it back.
type OnDisk = { file: string; start: number; end: number; part: number; sub: number | null };
const onDisk = new WeakMap<object, OnDisk>();

function readImageAt({ file, start, end, part, sub }: OnDisk): string | null {
  try {
    const buffer = Buffer.alloc(end - start);
    const fd = openSync(file, "r");
    try { readSync(fd, buffer, 0, buffer.length, start); } finally { closeSync(fd); }
    const block = JSON.parse(buffer.toString("utf8")).message?.content?.[part];
    const inner = sub === null ? block : block?.content?.[sub];
    return typeof inner?.source?.data === "string" ? inner.source.data : null;
  } catch { return null; }
}

// The base64 of one indexed image, from the record it sits in.
export function claudeImageData(index: ClaudeIndex, image: ClaudeImage): string | null {
  const block = index.chain[image.item]?.message?.content?.[image.part!];
  const inner = image.sub === null ? block : block?.content?.[image.sub];
  if (typeof inner?.source?.data === "string" && inner.source.data) return inner.source.data;
  const where = inner ? onDisk.get(inner) : undefined;
  return where ? readImageAt(where) : null;
}

// An empty index for a session without a transcript yet.
export function emptyClaudeIndex(sessionId: string): ClaudeIndex {
  return buildClaudeIndex(sessionId, []);
}

// v0.10: an earlier transcript, read for its history only: every image's digest and pixel fingerprint are taken while
// its data is at hand, then the data is left on disk (claudeImageData reads it back), so a long session followed back
// through several transcripts does not hold all their images in memory. Read again only if the file changes.
const histories = new Map<string, { size: number; mtimeMs: number; records: ClaudeRecord[] }>();
export function readHistoryTranscript(file: string): ClaudeRecord[] {
  const stat = statSync(file);
  const known = histories.get(file);
  if (known && known.size === stat.size && known.mtimeMs === stat.mtimeMs) return known.records;
  const buffer = readFileSync(file);
  const records: ClaudeRecord[] = [];
  let start = 0;
  for (let end = buffer.indexOf(0x0a); end >= 0; end = buffer.indexOf(0x0a, start)) {
    const text = buffer.toString("utf8", start, end).trim();
    if (text) {
      try {
        const record = JSON.parse(text) as ClaudeRecord;
        for (const found of imageBlocks(record.message?.content)) {
          const data = found.block.source.data as string;
          if (!data) continue;
          pixelHashOfData(imageDigest(found.block, data, mimeOf(found.block)), data);
          found.block.source = { ...found.block.source, data: "" };
          onDisk.set(found.block, { file, start, end, part: found.part, sub: found.sub });
        }
        records.push(record);
      } catch { /* damaged line */ }
    }
    start = end + 1;
  }
  histories.set(file, { size: stat.size, mtimeMs: stat.mtimeMs, records });
  return records;
}

// v0.10: the transcript a compaction happened in. The summary Claude Code wrote names it ("…read the full transcript
// at: <path>"; the last such line, after the model's own text); failing that, a transcript of the same project that
// holds the boundary with records before it. Only files under <home>/projects count. Remembered once found.
const TRANSCRIPT_AT = /read the full transcript at: ([^\n]+?\.jsonl)/g;
const originals = new Map<string, { file: string | null; at: number }>();
function underProjects(file: string, home: string): boolean {
  const root = resolve(home, "projects") + sep;
  const full = resolve(file);
  return process.platform === "win32" ? full.toLowerCase().startsWith(root.toLowerCase()) : full.startsWith(root);
}
const holdsBefore = (records: ClaudeRecord[], uuid: string) => {
  const first = records.findIndex((record) => typeof record.uuid === "string");
  const at = records.findIndex((record) => record.uuid === uuid);
  return at > first && first >= 0;
};
function originalOf(file: string, records: ClaudeRecord[], boundary: ClaudeRecord, home: string): string | null {
  const key = `${file}\0${boundary.uuid}`;
  const known = originals.get(key);
  if (known && (known.file || Date.now() - known.at < 10 * 60_000)) return known.file;
  const usable = (candidate: string) => {
    if (resolve(candidate) === resolve(file) || !underProjects(candidate, home) || !existsSync(candidate)) return false;
    try { return holdsBefore(readHistoryTranscript(candidate), boundary.uuid!); } catch { return false; }
  };
  const summary = records.find((record) => record.isCompactSummary && record.parentUuid === boundary.uuid);
  const content = summary?.message?.content;
  const text = typeof content === "string" ? content : Array.isArray(content) ? content.map(textOf).filter(Boolean).join("\n") : "";
  let found = [...text.matchAll(TRANSCRIPT_AT)].map((match) => match[1].trim()).reverse().find(usable) ?? null;
  // Else the project's transcripts written to since the compaction, holding its boundary.
  if (!found) {
    const since = typeof boundary.timestamp === "string" ? Date.parse(boundary.timestamp) : 0;
    const needle = Buffer.from(`"uuid":"${boundary.uuid}"`);
    let names: string[] = [];
    try { names = readdirSync(dirname(file)).filter((name) => name.endsWith(".jsonl")); } catch { /* none */ }
    for (const name of names) {
      const other = join(dirname(file), name);
      try {
        if (statSync(other).mtimeMs < since || !readFileSync(other).includes(needle)) continue;
      } catch { continue; }
      if (usable(other)) { found = other; break; }
    }
  }
  originals.set(key, { file: found, at: Date.now() });
  return found;
}

// v0.10: a transcript's records with the history its first compaction hides prepended: the records of the transcript
// that compaction happened in, up to its boundary, followed back as far as they go. `links` say where each such
// boundary leads.
export type WithHistory = { records: ClaudeRecord[]; links: Map<string, string> };
// The history read from an earlier transcript, per boundary, while that file is unchanged: only its conversation
// records before the boundary (the rest of it is in the newer transcript, or not part of this session), so the earlier
// file itself need not stay parsed.
const prefixes = new Map<string, { stamp: string; part: { prefix: ClaudeRecord[]; links: Map<string, string> } | null }>();
const stampOf = (file: string) => { const stat = statSync(file); return `${stat.size}:${stat.mtimeMs}`; };
export function withHistory(file: string, records: ClaudeRecord[], home = claudeHome(), depth = 0): WithHistory {
  const first = records.find((record) => typeof record.uuid === "string");
  if (!first || !isBoundary(first) || depth > 16) return { records, links: new Map() };
  const original = originalOf(file, records, first, home);
  if (!original) return { records, links: new Map() };
  const key = `${original}\0${first.uuid}`;
  let stamp: string;
  try { stamp = stampOf(original); } catch { return { records, links: new Map() }; }
  let cached = prefixes.get(key);
  if (!cached || cached.stamp !== stamp) {
    const older = withHistory(original, readHistoryTranscript(original), home, depth + 1);
    const at = older.records.findIndex((record) => record.uuid === first.uuid);
    const start = at < 0 ? null : historyStart(older.records, older.records[at]);
    const prefix = at < 0 || !start ? null : older.records.slice(0, at).filter((record) => typeof record.uuid === "string");
    cached = { stamp, part: prefix && start ? { prefix, links: new Map([...older.links, [first.uuid!, start]]) } : null };
    prefixes.set(key, cached);
    histories.delete(original);
  }
  if (!cached.part) return { records, links: new Map() };
  return { records: [...cached.part.prefix, ...records], links: cached.part.links };
}

// v0.10: the transcripts of one session in its project folder: those whose first conversation record is the session's
// start or one of its compactions, each with when it was started (its first stamped record, before the copied ones)
// and, for a fork, the session it came from. The head of each file is read once.
const heads = new Map<string, { start: string; created: string; sessionOf: string | null } | null>();
const listings = new Map<string, { at: number; names: string[] }>();
function headOf(file: string): { start: string; created: string; sessionOf: string | null } | null {
  if (heads.has(file)) return heads.get(file)!;
  let head: { start: string; created: string; sessionOf: string | null } | null = null;
  try {
    const fd = openSync(file, "r");
    const buffer = Buffer.alloc(1 << 20);
    let read = 0;
    try { read = readSync(fd, buffer, 0, buffer.length, 0); } finally { closeSync(fd); }
    let created: string | null = null;
    const lines = buffer.toString("utf8", 0, read).split("\n");
    for (const line of lines.slice(0, -1)) {
      let record: ClaudeRecord;
      try { record = JSON.parse(line); } catch { continue; }
      if (typeof record.uuid !== "string") { if (!created && typeof record.timestamp === "string") created = record.timestamp; continue; }
      const stamp = created ?? (typeof record.timestamp === "string" ? record.timestamp : null);
      if (stamp) head = { start: record.uuid, created: stamp, sessionOf: typeof record.sessionId === "string" ? record.sessionId : null };
      break;
    }
  } catch { /* unreadable */ }
  // Not cached while the file has no conversation record yet.
  if (head) heads.set(file, head);
  return head;
}
export function familyOf(file: string, starts: Set<string>): FamilyFile[] {
  const folder = dirname(file);
  let listing = listings.get(folder);
  // Listed again every 5 s, and at once when this transcript is new to the listing (a session just resumed).
  if (!listing || Date.now() - listing.at > 5000 || !listing.names.includes(basename(file))) {
    let names: string[] = [];
    try { names = readdirSync(folder).filter((name) => name.endsWith(".jsonl")); } catch { /* none */ }
    listing = { at: Date.now(), names };
    listings.set(folder, listing);
  }
  const family: FamilyFile[] = [];
  for (const name of listing.names) {
    const head = headOf(join(folder, name));
    if (!head || !starts.has(head.start)) continue;
    const sessionId = basename(name, ".jsonl");
    family.push({ sessionId, start: head.start, created: head.created, forkedFrom: head.sessionOf && head.sessionOf !== sessionId ? head.sessionOf : null });
  }
  return family.sort((a, b) => a.created.localeCompare(b.created));
}

// v0.10: `since` is when this version first ran here (selection.ts, stableIdsSince); before it, transcripts resumed
// after a compaction were numbered from their own start, and what was written then is translated back.
// The engine reads the index several times per request (whether to rewrite, the rewrite, the sizes): the last one is
// kept while the transcripts, the project folder and `since` are as they were. Callers only read it.
const loaded = new WeakMap<ClaudeRecord[], { key: string; index: ClaudeIndex }>();
export function loadClaudeIndex(sessionId: string, home = claudeHome(), since: string | null = null): ClaudeIndex {
  const file = transcriptOf(sessionId, home);
  if (!file) return emptyClaudeIndex(sessionId);
  const own = readTranscript(file);
  const { records, links } = withHistory(file, own, home);
  const key = [own.length, records.length, since, listings.get(dirname(file))?.names.length ?? -1].join("\0");
  const known = loaded.get(own);
  if (known && known.key === key) return known.index;
  const index = indexFor(sessionId, file, records, links, since);
  loaded.set(own, { key, index });
  return index;
}

function indexFor(sessionId: string, file: string, records: ClaudeRecord[], links: Map<string, string>, since: string | null): ClaudeIndex {
  const chain = activeChain(records, links);
  const starts = new Set([chain[0]?.uuid, ...chain.filter(isBoundary).map((record) => record.uuid)].filter((uuid): uuid is string => typeof uuid === "string"));
  return buildClaudeIndex(sessionId, records, file, { links, chain, eras: { family: familyOf(file, starts), since } });
}
