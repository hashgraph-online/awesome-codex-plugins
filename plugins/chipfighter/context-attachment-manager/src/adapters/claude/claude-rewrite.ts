// Purpose: v0.4 — the engine's rewrite of a Claude Code request: which index entry each image of the request is, and
// what the session's index knows of it; the rewrite itself is the Anthropic Messages translator's
// (adapters/protocols/anthropic-messages) and the core's.
// Matching to the index (claude-index.ts): an image inside a tool result by its tool_use_id; pasted images by
// content, a request message to the transcript record(s) holding the same images in the same order.
// v0.8: placeholders carry what the model noted (as noted by the image's own turn). v0.10: images sent once more for
// their feature line are marked in their labels.
// v0.11: split from claude-rewrite.ts (docs/v0.11/plan.md).
// Input: the request's messages, the session's index, the keys to leave out. Output: new messages plus a report.

import { notesBy } from "../../core/notes.ts";
import type { RewriteReport } from "../../core/plan.ts";
import { imageBlocks, rewriteBlocks, type MessagesOptions, type RequestImage } from "../protocols/anthropic-messages/rewrite.ts";
import type { ClaudeIndex, ClaudeImage } from "./claude-index.ts";

type Json = Record<string, any>;

const sameList = (a: string[], b: string[]) => a.length === b.length && a.every((value, i) => value === b[i]);

// Every image of the request, with the index key it matches (null: not in the index, e.g. pasted in this turn).
export function findRequestImages(messages: Json[], index: Pick<ClaudeIndex, "uploads">): RequestImage[] {
  const found = imageBlocks(messages);
  const pastedBy = new Map<number, RequestImage[]>();
  for (const image of found) if (image.sub === null) pastedBy.set(image.msg, [...(pastedBy.get(image.msg) ?? []), image]);
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

// v0.10: keys of the images sent once more for their feature line; their labels say so.
export type ClaudeRewriteOptions = Omit<MessagesOptions, "fetched"> & { awaiting?: Set<string> };

export function rewriteMessages(
  messages: Json[],
  index: Pick<ClaudeIndex, "uploads" | "byKey"> & Partial<Pick<ClaudeIndex, "notes" | "copies">>,
  leaveOut: Set<string>,
  pixelHash: (image: RequestImage) => string | null,
  options: ClaudeRewriteOptions = {},
): { messages: Json[]; report: RewriteReport } {
  const { awaiting = new Set<string>(), ...rest } = options;
  const refs = findRequestImages(messages, index);
  const describe = (ref: RequestImage): ClaudeImage | undefined => {
    const image = ref.key ? index.byKey.get(ref.key) : undefined;
    // v0.10: as noted by the image's own turn, so a placeholder stays as it first went out (notes.ts).
    const notes = image ? notesBy(index.notes?.get(image.id), image.turn) : undefined;
    if (!image) return undefined;
    return notes || awaiting.has(image.key) ? { ...image, ...(notes ? { notes } : {}), ...(awaiting.has(image.key) ? { awaiting: true } : {}) } : image;
  };
  // A copy the model fetched this turn is known as one, not as an image.
  return rewriteBlocks(messages, refs, describe, leaveOut, pixelHash, { ...rest, fetched: (ref) => !!(ref.key && index.copies?.has(ref.key)) });
}
