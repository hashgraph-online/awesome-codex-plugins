// Purpose: v0.8 — the record lines the model writes at the start of a reply (docs/v0.8/plan.md): a feature line for each
// image new in that turn, or a rating the user gave an image, each as a Markdown link definition, which neither Codex
// Desktop nor Claude Desktop shows (gate 1, 2026-10-19): `[//]: # (cam IMG-015 深蓝雨夜｜近景，正脸)`,
// `[//]: # (cam IMG-003 评价：太暗)`; in English `… (cam IMG-003 rated: too dark)`.
// Only the model's own replies are read (thread-index.ts, claude-index.ts): the same text in a user message or a tool
// result counts for nothing, so a web page cannot plant one.
// Input: the text of an assistant reply and its turn. Output: what the model noted, per image id.

// rating: the user's words the model noted, with the turn it noted them in.
export type Rating = { turn: number | null; text: string };
// line: the feature line, written once (the first one stands, unless corrected); ratings: oldest first.
export type Notes = { line: string | null; ratings: Rating[] };

const RECORD = /^ {0,3}\[\/\/\]:[ \t]*#[ \t]*\(cam[ \t]+(IMG-\d{3,})[ \t]+([^()\n]+?)[ \t]*\)[ \t]*$/gm;
const RATING = /^(?:评价|rated)[ \t]*[：:][ \t]*/i;
// v0.10: a feature line the model found wrong (e.g. the user pointed it out), written again in full.
const CORRECTION = /^(?:更正|corrected)[ \t]*[：:][ \t]*/i;

// v0.10: what a placeholder shows of an image's notes: the ratings noted by its own turn. A rating noted later would
// change a placeholder that went out before it, and the prompt cache from there on (claude-cache.ts); the model has it
// in its own reply. After a compaction the list shows everything noted before it (claude-index.ts, compactedNotes).
export function notesBy(notes: Notes | undefined, turn: number | null): Notes | undefined {
  if (!notes || turn === null) return notes;
  const ratings = notes.ratings.filter((rating) => rating.turn === null || rating.turn <= turn);
  if (ratings.length === notes.ratings.length) return notes;
  return notes.line || ratings.length ? { line: notes.line, ratings } : undefined;
}

export const copyNotes = (notes: Map<string, Notes>): Map<string, Notes> => new Map([...notes].map(([id, entry]) => [id, { line: entry.line, ratings: [...entry.ratings] }]));

// v0.10: `idOf` turns the id a line names into the image's id now (claude-index.ts: lines written while a resumed
// transcript was numbered from its own start); null drops the line.
export function addNotes(notes: Map<string, Notes>, text: string, turn: number | null, idOf: (id: string) => string | null = (id) => id): void {
  for (const [, named, body] of text.matchAll(RECORD)) {
    const id = idOf(named);
    if (!id) continue;
    const entry = notes.get(id) ?? { line: null, ratings: [] };
    const rating = RATING.exec(body);
    const correction = CORRECTION.exec(body);
    if (rating) {
      const said = body.slice(rating[0].length).trim();
      if (said) entry.ratings.push({ turn, text: said });
    } else if (correction) {
      const line = body.slice(correction[0].length).trim();
      if (line) entry.line = line;
    } else if (entry.line === null) entry.line = body.trim();
    notes.set(id, entry);
  }
}

// A reply as the user reads it: without its record lines.
export const withoutRecords = (text: string): string => text.replace(RECORD, "").trim();

// The scene: the feature line's first part, before "｜" (or " | " in English).
export function sceneOf(line: string | null): string | null {
  const scene = line?.split(/｜|\s\|\s/)[0]?.trim();
  return scene ? scene : null;
}
