// Purpose: v0.4 — the rewrite of an Anthropic Messages request (Claude Code): the plan of the core (core/plan.ts) put
// into the messages, with the same rules and words as for Codex.
// What is particular to this format: images sit in user messages and inside tool_result blocks; a placeholder keeps the
// cache breakpoint the image carried; the notes are mid-conversation system messages, which Anthropic allows only
// right after a user message (joined with one already there), so the note follows the message holding the omitted
// images instead of going before their turn (docs/v0.4/plan.md, D04-03). Everything else — thinking blocks included —
// is passed on unchanged.
// v0.8: the feature line note follows the user's own message of the turn holding the first image (never right after a
// tool result). v0.5: after a compaction, the images from before it go back right after the summary.
// v0.11: split from claude-rewrite.ts (docs/v0.11/plan.md): which index key a pasted image matches is the platform's
// business (adapters/claude/claude-rewrite.ts); an image in a tool result is keyed by its tool_use_id here.
// Input: the request's messages, its images with their keys, a lookup into the index. Output: new messages and a report.

import { imageDigest, type ImageDigest, type ImageKind } from "../../../core/images.ts";
import type { Lang } from "../../../core/lang.ts";
import { planRewrite, type PlanOptions, type RewriteReport } from "../../../core/plan.ts";
import { claudeNote, compactedNote, compactList, featureNote, hereNote, includedLabel, type Described } from "../../../core/words.ts";

type Json = Record<string, any>;
// msg: the message; part: the block in its content; sub: for an image in a tool result, its position in that result.
export type RequestImage = ImageDigest & { msg: number; part: number; sub: number | null; key: string | null; kind: ImageKind; name: null; label: null; replaceable: true; block: Json };

// Every image of the request in order: pasted ones without a key (the platform matches them to its records), the ones
// in a tool result keyed `tool:<tool_use_id>#<n>`.
export function imageBlocks(messages: Json[]): RequestImage[] {
  const found: RequestImage[] = [];
  const own = { name: null, label: null, replaceable: true } as const;
  messages.forEach((message, msg) => {
    if (message?.role !== "user" || !Array.isArray(message.content)) return;
    const perTool = new Map<string, number>();
    message.content.forEach((block: Json, part: number) => {
      if (block?.type === "image" && typeof block.source?.data === "string") {
        found.push({ ...imageDigest(block, block.source.data, block.source.media_type ?? null), msg, part, sub: null, key: null, kind: "upload", ...own, block });
      }
      if (block?.type === "tool_result" && Array.isArray(block.content)) {
        block.content.forEach((inner: Json, sub: number) => {
          if (inner?.type !== "image" || typeof inner.source?.data !== "string") return;
          const id = String(block.tool_use_id ?? "");
          const m = perTool.get(id) ?? 0;
          perTool.set(id, m + 1);
          found.push({ ...imageDigest(inner, inner.source.data, inner.source.media_type ?? null), msg, part, sub, key: `tool:${id}#${m}`, kind: "tool", ...own, block: inner });
        });
      }
    });
  });
  return found;
}

// noted (v0.5): the full note is given before these messages already (after a compaction summary holding placeholders).
export type MessagesOptions = Omit<PlanOptions<RequestImage>, "fetched"> & { noted?: boolean; fetched?: (ref: RequestImage) => boolean };

export function rewriteBlocks(
  messages: Json[],
  refs: RequestImage[],
  describe: (ref: RequestImage) => Described | undefined,
  leaveOut: Set<string>,
  pixelHash: (image: RequestImage) => string | null,
  options: MessagesOptions = {},
): { messages: Json[]; report: RewriteReport } {
  const { lang = "zh", auto, noted = false } = options;
  // v0.10: unknown images after the model's latest reply: Claude Code can send a request a moment before those records
  // reach its transcript, and they would go out without ids (the engine reads the transcript again, proxy.ts).
  const lastReply = messages.map((message) => message?.role).lastIndexOf("assistant");
  const plan = planRewrite(refs, describe, leaveOut, pixelHash, { ...options, late: (ref) => ref.msg > lastReply });
  const { report } = plan;
  if (!plan.changed) return { messages, report };
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
  for (const { slot, what, text } of plan.actions) edit(refs[slot], what === "label" ? 0 : 1, text, what === "label");
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
  const plainBy = new Map<number, Described[]>();
  for (const { slot, image } of plan.plain) plainBy.set(refs[slot].msg, [...(plainBy.get(refs[slot].msg) ?? []), image]);
  const holding = [...plainBy.keys()].sort((a, b) => a - b);
  for (const msg of [...holding].reverse()) {
    noteAfter(next, msg, `${msg === holding[0] && !noted ? `${claudeNote(lang, auto !== undefined)}\n` : ""}${hereNote(plainBy.get(msg)!, lang, auto !== undefined)}`);
  }
  if (holding.length && !noted) report.noteAt = holding[0] + 1;
  // v0.8: after the user's own message of the turn holding the first image, at or before the others; joined with a
  // note already there.
  if (plan.first !== null) {
    const at = promptOf(messages, refs[plan.first].msg);
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
  // v0.10: the ones still sent with their labels, then the others one line each (compactList), not a placeholder
  // apiece.
  const resent = listed.flatMap((image): Json[] => {
    const block = sent.get(image.id);
    return block ? [{ type: "text", text: includedLabel(image, lang) }, block] : [];
  });
  const missing = listed.filter((image) => !sent.has(image.id));
  const added: Json[] = [...resent, ...(missing.length ? [{ type: "text", text: compactList(missing, lang) }] : [])];
  content.splice(content.findIndex(holdsSummary(summary)) + 1, 0, ...added);
  const next = [...messages];
  next[at] = { ...message, content };
  const inserted = noteAfter(next, at, compactedNote(listed, new Set(sent.keys()), lang, auto));
  return { messages: next, at, inserted };
}
