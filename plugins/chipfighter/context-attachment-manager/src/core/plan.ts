// Purpose: v0.11 — what happens to each image of a request, whatever its format (docs/v0.11/plan.md 3.4). The rules
// were the same in the Codex and the Claude rewrite and are kept as they were (rewrite.ts, claude-rewrite.ts before
// v0.11): an unchecked image becomes a placeholder ("duplicate" when the same content is still sent), a copy the model
// fetched in an earlier turn becomes a short note, and once anything is left out (v0.8: once feature lines are on)
// every image still sent gets its id. Automatic selection (v0.3) leaves out earlier turns' images that are not pinned;
// its placeholders point to, and its labels mark, only images of earlier turns, so a copy fetched mid-turn changes
// nothing before it. Where the text goes in the request, and where the notes go, is the translator's business.
// Input: the request's images in order (slots), what the index knows of each, the keys to leave out. Output: a plan.

import type { ImageDigest, ImageKind } from "./images.ts";
import type { Lang } from "./lang.ts";
import { autoPlaceholder, copyNote, duplicatePlaceholder, includedLabel, newImageWord, plainPlaceholder, type Described } from "./words.ts";

export type Replacement = { id: string; key: string; kind: ImageKind; mode: "plain" | "duplicate"; sameAs: string | null; base64Chars: number };
// noteAt: where the note explaining omitted images was inserted, if one was. copies: the ids whose copies fetched in an
// earlier turn were left out. v0.8: featureAt, where the feature line note went; labeled, how many images sent got
// their id; unknown, how many images of the request the index did not know (e.g. not recorded yet). v0.10, Claude:
// late, how many of those came after the model's latest reply.
export type RewriteReport = { images: number; replaced: Replacement[]; locked: string[]; sentContentIds: string[]; copies: string[]; noteAt?: number; featureAt?: number; labeled?: number; unknown?: number; late?: number };

// An image of the request. key: the index key it matches (null: none, e.g. pasted in this turn and not recorded yet).
// replaceable: false for one that cannot become text (Codex's hosted generation result). name and label: the request's
// own, used only when an omitted image points to a new one.
export type Slot = ImageDigest & { key: string | null; kind: ImageKind; name: string | null; label: string | null; replaceable: boolean };

export type PlanOptions<S extends Slot> = {
  lang?: Lang;
  // Copies the model fetched in an earlier turn (key → the id they copy): left out in either mode.
  copies?: Map<string, string>;
  // Automatic selection: the turn the request belongs to.
  auto?: { currentTurn: number };
  // v0.8: feature lines: the note before the first image's turn, and ids on this turn's new images too.
  features?: boolean;
  // A copy the model fetched in this turn, known as one (not counted as unknown).
  fetched?: (slot: S) => boolean;
  // v0.10, Claude: an image after the model's latest reply; an unknown one there is counted as late (the records may
  // not have it yet).
  late?: (slot: S) => boolean;
};

// what: a placeholder in place of the image, a copy's note in its place, or a label right before it.
export type Action = { slot: number; what: "placeholder" | "copy" | "label"; text: string };
// changed: false when nothing is to be done (the request goes out as it is). plain: the plain placeholders, in order,
// for the notes that explain them. first: the first image the index knows, when feature lines are on (its turn gets the
// feature line note). unknown: the images the index does not know.
export type Plan = { report: RewriteReport; changed: boolean; actions: Action[]; plain: Array<{ slot: number; image: Described }>; first: number | null; unknown: number[] };

export function planRewrite<S extends Slot>(
  slots: S[],
  describe: (slot: S) => Described | undefined,
  leaveOut: Set<string>,
  pixelHash: (slot: S) => string | null,
  options: PlanOptions<S> = {},
): Plan {
  const { lang = "zh", copies = new Map<string, string>(), auto, features = false, fetched = () => false, late = () => false } = options;
  const report: RewriteReport = { images: slots.length, replaced: [], locked: [], sentContentIds: [], copies: [] };
  const copied = slots.filter((slot) => slot.key !== null && copies.has(slot.key) && slot.replaceable);
  const drop = slots.filter((slot) => slot.key !== null && !copies.has(slot.key) && leaveOut.has(slot.key) && slot.replaceable && describe(slot));
  for (const slot of slots) if (slot.key !== null && leaveOut.has(slot.key) && !slot.replaceable) report.locked.push(describe(slot)?.id ?? slot.key);
  const sent = slots.filter((slot) => !drop.includes(slot) && !copied.includes(slot));
  report.sentContentIds = sent.map((slot) => slot.contentId);
  const unknown = slots.flatMap((slot, at) => (!copied.includes(slot) && !fetched(slot) && !describe(slot) ? [at] : []));
  if (unknown.length) report.unknown = unknown.length;
  const lateCount = unknown.filter((at) => late(slots[at])).length;
  if (lateCount) report.late = lateCount;
  const firstSlot = features ? slots.find((slot) => describe(slot)) : undefined;
  const first = firstSlot ? slots.indexOf(firstSlot) : null;
  const plan: Plan = { report, changed: false, actions: [], plain: [], first, unknown };
  if (!drop.length && !copied.length && first === null) return plan;
  plan.changed = true;
  const earlier = (slot: S) => { const turn = describe(slot)?.turn; return auto !== undefined && turn !== null && turn !== undefined && turn < auto.currentTurn; };
  const lasting = auto ? sent.filter(earlier) : sent;
  const same = (a: S, b: S) => {
    if (a.contentId === b.contentId) return true;
    if (a.width !== b.width || a.height !== b.height) return false;
    const pixels = pixelHash(a);
    return pixels !== null && pixels === pixelHash(b);
  };
  for (const slot of drop) {
    const image = describe(slot)!;
    const copy = lasting.find((other) => same(other, slot));
    const copyImage: Described | null = copy ? describe(copy) ?? { id: newImageWord(lang), name: copy.name, label: copy.label, kind: copy.kind, turn: null, width: copy.width, height: copy.height } : null;
    const text = copyImage ? duplicatePlaceholder(image, copyImage, lang) : auto ? autoPlaceholder(image, lang) : plainPlaceholder(image, lang);
    if (!copyImage) plan.plain.push({ slot: slots.indexOf(slot), image });
    report.replaced.push({ id: image.id, key: slot.key!, kind: image.kind, mode: copyImage ? "duplicate" : "plain", sameAs: copyImage?.id ?? null, base64Chars: slot.base64Chars });
    plan.actions.push({ slot: slots.indexOf(slot), what: "placeholder", text });
  }
  for (const slot of copied) {
    plan.actions.push({ slot: slots.indexOf(slot), what: "copy", text: copyNote(copies.get(slot.key!)!, lang) });
    report.copies.push(copies.get(slot.key!)!);
  }
  // v0.1-25: a checked image sits in its old place among placeholders, so every image still sent is marked with its id.
  // v0.8: with feature lines, this turn's new images too.
  for (const slot of features ? sent : lasting) {
    const image = slot.replaceable ? describe(slot) : undefined;
    if (!image) continue;
    plan.actions.push({ slot: slots.indexOf(slot), what: "label", text: includedLabel(image, lang) });
    report.labeled = (report.labeled ?? 0) + 1;
  }
  return plan;
}
