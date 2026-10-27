// Purpose: v0.4 — keep the thinking in a Claude Code request valid when the engine has changed the history before it.
// Anthropic binds each thinking block to everything before it in the conversation (Fable 5.1, Opus 5.5, Sonnet 5.5,
// Haiku 5.5); accounts created from 2026-08-31 refuse a request whose thinking no longer matches, older ones let it
// through (docs/v0.4/plan.md §2). Thinking may be left out, as long as each block kept comes after exactly what it was
// made after. So once the engine has sent a session a changed history, it remembers what it sent for each history (as
// hash chains), and keeps a thinking block only when what comes before it now is what was sent when it was made. A
// block made after a history it has no entry for is left out: the record may be incomplete (a lost file, old entries).
// Input: a request's messages as Claude Code built them and as the engine will send them; the session's record.
// Output: the messages without the thinking that no longer fits, counts, the chains to remember;
// <data dir>/claude/thinking/<session>.json (flags and hashes; never content).

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { claudeThinkingDirOf } from "./paths.ts";

type Json = Record<string, any>;
const THINKING = new Set(["thinking", "redacted_thinking"]);
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
// The latest histories only: older thinking without an entry is left out.
const KEEP = 2000;

// What Anthropic compares: values, not JSON formatting or key order; content given as a string is the text block it
// stands for (Claude Code sends its trailing system message as a block with a cache breakpoint, and as a string in the
// requests after); cache breakpoints move from request to request.
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  const out: Json = {};
  for (const key of Object.keys(value).sort()) {
    const field = (value as Json)[key];
    if (key === "cache_control") continue;
    out[key] = key === "content" && typeof field === "string" ? [{ text: field, type: "text" }] : canonical(field);
  }
  return out;
}
export const link = (previous: string, message: Json): string =>
  createHash("sha256").update(previous).update("\n").update(JSON.stringify(canonical(message)) ?? "").digest("hex");
export const chainOf = (messages: Json[]): string => messages.reduce((chain: string, message) => link(chain, message), "");

const thinkingIn = (message: Json): number =>
  message?.role === "assistant" && Array.isArray(message.content) ? message.content.filter((block: Json) => THINKING.has(block?.type)).length : 0;

// edited: the engine has sent this session a changed history; until then every history went out as Claude Code built
// it. strict: Anthropic refused this session's thinking after a changed history (the account checks it).
export type ThinkingRecord = { edited: boolean; strict: boolean; sent: Map<string, string> };
export const newThinkingRecord = (): ThinkingRecord => ({ edited: false, strict: false, sent: new Map() });

// made: the histories the request's thinking was made after.
export type ThinkingFit = { messages: Json[]; kept: number; left: number; history: string; sent: string; made: string[] };

// The rewrite never adds, drops or edits an assistant message, so the n-th one of each list is the same. keep false
// leaves out all thinking, which Anthropic always accepts. An assistant message left empty goes too: Anthropic takes no
// empty message, and joins the user messages around it.
export function fitThinking(original: Json[], outgoing: Json[], record: ThinkingRecord, keep = true): ThinkingFit {
  const madeAfter: string[] = [];
  let history = "";
  for (const message of original) {
    if (message?.role === "assistant") madeAfter.push(history);
    history = link(history, message);
  }
  const sentAfter = (made: string) => (record.sent.has(made) ? record.sent.get(made) : record.edited ? null : made);
  let chain = "";
  let assistant = 0;
  let kept = 0;
  let left = 0;
  const made: string[] = [];
  const messages: Json[] = [];
  for (const message of outgoing) {
    let next: Json | null = message;
    if (message?.role === "assistant") {
      const after = madeAfter[assistant++];
      const count = thinkingIn(message);
      if (count && after !== undefined) made.push(after);
      if (count && keep && after !== undefined && sentAfter(after) === chain) kept += count;
      else if (count) {
        left += count;
        const rest = message.content.filter((block: Json) => !THINKING.has(block?.type));
        next = rest.length ? { ...message, content: rest } : null;
      }
    }
    if (!next) continue;
    chain = link(chain, next);
    messages.push(next);
  }
  return { messages, kept, left, history, sent: chain, made };
}

// What went out for a history (latest last).
export function rememberSent(record: ThinkingRecord, history: string, sent: string): void {
  record.sent.delete(history);
  record.sent.set(history, sent);
  for (const key of record.sent.keys()) {
    if (record.sent.size <= KEEP) break;
    record.sent.delete(key);
  }
}

// After a request went through: what it sent for its history. The first changed history the engine sends a session
// starts the record, with the histories its thinking so far was made after (they went out as they were). Returns
// whether the record changed.
export function recordSent(record: ThinkingRecord, history: string, sent: string, made: string[]): boolean {
  if (!record.edited && sent === history) return false;
  if (!record.edited) {
    record.edited = true;
    for (const before of made) rememberSent(record, before, before);
  }
  rememberSent(record, history, sent);
  return true;
}

export function readThinkingRecord(sessionId: string, dir = claudeThinkingDirOf()): ThinkingRecord {
  if (!SESSION_ID.test(sessionId)) return newThinkingRecord();
  const file = join(dir, `${sessionId}.json`);
  if (!existsSync(file)) return newThinkingRecord();
  try {
    const json = JSON.parse(readFileSync(file, "utf8"));
    const pairs = Array.isArray(json.sent) ? json.sent.filter((pair: unknown) => Array.isArray(pair) && pair.length === 2 && pair.every((hash) => typeof hash === "string")) : [];
    // A record is written once the engine has sent a changed history.
    return { edited: json.edited !== false, strict: json.strict === true, sent: new Map(pairs) };
  } catch {
    // Unreadable: what went out is unknown, so the thinking made so far is left out.
    return { edited: true, strict: false, sent: new Map() };
  }
}

export function writeThinkingRecord(sessionId: string, record: ThinkingRecord, dir = claudeThinkingDirOf()): void {
  if (!SESSION_ID.test(sessionId)) return;
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `${sessionId}.json`);
  writeFileSync(`${file}.tmp`, JSON.stringify({ edited: record.edited, strict: record.strict, sent: [...record.sent] }));
  renameSync(`${file}.tmp`, file);
}
