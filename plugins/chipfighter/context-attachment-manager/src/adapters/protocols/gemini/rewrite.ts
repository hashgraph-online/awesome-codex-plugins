// Purpose: v0.11 — the Gemini generateContent request format (Gemini CLI, and the Google provider of other clients;
// docs/v0.11/plan.md 3.8): where its images are, which turn each belongs to, and the core's plan put into the contents.
// Images are `inlineData` parts of user contents (a file reference is left alone); the user content that answers a
// function call holds no prompt. A turn starts with each user content that has text and answers no call. Gemini takes
// no system text in mid-conversation, so the text for the model goes in as text parts of the content that held the
// images. Gemini CLI signed in with Google sends the same contents inside `request` (Code Assist).
// Input: the request's contents. Output: its images with their turns; new contents and a report.

import { fetchedIdIn, imageDigest, type ImageDigest, type ImageKind } from "../../../core/images.ts";
import { planRewrite, type PlanOptions, type RewriteReport } from "../../../core/plan.ts";
import { autoNote, featureNote, omissionNote, type Described } from "../../../core/words.ts";

type Json = Record<string, any>;
export type GeminiImage = ImageDigest & { key: string; kind: ImageKind; name: null; label: null; replaceable: true; msg: number; part: number; turn: number; fetchedOf: string | null; data: string };

const textOf = (part: Json): string => (typeof part?.text === "string" && !part.thought ? part.text : "");
const isPrompt = (content: Json) => content?.role === "user" && Array.isArray(content.parts) && content.parts.some((part: Json) => textOf(part).trim() !== "") && !content.parts.some((part: Json) => part?.functionResponse);

// Where the contents are: at the top, or inside `request` (Code Assist).
export function geminiContents(body: Json): Json[] | null {
  if (Array.isArray(body?.contents)) return body.contents;
  if (Array.isArray(body?.request?.contents)) return body.request.contents;
  return null;
}
export function withContents(body: Json, contents: Json[]): Json {
  return Array.isArray(body?.contents) ? { ...body, contents } : { ...body, request: { ...body.request, contents } };
}

export function geminiImages(contents: Json[]): { images: GeminiImage[]; turns: number; first: string } {
  const images: GeminiImage[] = [];
  let turns = 0;
  let first = "";
  contents.forEach((content, msg) => {
    const prompt = isPrompt(content);
    if (prompt) {
      turns++;
      if (turns === 1) first = content.parts.map(textOf).join("\n");
    }
    if (content?.role !== "user" || !Array.isArray(content.parts)) return;
    content.parts.forEach((part: Json, at: number) => {
      const inline = part?.inlineData;
      if (!inline || typeof inline.data !== "string" || !/^image\//.test(String(inline.mimeType ?? ""))) return;
      const before = at > 0 ? textOf(content.parts[at - 1]) : "";
      images.push({ ...imageDigest(part, inline.data, inline.mimeType), key: `c${msg}:p${at}`, kind: prompt ? "upload" : "tool", name: null, label: null, replaceable: true, msg, part: at, turn: Math.max(turns, 1), fetchedOf: before ? fetchedIdIn(before) : null, data: inline.data });
    });
  });
  return { images, turns: Math.max(turns, 1), first };
}

export function rewriteGemini(
  contents: Json[],
  images: GeminiImage[],
  describe: (image: GeminiImage) => Described | undefined,
  leaveOut: Set<string>,
  pixelHash: (image: GeminiImage) => string | null,
  options: PlanOptions<GeminiImage> = {},
): { contents: Json[]; report: RewriteReport } {
  const { lang = "zh", auto } = options;
  const plan = planRewrite(images, describe, leaveOut, pixelHash, options);
  const { report } = plan;
  if (!plan.changed) return { contents, report };
  const edits = new Map<number, Array<{ at: number; remove: number; text: string }>>();
  for (const { slot, what, text } of plan.actions) {
    const image = images[slot];
    edits.set(image.msg, [...(edits.get(image.msg) ?? []), { at: image.part, remove: what === "label" ? 0 : 1, text }]);
  }
  // The note on omitted images goes first in the content holding the first of them; the feature line note (v0.8), first
  // in the prompt of the turn holding the first image the index knows.
  const noteIn = plan.plain.length ? images[plan.plain[0].slot].msg : null;
  const prompts = contents.flatMap((content, msg) => (isPrompt(content) ? [msg] : []));
  const featureIn = plan.first !== null ? prompts[images[plan.first].turn - 1] ?? images[plan.first].msg : null;
  const next = contents.map((content, msg) => {
    const list = edits.get(msg);
    if (!list && msg !== featureIn) return content;
    const parts: Json[] = [...content.parts];
    for (const { at, remove, text } of (list ?? []).sort((a, b) => b.at - a.at || b.remove - a.remove)) parts.splice(at, remove, { text });
    if (msg === noteIn) parts.unshift({ text: auto ? autoNote(lang) : omissionNote(lang) });
    if (msg === featureIn) parts.unshift({ text: featureNote(lang) });
    return { ...content, parts };
  });
  if (noteIn !== null) report.noteAt = noteIn;
  if (featureIn !== null) report.featureAt = featureIn;
  return { contents: next, report };
}
