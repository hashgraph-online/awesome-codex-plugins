// Purpose: what the core knows of a session's images, whatever the platform reads them from (v0.11: the shape both the
// Codex and the Claude index had, moved here from thread-index.ts, docs/v0.11/plan.md). Ids follow the order the
// images first appeared in, and never change.
// Input: a platform's index. Output: types, and whether an image is waiting for its feature line.

import type { ImageDigest, ImageKind, ImageSource } from "./images.ts";
import type { Notes } from "./notes.ts";

type Json = Record<string, any>;

// An image occurrence of the session. key: names the same occurrence in a request and in the records. v0.10:
// compacted, before the platform last compacted the session and not in the history it kept: the engine puts it back
// after the compaction.
export type IndexedImage = ImageDigest & {
  key: string; kind: ImageKind; name: string | null; label: string | null; source: ImageSource; replaceable: boolean;
  id: string; turn: number | null; bytes: number; pixelSha256: string | null; compacted?: boolean;
  // v0.2: a PDF comment screenshot's page and file (Codex desktop), for the panel.
  pdfPage?: number | null; pdfName?: string | null;
};
// v0.3: an image the model fetched with our tool, a copy of `of` sent in its own turn only (spec: automatic selection).
export type FetchedCopy = { key: string; of: string; turn: number | null };
// v0.10: items, the items of the history (Codex), which image positions point into. interrupted: the turns the user
// stopped before the model wrote its last reply (its record lines); skipped: turns that are only Claude Code's mark of
// such a stop.
export type SessionIndex<I extends IndexedImage = IndexedImage> = { threadId: string; images: I[]; byKey: Map<string, I>; turns: number; turnNumbers: Map<string, number>; copies: Map<string, FetchedCopy>; notes: Map<string, Notes>; items?: Json[]; interrupted?: Set<number>; skipped?: Set<number> };

// v0.10 (docs/v0.10/plan.md): an image of an interrupted turn without a feature line yet, with no turn finished since:
// sent once more in the current turn, so the model can write its line (automatic selection would leave it out).
export function awaitingLine(index: SessionIndex<IndexedImage>, image: IndexedImage, current: number): boolean {
  if (image.turn === null || image.turn >= current || index.notes.get(image.id)?.line || !index.interrupted?.has(image.turn)) return false;
  for (let turn = image.turn + 1; turn < current; turn++) if (!index.interrupted.has(turn) && !index.skipped?.has(turn)) return false;
  return true;
}

// v0.3: the copies the model fetched before the request's turn (key → the id each copies), left out in either mode.
export function earlierCopies(index: SessionIndex<IndexedImage>, current: number): Map<string, string> {
  return new Map([...index.copies.values()].filter((copy) => copy.turn === null || copy.turn < current).map((copy) => [copy.key, copy.of]));
}

// v0.12: an image of the turn just before without a feature line, whose content went out in that turn before the
// platform recorded it (the engine's `late` images: Claude Code wrote a session's first message to its transcript only
// after the request, so the image had no id then and the model was not asked for its line; Haiku 5.5 and Sonnet 5.5,
// 2026-11-22): sent once more, like an interrupted turn's. missed: the contents the engine saw go out that way.
export function missedLine(index: SessionIndex<IndexedImage>, image: IndexedImage, current: number, missed: ReadonlySet<string>): boolean {
  return image.turn !== null && image.turn === current - 1 && !index.notes.get(image.id)?.line && missed.has(image.contentId);
}
// v0.12: at most this many images go out once more for their lines, the newest: a turn of screenshots may hold dozens.
export const AWAITING_MAX = 5;

// v0.12 (docs/v0.12/plan.md §4): a turn of computer use takes dozens of screenshots, each request of it carrying them
// all. The images tools returned in the current turn (not files viewed with Read or view_image, not uploads, not
// generated images) are left out too once there are many: the newest KEEP_IN_TURN stay originals, the older ones go in
// batches of BATCH_IN_TURN, so the history changes, and the prompt cache breaks, once a batch, not at every step. Up to
// KEEP_IN_TURN + BATCH_IN_TURN - 1 of them nothing changes. The model fetches one back with cam_view_image if it needs it.
export const KEEP_IN_TURN = 5;
export const BATCH_IN_TURN = 10;
export function inTurnOut(index: SessionIndex<IndexedImage>, current: number, pinned: Record<string, unknown>): string[] {
  const returned = index.images.filter((image) => image.turn === current && image.kind === "tool" && image.replaceable && !pinned[image.key]);
  const older = returned.length - KEEP_IN_TURN;
  const out = older >= BATCH_IN_TURN ? Math.floor(older / BATCH_IN_TURN) * BATCH_IN_TURN : 0;
  return returned.slice(0, out).map((image) => image.key);
}

// v0.3: what automatic selection leaves out of a request of turn `current`: the images of earlier turns that can become
// text and are not pinned. v0.10: where feature lines are written, an image waiting for its line (awaitingLine) is sent
// once more instead. v0.11: decided here for every platform (it was written out in the Codex and the Claude engine).
// v0.12: also one whose line was missed (missedLine); the newest AWAITING_MAX of them. And the current turn's older
// tool images (inTurnOut).
export function autoChoice(index: SessionIndex<IndexedImage>, current: number, pinned: Record<string, unknown>, features: boolean, missed: ReadonlySet<string> = new Set()): { leaveOut: Set<string>; awaiting: Set<string> } {
  const waiting = features ? index.images.filter((image) => awaitingLine(index, image, current) || missedLine(index, image, current, missed)) : [];
  const awaiting = new Set(waiting.slice(-AWAITING_MAX).map((image) => image.key));
  const leaveOut = new Set(index.images.filter((image) => image.replaceable && image.turn !== null && image.turn < current && !pinned[image.key] && !awaiting.has(image.key)).map((image) => image.key));
  for (const key of inTurnOut(index, current, pinned)) leaveOut.add(key);
  return { leaveOut, awaiting };
}
