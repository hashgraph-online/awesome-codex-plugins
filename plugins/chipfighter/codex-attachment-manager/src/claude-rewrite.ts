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
// Input: the request's messages, the session's index, the keys to leave out. Output: new messages plus a report.

import type { ClaudeIndex, ClaudeImage } from "./claude-index.ts";
import { imageDigest, type ImageDigest, type ImageKind } from "./images.ts";
import type { Lang } from "./language.ts";
import { autoPlaceholder, claudeNote, copyNote, duplicatePlaceholder, hereNote, includedLabel, newImageWord, plainPlaceholder, type Described, type RewriteReport } from "./rewrite.ts";

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
};

export function rewriteMessages(
  messages: Json[],
  index: Pick<ClaudeIndex, "uploads" | "byKey">,
  leaveOut: Set<string>,
  pixelHash: (image: RequestImage) => string | null,
  options: ClaudeRewriteOptions = {},
): { messages: Json[]; report: RewriteReport } {
  const { lang = "zh", copies = new Map<string, string>(), auto } = options;
  const refs = findRequestImages(messages, index);
  const describe = (ref: RequestImage): ClaudeImage | undefined => (ref.key ? index.byKey.get(ref.key) : undefined);
  const report: RewriteReport = { images: refs.length, replaced: [], locked: [], sentContentIds: [], copies: [] };
  const copied = refs.filter((ref) => ref.key !== null && copies.has(ref.key));
  const drop = refs.filter((ref) => ref.key !== null && !copies.has(ref.key) && leaveOut.has(ref.key) && describe(ref));
  const sent = refs.filter((ref) => !drop.includes(ref) && !copied.includes(ref));
  report.sentContentIds = sent.map((ref) => ref.contentId);
  if (!drop.length && !copied.length) return { messages, report };
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
  // v0.1-25: once anything is left out, every image still sent says which id it is.
  for (const ref of lasting) {
    const image = describe(ref);
    if (image) edit(ref, 0, includedLabel(image, lang), true);
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
  // 2026-10-09). A note goes right after the user message, the only place Anthropic allows a system message; when
  // Claude Code put a system message there already, the note joins it, since two may not follow each other. Later
  // messages first, so the earlier positions stay as they are.
  const holding = [...plainBy.keys()].sort((a, b) => a - b);
  for (const msg of [...holding].reverse()) {
    const text = `${msg === holding[0] ? `${claudeNote(lang, auto !== undefined)}\n` : ""}${hereNote(plainBy.get(msg)!, lang, auto !== undefined)}`;
    const after = next[msg + 1];
    if (after?.role === "system") {
      const content = typeof after.content === "string" ? [{ type: "text", text: after.content }] : after.content;
      next[msg + 1] = { ...after, content: [{ type: "text", text }, ...content] };
    } else {
      next.splice(msg + 1, 0, { role: "system", content: text });
    }
  }
  if (holding.length) report.noteAt = holding[0] + 1;
  return { messages: next, report };
}
