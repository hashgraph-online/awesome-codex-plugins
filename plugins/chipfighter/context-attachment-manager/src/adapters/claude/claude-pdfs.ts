// Purpose: v0.13 — what the engine knows of a Claude Code session's PDFs (docs/design.md §14): each PDF of a request as
// the session's index has it (claude-index.ts); whether it goes out as a placeholder (read in an earlier turn, with
// automatic selection on); what its placeholder says of it (core/pdf.ts, kept per content); and the pages a fetch asks
// for, cut from the file (kept a while, since every later request sends them again).
// Input: the session's index, the request's messages and turn, whether automatic selection is on. Output: a PdfSource
// for the Anthropic Messages translator (anthropic-messages/documents.ts).

import { imageDigest } from "../../core/images.ts";
import { pdfFacts, pdfWithPages, type PdfFacts } from "../../core/pdf.ts";
import type { PdfDescribed } from "../../core/words.ts";
import { turnsAfter, type PdfSource } from "../protocols/anthropic-messages/documents.ts";
import { claudePdfData, type ClaudeIndex, type ClaudePdf } from "./claude-index.ts";

type Json = Record<string, any>;

const facts = new Map<string, PdfFacts | null>();
const cuts = new Map<string, Buffer | null>();
function remember<T>(map: Map<string, T>, key: string, value: T, max: number): void {
  map.delete(key);
  map.set(key, value);
  if (map.size > max) map.delete(map.keys().next().value!);
}

// Pages and how many carry text, read once per content (null: the file could not be read).
export function factsOf(pdf: ClaudePdf): PdfFacts | null {
  if (facts.has(pdf.contentId)) return facts.get(pdf.contentId)!;
  const data = claudePdfData(pdf);
  if (!data) return null;
  const found = pdfFacts(Buffer.from(data, "base64"));
  remember(facts, pdf.contentId, found, 256);
  return found;
}

// turn: the turn this read of it was in (a placeholder names it), by default the first; said: the reply that ended it.
export function describePdf(pdf: ClaudePdf, turn: number | null = pdf.turn, said: string | null = null): PdfDescribed {
  const known = factsOf(pdf);
  return { id: pdf.id, name: pdf.name, turn, pages: known?.pages ?? null, textPages: known?.textPages ?? null, ...(said ? { said } : {}) };
}

export type PdfIndex = Partial<Pick<ClaudeIndex, "pdfs" | "pdfByContent" | "pdfReads">>;

// A later turn has begun after message `msg` by the records (its turn is before the request's), or by the request
// itself: Claude Code may send a turn's first request a moment before its prompt reaches the transcript (2026-11-23,
// 16–21 ms in a headless run), and the records still say the turn before is the current one.
export function claudePdfSource(index: PdfIndex, messages: Json[], current: number, auto: boolean): PdfSource {
  const byId = new Map((index.pdfs ?? []).map((pdf) => [pdf.id, pdf]));
  const earlier = (turn: number | null | undefined, msg: number) => (turn !== null && turn !== undefined && turn < current) || turnsAfter(messages, msg);
  return {
    pdf: (ref) => {
      if (ref.key) {
        const read = index.pdfReads?.get(ref.key);
        if (!read) return null;
        return { described: describePdf(read.pdf, read.turn, read.said ?? null), leaveOut: auto && earlier(read.turn, ref.msg) };
      }
      // One in a message itself (a PDF named with @): known by its content; left out once a later turn has begun.
      const pdf = index.pdfByContent?.get(imageDigest(ref.block, ref.block.source.data, "application/pdf").contentId);
      return pdf ? { described: describePdf(pdf), leaveOut: auto && turnsAfter(messages, ref.msg) } : null;
    },
    describe: (id) => {
      const pdf = byId.get(id);
      return pdf ? describePdf(pdf) : undefined;
    },
    file: (id, pages) => {
      const pdf = byId.get(id);
      const data = pdf ? claudePdfData(pdf) : null;
      if (!pdf || !data) return null;
      if (!pages) return { data, pages: null };
      const key = `${pdf.contentId}:${pages.join(",")}`;
      if (!cuts.has(key)) remember(cuts, key, pdfWithPages(Buffer.from(data, "base64"), pages), 16);
      const cut = cuts.get(key);
      return cut ? { data: cut.toString("base64"), pages } : { data, pages: null };
    },
  };
}
