// Purpose: v0.13 — the little of a PDF the engine needs (docs/design.md §14): how many pages it has, how many of them
// carry text (a font) rather than only pictures (a scan), and a new PDF holding only some of its pages, so the model
// can get a few pages back instead of the whole file. The file is read through from its start: objects are taken
// where they are written, those packed into object streams too, so a damaged cross-reference table does not matter.
// An encrypted file gives its page facts but no copy (its streams would not read without its key). Anything
// unexpected gives null, and the caller sends the whole file instead.
// Input: the bytes of a PDF. Output: page facts, or the bytes of a new PDF (pure, no I/O).

import { constants, inflateSync } from "node:zlib";

// A value as the file writes it. Numbers, strings, booleans and null keep their text and are written back as they were;
// a name keeps its slash. A dictionary's keys are names without it.
// (Plain fields, no parameter properties: Node runs this file by stripping its types.)
class Ref { num: number; gen: number; constructor(num: number, gen: number) { this.num = num; this.gen = gen; } }
class Name { raw: string; constructor(raw: string) { this.raw = raw; } }
class Raw { raw: string; constructor(raw: string) { this.raw = raw; } }
class Dict {
  entries: Map<string, Value>;
  constructor(entries: Map<string, Value>) { this.entries = entries; }
  get(key: string): Value | undefined { return this.entries.get(key); }
}
class Stream { dict: Dict; data: Buffer; constructor(dict: Dict, data: Buffer) { this.dict = dict; this.data = data; } }
type Value = Ref | Name | Raw | Dict | Stream | Value[];

const isSpace = (c: number) => c === 32 || c === 10 || c === 13 || c === 9 || c === 12 || c === 0;
const isDelimiter = (c: number) => c === 40 || c === 41 || c === 60 || c === 62 || c === 91 || c === 93 || c === 123 || c === 125 || c === 47 || c === 37;
const DIGITS = /^\d+$/;
const MAX_DEPTH = 64;
// Guards against a hostile or broken file: how far a decompressed stream may grow, how many pages are walked.
const MAX_INFLATED = 64 << 20;
const MAX_PAGES = 20_000;

class Reader {
  s: string;
  at: number;
  constructor(s: string, at = 0) { this.s = s; this.at = at; }

  // Whitespace and comments.
  skip(): void {
    const s = this.s;
    for (;;) {
      const c = s.charCodeAt(this.at);
      if (isSpace(c)) { this.at++; continue; }
      if (c === 37) {
        while (this.at < s.length && s.charCodeAt(this.at) !== 10 && s.charCodeAt(this.at) !== 13) this.at++;
        continue;
      }
      return;
    }
  }

  // A run of regular characters: a number, a keyword, a name's text.
  word(): string {
    const start = this.at;
    while (this.at < this.s.length) {
      const c = this.s.charCodeAt(this.at);
      if (isSpace(c) || isDelimiter(c)) break;
      this.at++;
    }
    return this.s.slice(start, this.at);
  }

  literal(): string {
    const s = this.s;
    const start = this.at;
    let depth = 0;
    for (; this.at < s.length; this.at++) {
      const c = s.charCodeAt(this.at);
      if (c === 92) { this.at++; continue; }
      if (c === 40) depth++;
      else if (c === 41 && --depth === 0) { this.at++; return s.slice(start, this.at); }
    }
    throw new Error("unclosed string");
  }

  value(depth = 0): Value {
    if (depth > MAX_DEPTH) throw new Error("nested too deep");
    this.skip();
    const s = this.s;
    const c = s.charCodeAt(this.at);
    if (Number.isNaN(c)) throw new Error("end of data");
    if (c === 47) {
      const start = this.at++;
      this.word();
      return new Name(s.slice(start, this.at));
    }
    if (c === 40) return new Raw(this.literal());
    if (c === 60 && s.charCodeAt(this.at + 1) === 60) {
      this.at += 2;
      const entries = new Map<string, Value>();
      for (;;) {
        this.skip();
        if (s.charCodeAt(this.at) === 62 && s.charCodeAt(this.at + 1) === 62) { this.at += 2; return new Dict(entries); }
        const key = this.value(depth + 1);
        if (!(key instanceof Name)) throw new Error("a dictionary key that is not a name");
        entries.set(key.raw.slice(1), this.value(depth + 1));
      }
    }
    if (c === 60) {
      const end = s.indexOf(">", this.at);
      if (end < 0) throw new Error("unclosed hex string");
      const raw = s.slice(this.at, end + 1);
      this.at = end + 1;
      return new Raw(raw);
    }
    if (c === 91) {
      this.at++;
      const items: Value[] = [];
      for (;;) {
        this.skip();
        if (s.charCodeAt(this.at) === 93) { this.at++; return items; }
        items.push(this.value(depth + 1));
      }
    }
    if (isDelimiter(c)) throw new Error(`unexpected ${s[this.at]}`);
    const word = this.word();
    // "12 0 R": a reference.
    if (DIGITS.test(word)) {
      const back = this.at;
      this.skip();
      const gen = this.word();
      if (DIGITS.test(gen)) {
        this.skip();
        const after = s.charCodeAt(this.at + 1);
        if (s[this.at] === "R" && (Number.isNaN(after) || isSpace(after) || isDelimiter(after))) {
          this.at++;
          return new Ref(Number(word), Number(gen));
        }
      }
      this.at = back;
    }
    return new Raw(word);
  }
}

const nameOf = (value: Value | undefined): string | null => (value instanceof Name ? value.raw : null);
const integerOf = (value: Value | undefined): number | null => (value instanceof Raw && DIGITS.test(value.raw) ? Number(value.raw) : null);

// "12 0 obj" at the start of an object; not inside a longer number.
const OBJECT = /(?<![0-9])(\d{1,10})[\0\t\n\f\r ]+(\d{1,5})[\0\t\n\f\r ]+obj(?![^\0\t\n\f\r ()<>[\]{}/%])/g;
const TRAILER = /trailer[\0\t\n\f\r ]*<</g;
// The keys a page takes from the page tree above it when it has none of its own.
const INHERITED = ["Resources", "MediaBox", "CropBox", "Rotate"];

type Place = { at: number; offset: number } | { at: number; stream: number; index: number };
export type PdfPage = { num: number; dict: Dict; inherited: Map<string, Value> };

type Pack = { text: string; first: number; header: Array<[number, number]> };

class Doc {
  bytes: Buffer;
  s: string;
  places = new Map<number, Place>();
  private values = new Map<number, Value | null>();
  private trailers: Array<{ at: number; dict: Dict }> = [];
  private unpacked = new Map<number, Pack | null>();

  constructor(bytes: Buffer) {
    this.bytes = bytes;
    this.s = bytes.toString("latin1");
    this.scan();
  }

  // Every object where it is written; a later one with the same number wins (an incremental update).
  private scan(): void {
    const packs: Array<{ num: number; at: number }> = [];
    let from = 0;
    for (;;) {
      OBJECT.lastIndex = from;
      const found = OBJECT.exec(this.s);
      if (!found) break;
      const num = Number(found[1]);
      let end = found.index + found[0].length;
      try {
        const object = this.objectAt(found.index, false);
        end = object.end;
        this.places.set(num, { at: found.index, offset: found.index });
        const dict = object.value instanceof Stream ? object.value.dict : object.value instanceof Dict ? object.value : null;
        const type = nameOf(dict?.get("Type"));
        if (type === "/ObjStm") packs.push({ num, at: found.index });
        if (type === "/XRef" && dict) this.trailers.push({ at: found.index, dict });
      } catch { /* skipped: not an object after all, or a damaged one */ }
      from = Math.max(end, found.index + found[0].length);
    }
    for (const found of this.s.matchAll(TRAILER)) {
      try {
        const value = new Reader(this.s, found.index + "trailer".length).value();
        if (value instanceof Dict) this.trailers.push({ at: found.index, dict: value });
      } catch { /* a damaged trailer */ }
    }
    // Objects packed into object streams, where the stream is the newest place they are written.
    for (const pack of packs) {
      const header = this.packHeader(pack.num);
      header?.forEach(([num], index) => {
        const known = this.places.get(num);
        if (!known || known.at < pack.at) this.places.set(num, { at: pack.at, stream: pack.num, index });
      });
    }
  }

  // "n g obj <value> [stream … endstream] endobj" at `offset`. `lengths`: whether an indirect /Length may be looked
  // up (not while scanning, when the object holding it may come later); otherwise the stream ends at "endstream".
  private objectAt(offset: number, lengths = true): { value: Value; end: number } {
    const reader = new Reader(this.s, offset);
    reader.word();
    reader.skip();
    reader.word();
    reader.skip();
    if (reader.word() !== "obj") throw new Error("not an object");
    const value = reader.value();
    reader.skip();
    if (!(value instanceof Dict) || !this.s.startsWith("stream", reader.at)) return { value, end: reader.at };
    let start = reader.at + "stream".length;
    if (this.s.charCodeAt(start) === 13) start++;
    if (this.s.charCodeAt(start) === 10) start++;
    const declared = value.get("Length");
    const length = declared instanceof Ref ? (lengths ? integerOf(this.resolve(declared)) : null) : integerOf(declared);
    let end = -1;
    if (length !== null && start + length <= this.s.length) {
      const after = new Reader(this.s, start + length);
      after.skip();
      if (this.s.startsWith("endstream", after.at)) end = start + length;
    }
    if (end < 0) {
      const marker = this.s.indexOf("endstream", start);
      if (marker < 0) throw new Error("unclosed stream");
      end = marker;
      if (this.s.charCodeAt(end - 1) === 10) end--;
      if (this.s.charCodeAt(end - 1) === 13) end--;
      end = Math.max(start, end);
    }
    const close = this.s.indexOf("endstream", end);
    return { value: new Stream(value, this.bytes.subarray(start, end)), end: close < 0 ? end : close + "endstream".length };
  }

  // The object numbers an object stream holds, in order, with where each starts in its decoded data.
  private pack(num: number): Pack | null {
    if (this.unpacked.has(num)) return this.unpacked.get(num)!;
    this.unpacked.set(num, null);
    let result: Pack | null = null;
    try {
      const place = this.places.get(num);
      const stream = place && "offset" in place ? this.objectAt(place.offset).value : null;
      const data = stream instanceof Stream ? decoded(stream, this) : null;
      const count = stream instanceof Stream ? integerOf(this.resolve(stream.dict.get("N"))) : null;
      const first = stream instanceof Stream ? integerOf(this.resolve(stream.dict.get("First"))) : null;
      if (data && count !== null && first !== null) {
        const text = data.toString("latin1");
        const reader = new Reader(text);
        const header: Array<[number, number]> = [];
        for (let i = 0; i < count; i++) {
          reader.skip();
          const objectNum = reader.word();
          reader.skip();
          const at = reader.word();
          if (!DIGITS.test(objectNum) || !DIGITS.test(at)) break;
          header.push([Number(objectNum), Number(at)]);
        }
        result = { text, first, header };
      }
    } catch { result = null; }
    this.unpacked.set(num, result);
    return result;
  }
  private packHeader(num: number): Array<[number, number]> | null {
    return this.pack(num)?.header ?? null;
  }

  get(num: number): Value | undefined {
    if (this.values.has(num)) return this.values.get(num) ?? undefined;
    this.values.set(num, null);
    let value: Value | undefined;
    try {
      const place = this.places.get(num);
      if (place && "offset" in place) value = this.objectAt(place.offset).value;
      else if (place) {
        const pack = this.pack(place.stream);
        const entry = pack?.header[place.index];
        if (pack && entry) value = new Reader(pack.text, pack.first + entry[1]).value();
      }
    } catch { value = undefined; }
    this.values.set(num, value ?? null);
    return value;
  }

  resolve(value: Value | undefined): Value | undefined {
    for (let hops = 0; value instanceof Ref && hops < 32; hops++) value = this.get(value.num);
    return value instanceof Ref ? undefined : value;
  }

  // The newest trailer that names the catalog (a classic trailer or a cross-reference stream's dictionary).
  private trailer(): Dict | null {
    const named = this.trailers.filter((trailer) => trailer.dict.get("Root") instanceof Ref).sort((a, b) => b.at - a.at);
    return named[0]?.dict ?? null;
  }
  get encrypted(): boolean {
    return this.trailers.some((trailer) => trailer.dict.get("Encrypt") !== undefined);
  }
  get rootNum(): number | null {
    const root = this.trailer()?.get("Root");
    if (root instanceof Ref && this.resolve(root) instanceof Dict) return root.num;
    // No trailer to go by: the newest catalog written.
    let best: { num: number; at: number } | null = null;
    for (const [num, place] of this.places) {
      if (best && place.at < best.at) continue;
      const value = this.get(num);
      if (value instanceof Dict && nameOf(value.get("Type")) === "/Catalog") best = { num, at: place.at };
    }
    return best?.num ?? null;
  }

  // The pages in order, each with what it takes from the tree above it; `nodes`, the tree's own objects.
  pages(): { list: PdfPage[]; nodes: Set<number>; root: number } | null {
    const root = this.rootNum;
    const catalog = root === null ? undefined : this.get(root);
    const top = catalog instanceof Dict ? catalog.get("Pages") : undefined;
    if (!(top instanceof Ref) || root === null) return null;
    const list: PdfPage[] = [];
    const nodes = new Set<number>();
    const seen = new Set<number>();
    const walk = (ref: Ref, inherited: Map<string, Value>, depth: number) => {
      if (depth > MAX_DEPTH || seen.has(ref.num) || list.length >= MAX_PAGES) return;
      seen.add(ref.num);
      const node = this.resolve(ref);
      if (!(node instanceof Dict)) return;
      const kids = this.resolve(node.get("Kids"));
      const type = nameOf(node.get("Type"));
      if (type === "/Pages" || (type !== "/Page" && Array.isArray(kids))) {
        nodes.add(ref.num);
        const passed = new Map(inherited);
        for (const key of INHERITED) { const value = node.get(key); if (value !== undefined) passed.set(key, value); }
        if (Array.isArray(kids)) for (const kid of kids) if (kid instanceof Ref) walk(kid, passed, depth + 1);
        return;
      }
      list.push({ num: ref.num, dict: node, inherited });
    };
    walk(top, new Map(), 0);
    return list.length ? { list, nodes, root } : null;
  }

  // Whether resources hold a font, here or in a form they draw (a scan's pages hold only images).
  hasFont(resources: Value | undefined, depth = 0): boolean {
    const dict = this.resolve(resources);
    if (!(dict instanceof Dict)) return false;
    const fonts = this.resolve(dict.get("Font"));
    if (fonts instanceof Dict && fonts.entries.size > 0) return true;
    const objects = depth < 3 ? this.resolve(dict.get("XObject")) : undefined;
    if (!(objects instanceof Dict)) return false;
    for (const entry of objects.entries.values()) {
      const object = this.resolve(entry);
      if (object instanceof Stream && nameOf(object.dict.get("Subtype")) === "/Form" && this.hasFont(object.dict.get("Resources"), depth + 1)) return true;
    }
    return false;
  }
}

// A stream's data decoded: Flate only (what object streams use), without predictors.
function decoded(stream: Stream, doc: Doc): Buffer | null {
  const filter = doc.resolve(stream.dict.get("Filter"));
  const filters = filter === undefined ? [] : Array.isArray(filter) ? filter : [filter];
  const parms = doc.resolve(stream.dict.get("DecodeParms"));
  const predictors = (Array.isArray(parms) ? parms : [parms]).map((entry) => (entry instanceof Dict ? integerOf(doc.resolve(entry.get("Predictor"))) ?? 1 : 1));
  if (predictors.some((predictor) => predictor > 1)) return null;
  let data = stream.data;
  for (const entry of filters) {
    const name = nameOf(doc.resolve(entry));
    if (name !== "/FlateDecode" && name !== "/Fl") return null;
    data = inflateSync(data, { finishFlush: constants.Z_SYNC_FLUSH, maxOutputLength: MAX_INFLATED });
  }
  return data;
}

function open(bytes: Buffer): Doc | null {
  if (!bytes.subarray(0, 1024).toString("latin1").includes("%PDF-")) return null;
  try { return new Doc(bytes); } catch { return null; }
}

// pages: how many; textPages: how many carry a font (a scan's carry none, one with recognized text carries one).
export type PdfFacts = { pages: number; textPages: number };

export function pdfFacts(bytes: Buffer): PdfFacts | null {
  const doc = open(bytes);
  const tree = doc?.pages();
  if (!doc || !tree) return null;
  let textPages = 0;
  for (const page of tree.list) if (doc.hasFont(page.dict.get("Resources") ?? page.inherited.get("Resources"))) textPages++;
  return { pages: tree.list.length, textPages };
}

// Page numbers from what the model asked for: "3", "2-4", "1,3,5-6" (en or em dashes, Chinese commas, spaces), within
// 1..count, in order and once each. null when it names none of them.
export function pagesWanted(spec: string, count: number): number[] | null {
  const pages = new Set<number>();
  for (const part of spec.split(/[,，、;；\s]+/).filter(Boolean)) {
    const range = /^(?:p\.?|page|第)?\s*(\d+)\s*(?:页)?(?:\s*[-–—~～至到]\s*(?:p\.?|page|第)?\s*(\d+)\s*(?:页)?)?$/i.exec(part);
    if (!range) continue;
    const first = Number(range[1]);
    const last = range[2] === undefined ? first : Number(range[2]);
    for (let page = Math.max(1, Math.min(first, last)); page <= Math.min(count, Math.max(first, last)); page++) pages.add(page);
  }
  return pages.size ? [...pages].sort((a, b) => a - b) : null;
}

// A new PDF with only `wanted` (page numbers from 1, in order): a catalog, a page tree, those pages with what they took
// from the tree above them made their own, and everything they use, renumbered. A reference to another page or to the
// old tree becomes null (a link to a page left out leads nowhere). Streams are copied as they are, still compressed.
// null when the file cannot be read that far, is encrypted, or the copy does not read back with those pages.
export function pdfWithPages(bytes: Buffer, wanted: number[]): Buffer | null {
  const doc = open(bytes);
  if (!doc || doc.encrypted) return null;
  const tree = doc.pages();
  if (!tree || !wanted.length) return null;
  const chosen = wanted.map((page) => tree.list[page - 1]);
  if (chosen.some((page) => !page)) return null;
  const pageNums = new Set(tree.list.map((page) => page.num));
  const blocked = new Set([...tree.nodes, tree.root]);
  const numbers = new Map<number, number>();
  chosen.forEach((page, at) => numbers.set(page.num, 3 + at));
  let next = 3 + chosen.length;
  const queue: number[] = [];
  const ref = (value: Ref): string => {
    if (pageNums.has(value.num) || blocked.has(value.num)) { const own = numbers.get(value.num); return own ? `${own} 0 R` : "null"; }
    if (!doc.places.has(value.num)) return "null";
    let own = numbers.get(value.num);
    if (!own) { own = next++; numbers.set(value.num, own); queue.push(value.num); }
    return `${own} 0 R`;
  };
  const text = (value: Value): string => {
    if (value instanceof Ref) return ref(value);
    if (value instanceof Name || value instanceof Raw) return value.raw;
    if (value instanceof Dict) return `<<${[...value.entries].map(([key, entry]) => `/${key} ${text(entry)}`).join(" ")}>>`;
    if (Array.isArray(value)) return `[${value.map(text).join(" ")}]`;
    return "null";
  };
  const version = /%PDF-(\d\.\d)/.exec(doc.s.slice(0, 1024))?.[1] ?? "1.7";
  const parts: Buffer[] = [Buffer.from(`%PDF-${version}\n%\xE2\xE3\xCF\xD3\n`, "latin1")];
  let size = parts[0].length;
  const offsets = new Map<number, number>();
  const add = (num: number, ...chunks: Array<string | Buffer>) => {
    offsets.set(num, size);
    for (const chunk of [`${num} 0 obj\n`, ...chunks, "\nendobj\n"]) {
      const buffer = typeof chunk === "string" ? Buffer.from(chunk, "latin1") : chunk;
      parts.push(buffer);
      size += buffer.length;
    }
  };
  add(1, "<</Type /Catalog /Pages 2 0 R>>");
  add(2, `<</Type /Pages /Kids [${chosen.map((_, at) => `${3 + at} 0 R`).join(" ")}] /Count ${chosen.length}>>`);
  chosen.forEach((page, at) => {
    const entries = new Map([...page.dict.entries].filter(([key]) => key !== "Parent" && key !== "B"));
    for (const key of INHERITED) if (!entries.has(key) && page.inherited.has(key)) entries.set(key, page.inherited.get(key)!);
    add(3 + at, `<</Parent 2 0 R ${[...entries].map(([key, entry]) => `/${key} ${text(entry)}`).join(" ")}>>`);
  });
  while (queue.length) {
    const num = queue.shift()!;
    const value = doc.get(num);
    const own = numbers.get(num)!;
    if (value instanceof Stream) {
      const entries = [...value.dict.entries].filter(([key]) => key !== "Length").map(([key, entry]) => `/${key} ${text(entry)}`);
      add(own, `<<${[...entries, `/Length ${value.data.length}`].join(" ")}>>\nstream\n`, value.data, "\nendstream");
    } else add(own, value === undefined ? "null" : text(value));
  }
  const count = next;
  const table = [`xref\n0 ${count}\n0000000000 65535 f \n`];
  for (let num = 1; num < count; num++) table.push(`${String(offsets.get(num) ?? 0).padStart(10, "0")} ${offsets.has(num) ? "00000 n" : "65535 f"} \n`);
  parts.push(Buffer.from(`${table.join("")}trailer\n<</Size ${count} /Root 1 0 R>>\nstartxref\n${size}\n%%EOF\n`, "latin1"));
  const out = Buffer.concat(parts);
  return pdfFacts(out)?.pages === chosen.length ? out : null;
}
