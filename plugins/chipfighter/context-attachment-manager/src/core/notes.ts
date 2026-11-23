// Purpose: v0.8 — the record lines the model writes at the start of a reply (docs/v0.8/plan.md): a feature line for each
// image new in that turn, or a rating the user gave an image, each as a Markdown link definition, which neither Codex
// Desktop nor Claude Desktop shows (gate 1, 2026-10-19): `[//]: # (cam IMG-015 深蓝雨夜｜近景，正脸)`,
// `[//]: # (cam IMG-003 评价：太暗)`; in English `… (cam IMG-003 rated: too dark)`.
// Only the model's own replies are read (thread-index.ts, claude-index.ts): the same text in a user message or a tool
// result counts for nothing, so a web page cannot plant one.
// v0.12 (docs/v0.12/plan.md §2): a feature line starts with its category and name and may list the characters in the
// picture (`场景:雨夜街头｜林夏、阿橘｜中景，打红伞`); one line may stand for a run of screenshots
// (`IMG-020~IMG-034`). lineParts reads a line into what the panel groups by; lines in the v0.8–v0.11 form still count.
// Input: the text of an assistant reply and its turn. Output: what the model noted, per image id.

// rating: the user's words the model noted, with the turn it noted them in.
export type Rating = { turn: number | null; text: string };
// line: the feature line, written once (the first one stands, unless corrected); ratings: oldest first.
// run: v0.12, the run of screenshots one line stood for ("IMG-020~IMG-034"), on each of them.
export type Notes = { line: string | null; ratings: Rating[]; run?: string };

const ID = String.raw`IMG-\d{3,}`;
// v0.12: an id, or a run of them: "IMG-020~IMG-034", "IMG-020～034", "IMG-020-IMG-034".
const IDS = String.raw`${ID}(?:[ \t]*[~～–—-][ \t]*(?:IMG-)?\d{3,})?`;
const RECORD = new RegExp(String.raw`^ {0,3}\[\/\/\]:[ \t]*#[ \t]*\(cam[ \t]+(${IDS})[ \t]+([^()\n]+?)[ \t]*\)[ \t]*$`, "gm");
const RATING = /^(?:评价|rated)[ \t]*[：:][ \t]*/i;
// v0.10: a feature line the model found wrong (e.g. the user pointed it out), written again in full.
const CORRECTION = /^(?:更正|corrected)[ \t]*[：:][ \t]*/i;
// The longest run one line may stand for; a longer one counts for its first image only.
const MAX_RUN = 200;

// v0.10: what a placeholder shows of an image's notes: the ratings noted by its own turn. A rating noted later would
// change a placeholder that went out before it, and the prompt cache from there on (anthropic-messages/cache.ts); the model has it
// in its own reply. After a compaction the list shows everything noted before it (claude-index.ts, compactedNotes).
export function notesBy(notes: Notes | undefined, turn: number | null): Notes | undefined {
  if (!notes || turn === null) return notes;
  const ratings = notes.ratings.filter((rating) => rating.turn === null || rating.turn <= turn);
  if (ratings.length === notes.ratings.length) return notes;
  return notes.line || ratings.length ? { ...notes, ratings } : undefined;
}

export const copyNotes = (notes: Map<string, Notes>): Map<string, Notes> => new Map([...notes].map(([id, entry]) => [id, { ...entry, ratings: [...entry.ratings] }]));

// v0.12: the ids a record line names: one, or each of a run (null run for a single id).
function namedIds(named: string): { ids: string[]; run: string | null } {
  const [first, last] = named.match(/\d{3,}/g)!.map(Number);
  if (last === undefined || last <= first || last - first >= MAX_RUN) return { ids: [named.match(new RegExp(ID))![0]], run: null };
  const ids = Array.from({ length: last - first + 1 }, (_, at) => `IMG-${String(first + at).padStart(3, "0")}`);
  return { ids, run: `${ids[0]}~${ids[ids.length - 1]}` };
}

// v0.10: `idOf` turns the id a line names into the image's id now (claude-index.ts: lines written while a resumed
// transcript was numbered from its own start); null drops the line.
export function addNotes(notes: Map<string, Notes>, text: string, turn: number | null, idOf: (id: string) => string | null = (id) => id): void {
  for (const [, named, body] of text.matchAll(RECORD)) {
    const { ids, run } = namedIds(named);
    const rating = RATING.exec(body);
    const correction = CORRECTION.exec(body);
    for (const name of ids) {
      const id = idOf(name);
      if (!id) continue;
      const entry = notes.get(id) ?? { line: null, ratings: [] };
      if (rating) {
        const said = body.slice(rating[0].length).trim();
        if (said) entry.ratings.push({ turn, text: said });
      } else if (correction) {
        const line = body.slice(correction[0].length).trim();
        if (line) {
          entry.line = line;
          if (run) entry.run = run; else delete entry.run;
        }
      } else if (entry.line === null) {
        entry.line = body.trim();
        if (run) entry.run = run;
      }
      notes.set(id, entry);
    }
  }
}

// A reply as the user reads it: without its record lines.
export const withoutRecords = (text: string): string => text.replace(RECORD, "").trim();

// The scene: the feature line's first part, before "｜" (or " | " in English).
export function sceneOf(line: string | null): string | null {
  const scene = line?.split(/｜|\s\|\s/)[0]?.trim();
  return scene ? scene : null;
}

// v0.12: the five categories the panel browses by (docs/v0.12/plan.md §2).
export type Category = "character" | "place" | "screen" | "document" | "other";
// What a feature line says. name: as written ("雨夜街头", "淘宝·订单页", "租房合同 第3页"; null: the old form named
// none); card: what the panel groups it under (the name; a screen's app or site; a document without its page);
// part: a screen's page ("订单页"); page: a document's page number; features: the rest of the line.
export type LineParts = { category: Category; name: string | null; card: string | null; part: string | null; page: number | null; characters: string[]; features: string };

const CATEGORIES: Array<[Category, RegExp]> = [
  ["character", /^(?:角色|人物|character|char)$/i],
  ["place", /^(?:场景|地点|place|scene|location)$/i],
  ["screen", /^(?:界面|截图|网页|页面|screen|screenshot|ui|web ?page)$/i],
  ["document", /^(?:文档|文件|document|doc|pdf)$/i],
  ["other", /^(?:其他|其它|other)$/i],
];
// v0.8–v0.11 lines start with a place, or with what an image set nowhere is (words.ts before v0.12).
const OLD_WORDS: Array<[RegExp, Category, string | null]> = [
  [/^(?:角色|character)$/i, "character", null],
  [/^物品$/, "other", "物品"],
  [/^object$/i, "other", "object"],
  [/^(?:文档|document)$/i, "document", null],
  [/^(?:网页|web ?page)$/i, "screen", null],
  [/^多个地点$/, "other", "分镜"],
  [/^several places$/i, "other", "storyboard"],
];
const SEGMENTS = /\s*[｜|]\s*/;
const KIND_NAME = /^([^:：]{1,16}?)\s*[:：]\s*(.*)$/;
const NAMES = /\s*[、,，;；/]\s*|\s+(?:and|&)\s+/i;
const NOBODY = /^(?:无|没有|无人|none|no one|nobody|[-—–])$/i;
const PAGE = /^(.*?)[\s·・,，]*(?:第\s*(\d+)\s*页|p\.?\s*(\d+)|page\s*(\d+))$/i;
const SCREEN_PART = /\s*[·・]\s*|\s+-\s+/;

export function lineParts(line: string | null): LineParts | null {
  const text = line?.trim();
  if (!text) return null;
  const [head, ...rest] = text.split(SEGMENTS);
  const named = KIND_NAME.exec(head);
  const category = named ? CATEGORIES.find(([, words]) => words.test(named[1].trim()))?.[0] : undefined;
  if (named && category) {
    // Three parts: the middle one lists the characters in the picture; two: there were none. A screen or a document has
    // no characters to list: a third part there is more features (Haiku 5.5, gate 1: "document: lease p. 3 | scanned,
    // red stamp | page of dark lines").
    const cast = rest.length >= 2 && category !== "screen" && category !== "document";
    const listed = cast ? rest[0].split(NAMES).map((one) => one.trim()).filter((one) => one && !NOBODY.test(one)) : [];
    return finish(category, named[2].trim() || null, [...new Set(listed)], (cast ? rest.slice(1) : rest).join("｜"));
  }
  const old = OLD_WORDS.find(([words]) => words.test(head));
  return finish(old ? old[1] : "place", old ? old[2] : head || null, [], rest.join("｜"));
}

function finish(category: Category, name: string | null, characters: string[], features: string): LineParts {
  let card = name;
  let part: string | null = null;
  let page: number | null = null;
  if (name && category === "screen") {
    const [app, ...pages] = name.split(SCREEN_PART);
    if (app && pages.length) { card = app; part = pages.join("·"); }
  }
  if (name && category === "document") {
    const found = PAGE.exec(name);
    if (found) {
      page = Number(found[2] ?? found[3] ?? found[4]);
      card = found[1].trim() || null;
    }
  }
  return { category, name, card, part, page, characters, features: features.trim() };
}
