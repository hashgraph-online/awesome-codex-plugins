// Purpose: P2 — the rewrite of a Responses request's `input` (Codex): the plan of the core (core/plan.ts) put into the
// items. A placeholder takes the place of the image, together with Codex's `<image name=…>` and `</image>` parts around
// an upload; a copy's note takes the image's place; a label goes right before the image (or its opening tag). Nothing
// else changes: checked images, unknown images and all other items are forwarded as they are.
// The notes are developer messages: the one explaining omitted images before the user message that opens the turn of
// the first plain placeholder (placeholders are user content, which the model does not take as proof; v0.1), and v0.8's
// feature line note before the turn of the first image, at or before the other one. Neither ever splits a tool call
// from its output.
// v0.10: after Codex compacted the task, the images its compaction did not keep go back right after its compaction item.
// v0.11: split from rewrite.ts; the decisions are the core's, the words core/words.ts (docs/v0.11/plan.md).
// Input: request items, a lookup into the thread index, the keys to leave out. Output: new items plus a metadata report.

import { planRewrite, type RewriteReport } from "../../../core/plan.ts";
import type { Lang } from "../../../core/lang.ts";
import { autoNote, codexCompactedNote, compactList, featureNote, includedLabel, omissionNote, type Described } from "../../../core/words.ts";
import { findImages, type ImageRef } from "./images.ts";

type Json = Record<string, any>;

// v0.10, Codex: right after its compaction item, the images that compaction did not keep (thread-index.ts,
// compacted): a developer message with the note and the list, then the ones still sent (pinned, or checked in manual
// mode) as originals with their labels, in a user message. The same selection gives the same items, so the cached
// prefix holds. No compaction item in the request: nothing changes.
export function addCodexCompacted(items: Json[], listed: Described[], resend: Array<{ image: Described; url: string }>, options: { lang?: Lang; auto?: boolean } = {}): { items: Json[]; at: number | null } {
  const { lang = "zh", auto = false } = options;
  let at = -1;
  items.forEach((item, position) => { if (item?.type === "compaction") at = position; });
  if (at < 0 || !listed.length) return { items, at: null };
  const sent = new Set(resend.map(({ image }) => image.id));
  const missing = listed.filter((image) => !sent.has(image.id));
  const text = [codexCompactedNote(listed.length, resend.length, auto, lang), ...(missing.length ? ["", compactList(missing, lang)] : [])].join("\n");
  const added: Json[] = [{ type: "message", role: "developer", content: [{ type: "input_text", text }] }];
  if (resend.length) added.push({ type: "message", role: "user", content: resend.flatMap(({ image, url }) => [{ type: "input_text", text: includedLabel(image, lang) }, { type: "input_image", image_url: url }]) });
  return { items: [...items.slice(0, at + 1), ...added, ...items.slice(at + 1)], at };
}

export type RewriteOptions = {
  lang?: Lang;
  // Copies the model fetched in an earlier turn (key → the id they copy): left out in either mode.
  copies?: Map<string, string>;
  // Automatic selection: the turn the request belongs to (core/plan.ts).
  auto?: { currentTurn: number };
  // v0.8: the feature line note and an id label on every image sent.
  features?: boolean;
};

export function rewriteItems(
  items: Json[],
  describe: (ref: ImageRef) => Described | undefined,
  unchecked: Set<string>,
  pixelHash: (ref: ImageRef) => string | null,
  options: Lang | RewriteOptions = "zh",
): { items: Json[]; report: RewriteReport } {
  const { lang = "zh", copies = new Map<string, string>(), auto, features = false }: RewriteOptions = typeof options === "string" ? { lang: options } : options;
  const refs = findImages(items);
  // A copy the model fetched this turn is known by the line our fetch tool writes before it.
  const plan = planRewrite(refs, describe, unchecked, pixelHash, { lang, copies, auto, features, fetched: (ref) => !!ref.fetchedId });
  if (!plan.changed) return { items, report: plan.report };

  // Each edit puts one text part at `at`, in place of `remove` parts (none for a label).
  const edits = new Map<number, Array<{ at: number; remove: number; text: string }>>();
  const edit = (item: number, at: number, remove: number, text: string) => edits.set(item, [...(edits.get(item) ?? []), { at, remove, text }]);
  for (const { slot, what, text } of plan.actions) {
    const ref = refs[slot];
    if (what === "placeholder") {
      const at = ref.openTag ?? ref.part!;
      edit(ref.item, at, (ref.closeTag ?? ref.part!) - at + 1, text);
    } else if (what === "copy") edit(ref.item, ref.part!, 1, text);
    else edit(ref.item, ref.openTag ?? ref.part!, 0, text);
  }
  const next = items.map((item, index) => {
    const list = edits.get(index);
    if (!list) return item;
    const field = item.type === "message" ? "content" : "output";
    const parts: Json[] = [...item[field]];
    for (const { at, remove, text } of list.sort((a, b) => b.at - a.at)) parts.splice(at, remove, { type: "input_text", text });
    return { ...item, [field]: parts };
  });
  const turnStart = (from: number) => {
    let at = from;
    while (at > 0 && !(next[at].type === "message" && next[at].role === "user")) at--;
    return at;
  };
  const developer = (text: string) => ({ type: "message", role: "developer", content: [{ type: "input_text", text }] });
  const { report } = plan;
  const noteAt = plan.plain.length ? turnStart(refs[plan.plain[0].slot].item) : null;
  const featureAt = plan.first !== null ? turnStart(refs[plan.first].item) : null;
  if (noteAt !== null) next.splice(noteAt, 0, developer(auto ? autoNote(lang) : omissionNote(lang)));
  if (featureAt !== null) {
    next.splice(featureAt, 0, developer(featureNote(lang)));
    report.featureAt = featureAt;
  }
  if (noteAt !== null) report.noteAt = noteAt + (featureAt !== null ? 1 : 0);
  return { items: next, report };
}
