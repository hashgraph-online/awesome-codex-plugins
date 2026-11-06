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

// v0.3: what automatic selection leaves out of a request of turn `current`: the images of earlier turns that can become
// text and are not pinned. v0.10: where feature lines are written, an image waiting for its line (awaitingLine) is sent
// once more instead. v0.11: decided here for every platform (it was written out in the Codex and the Claude engine).
export function autoChoice(index: SessionIndex<IndexedImage>, current: number, pinned: Record<string, unknown>, features: boolean): { leaveOut: Set<string>; awaiting: Set<string> } {
  const awaiting = new Set(features ? index.images.filter((image) => awaitingLine(index, image, current)).map((image) => image.key) : []);
  const leaveOut = new Set(index.images.filter((image) => image.replaceable && image.turn !== null && image.turn < current && !pinned[image.key] && !awaiting.has(image.key)).map((image) => image.key));
  return { leaveOut, awaiting };
}
