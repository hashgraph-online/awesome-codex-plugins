// Purpose: v0.8 — the record lines the model writes at the start of a reply (docs/v0.8/plan.md): a feature line for each
// image new in that turn, or a rating the user gave an image, each as a Markdown link definition, which neither Codex
// Desktop nor Claude Desktop shows (gate 1, 2026-10-19): `[//]: # (cam IMG-015 深蓝雨夜｜近景，正脸)`,
// `[//]: # (cam IMG-003 评价：太暗)`; in English `… (cam IMG-003 rated: too dark)`.
// Only the model's own replies are read (thread-index.ts, claude-index.ts): the same text in a user message or a tool
// result counts for nothing, so a web page cannot plant one.
// Input: the text of an assistant reply and its turn. Output: what the model noted, per image id.

// rating: the user's words the model noted, with the turn it noted them in.
export type Rating = { turn: number | null; text: string };
// line: the feature line, written once (the first one stands); ratings: oldest first.
export type Notes = { line: string | null; ratings: Rating[] };

const RECORD = /^ {0,3}\[\/\/\]:[ \t]*#[ \t]*\(cam[ \t]+(IMG-\d{3,})[ \t]+([^()\n]+?)[ \t]*\)[ \t]*$/gm;
const RATING = /^(?:评价|rated)[ \t]*[：:][ \t]*/i;

export function addNotes(notes: Map<string, Notes>, text: string, turn: number | null): void {
  for (const [, id, body] of text.matchAll(RECORD)) {
    const entry = notes.get(id) ?? { line: null, ratings: [] };
    const rating = RATING.exec(body);
    if (rating) {
      const said = body.slice(rating[0].length).trim();
      if (said) entry.ratings.push({ turn, text: said });
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
