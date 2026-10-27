// Purpose: v0.4 — the engine's rewrite of a Claude Code request (Anthropic Messages), with the same rules and words as
// rewrite.ts for Codex: an image the user unchecked becomes a placeholder (a "duplicate" one when the same content is
// still sent), every image still sent gets an "included" label once anything is left out, and a context management
// note explains the placeholders. Automatic selection (v0.3) leaves out earlier turns' images that are not pinned;
// copies the model fetched are sent in their own turn only.
// What changes for Claude: images sit in user messages (pasted) and inside tool_result blocks; the note is a
// mid-conversation system message, which Anthropic allows only right after a user message, so it goes right after
// the message holding the first omitted image instead of before its turn (docs/v0.4/plan.md, D04-03). Everything else
// — thinking blocks included — is passed on unchanged.
// Matching to the index (claude-index.ts): an image inside a tool result by its tool_use_id; pasted images by
// content, a request message to the transcript record(s) holding the same images in the same order.
// v0.8: the feature line note follows the user's own message of the turn holding the first image (a system message, as
// the other notes, but never right after a tool result), and every image sent gets its id, also the ones new in this
// turn; placeholders carry what the model noted.
// Input: the request's messages, the session's index, the keys to leave out. Output: new messages plus a report.

import type { ClaudeIndex, ClaudeImage } from "./claude-index.ts";
import { imageDigest, type ImageDigest, type ImageKind } from "./images.ts";
import type { Lang } from "./language.ts";
import { autoPlaceholder, claudeNote, compactedNote, copyNote, duplicatePlaceholder, featureNote, hereNote, includedLabel, newImageWord, plainPlaceholder, type Described, type RewriteReport } from "./rewrite.ts";

type Json = Record<string, any>;
// msg: the message; part: the block in its content; sub: for an image in a tool result, its position in that result.
export type RequestImage = ImageDigest & { msg: number; part: number; sub: number | null; key: string | null; kind: ImageKind; block: Json };

const sameList = (a: string[], b: string[]) => a.length === b.length && a.every((value, i) => value === b[i]);

// Every image of the request, with the index key it matches (null: not in the index, e.g. pasted in this turn).
export function findRequestImages(messages: Json[], index: Pick<ClaudeIndex, "uploads">): RequestImage[] {
  const found: RequestImage[] = [];
  const pastedBy = new Map<number, RequestImage[]>();
  messages.forEach((message, msg) => {
    if (message?.role !== "user" || !Array.isArray(message.content)) return;
    const perTool = new Map<string, number>();
    message.content.forEach((block: Json, part: number) => {
      if (block?.type === "image" && typeof block.source?.data === "string") {
        const image: RequestImage = { ...imageDigest(block, block.source.data, block.source.media_type ?? null), msg, part, sub: null, key: null, kind: "upload", block };
        found.push(image);
        pastedBy.set(msg, [...(pastedBy.get(msg) ?? []), image]);
      }
      if (block?.type === "tool_result" && Array.isArray(block.content)) {
        block.content.forEach((inner: Json, sub: number) => {
          if (inner?.type !== "image" || typeof inner.source?.data !== "string") return;
          const id = String(block.tool_use_id ?? "");
          const m = perTool.get(id) ?? 0;
          perTool.set(id, m + 1);
          found.push({ ...imageDigest(inner, inner.source.data, inner.source.media_type ?? null), msg, part, sub, key: `tool:${id}#${m}`, kind: "tool", block: inner });
        });
      }
    });
  });
  // Pasted images: each message, in order, to the next record(s) after the last match holding the same images in the
  // same order (Claude Code may join consecutive records into one message). Records before the latest compaction are
  // looked at only when nothing later matches.
  const uploads = index.uploads;
  const used = new Set<number>();
  let next = uploads.findIndex((upload) => !upload.compacted);
  if (next < 0) next = uploads.length;
  const matchAt = (start: number, ids: string[]): number[] | null => {
    const taken: number[] = [];
    let at = 0;
    for (let i = start; i < uploads.length && at < ids.length; i++) {
      if (used.has(i)) return null;
      const part = uploads[i].contentIds;
      if (!sameList(part, ids.slice(at, at + part.length))) return null;
      taken.push(i);
      at += part.length;
    }
    return at === ids.length ? taken : null;
  };
  for (const [, images] of [...pastedBy].sort((a, b) => a[0] - b[0])) {
    const ids = images.map((image) => image.contentId);
    let taken: number[] | null = null;
    for (let start = next; start < uploads.length && !taken; start++) taken = matchAt(start, ids);
    for (let start = 0; start < next && !taken; start++) taken = matchAt(start, ids);
    if (!taken) continue;
    let position = 0;
    for (const i of taken) {
      uploads[i].contentIds.forEach((_, n) => { images[position++].key = `${uploads[i].uuid}#${n}`; });
      used.add(i);
    }
    next = Math.max(next, taken.at(-1)! + 1);
  }
  return found;
}

export type ClaudeRewriteOptions = {
  lang?: Lang;
  // Copies the model fetched in an earlier turn (key → the id they copy): left out in either mode.
  copies?: Map<string, string>;
  // Automatic selection: its wording; placeholders point to, and labels mark, only earlier turns' (pinned) images.
  auto?: { currentTurn: number };
  // v0.5: the full note is given before these messages already (after a compaction summary holding placeholders).
  noted?: boolean;
  // v0.8: the feature line note and ids on this turn's new images too (rewrite.ts).
  features?: boolean;
};

export function rewriteMessages(
  messages: Json[],
  index: Pick<ClaudeIndex, "uploads" | "byKey"> & Partial<Pick<ClaudeIndex, "notes" | "copies">>,
  leaveOut: Set<string>,
  pixelHash: (image: RequestImage) => string | null,
  options: ClaudeRewriteOptions = {},
): { messages: Json[]; report: RewriteReport } {
  const { lang = "zh", copies = new Map<string, string>(), auto, noted = false, features = false } = options;
  const refs = findRequestImages(messages, index);
  const describe = (ref: RequestImage): ClaudeImage | undefined => {
    const image = ref.key ? index.byKey.get(ref.key) : undefined;
    const notes = image ? index.notes?.get(image.id) : undefined;
    return image && notes ? { ...image, notes } : image;
  };
  const report: RewriteReport = { images: refs.length, replaced: [], locked: [], sentContentIds: [], copies: [] };
  const copied = refs.filter((ref) => ref.key !== null && copies.has(ref.key));
  const drop = refs.filter((ref) => ref.key !== null && !copies.has(ref.key) && leaveOut.has(ref.key) && describe(ref));
  const sent = refs.filter((ref) => !drop.includes(ref) && !copied.includes(ref));
  report.sentContentIds = sent.map((ref) => ref.contentId);
  // A copy the model fetched this turn is known as one, not as an image.
  const unknown = refs.filter((ref) => !copied.includes(ref) && !(ref.key && index.copies?.has(ref.key)) && !describe(ref)).length;
  if (unknown) report.unknown = unknown;
  // v0.8: the first image the index knows; the feature line note follows its message.
  const first = features ? refs.find((ref) => describe(ref)) : undefined;
  if (!drop.length && !copied.length && !first) return { messages, report };
  const earlier = (ref: RequestImage) => { const turn = describe(ref)?.turn; return auto !== undefined && turn !== null && turn !== undefined && turn < auto.currentTurn; };
  const lasting = auto ? sent.filter(earlier) : sent;
  const same = (a: RequestImage, b: RequestImage) => {
    if (a.contentId === b.contentId) return true;
    if (a.width !== b.width || a.height !== b.height) return false;
    const pixels = pixelHash(a);
    return pixels !== null && pixels === pixelHash(b);
  };
  // Edits per content array: the message's own content ("3"), or a tool result's ("3:1"). Each puts text blocks at
  // `at`, in place of `remove` blocks (none for a label).
  type Edit = { at: number; remove: number; blocks: Json[] };
  const edits = new Map<string, Edit[]>();
  const edit = (ref: RequestImage, remove: number, text: string, before = false) => {
    const where = ref.sub === null ? `${ref.msg}` : `${ref.msg}:${ref.part}`;
    const at = ref.sub === null ? ref.part : ref.sub;
    // A placeholder keeps the cache breakpoint the image carried, so Claude Code's caching stays where it put it.
    const carried = !before && ref.block.cache_control ? { cache_control: ref.block.cache_control } : {};
    edits.set(where, [...(edits.get(where) ?? []), { at, remove, blocks: [{ type: "text", text, ...carried }] }]);
  };
  // The messages holding plain placeholders, each with its omitted images, for the notes that follow them.
  const plainBy = new Map<number, Described[]>();
  for (const ref of drop) {
    const image = describe(ref)!;
    const copy = lasting.find((other) => same(other, ref));
    const copyImage: Described | null = copy ? describe(copy) ?? { id: newImageWord(lang), name: null, label: null, kind: copy.kind, turn: null, width: copy.width, height: copy.height } : null;
    const text = copyImage ? duplicatePlaceholder(image, copyImage, lang) : auto ? autoPlaceholder(image, lang) : plainPlaceholder(image, lang);
    if (!copyImage) plainBy.set(ref.msg, [...(plainBy.get(ref.msg) ?? []), image]);
    report.replaced.push({ id: image.id, key: ref.key!, kind: image.kind, mode: copyImage ? "duplicate" : "plain", sameAs: copyImage?.id ?? null, base64Chars: ref.base64Chars });
    edit(ref, 1, text);
  }
  for (const ref of copied) {
    edit(ref, 1, copyNote(copies.get(ref.key!)!, lang));
    report.copies.push(copies.get(ref.key!)!);
  }
  // v0.1-25: once anything is left out, every image still sent says which id it is. v0.8: with feature lines, this
  // turn's new images too.
  for (const ref of features ? sent : lasting) {
    const image = describe(ref);
    if (!image) continue;
    edit(ref, 0, includedLabel(image, lang), true);
    report.labeled = (report.labeled ?? 0) + 1;
  }
  const apply = (blocks: Json[], list: Edit[]) => {
    const out = [...blocks];
    // Later positions first; at one position, a replacement before the label that goes in front of it.
    for (const { at, remove, blocks: added } of [...list].sort((a, b) => b.at - a.at || b.remove - a.remove)) out.splice(at, remove, ...added);
    return out;
  };
  const next = messages.map((message, msg) => {
    const own = edits.get(`${msg}`);
    const inner = [...edits.keys()].filter((where) => where.startsWith(`${msg}:`));
    if (!own && !inner.length) return message;
    let content: Json[] = [...message.content];
    for (const where of inner) {
      const part = Number(where.split(":")[1]);
      content[part] = { ...content[part], content: apply(content[part].content, edits.get(where)!) };
    }
    if (own) content = apply(content, own);
    return { ...message, content };
  });
  // Only plain placeholders need a note (a duplicate's content is still in view). Each message holding one is followed
  // by a short note naming its omitted images, and the first of them also by the full note: Claude does not believe
  // what a tool result says about itself, and a note far from the placeholder was not enough (desktop tests,
  // 2026-10-09). Later messages first, so the earlier positions stay as they are. v0.5: after a compaction summary
  // holding placeholders, the full note is there already (`noted`).
  const holding = [...plainBy.keys()].sort((a, b) => a - b);
  for (const msg of [...holding].reverse()) {
    noteAfter(next, msg, `${msg === holding[0] && !noted ? `${claudeNote(lang, auto !== undefined)}\n` : ""}${hereNote(plainBy.get(msg)!, lang, auto !== undefined)}`);
  }
  if (holding.length && !noted) report.noteAt = holding[0] + 1;
  // v0.8: after the user's own message of the turn holding the first image, at or before the others; joined with a
  // note already there.
  if (first) {
    const at = promptOf(messages, first.msg);
    const added = noteAfter(next, at, featureNote(lang));
    report.featureAt = at + 1;
    if (added && report.noteAt !== undefined && report.noteAt > at) report.noteAt += 1;
  }
  return { messages: next, report };
}

// The user's own message of the turn holding message `msg` (its prompt, or the summary after a compaction). Sonnet 5.5
// and Haiku 5.5 may take a system message right after a tool result for part of it and ignore it (Anthropic's page on
// mid-conversation system messages; desktop test 2026-10-19: Haiku called the feature line note something the Read
// tool returned, did not follow it and told the user). Without such a message right before an assistant's, `msg`.
const holdsToolResult = (message: Json) => Array.isArray(message?.content) && message.content.some((block: Json) => block?.type === "tool_result");
function promptOf(messages: Json[], msg: number): number {
  for (let at = msg; at >= 0; at--) {
    const message = messages[at];
    if (message?.role !== "user" || holdsToolResult(message)) continue;
    return messages[at + 1]?.role === "user" ? msg : at;
  }
  return msg;
}

// A note goes right after a user message, the only place Anthropic allows a system message; when Claude Code put a
// system message there already, the note joins it, since two may not follow each other. True when a message was added.
function noteAfter(messages: Json[], msg: number, text: string): boolean {
  const after = messages[msg + 1];
  if (after?.role === "system") {
    const content = typeof after.content === "string" ? [{ type: "text", text: after.content }] : after.content;
    messages[msg + 1] = { ...after, content: [{ type: "text", text }, ...content] };
    return false;
  }
  messages.splice(msg + 1, 0, { role: "system", content: text });
  return true;
}

// v0.5: after a compaction Claude Code starts each request with the summary and sends no image from before it
// (2.1.295: the user message holding the summary as a string, then the last reply kept). The engine puts them back
// right after the summary, in their order: the ones the user keeps sending with their labels, the others as
// placeholders, as anywhere else in a request. The note follows that message, as v0.4's notes do: the model did not
// believe it inside the message (desktop test, 2026-10-12). The same selection gives the same messages, so the cached
// prefix holds. No summary in the request: nothing changes.
export type Resend = { image: Described; block: Json };
const holdsSummary = (summary: string) => (block: Json) => block?.type === "text" && block.text === summary;
export function summaryAt(messages: Json[], summary: string): number | null {
  const isSummary = holdsSummary(summary);
  const at = messages.findIndex((message) => message?.role === "user" && (message.content === summary || (Array.isArray(message.content) && message.content.some(isSummary))));
  return at < 0 ? null : at;
}
export function addCompacted(messages: Json[], summary: string, listed: Described[], resend: Resend[], options: { lang?: Lang; auto?: boolean } = {}): { messages: Json[]; at: number | null; inserted: boolean } {
  const { lang = "zh", auto = false } = options;
  const at = summaryAt(messages, summary);
  if (at === null) return { messages, at: null, inserted: false };
  const message = messages[at];
  const content: Json[] = typeof message.content === "string" ? [{ type: "text", text: message.content }] : [...message.content];
  const sent = new Map(resend.map(({ image, block }) => [image.id, block]));
  const added = listed.flatMap((image): Json[] => {
    const block = sent.get(image.id);
    if (block) return [{ type: "text", text: includedLabel(image, lang) }, block];
    return [{ type: "text", text: auto ? autoPlaceholder(image, lang) : plainPlaceholder(image, lang) }];
  });
  content.splice(content.findIndex(holdsSummary(summary)) + 1, 0, ...added);
  const next = [...messages];
  next[at] = { ...message, content };
  const inserted = noteAfter(next, at, compactedNote(listed, new Set(sent.keys()), lang, auto));
  return { messages: next, at, inserted };
}
