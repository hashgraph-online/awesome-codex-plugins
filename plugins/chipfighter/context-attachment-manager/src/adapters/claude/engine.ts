// Purpose: the engine's part for Claude Code (v0.11: split from proxy.ts, docs/v0.11/plan.md): which session a request
// belongs to (Claude Code's own headers), whether its requests are rewritten, and the rewrite of an Anthropic Messages
// body with the session's transcript and selection: what to send, and what next when Anthropic refuses the thinking
// after the changed history.
// v0.4: Claude Code. v0.5: images put back after a compaction. v0.8: feature lines. v0.10: cache marks, late images.
// Input: request headers and bodies, the session's transcript and selection. Output: attempts to send and a report.

import type { IncomingHttpHeaders } from "node:http";
import { decodeBody, encodeBody, hasUnsafeInteger } from "../../core/engine/transport.ts";
import { claudeSelectionDirOf } from "../../core/paths.ts";
import type { Lang } from "../../core/lang.ts";
import { currentLang } from "../../core/language.ts";
import { claudeSelection } from "./selection.ts";
import { stableIdsSince } from "../../core/selection.ts";
import { autoChoice, earlierCopies } from "../../core/session.ts";
import { pixelHashOfData } from "../../core/pixels.ts";
import { keepCacheRead, marksOutside, sentPrefixOf, type SentPrefix } from "../protocols/anthropic-messages/cache.ts";
import { addCompacted, summaryAt, type RequestImage, type Resend } from "../protocols/anthropic-messages/rewrite.ts";
import { chainOf, fitThinking, type ThinkingRecord } from "../protocols/anthropic-messages/thinking.ts";
import { claudeHome, claudeImageData, claudeStartedAt, loadClaudeIndex, type ClaudeIndex } from "./claude-index.ts";
import { findRequestImages, rewriteMessages } from "./claude-rewrite.ts";

type Json = Record<string, any>;
// v0.4: Claude Code's API host.
export const CLAUDE_HOST = "api.anthropic.com";

// v0.4: which Claude Code session a request belongs to, and whether a subagent's loop sent it (its own conversation).
export function claudeIdentity(headers: IncomingHttpHeaders): { sessionId: string | null; agentId: string | null } {
  const one = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) || null;
  return { sessionId: one(headers["x-claude-code-session-id"]), agentId: one(headers["x-claude-code-agent-id"]) };
}

// v0.4: the requests the panel's "last request" line is about: the session's conversation as the model works on it,
// Claude Code's main loop, which always carries its tools. Claude Desktop also sends side requests in the session (a
// status summary while the user is away, auto mode's safety check): no tools and none of the conversation's images.
// They are rewritten like the rest; only the line leaves them out (2026-10-10: it said "nothing replaced" after a turn
// whose four images had all been left out).
export const claudeConversationRequest = (details: Json): boolean => details.kind === "messages" && details.tools > 0;

// v0.4: a Claude Code session's requests are rewritten once something is unchecked there, or automatic selection was
// used (copies the model fetched may be in its history from then on). v0.5: or once it was compacted with images
// before the compaction, which the user may keep sending. v0.8: or once it has any image, for the feature line note
// and the ids (Claude Code sends the whole history every time, so this costs no upload; docs/v0.8/plan.md).
export function claudeNeedsRewrite(sessionId: string | null, dir = claudeSelectionDirOf(), home = claudeHome()): boolean {
  if (!sessionId) return false;
  let index: ClaudeIndex | null = null;
  try { index = loadClaudeIndex(sessionId, home, stableIdsSince(dir)); } catch { /* the selection still decides */ }
  try {
    const selection = claudeSelection(sessionId, dir, index ? claudeStartedAt(index) : null, index?.previous ?? []);
    if (Object.keys(selection.unchecked).length > 0 || selection.autoSince) return true;
  } catch { /* the transcript still decides */ }
  return !!index?.images.length;
}

// The images a Claude Code request carried, by index key, with the base64 characters each took (the panel's
// baseline); images not in the transcript yet are left out.
export function claudeImageSizes(messages: Json[], index: ClaudeIndex): Record<string, number> {
  return Object.fromEntries(findRequestImages(messages, index).filter((ref) => ref.key).map((ref) => [ref.key!, ref.base64Chars]));
}

// Anthropic refuses a request whose earlier content changed under the thinking that followed it (accounts created from
// 2026-08-31, or a request that asks for it): docs/v0.4/plan.md §2.2. The engine then sends the original instead.
export function thinkingRejected(status: number, body: string): boolean {
  return status === 400 && /thinking/i.test(body) && /signature|bound to a different conversation|prefix/i.test(body);
}

// v0.4: what to send for a Claude Code request, each next one when Anthropic refuses the thinking after the changed
// history (thinkingRejected): the rewrite with all its thinking (an account that lets it through); the rewrite without
// the thinking that no longer fits (anthropic-messages/thinking.ts), first once the account is known to refuse it; the rewrite
// without any thinking, always accepted; the original as Claude Code built it. history/sent: the chains to remember
// once the attempt goes through (null: not the session's conversation); made: the histories its thinking was made
// after; sure: the record says all its thinking fits, so a refusal means the record misses what went out.
// prefix: where its cache marks are, to remember once it is sent (anthropic-messages/cache.ts).
export type ClaudeAttempt = { body: Buffer; report: Json; history: string | null; sent: string | null; made: string[]; sure: boolean; prefix?: SentPrefix };
// v0.10: how long a request waits for its newest images to reach the transcript (a long-task eval caught 3 of a turn's
// images going out without ids, the transcript written a moment after the request; the user's logs had 119 such of
// 8904 requests). A request whose images never reach it waits the whole time once.
export const LATE_WAIT_MS = 1500;
export const LATE_STEP_MS = 100;

// v0.4: the same rules as rewriteBody, for a Claude Code request (Anthropic Messages, anthropic-messages/rewrite.ts). The current
// turn is the transcript's latest prompt: Claude Code writes it before it sends the request.
// CAM_EXPERIMENT_BLOCK_BINDING (experiments only, docs/v0.4/tasks.md T04-01): asks Anthropic to check thinking with
// that prefix_mismatch_behavior, as for an account created from 2026-08-31; the report names the beta header to add.
// v0.11: lang, the language of the text for the model; the engine passes the one the core and Codex's setting choose.
export function rewriteClaudeBody(original: Buffer, encoding: string | undefined, sessionId: string, dir = claudeSelectionDirOf(), home = claudeHome(), env = process.env, thinking: ThinkingRecord | null = null, previous: SentPrefix[] = [], lang: Lang = currentLang()): { body: Buffer; report: Json; attempts: ClaudeAttempt[]; prefix?: SentPrefix } {
  const asIs = (report: Json) => ({ body: original, report, attempts: [] });
  const decoded = decodeBody(original, encoding);
  if (!decoded) return asIs({ skipped: "undecodable body" });
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return asIs({ skipped: "unparsable body" }); }
  if (!Array.isArray(json.messages)) return asIs({ skipped: "no messages array" });
  if (hasUnsafeInteger(text)) return asIs({ skipped: "integer beyond 2^53 would change when re-serialized" });
  let index: ClaudeIndex;
  try { index = loadClaudeIndex(sessionId, home, stableIdsSince(dir)); } catch (error) { return asIs({ skipped: `thread index: ${String(error)}` }); }
  const selection = claudeSelection(sessionId, dir, claudeStartedAt(index), index.previous);
  const current = index.turns;
  const copies = earlierCopies(index, current);
  // v0.3: automatic selection (core/session.ts); v0.10: images of an interrupted turn without a feature line yet are
  // sent once more.
  const chosen = selection.auto ? autoChoice(index, current, selection.pinned ?? {}, true) : null;
  const leaveOut = chosen?.leaveOut ?? new Set(Object.keys(selection.unchecked));
  const awaiting = chosen?.awaiting ?? new Set<string>();
  const pixels = (ref: RequestImage) => (ref.key ? index.byKey.get(ref.key)?.pixelSha256 : undefined) ?? pixelHashOfData(ref, ref.block.source.data);
  // v0.5: after a compaction, the images from before it go back right after the summary (anthropic-messages/rewrite.ts): the ones
  // the user keeps sending (checked, or pinned with automatic selection) read from the transcript, the others as
  // placeholders. With any of those, the full note follows the summary, and later messages get only their short notes.
  // v0.8: each with what the model noted about it, for its placeholder.
  const compactedImages = index.images.filter((image) => image.compacted).map((image) => {
    // v0.10: as they stood at the compaction, so the list stays the same until the next one (claude-index.ts).
    const notes = index.compactedNotes.get(image.id);
    return notes ? { ...image, notes } : image;
  });
  const summaryIn = index.summary && compactedImages.length ? summaryAt(json.messages, index.summary) : null;
  const resend: Resend[] = summaryIn === null ? [] : compactedImages.filter((image) => !leaveOut.has(image.key)).flatMap((image) => {
    const data = claudeImageData(index, image);
    return data && image.mime ? [{ image, block: { type: "image", source: { type: "base64", media_type: image.mime, data } } }] : [];
  });
  const compactedOut = summaryIn !== null && resend.length < compactedImages.length;
  // v0.8: feature lines in every main conversation (a subagent's requests do not come here).
  const rewrote = rewriteMessages(json.messages, index, leaveOut, pixels, { lang, copies, noted: compactedOut, features: true, awaiting, ...(selection.auto ? { auto: { currentTurn: current } } : {}) });
  const report = rewrote.report;
  let messages = rewrote.messages;
  let compacted: Json | null = null;
  if (summaryIn !== null) {
    const added = addCompacted(messages, index.summary!, compactedImages, resend, { lang, auto: !!selection.auto });
    if (added.at !== null) {
      messages = added.messages;
      // The note's place: after the summary when it holds placeholders; a later one moves down with a message added.
      if (compactedOut) report.noteAt = added.at + 1;
      else if (added.inserted && report.noteAt !== undefined && report.noteAt > added.at) report.noteAt += 1;
      if (added.inserted && report.featureAt !== undefined && report.featureAt > added.at) report.featureAt += 1;
      compacted = { at: added.at, listed: compactedImages.length, resent: resend.map(({ image }) => image.id) };
    }
  }
  const summary: Json = {
    images: report.images,
    replaced: report.replaced.map(({ key: _key, ...rest }) => rest),
    locked: report.locked,
    sentImageHashes: report.sentContentIds.map((id) => id.slice(0, 16)),
    thinkingBlocks: json.messages.reduce((sum: number, message: Json) => sum + (Array.isArray(message?.content) ? message.content.filter((block: Json) => block?.type === "thinking" || block?.type === "redacted_thinking").length : 0), 0),
    ...(report.noteAt !== undefined ? { noteAt: report.noteAt } : {}),
    ...(selection.auto ? { auto: true } : {}),
    ...(report.copies.length ? { copies: report.copies } : {}),
    ...(compacted ? { compacted } : {}),
    ...(report.featureAt !== undefined ? { featureAt: report.featureAt, labeled: report.labeled ?? 0 } : {}),
    ...(report.unknown ? { unknown: report.unknown } : {}),
    ...(report.late ? { late: report.late } : {}),
  };
  const changed = report.replaced.length > 0 || report.copies.length > 0 || compacted !== null || report.featureAt !== undefined;
  // Once the engine has sent the session a changed history, thinking made after it may be in every later request, even
  // with nothing left out now (an image checked again).
  // Side requests (no tools: the desktop's status summary, auto mode's check) are not the conversation.
  const conversation = Array.isArray(json.tools) && json.tools.length > 0;
  if (!changed && !thinking?.edited) return { body: original, report: summary, attempts: [], ...(conversation ? { prefix: sentPrefixOf(json.messages) } : {}) };
  const rewritten = changed ? messages : json.messages;
  const fit = thinking ? fitThinking(json.messages, rewritten, thinking) : null;
  const history = fit && conversation ? fit.history : null;
  const experiment = env.CAM_EXPERIMENT_BLOCK_BINDING?.trim();
  // v0.10: the cache marks placed so this request reads what the ones before wrote, and the next one can read this
  // one after the images still sent as originals are left out (anthropic-messages/cache.ts): with automatic selection, the first
  // such image that is not pinned.
  const pinnedNow = selection.pinned ?? {};
  const volatileIn = (list: Json[]) => {
    const ref = selection.auto ? findRequestImages(list, index).find((found) => !(found.key && pinnedNow[found.key])) : undefined;
    return ref ? { message: ref.msg, block: ref.part } : null;
  };
  const encode = (list: Json[], extra: Json) => {
    const placed = conversation ? keepCacheRead(list, previous, marksOutside(json), volatileIn(list)) : { messages: list, marks: null };
    const out: Json = { ...json, messages: placed.messages };
    const asked = experiment && json.thinking && typeof json.thinking === "object";
    if (asked) out.thinking = { ...json.thinking, block_binding: { prefix_mismatch_behavior: experiment } };
    const next = Buffer.from(JSON.stringify(out), "utf8");
    const body = encodeBody(next, encoding);
    return { body, report: { ...summary, ...extra, ...(placed.marks ? { cacheMarks: placed.marks } : {}), ...(asked ? { experiment: { blockBinding: experiment, beta: "thinking-binding-controls-2026-08-01" } } : {}), decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length }, ...(conversation ? { prefix: sentPrefixOf(placed.messages) } : {}) };
  };
  const attempts: ClaudeAttempt[] = [];
  const made = fit?.made ?? [];
  const add = (list: Json[], extra: Json, sent: string, sure: boolean) => attempts.push({ ...encode(list, extra), history, sent: history ? sent : null, made, sure });
  const asBuilt = (extra: Json, sure: boolean) => attempts.push({ body: original, report: { ...summary, ...extra }, history, sent: history, made, sure, ...(conversation ? { prefix: sentPrefixOf(json.messages) } : {}) });
  if (!thinking?.strict) {
    if (changed) add(rewritten, {}, chainOf(rewritten), fit?.left === 0);
    else asBuilt({}, fit!.left === 0);
  }
  if (fit && (thinking!.strict || fit.left)) add(fit.messages, { thinking: { kept: fit.kept, left: fit.left }, ...(thinking!.strict ? {} : { retry: "thinking-signature" }) }, fit.sent, true);
  if (fit?.kept) {
    const bare = fitThinking(json.messages, rewritten, thinking!, false);
    add(bare.messages, { thinking: { kept: 0, left: bare.left }, retry: "thinking-signature" }, bare.sent, false);
  }
  if (changed || thinking?.strict) asBuilt(changed ? { fallback: "thinking-signature" } : {}, false);
  return { body: attempts[0].body, report: attempts[0].report, attempts };
}
