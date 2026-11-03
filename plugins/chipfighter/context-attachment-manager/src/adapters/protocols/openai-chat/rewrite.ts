// Purpose: v0.11 — the OpenAI Chat Completions request format (WorkBuddy, and OpenAI-compatible providers of OpenCode,
// pi, …; docs/v0.11/plan.md 3.8): where its images are, which turn each belongs to, and the core's plan put into the
// messages. Images are `image_url` parts with a data URL (a link to elsewhere is left alone), in user messages and, for
// clients that send them there, in tool messages. A turn starts with each user message that has text of its own. The
// text for the model goes in as text parts of the messages that held the images: every Chat Completions server takes
// that, while a system message in mid-conversation is not taken everywhere.
// Input: the request's messages. Output: its images with their turns; new messages and a report.

import { fetchedIdIn, imageDigest, type ImageDigest, type ImageKind } from "../../../core/images.ts";
import { planRewrite, type PlanOptions, type RewriteReport } from "../../../core/plan.ts";
import { autoNote, featureNote, omissionNote, type Described } from "../../../core/words.ts";

type Json = Record<string, any>;
// msg: the message; part: the part in its content. turn: 1 for the first prompt's turn. fetchedOf: the id our fetch
// tool's line right before it names. data: raw base64.
export type ChatImage = ImageDigest & { key: string; kind: ImageKind; name: null; label: null; replaceable: true; msg: number; part: number; turn: number; fetchedOf: string | null; data: string };

const DATA_URL = /^data:([^;,]+);base64,(.*)$/s;
const urlOf = (part: Json): string | null => (typeof part?.image_url === "string" ? part.image_url : typeof part?.image_url?.url === "string" ? part.image_url.url : null);
const textOf = (part: Json): string => (part?.type === "text" && typeof part.text === "string" ? part.text : "");
const hasOwnText = (message: Json) => (typeof message?.content === "string" ? message.content.trim() !== "" : Array.isArray(message?.content) && message.content.some((part: Json) => textOf(part).trim() !== ""));

// turns: how many prompts the request has (the current turn). first: the first prompt's text.
export function chatImages(messages: Json[]): { images: ChatImage[]; turns: number; first: string } {
  const images: ChatImage[] = [];
  let turns = 0;
  let first = "";
  messages.forEach((message, msg) => {
    if (message?.role === "user" && hasOwnText(message)) {
      turns++;
      if (turns === 1) first = typeof message.content === "string" ? message.content : message.content.map(textOf).join("\n");
    }
    if ((message?.role !== "user" && message?.role !== "tool") || !Array.isArray(message.content)) return;
    message.content.forEach((part: Json, at: number) => {
      const found = part?.type === "image_url" ? DATA_URL.exec(urlOf(part) ?? "") : null;
      if (!found) return;
      const before = at > 0 ? textOf(message.content[at - 1]) : "";
      const kind: ImageKind = message.role === "user" && hasOwnText(message) ? "upload" : "tool";
      images.push({ ...imageDigest(part, found[2], found[1]), key: `m${msg}:p${at}`, kind, name: null, label: null, replaceable: true, msg, part: at, turn: Math.max(turns, 1), fetchedOf: before ? fetchedIdIn(before) : null, data: found[2] });
    });
  });
  return { images, turns: Math.max(turns, 1), first };
}

export function rewriteChat(
  messages: Json[],
  images: ChatImage[],
  describe: (image: ChatImage) => Described | undefined,
  leaveOut: Set<string>,
  pixelHash: (image: ChatImage) => string | null,
  options: PlanOptions<ChatImage> = {},
): { messages: Json[]; report: RewriteReport } {
  const { lang = "zh", auto } = options;
  const plan = planRewrite(images, describe, leaveOut, pixelHash, options);
  const { report } = plan;
  if (!plan.changed) return { messages, report };
  // Each edit puts one text part at `at`, in place of `remove` parts (none for a label).
  const edits = new Map<number, Array<{ at: number; remove: number; text: string }>>();
  for (const { slot, what, text } of plan.actions) {
    const image = images[slot];
    edits.set(image.msg, [...(edits.get(image.msg) ?? []), { at: image.part, remove: what === "label" ? 0 : 1, text }]);
  }
  // The note on omitted images goes first in the message holding the first of them; the feature line note (v0.8), first
  // in the prompt of the turn holding the first image the index knows.
  const noteIn = plan.plain.length ? images[plan.plain[0].slot].msg : null;
  const prompts = messages.flatMap((message, msg) => (message?.role === "user" && hasOwnText(message) ? [msg] : []));
  const featureIn = plan.first !== null ? prompts[images[plan.first].turn - 1] ?? images[plan.first].msg : null;
  const next = messages.map((message, msg) => {
    const list = edits.get(msg);
    if (!list && msg !== featureIn) return message;
    const parts: Json[] = typeof message.content === "string" ? [{ type: "text", text: message.content }] : [...message.content];
    // Later positions first; at one position, a replacement before the label that goes in front of it.
    for (const { at, remove, text } of (list ?? []).sort((a, b) => b.at - a.at || b.remove - a.remove)) parts.splice(at, remove, { type: "text", text });
    if (msg === noteIn) parts.unshift({ type: "text", text: auto ? autoNote(lang) : omissionNote(lang) });
    if (msg === featureIn) parts.unshift({ type: "text", text: featureNote(lang) });
    return { ...message, content: parts };
  });
  if (noteIn !== null) report.noteAt = noteIn;
  if (featureIn !== null) report.featureAt = featureIn;
  return { messages: next, report };
}
