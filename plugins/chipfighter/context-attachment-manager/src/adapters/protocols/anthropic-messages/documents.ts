// Purpose: v0.13 — PDFs in an Anthropic Messages request (Claude Code; docs/design.md §14). Claude Code's Read puts a
// whole PDF into its tool result as a document block, and every later request sends it again. A PDF the platform says
// to leave out goes out as a placeholder, and the message holding it is followed by a note naming it (the first such
// message by the full note too, as for images: rewrite.ts). The model gets pages back with the fetch tool
// (cam_view_image): its result carries a marker per PDF (core/words.ts, PDF_MARKER), which the engine replaces with the
// pages cut from the file (core/pdf.ts). Those pages stay there in later turns: a line in their place was read as all
// the tool had returned, and the answer given from them was taken back (2026-11-23, Haiku 5.5 and once Sonnet 5.5); the
// few pages asked for cost little, and the cached prefix stays as it was.
// Input: the request's messages, what the platform knows of each PDF. Output: new messages and a report.

import type { Lang } from "../../../core/lang.ts";
import { pagesWanted } from "../../../core/pdf.ts";
import { claudeFetchWords, PDF_MARKER, pdfFetchedLabel, pdfNote, pdfPlaceholder, type PdfDescribed, type PdfNoted } from "../../../core/words.ts";
import { noteAfter } from "./rewrite.ts";

type Json = Record<string, any>;

export const isPdfBlock = (block: Json): boolean => block?.type === "document" && block.source?.type === "base64" && block.source?.media_type === "application/pdf" && typeof block.source?.data === "string";

// A PDF of the request: its message, its block there, its place inside a tool result, and for one in a tool result
// the key "tool:<tool_use_id>#<n>" (n counting the PDFs of that result; null for one in a message itself).
export type RequestPdf = { msg: number; part: number; sub: number | null; key: string | null; block: Json };

export function pdfBlocks(messages: Json[]): RequestPdf[] {
  const found: RequestPdf[] = [];
  messages.forEach((message, msg) => {
    if (message?.role !== "user" || !Array.isArray(message.content)) return;
    message.content.forEach((block: Json, part: number) => {
      if (isPdfBlock(block)) found.push({ msg, part, sub: null, key: null, block });
      if (block?.type !== "tool_result" || !Array.isArray(block.content)) return;
      let n = 0;
      block.content.forEach((inner: Json, sub: number) => {
        if (isPdfBlock(inner)) found.push({ msg, part, sub, key: `tool:${String(block.tool_use_id ?? "")}#${n++}`, block: inner });
      });
    });
  });
  return found;
}

// Whether the model replied after message `msg` and a new turn has begun since: a later user message that holds no
// tool result (a prompt) after an assistant message.
export function turnsAfter(messages: Json[], msg: number): boolean {
  let replied = false;
  for (let at = msg + 1; at < messages.length; at++) {
    const message = messages[at];
    if (message?.role === "assistant") replied = true;
    else if (replied && message?.role === "user" && !(Array.isArray(message.content) && message.content.some((block: Json) => block?.type === "tool_result"))) return true;
  }
  return false;
}

// The fetch tool, whatever prefix Claude Code gives an MCP server's tools; the calls of it in a request, with their input.
const FETCH_TOOL = /(?:^|__)cam_view_image$/;
export function fetchCalls(messages: Json[]): Map<string, Json> {
  const calls = new Map<string, Json>();
  for (const message of messages) {
    if (message?.role !== "assistant" || !Array.isArray(message.content)) continue;
    for (const block of message.content) if (block?.type === "tool_use" && FETCH_TOOL.test(String(block.name ?? "")) && block.id) calls.set(String(block.id), block.input ?? {});
  }
  return calls;
}
const pagesOf = (value: unknown): string | null => (typeof value === "number" ? String(value) : Array.isArray(value) ? value.join(",") : typeof value === "string" && value.trim() ? value.trim() : null);

// What the platform knows. pdf: a PDF of the request (null: unknown, sent as it is) and whether it is left out.
// describe: a PDF by id. file: its data, only `pages` of it when it can cut them (pages null: the whole file).
export type PdfSource = {
  pdf: (ref: RequestPdf) => { described: PdfDescribed; leaveOut: boolean } | null;
  describe: (id: string) => PdfDescribed | undefined;
  file: (id: string, pages: number[] | null) => { data: string; pages: number[] | null } | null;
};
export type PdfReport = { replaced: string[]; replacedChars: number; fetched: Array<{ id: string; pages: number[] | null }>; unavailable: string[] };

export function rewritePdfs(messages: Json[], source: PdfSource, lang: Lang = "zh"): { messages: Json[]; report: PdfReport; changed: boolean } {
  const report: PdfReport = { replaced: [], replacedChars: 0, fetched: [], unavailable: [] };
  // Edits per content array, as in rewrite.ts: the message's own ("3") or a tool result's ("3:1"); each block replaced.
  const edits = new Map<string, Map<number, Json[]>>();
  const edit = (where: string, at: number, blocks: Json[]) => {
    const list = edits.get(where) ?? new Map<number, Json[]>();
    list.set(at, blocks);
    edits.set(where, list);
  };
  // The PDFs each message holds placeholders of, for the notes after it.
  const held = new Map<number, PdfNoted[]>();
  for (const ref of pdfBlocks(messages)) {
    const choice = source.pdf(ref);
    if (!choice?.leaveOut) continue;
    const carried = ref.block.cache_control ? { cache_control: ref.block.cache_control } : {};
    edit(ref.sub === null ? `${ref.msg}` : `${ref.msg}:${ref.part}`, ref.sub ?? ref.part, [{ type: "text", text: pdfPlaceholder(choice.described, lang), ...carried }]);
    report.replaced.push(choice.described.id);
    report.replacedChars += ref.block.source.data.length;
    const list = held.get(ref.msg) ?? [];
    if (!list.some((other) => other.id === choice.described.id)) list.push({ id: choice.described.id, name: choice.described.name });
    held.set(ref.msg, list);
  }
  // Fetches: the markers in each fetch call's result.
  const calls = fetchCalls(messages);
  if (calls.size) {
    messages.forEach((message, msg) => {
      if (message?.role !== "user" || !Array.isArray(message.content)) return;
      message.content.forEach((block: Json, part: number) => {
        if (block?.type !== "tool_result" || !calls.has(String(block.tool_use_id))) return;
        const content = typeof block.content === "string" ? [{ type: "text", text: block.content }] : Array.isArray(block.content) ? block.content : [];
        const replaced = fetchedPages(content, calls.get(String(block.tool_use_id))!, source, lang, report);
        if (replaced) edit(`${msg}`, part, [{ ...block, content: replaced }]);
      });
    });
  }
  if (!edits.size) return { messages, report, changed: false };
  const apply = (blocks: Json[], list: Map<number, Json[]>) => blocks.flatMap((block, at) => list.get(at) ?? [block]);
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
  // Later messages first, so the earlier positions stay as they are; the first one also gets the full note.
  const holding = [...held.keys()].sort((a, b) => a - b);
  for (const msg of [...holding].reverse()) noteAfter(next, msg, pdfNote(held.get(msg)!, lang, msg === holding[0]));
  return { messages: next, report, changed: true };
}

// A fetch call's result with each PDF marker replaced by a line naming the pages and the pages themselves; null when it
// holds no marker.
function fetchedPages(content: Json[], input: Json, source: PdfSource, lang: Lang, report: PdfReport): Json[] | null {
  const spec = pagesOf(input.pages);
  let touched = false;
  const out: Json[] = [];
  for (const block of content) {
    const lines = block?.type === "text" && typeof block.text === "string" ? block.text.split("\n") : null;
    if (!lines?.some((line) => PDF_MARKER.test(line))) { out.push(block); continue; }
    touched = true;
    const start = out.length;
    let pending: string[] = [];
    const flush = () => { if (pending.length) out.push({ type: "text", text: pending.join("\n") }); pending = []; };
    for (const line of lines) {
      const id = PDF_MARKER.exec(line)?.[1];
      if (!id) { pending.push(line); continue; }
      const pdf = source.describe(id);
      const wanted = pdf?.pages && spec ? pagesWanted(spec, pdf.pages) : null;
      const some = wanted && pdf?.pages && wanted.length < pdf.pages ? wanted : null;
      const file = pdf ? source.file(id, some) : null;
      if (!pdf || !file) { pending.push(claudeFetchWords(lang).pdfUnavailable(id)); report.unavailable.push(id); continue; }
      flush();
      out.push({ type: "text", text: pdfFetchedLabel(pdf, file.pages, lang) }, { type: "document", source: { type: "base64", media_type: "application/pdf", data: file.data } });
      report.fetched.push({ id, pages: file.pages });
    }
    flush();
    // A cache mark the marker's block carried stays at the end of what replaced it.
    if (block.cache_control && out.length > start) out[out.length - 1] = { ...out[out.length - 1], cache_control: block.cache_control };
  }
  return touched ? out : null;
}
