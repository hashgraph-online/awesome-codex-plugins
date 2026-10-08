// Purpose: P2 — find every image in a list of Responses items (a request's `input`, or a rollout's response_items)
// and describe it: a key that names the same occurrence in both places, its kind and name, and a content digest.
// v0.2 — the source the panel filters by: the kind, except for the screenshots Codex desktop attaches to a comment on a
// PDF page or a web page, told apart by the caption Codex writes before them. The text for the model does not use it.
// v0.3 — an image our fetch tool returned carries, in the line before it, the id it is a copy of (thread-index.ts).
// Input: items as parsed JSON. Output: ImageRef[] in item order (pure, no I/O).

import { createHash } from "node:crypto";

type Json = Record<string, any>;
export type ImageKind = "upload" | "view" | "generated" | "tool";
export type ImageSource = ImageKind | "pdf" | "browser";
export type ImageDigest = { contentId: string; mime: string | null; base64Chars: number; width: number | null; height: number | null };

export type ImageRef = ImageDigest & {
  key: string;
  item: number;
  // Index in the item's content/output array; null for a hosted image_generation_call result.
  part: number | null;
  // Codex's own `<image name=[Image #N] path="…">` and `</image>` parts around an upload, replaced together with it.
  openTag: number | null;
  closeTag: number | null;
  kind: ImageKind;
  // A hosted image_generation_call keeps its image in a required `result` field that cannot become text.
  replaceable: boolean;
  name: string | null;
  label: string | null;
  turnId: string | null;
  source: ImageSource;
  // A PDF comment screenshot's page (null when Codex does not say), and the PDF's file name when the message's comments
  // name only one PDF.
  pdfPage: number | null;
  pdfName: string | null;
  // v0.3: in a tool output, the id named by our fetch tool's line right before the image ("[图片 IMG-001 取回的原图｜…]").
  fetchedId: string | null;
};

// v0.3 — the state our fetch tool (cam_view_image) writes in the line before each image it returns, in either
// language, so the image is known as a copy of that id. The rest of the line is the usual heading (rewrite.ts).
export const FETCHED_STATE = { zh: "取回的原图", en: "fetched original" } as const;
const FETCHED_LINE = new RegExp(`^\\[(?:图片|Image) (IMG-\\d{3,}) (?:${FETCHED_STATE.zh}|${FETCHED_STATE.en})(?:｜| \\|)`);

const OPEN_TAG = /^<image name=(\[Image #\d+\]) path="(.*)">$/s;
// Codex desktop 26.924's own wording: the caption right before a comment's screenshot, and the line naming the PDF in
// the comment's text. Worded otherwise, a screenshot counts as an upload, as it did before v0.2.
const PDF_CAPTION = /^The next image shows (?:PDF page (\d+)|the PDF page) at the time of Comment \d+\./;
const BROWSER_CAPTION = /^The next image (?:shows the browser page at the time of|is untrusted page evidence from the browser page for) Comment \d+\./;
const PDF_PATH = /^PDF path: (.+)$/gm;

export function baseName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

// Width and height from the image header only, so large images are not decoded.
export function imageSize(bytes: Buffer): { width: number; height: number } | null {
  if (bytes.length >= 24 && bytes.readUInt32BE(0) === 0x89504e47) return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
  if (bytes.length >= 10 && bytes.toString("ascii", 0, 3) === "GIF") return { width: bytes.readUInt16LE(6), height: bytes.readUInt16LE(8) };
  if (bytes.length >= 30 && bytes.toString("ascii", 0, 4) === "RIFF" && bytes.toString("ascii", 8, 12) === "WEBP") {
    const chunk = bytes.toString("ascii", 12, 16);
    if (chunk === "VP8X") return { width: bytes.readUIntLE(24, 3) + 1, height: bytes.readUIntLE(27, 3) + 1 };
    if (chunk === "VP8 ") return { width: bytes.readUInt16LE(26) & 0x3fff, height: bytes.readUInt16LE(28) & 0x3fff };
    if (chunk === "VP8L") { const bits = bytes.readUInt32LE(21); return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 }; }
    return null;
  }
  if (bytes.length >= 4 && bytes[0] === 0xff && bytes[1] === 0xd8) {
    let offset = 2;
    while (offset + 9 < bytes.length) {
      if (bytes[offset] !== 0xff) return null;
      const marker = bytes[offset + 1];
      if (marker === 0xff) { offset++; continue; }
      const length = bytes.readUInt16BE(offset + 2);
      // SOF0–SOF15 carry the frame size, except DHT (C4), JPG (C8) and DAC (CC).
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) return { width: bytes.readUInt16BE(offset + 7), height: bytes.readUInt16BE(offset + 5) };
      offset += 2 + length;
    }
  }
  return null;
}

const digests = new WeakMap<object, ImageDigest>();

// Keyed by the part object, so re-reading the same cached rollout records does not hash the same images again.
function digest(owner: object, value: string, mime: string | null): ImageDigest {
  const known = digests.get(owner);
  if (known) return known;
  const header = Buffer.from(value.slice(0, 96 * 1024), "base64");
  const size = imageSize(header);
  const result = { contentId: createHash("sha256").update(value).digest("hex"), mime, base64Chars: value.length, width: size?.width ?? null, height: size?.height ?? null };
  digests.set(owner, result);
  return result;
}

function partDigest(part: Json): ImageDigest | null {
  if (part?.type !== "input_image" && part?.type !== "output_image") return null;
  if (typeof part.file_id === "string") return { contentId: `file:${part.file_id}`, mime: null, base64Chars: 0, width: null, height: null };
  const inline = typeof part.image_url === "string" ? /^data:([^;,]+);base64,/.exec(part.image_url) : null;
  return inline ? digest(part, part.image_url.slice(inline[0].length), inline[1]) : null;
}

// A tool output's images get names from the call that produced them: view_image paths, or the saved-image hint
// that Codex's image generation adds next to its result.
function toolContext(call: Json | undefined, output: Json[]): { kind: ImageKind; names: string[] } {
  const hints = output.flatMap((part) => (typeof part?.text === "string" ? [...part.text.matchAll(/Generated images are saved to .*? as (.+?\.png) by default/g)].map((m) => baseName(m[1])) : []));
  if (hints.length) return { kind: "generated", names: hints };
  if (!call) return { kind: "tool", names: [] };
  if (call.type === "function_call") {
    if (call.name === "view_image") {
      try { return { kind: "view", names: [baseName(JSON.parse(call.arguments).path)] }; } catch { return { kind: "view", names: [] }; }
    }
    return { kind: /imagegen|image_gen/.test(call.name ?? "") ? "generated" : "tool", names: [] };
  }
  const source = String(call.input ?? "");
  // Paths written inline are read; paths passed through variables leave the names unknown.
  const views = [...source.matchAll(/view_image\(\s*\{\s*path\s*:\s*(["'])((?:(?!\1)[^\\]|\\.)*)\1/g)].map((m) => baseName(m[2].replace(/\\(.)/g, "$1")));
  if (views.length || source.includes("view_image")) return { kind: "view", names: views };
  return { kind: /image_gen|imagegen|generatedImage\(/.test(source) ? "generated" : "tool", names: [] };
}

// The PDF a message's comments are about, when they name only one.
function onlyPdf(parts: Json[]): string | null {
  const paths = new Set(parts.flatMap((part) => (part?.type === "input_text" && typeof part.text === "string" ? [...part.text.matchAll(PDF_PATH)].map((m) => m[1].trim()) : [])));
  return paths.size === 1 ? baseName([...paths][0]) : null;
}

export function findImages(items: Json[]): ImageRef[] {
  const calls = new Map<string, Json>();
  const seenFallback = new Map<string, number>();
  const refs: ImageRef[] = [];
  items.forEach((item, index) => {
    if (!item || typeof item !== "object") return;
    if ((item.type === "function_call" || item.type === "custom_tool_call") && item.call_id) calls.set(item.call_id, item);
    const turnId: string | null = item.internal_chat_message_metadata_passthrough?.turn_id ?? null;
    const keyFor = (n: number, contentId: string) => {
      if (typeof item.id === "string" && item.id) return `${item.id}#${n}`;
      if (typeof item.call_id === "string" && item.call_id) return `${item.type}:${item.call_id}#${n}`;
      const base = `${item.type}:${item.role ?? ""}:${turnId ?? ""}:${contentId}`;
      const seen = seenFallback.get(base) ?? 0;
      seenFallback.set(base, seen + 1);
      return `${base}#${seen}`;
    };

    if (item.type === "image_generation_call" && typeof item.result === "string" && item.result) {
      const found = digest(item, item.result, "image/png");
      refs.push({ ...found, key: keyFor(0, found.contentId), item: index, part: null, openTag: null, closeTag: null, kind: "generated", replaceable: false, name: null, label: null, turnId, source: "generated", pdfPage: null, pdfName: null, fetchedId: null });
      return;
    }
    const field = item.type === "message" ? item.content : item.type === "function_call_output" || item.type === "custom_tool_call_output" ? item.output : null;
    if (!Array.isArray(field)) return;
    const context = item.type === "message" ? null : toolContext(calls.get(item.call_id), field);
    // Read once per message, and only for one with a PDF comment screenshot.
    let pdfName: string | null | undefined;
    let n = 0;
    field.forEach((part: Json, partIndex: number) => {
      const found = partDigest(part);
      if (!found) return;
      const before = field[partIndex - 1]?.type === "input_text" ? String(field[partIndex - 1].text) : null;
      const after = field[partIndex + 1]?.type === "input_text" ? String(field[partIndex + 1].text) : null;
      const open = before !== null && (OPEN_TAG.test(before) || before === "<image>");
      const close = open && after === "</image>";
      const tag = before ? OPEN_TAG.exec(before) : null;
      const kind: ImageKind = context?.kind ?? (item.role === "user" ? "upload" : "tool");
      // A caption counts only as its own text part right before an image in the user's message.
      const pdf = kind === "upload" ? before?.match(PDF_CAPTION) : null;
      const source: ImageSource = pdf ? "pdf" : kind === "upload" && before !== null && BROWSER_CAPTION.test(before) ? "browser" : kind;
      if (pdf && pdfName === undefined) pdfName = onlyPdf(field);
      refs.push({
        ...found,
        key: keyFor(n, found.contentId),
        item: index,
        part: partIndex,
        openTag: open ? partIndex - 1 : null,
        closeTag: close ? partIndex + 1 : null,
        kind,
        replaceable: true,
        name: tag ? baseName(tag[2]) : context?.names[n] ?? null,
        label: tag ? tag[1] : null,
        turnId,
        source,
        pdfPage: pdf?.[1] ? Number(pdf[1]) : null,
        pdfName: pdf ? pdfName ?? null : null,
        fetchedId: context && before !== null ? FETCHED_LINE.exec(before)?.[1] ?? null : null,
      });
      n++;
    });
  });
  return refs;
}
