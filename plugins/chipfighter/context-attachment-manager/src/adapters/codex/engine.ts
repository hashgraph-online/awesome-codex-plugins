// Purpose: the engine's part for Codex (v0.11: split from proxy.ts, docs/v0.11/plan.md): where its requests go, which
// task and turn a request belongs to (Codex's own headers), whether the task's requests are rewritten (and so sent
// over HTTP), and the rewrite of a Responses request body with the task's index and selection.
// P2: requests of threads with unchecked images are rewritten. v0.3: automatic selection. v0.7: subagents and side
// chats. v0.8: feature lines. v0.10: images put back after a compaction. 2026-10-22: Codex logged in with an API key
// goes to api.openai.com/v1.
// Input: request headers and bodies, the thread's rollout and selection. Output: the body to send and a report.

import type { IncomingHttpHeaders } from "node:http";
import { join } from "node:path";
import { decodeBody, encodeBody, hasUnsafeInteger } from "../../core/engine/transport.ts";
import type { Described } from "../../core/words.ts";
import { currentLang } from "./language.ts";
import { effectiveSelection, sideChatSelection } from "./selection.ts";
import { selectionDir } from "../../core/selection.ts";
import { findImages, type ImageRef } from "../protocols/openai-responses/images.ts";
import { addCodexCompacted, rewriteItems } from "../protocols/openai-responses/rewrite.ts";
import { codexHome } from "./codexconfig.ts";
import { autoChoice, earlierCopies } from "../../core/session.ts";
import { imageData, loadThreadIndex, pixelHashOf, sideChatOrigin, writesNotes, type ThreadIndex } from "./thread-index.ts";

type Json = Record<string, any>;
export const UPSTREAM_HOST = "chatgpt.com";
// Where Codex logged in with an API key sends its requests without the plugin (its base URL https://api.openai.com/v1).
export const OPENAI_API_HOST = "api.openai.com";
export const CODEX_BASE = "/backend-api/codex/";

// Which task a request belongs to, from Codex's own turn metadata header.
// v0.7: and where that task came from: a side chat (a fork Codex keeps in memory only) names the task it was forked
// from, a subagent its parent (also in Codex's own header).
export type RequestIdentity = { threadId: string | null; turnId: string | null; windowId: string | null; forkedFrom: string | null; parentThreadId: string | null; subagentKind: string | null; turnTrigger: string | null };
export function requestIdentity(headers: IncomingHttpHeaders): RequestIdentity {
  let meta: Json = {};
  try { meta = JSON.parse(String(headers["x-codex-turn-metadata"] ?? "{}")); } catch { /* not JSON */ }
  const header = (name: string) => { const value = headers[name]; return (Array.isArray(value) ? value[0] : value) || null; };
  return {
    threadId: meta.thread_id ?? meta.session_id ?? null, turnId: meta.turn_id ?? null, windowId: header("x-codex-window-id"),
    forkedFrom: meta.forked_from_thread_id ?? null, parentThreadId: meta.parent_thread_id ?? header("x-codex-parent-thread-id"), subagentKind: meta.subagent_kind ?? null,
    turnTrigger: meta.turn_trigger ?? null,
  };
}

// The images a request carried and the base64 characters each took, under the same keys as the thread index.
export function imageSizesOf(input: Json[]): Record<string, number> {
  return Object.fromEntries(findImages(input).map((ref) => [ref.key, ref.base64Chars]));
}

// Whether a thread's requests go through the rewrite (and so over HTTP): something unchecked, or automatic selection
// used at some point (v0.3), since from then on the history may hold copies the model fetched, left out of later turns.
// v0.7: a side chat's, always (v0.8: the switch for subagents and side chats is gone).
export function needsRewrite(threadId: string | null, dir = selectionDir, sessionsDir = join(codexHome(), "sessions"), forkedFrom: string | null = null): boolean {
  if (!threadId) return false;
  try {
    if (sideChatOrigin(threadId, forkedFrom, sessionsDir)) return true;
    const selection = effectiveSelection(threadId, sessionsDir, dir);
    return Object.keys(selection.unchecked).length > 0 || !!selection.autoSince;
  } catch { return false; }
}

// The turn a request belongs to, as numbered in the index; a turn not written to the rollout yet comes after the last.
// Without a turn id the last one counts as current, so its images are sent rather than left out.
export function currentTurnOf(index: ThreadIndex, turnId: string | null): number {
  if (!turnId) return index.turns;
  return index.turnNumbers.get(turnId) ?? index.turns + 1;
}

// P2: replace the thread's unchecked images with placeholders. Whenever the body cannot be handled safely it is
// forwarded unchanged and the reason is logged; the report never contains conversation content.
// v0.3: with automatic selection on, the images of earlier turns that are not pinned instead; in either mode, copies
// the model fetched in an earlier turn.
// v0.7: a side chat's request carries the history of the task it came from: that task's index, with every one of its
// turns counting as earlier (sideChatSelection).
export function rewriteBody(original: Buffer, encoding: string | undefined, threadId: string, sessionsDir: string, dir = selectionDir, turnId: string | null = null, forkedFrom: string | null = null): { body: Buffer; report: Json } {
  const origin = sideChatOrigin(threadId, forkedFrom, sessionsDir);
  const side = origin ? sideChatSelection(origin, sessionsDir, dir) : null;
  const decoded = decodeBody(original, encoding);
  if (!decoded) return { body: original, report: { skipped: "undecodable body" } };
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return { body: original, report: { skipped: "unparsable body" } }; }
  if (!Array.isArray(json.input)) return { body: original, report: { skipped: "no input array" } };
  if (hasUnsafeInteger(text)) return { body: original, report: { skipped: "integer beyond 2^53 would change when re-serialized" } };
  let index: ThreadIndex;
  try { index = loadThreadIndex(sessionsDir, origin ?? threadId); } catch (error) { return { body: original, report: { skipped: `thread index: ${String(error)}` } }; }
  const selection = side ?? effectiveSelection(threadId, sessionsDir, dir);
  // v0.8: feature lines in a task's own requests, not a side chat's or a subagent's.
  const features = !origin && writesNotes(sessionsDir, threadId);
  const current = side ? index.turns + 1 : currentTurnOf(index, turnId);
  const copies = earlierCopies(index, current);
  // v0.3: automatic selection (core/session.ts); v0.10: images sent once more for their feature line, marked in their
  // labels.
  const chosen = selection.auto ? autoChoice(index, current, selection.pinned ?? {}, features) : null;
  const leaveOut = chosen?.leaveOut ?? new Set(Object.keys(selection.unchecked));
  const awaiting = chosen?.awaiting ?? new Set<string>();
  const describe = (ref: ImageRef): Described | undefined => {
    const known = index.byKey.get(ref.key);
    // v0.8: with what the model noted about it, for its placeholder.
    const notes = known ? index.notes.get(known.id) : undefined;
    if (known) return { ...known, ...(notes ? { notes } : {}), ...(awaiting.has(known.key) ? { awaiting: true } : {}) };
    const stored = selection.unchecked[ref.key];
    return stored ? { id: stored.id, name: ref.name, label: ref.label, kind: ref.kind, turn: null, width: ref.width, height: ref.height } : undefined;
  };
  const pixels = (ref: ImageRef) => index.byKey.get(ref.key)?.pixelSha256 ?? pixelHashOf(json.input, ref);
  const rewritten = rewriteItems(json.input, describe, leaveOut, pixels, { lang: currentLang(), copies, features, ...(selection.auto ? { auto: { currentTurn: current } } : {}) });
  const { report } = rewritten;
  let items = rewritten.items;
  // v0.10: after Codex compacted the task, the images its compaction did not keep (thread-index.ts), right after its
  // compaction item: pinned ones (in manual mode, checked ones) as originals, the others one line each.
  let compacted: Json | null = null;
  const dropped = features ? index.images.filter((image) => image.compacted) : [];
  if (dropped.length) {
    const inRequest = new Set(findImages(json.input).map((ref) => ref.key));
    const listed = dropped.filter((image) => !inRequest.has(image.key) && !copies.has(image.key)).map((image) => describe(image)!).filter(Boolean);
    const resend = dropped.filter((image) => !inRequest.has(image.key) && !leaveOut.has(image.key) && !copies.has(image.key)).flatMap((image) => {
      const data = index.items ? imageData(index.items, image) : null;
      return data ? [{ image: describe(image)!, url: `data:${image.mime ?? "image/png"};base64,${data}` }] : [];
    });
    const added = addCodexCompacted(items, listed, resend, { lang: currentLang(), auto: !!selection.auto });
    if (added.at !== null) {
      items = added.items;
      compacted = { at: added.at, listed: listed.length, resent: resend.map(({ image }) => image.id) };
    }
  }
  const summary: Json = {
    images: report.images,
    replaced: report.replaced.map(({ key: _key, ...rest }) => rest),
    locked: report.locked,
    sentImageHashes: report.sentContentIds.map((id) => id.slice(0, 16)),
    ...(selection.auto ? { auto: true } : {}),
    ...(report.copies.length ? { copies: report.copies } : {}),
    ...(origin ? { sideChatOf: origin } : {}),
    ...(report.featureAt !== undefined ? { featureAt: report.featureAt, labeled: report.labeled ?? 0 } : {}),
    ...(report.unknown ? { unknown: report.unknown } : {}),
    ...(compacted ? { compacted } : {}),
  };
  if (!report.replaced.length && !report.copies.length && report.featureAt === undefined && !compacted) return { body: original, report: summary };
  json.input = items;
  const next = Buffer.from(JSON.stringify(json), "utf8");
  const body = encodeBody(next, encoding);
  return { body, report: { ...summary, decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length } };
}
