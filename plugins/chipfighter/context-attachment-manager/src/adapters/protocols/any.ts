// Purpose: v0.11 — the rewrite for a platform that uses the core alone, without a panel (docs/v0.11/plan.md 3.8),
// whatever request format it speaks: the format is told by the path, the images and their turns by the format's
// translator, their ids by the session's request index (core/request-index.ts). Automatic selection is always on there:
// the images of earlier turns go out as placeholders, and the model fetches what it needs with cam_view_image; a copy
// it fetched is sent in its own turn only. Feature lines stay off: the model's record lines would show as text in a
// terminal.
// Input: the request path and body, the platform, the session its headers name (if any). Output: the body to send, a
// report, the session.

import { createHash } from "node:crypto";
import { decodeBody, encodeBody, hasUnsafeInteger } from "../../core/engine/transport.ts";
import { fetchedIdIn, type ImageDigest, type ImageKind } from "../../core/images.ts";
import type { Lang } from "../../core/lang.ts";
import type { RewriteReport } from "../../core/plan.ts";
import { pixelHashOfData } from "../../core/pixels.ts";
import { markLatest, openRequestIndex, remember, saveRequestIndex, type RequestIndex } from "../../core/request-index.ts";
import { sessionKeyOf } from "../../core/selection.ts";
import type { Described } from "../../core/words.ts";
import { imageBlocks, rewriteBlocks, type RequestImage } from "./anthropic-messages/rewrite.ts";
import { geminiContents, geminiImages, rewriteGemini, withContents, type GeminiImage } from "./gemini/rewrite.ts";
import { chatImages, rewriteChat, type ChatImage } from "./openai-chat/rewrite.ts";
import { findImages, type ImageRef } from "./openai-responses/images.ts";
import { rewriteItems } from "./openai-responses/rewrite.ts";

type Json = Record<string, any>;
export type FormatName = "openai-responses" | "anthropic-messages" | "openai-chat" | "gemini";

export function formatOf(path: string): FormatName | null {
  if (/\/chat\/completions$/.test(path)) return "openai-chat";
  if (/\/responses$/.test(path)) return "openai-responses";
  if (/\/messages$/.test(path)) return "anthropic-messages";
  if (/:(stream)?[Gg]enerateContent$/.test(path)) return "gemini";
  return null;
}

// What every format's reader gives: each image with its key, turn and data, and the first prompt (to tell sessions
// apart when the platform names none).
type AnyImage = ImageDigest & { key: string; kind: ImageKind; replaceable: boolean; turn: number; fetchedOf: string | null; data: string | null };
type Rewrite = (describe: (image: AnyImage) => Described | undefined, leaveOut: Set<string>, pixels: (image: AnyImage) => string | null, options: { lang: Lang; copies: Map<string, string>; auto: { currentTurn: number }; fetched: (image: AnyImage) => boolean }) => { body: Json; report: RewriteReport };
type Read = { images: AnyImage[]; turns: number; first: string; conversation: boolean; rewrite: Rewrite };

const hasTools = (json: Json) => (Array.isArray(json.tools) && json.tools.length > 0) || (Array.isArray(json.request?.tools) && json.request.tools.length > 0);
const DATA_URL = /^data:[^;,]+;base64,(.*)$/s;

function readRequest(format: FormatName, json: Json): Read | null {
  const conversation = hasTools(json);
  if (format === "openai-chat") {
    if (!Array.isArray(json.messages)) return null;
    const found = chatImages(json.messages);
    return { ...found, conversation, rewrite: (describe, leaveOut, pixels, options) => {
      const out = rewriteChat(json.messages, found.images, describe as (image: ChatImage) => Described | undefined, leaveOut, pixels as (image: ChatImage) => string | null, options as never);
      return { body: { ...json, messages: out.messages }, report: out.report };
    } };
  }
  if (format === "gemini") {
    const contents = geminiContents(json);
    if (!contents) return null;
    const found = geminiImages(contents);
    return { ...found, conversation, rewrite: (describe, leaveOut, pixels, options) => {
      const out = rewriteGemini(contents, found.images, describe as (image: GeminiImage) => Described | undefined, leaveOut, pixels as (image: GeminiImage) => string | null, options as never);
      return { body: withContents(json, out.contents), report: out.report };
    } };
  }
  if (format === "anthropic-messages") {
    if (!Array.isArray(json.messages)) return null;
    const messages: Json[] = json.messages;
    // A turn starts with each user message that has text and is not only tool results.
    const prompts: number[] = [];
    messages.forEach((message, msg) => {
      const content = message?.content;
      const own = typeof content === "string" ? content.trim() !== "" : Array.isArray(content) && content.some((block: Json) => block?.type === "text" && String(block.text ?? "").trim() !== "");
      if (message?.role === "user" && own && !(Array.isArray(content) && content.some((block: Json) => block?.type === "tool_result"))) prompts.push(msg);
    });
    const turnAt = (msg: number) => Math.max(prompts.filter((at) => at <= msg).length, 1);
    const refs = imageBlocks(messages).map((ref) => {
      const list: Json[] = ref.sub === null ? messages[ref.msg].content : messages[ref.msg].content[ref.part].content;
      const before = list[(ref.sub ?? ref.part) - 1];
      const fetchedOf = before?.type === "text" ? fetchedIdIn(String(before.text ?? "")) : null;
      return Object.assign(ref, { key: ref.key ?? `m${ref.msg}:p${ref.part}`, turn: turnAt(ref.msg), fetchedOf, data: String(ref.block.source.data) });
    });
    const first = prompts.length ? textOfAnthropic(messages[prompts[0]].content) : "";
    return { images: refs, turns: Math.max(prompts.length, 1), first, conversation, rewrite: (describe, leaveOut, pixels, options) => {
      const out = rewriteBlocks(messages, refs as RequestImage[], describe as (ref: RequestImage) => Described | undefined, leaveOut, pixels as (ref: RequestImage) => string | null, options as never);
      return { body: { ...json, messages: out.messages }, report: out.report };
    } };
  }
  if (!Array.isArray(json.input)) return null;
  const items: Json[] = json.input;
  const prompts = items.flatMap((item, at) => (item?.type === "message" && item.role === "user" && Array.isArray(item.content) && item.content.some((part: Json) => part?.type === "input_text" && String(part.text ?? "").trim() !== "") ? [at] : []));
  const turnAt = (at: number) => Math.max(prompts.filter((prompt) => prompt <= at).length, 1);
  const refs = findImages(items);
  const dataOf = (ref: ImageRef): string | null => {
    const item = items[ref.item];
    if (ref.part === null) return typeof item.result === "string" ? item.result : null;
    const part = (item.type === "message" ? item.content : item.output)?.[ref.part];
    const url = typeof part?.image_url === "string" ? part.image_url : "";
    return DATA_URL.exec(url)?.[1] ?? null;
  };
  const images: AnyImage[] = refs.map((ref) => ({ ...ref, turn: turnAt(ref.item), fetchedOf: ref.fetchedId, data: dataOf(ref) }));
  const byKey = new Map(images.map((image) => [image.key, image]));
  const first = prompts.length ? items[prompts[0]].content.filter((part: Json) => part?.type === "input_text").map((part: Json) => String(part.text)).join("\n") : "";
  return { images, turns: Math.max(prompts.length, 1), first, conversation, rewrite: (describe, leaveOut, pixels, options) => {
    // The translator finds the images again; the same keys name them.
    const out = rewriteItems(items, (ref) => { const image = byKey.get(ref.key); return image ? describe(image) : undefined; }, leaveOut, (ref) => { const image = byKey.get(ref.key); return image ? pixels(image) : null; }, { lang: options.lang, copies: options.copies, auto: options.auto });
    return { body: { ...json, input: out.items }, report: out.report };
  } };
}

const textOfAnthropic = (content: unknown): string => (typeof content === "string" ? content : Array.isArray(content) ? content.filter((block: Json) => block?.type === "text").map((block: Json) => String(block.text)).join("\n") : "");

// The session a request belongs to: the one its headers name, else its first prompt (the same first prompt on the same
// platform counts as the same session; ids go by content anyway).
export function sessionOfRequest(platform: string, named: string | null, first: string): string | null {
  if (named) return sessionKeyOf(`${platform}\n${named}`);
  if (!first.trim()) return null;
  return createHash("sha256").update(`${platform}\nfirst prompt\n${first}`).digest("hex").slice(0, 32);
}

export type PlatformRewrite = { body: Buffer; report: Json; session: string | null };

export function rewritePlatformRequest(platform: string, path: string, original: Buffer, encoding: string | undefined, named: string | null, root: string, lang: Lang): PlatformRewrite {
  const asIs = (report: Json, session: string | null = null): PlatformRewrite => ({ body: original, report, session });
  const format = formatOf(path);
  if (!format) return asIs({ skipped: "not a model request" });
  const decoded = decodeBody(original, encoding);
  if (!decoded) return asIs({ skipped: "undecodable body" });
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return asIs({ skipped: "unparsable body" }); }
  if (hasUnsafeInteger(text)) return asIs({ skipped: "integer beyond 2^53 would change when re-serialized" });
  const read = readRequest(format, json);
  if (!read) return asIs({ skipped: `no ${format} history` });
  const session = sessionOfRequest(platform, named, read.first);
  if (!session) return asIs({ skipped: "no session" });
  let index: RequestIndex;
  try { index = openRequestIndex(platform, session, root); } catch (error) { return asIs({ skipped: `request index: ${String(error)}` }, session); }
  const current = read.turns;
  const ids = new Map<string, Described>();
  for (const image of read.images) {
    if (image.fetchedOf || image.data === null) continue;
    const seen = remember(index, image, image.data, image.turn, root);
    ids.set(image.key, { id: seen.id, name: null, label: null, kind: image.kind, turn: image.turn, width: image.width, height: image.height });
  }
  try { saveRequestIndex(index, root); } catch { /* the ids are given again next time */ }
  if (read.conversation) { try { markLatest(platform, session, root); } catch { /* a fetch then finds the session before */ } }
  const copies = new Map(read.images.filter((image) => image.fetchedOf && image.turn < current).map((image) => [image.key, image.fetchedOf!]));
  const leaveOut = new Set(read.images.filter((image) => image.replaceable && !image.fetchedOf && image.turn < current && ids.has(image.key)).map((image) => image.key));
  const out = read.rewrite((image) => ids.get(image.key), leaveOut, (image) => (image.data === null ? null : pixelHashOfData(image, image.data)), { lang, copies, auto: { currentTurn: current }, fetched: (image) => !!image.fetchedOf });
  const { report } = out;
  const summary: Json = { format, auto: true, images: report.images, replaced: report.replaced.map(({ key: _key, ...rest }) => rest), sentImageHashes: report.sentContentIds.map((id) => id.slice(0, 16)), ...(report.copies.length ? { copies: report.copies } : {}) };
  if (!report.replaced.length && !report.copies.length) return asIs(summary, session);
  const next = Buffer.from(JSON.stringify(out.body), "utf8");
  const body = encodeBody(next, encoding);
  return { body, report: { ...summary, decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length }, session };
}
