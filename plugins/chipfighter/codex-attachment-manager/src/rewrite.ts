// Purpose: P2 — replace the images the user unchecked with placeholder text in a Responses request's `input`.
// Nothing else changes: checked images, unknown images and all other items are forwarded as they are.
// v0.1 — placeholders say the image was seen when it appeared and is left out now by the user's choice, so the model
// keeps trusting what it said about it (user report 2026-09-25).
// v0.1-14 — in the user's language (Codex's interface language, language.ts): the Chinese wording is the one tested on
// 2026-09-25; the English one says the same and is checked by the same self-test (v01-placeholder-selftest.ts --lang en).
// v0.1-24 — how to ask for an image back is spelled out, for every GPT-6 model (self-tests with CAM_TEST_MODEL).
// v0.1-25 — once anything is left out, each image still sent carries its id, and the note says a checked image is back
// in its old place: GPT-6 Luna looked for it in the newest message and said it could not see it (user 2026-09-28).
// v0.3 — automatic selection (user 2026-10-06): images from earlier turns that are not pinned are left out, in their own
// wording, and the model fetches what it needs with cam_view_image (whose words are here too, as text for the model).
// A copy it fetched is sent in that turn only. Drafts of this wording were tried on the three GPT-6 models in Chinese
// and English before it was built (spike/src/auto-fetch-selftest.ts).
// Input: request items, a lookup into the thread index, the keys to leave out. Output: new items plus a metadata report.

import { FETCHED_STATE, findImages, type ImageKind, type ImageRef } from "./images.ts";
import type { Lang } from "./language.ts";

type Json = Record<string, any>;
export type Described = { id: string; name: string | null; label: string | null; kind: ImageKind; turn: number | null; width: number | null; height: number | null };
export type Replacement = { id: string; key: string; kind: ImageKind; mode: "plain" | "duplicate"; sameAs: string | null; base64Chars: number };
// noteAt: where the developer message explaining omitted images was inserted, if one was. copies: the ids whose copies
// fetched in an earlier turn were left out.
export type RewriteReport = { images: number; replaced: Replacement[]; locked: string[]; sentContentIds: string[]; copies: string[]; noteAt?: number };

type FetchWords = { title: string; description: string; ids: string; missing: (id: string) => string; unavailable: (id: string) => string; off: string };
type Words = {
  kind: Record<ImageKind, string>; unnamed: string; turn: (n: number) => string; thisTurn: string; newImage: string;
  omitted: string; notRepeated: string; included: string; separator: string;
  heading: (id: string, label: string | null, state: string, fields: string[]) => string;
  plain: (id: string) => string; duplicate: (id: string, where: string) => string; note: string;
  autoPlain: (id: string) => string; autoNote: string; copy: (id: string) => string; fetch: FetchWords;
  // v0.4, Claude Code only (claude-rewrite.ts): what the note adds about tool results, and the short note that follows
  // each message holding omitted images, naming them.
  toolNote: string; here: (list: string) => string; hereAuto: (list: string) => string; listItem: (id: string, name: string | null, kind: string) => string;
};

// The image sits in the history, so the model concludes it never saw it and takes back what it said about it (user
// report 2026-09-25). Saying otherwise inside the placeholder did not help: it is user content, which the model does
// not take as proof. So the explanation goes once into a developer message, before the turn where the first omitted
// image appeared, and each placeholder only points to it.
const WORDS: Record<Lang, Words> = {
  zh: {
    kind: { upload: "用户上传", view: "工具查看的图片", generated: "生成的图片", tool: "工具结果里的图片" },
    unnamed: "未命名",
    turn: (n) => `第 ${n} 轮`,
    thisTurn: "本轮",
    newImage: "（新图片）",
    omitted: "已省略",
    notRepeated: "未重复提供",
    included: "已提供",
    separator: "，",
    heading: (id, label, state, fields) => `[图片 ${id}${label ? `（${label}）` : ""} ${state}｜${fields.join("｜")}]`,
    plain: (id) => `原图被用户省略以节省上下文，情况见前面的“上下文管理说明”；需要重新看这张图时，在回复里写出“需要 ${id}”。`,
    duplicate: (id, where) => `这张图和 ${id}（${where}）内容完全相同，那一条在本次请求里照常提供，请直接参考那一条。`,
    note: [
      "上下文管理说明（来自用户安装的上下文素材管理工具）：为了节省上下文，用户取消勾选了这个任务里的部分图片。后面的对话里，这些图片原来的位置被换成了“[图片 IMG-xxx 已省略…]”这样的占位文字；仍在提供的图片前面标着“[图片 IMG-xxx 已提供…]”，紧接着就是原图。",
      "这些图片在它们出现的那一轮真实存在，你当时收到并看过；你之前对它们的描述，以及据此做出的判断，都是看着原图做出的，仍然有效。不要因为现在看不到，就认为之前的回答是猜测或错误，也不要收回或道歉。",
      "被问到现在能不能看到某张被省略的图片时，如实说明现在看不到（被用户省略了），并说明之前的描述仍然有效。现在看不到画面，就不要补充之前没说过的细节。需要重新看某张图时，在回复里原样写出“需要 IMG-xxx”（几张就写“需要 IMG-002、IMG-003”）：工具靠这几个字认出你要的图。用户重新勾选后，原图会回到它在对话里原来的位置：那里的占位文字换成“[图片 IMG-xxx 已提供…]”和原图；它不会出现在用户的新消息里，所以不要让用户重新上传或附上图片。不要自己用工具去读取这些图片。",
      "标着“[图片 IMG-xxx 已提供…]”的图片现在就在你面前，即使它之前被省略过、或者正是你要过的图：被问到它时，直接看图回答，不要说看不到。",
    ].join("\n"),
    autoPlain: (id) => `之前各轮的图片默认省略以节省上下文（自动选图），情况见前面的“上下文管理说明”；需要看这张图的原图时，调用 cam_view_image 工具，传入“${id}”。`,
    autoNote: [
      "上下文管理说明（来自用户安装的上下文素材管理工具）：这个任务开着“自动选图”。为了节省上下文，之前各轮的图片默认不再随请求提供，后面的对话里，它们原来的位置换成了“[图片 IMG-xxx 已省略…]”这样的占位文字；本轮新出现的图片照常提供，用户固定发送的图片也照常提供，前面标着“[图片 IMG-xxx 已提供…]”，紧接着就是原图。",
      "这些图片在它们出现的那一轮真实存在，你当时收到并看过；你之前对它们的描述，以及据此做出的判断，都是看着原图做出的，仍然有效。不要因为现在看不到，就认为之前的回答是猜测或错误，也不要收回或道歉。",
      "回答需要看某张被省略的图片、而你之前说过的内容不够用时，调用 cam_view_image 工具，传入它的编号（几张就一次传几个），原图会出现在这次的工具结果里，前面标着“[图片 IMG-xxx 取回的原图…]”，拿到后看图回答。之前说过的内容够用时，不要调用。现在看不到的画面细节，不要猜测或补充；不要让用户重新上传图片，也不要用其他工具去读取图片文件。",
      "用 cam_view_image 取回的图片只在本轮提供，下一轮又会换回占位文字；之后还需要时，再调用一次。标着“已提供”或“取回的原图”的图片现在就在你面前：被问到它时，直接看图回答，不要说看不到。",
    ].join("\n"),
    copy: (id) => `[${id} 的原图：模型当时用 cam_view_image 取回，只在那一轮提供，现在已省略]`,
    // v0.4: in Claude Code desktop tests (Haiku 5.5, 2026-10-09) the model read a placeholder inside a Read result as
    // what the tool had returned, said it had never seen the image and took back its correct description; the same
    // words inside the tool result were not believed ("I should not follow the placeholder"). With the note right after
    // the message holding the image, it answered as intended. So each such message is followed by a short note.
    // 2026-10-10, Haiku 5.5, tool images, 3 runs per language: it kept its answers and guessed nothing, but asked for
    // the image by number in 2 of 3 Chinese runs (as an option) and in no English run; a question about a detail it
    // never described got "I can't answer that". The note now says when to write "需要 IMG-xxx", and why.
    toolNote: "工具结果里的图片也一样：那次工具调用当时返回的是原图，你当时看到了；工具结果里的占位文字是后来才换上的，不是工具当时的返回。",
    here: (list) => `上下文管理说明：上面这条消息里的 ${list} 当时是原图，你当时看过；你之前对它们的描述和据此做出的判断仍然有效，不要收回，也不要说成是猜测或编造。那里的占位文字是这次请求才换上的，不是当时的内容。现在你看不到它们：被问到时，如实说现在看不到（被用户省略了），不要补充之前没说过的细节。问题得看其中某张图才能回答时，不要只说答不了，在回复里单独写一行“需要 IMG-xxx”（写出编号，几张就都写上）：用户看到这一行才知道该勾回哪张图，勾回后原图回到原处，你就能看着回答。`,
    hereAuto: (list) => `上下文管理说明：上面这条消息里的 ${list} 当时是原图，你当时看过；你之前对它们的描述和据此做出的判断仍然有效，不要收回，也不要说成是猜测或编造。那里的占位文字是这次请求才换上的（自动选图），不是当时的内容。之前说过的内容不够用时，调用 cam_view_image 取回原图；不要补充之前没说过的细节。`,
    listItem: (id, name, kind) => `${id}（${[name, kind].filter(Boolean).join("，")}）`,
    fetch: {
      title: "查看被省略的图片",
      description: "查看这个任务里一张或几张被省略的图片的原图。被省略的图片在对话里显示为“[图片 IMG-xxx 已省略…]”。只在回答需要看图、而你之前对它说过的内容不够用时调用；取回的原图只在本轮提供。",
      ids: "要查看的图片编号，例如 [\"IMG-004\"]；几张就一次传几个。",
      missing: (id) => `这个任务里没有 ${id}。`,
      unavailable: (id) => `${id} 的原图读不出来。`,
      off: "这个任务没有开自动选图：被省略的图片要由用户勾选。需要时在回复里写“需要 IMG-xxx”。",
    },
  },
  en: {
    kind: { upload: "uploaded by the user", view: "viewed with a tool", generated: "generated image", tool: "image from a tool result" },
    unnamed: "unnamed",
    turn: (n) => `turn ${n}`,
    thisTurn: "this turn",
    newImage: "(new image)",
    omitted: "omitted",
    notRepeated: "not repeated",
    included: "included",
    separator: ", ",
    heading: (id, label, state, fields) => `[Image ${id}${label ? ` (${label})` : ""} ${state} | ${fields.join(" | ")}]`,
    plain: (id) => `The user left out the original image to save context; see the "Context management note" above. If you need to see this image again, write "need ${id}" in your reply.`,
    duplicate: (id, where) => `This image is identical to ${id} (${where}), which is included in this request as usual; refer to that one.`,
    note: [
      "Context management note (from the context asset manager the user installed): to save context, the user unchecked some images in this task. Further on in the conversation, where those images were, there is now placeholder text such as \"[Image IMG-xxx omitted…]\"; each image still included is marked \"[Image IMG-xxx included…]\", with the original image right after it.",
      "These images really existed in the turn where they appeared, and you received and looked at them then; what you said about them before, and the judgments you based on it, were made looking at the original images and remain valid. Do not treat your earlier answers as guesses or mistakes because you cannot see the images now, and do not take them back or apologize.",
      "If asked whether you can see an omitted image now, say truthfully that you cannot see it now (the user left it out), and that your earlier descriptions remain valid. Since you cannot see it now, do not add details you did not mention before. If you need to look at an image again, write exactly \"need IMG-xxx\" in your reply (for several: \"need IMG-002, IMG-003\"): the tool finds the images you want by these words. Once the user checks an image again, its original is back in its old place in the conversation: the placeholder there becomes \"[Image IMG-xxx included…]\" followed by the original image. It does not come in the user's new message, so do not ask the user to upload or attach it again. Do not read these images yourself with tools.",
      "An image marked \"[Image IMG-xxx included…]\" is in front of you now, even if it was omitted before or is one you asked for: when asked about it, look at it and answer from it, and do not say you cannot see it.",
    ].join("\n"),
    autoPlain: (id) => `Images from earlier turns are left out by default to save context (automatic image selection); see the "Context management note" above. To see the original of this image, call the cam_view_image tool with "${id}".`,
    autoNote: [
      "Context management note (from the context asset manager the user installed): this task has automatic image selection on. To save context, images from earlier turns are no longer included in requests by default: further on in the conversation, where those images were, there is now placeholder text such as \"[Image IMG-xxx omitted…]\". Images new in this turn are included as usual, and so are the images the user pinned, marked \"[Image IMG-xxx included…]\" with the original image right after it.",
      "These images really existed in the turn where they appeared, and you received and looked at them then; what you said about them before, and the judgments you based on it, were made looking at the original images and remain valid. Do not treat your earlier answers as guesses or mistakes because you cannot see the images now, and do not take them back or apologize.",
      "When an answer needs an omitted image and what you said about it before is not enough, call the cam_view_image tool with its id (several ids at once if you need several); the original comes back in that tool result, marked \"[Image IMG-xxx fetched original…]\", and you answer from it. When what you said before is enough, do not call it. Do not guess or add visual details you cannot see now; do not ask the user to upload images again, and do not read image files with other tools.",
      "An image you get with cam_view_image is included only in this turn; from the next turn on it is a placeholder again. Call the tool again if you need it later. An image marked \"included\" or \"fetched original\" is in front of you now: when asked about it, look at it and answer from it, and do not say you cannot see it.",
    ].join("\n"),
    copy: (id) => `[Original of ${id}: fetched by the model with cam_view_image, included only in that turn, now omitted]`,
    toolNote: "The same holds for images in tool results: the tool call returned the original image at the time and you saw it; a placeholder inside a tool result was put there later, it is not what the tool returned.",
    here: (list) => `Context management note: in the message above, ${list} were original images at the time, and you looked at them then; what you said about them and the judgments you based on it remain valid, so do not take them back or call them guesses or made up. The placeholder text there was put in only for this request; it is not what was there at the time. You cannot see them now: if asked, say so truthfully (the user left them out), and do not add details you did not mention before. When a question can only be answered by looking at one of them, do not just say you cannot answer; write a line "need IMG-xxx" in your reply (with its number; list each one needed): that line is how the user learns which image to check again, and once they do, the original comes back in its place and you can answer from it.`,
    hereAuto: (list) => `Context management note: in the message above, ${list} were original images at the time, and you looked at them then; what you said about them and the judgments you based on it remain valid, so do not take them back or call them guesses or made up. The placeholder text there was put in only for this request (automatic image selection); it is not what was there at the time. When what you said before is not enough, fetch the original with cam_view_image; do not add details you did not mention before.`,
    listItem: (id, name, kind) => `${id} (${[name, kind].filter(Boolean).join(", ")})`,
    fetch: {
      title: "View omitted images",
      description: "View the originals of one or more omitted images in this task. Omitted images appear in the conversation as \"[Image IMG-xxx omitted…]\". Call it only when an answer needs to look at an image and what you said about it before is not enough; the originals are included only in this turn.",
      ids: "Ids of the images to view, e.g. [\"IMG-004\"]; pass several at once if you need several.",
      missing: (id) => `This task has no ${id}.`,
      unavailable: (id) => `The original of ${id} could not be read.`,
      off: "Automatic image selection is off in this task: omitted images come back only when the user checks them. If you need one, write \"need IMG-xxx\" in your reply.",
    },
  },
};

// The Chinese note, tested on 2026-09-25; v0.1-24 (2026-09-28) spells out how to ask for an image back ("需要 IMG-xxx",
// several at once, no re-uploading), after GPT-6 Luna asked the user to "reattach" images instead; v0.1-25 says where a
// checked image comes back (its old place, marked "已提供"), after Luna looked for it in the newest message instead.
export const OMISSION_NOTE = WORDS.zh.note;
export const omissionNote = (lang: Lang) => WORDS[lang].note;

function heading(words: Words, image: Described, state: string): string {
  const fields = [image.name ?? words.unnamed, words.kind[image.kind]];
  if (image.turn !== null) fields.push(words.turn(image.turn));
  if (image.width && image.height) fields.push(`${image.width}×${image.height}`);
  return words.heading(image.id, image.label, state, fields);
}

export function plainPlaceholder(image: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  return `${heading(words, image, words.omitted)}\n${words.plain(image.id)}`;
}

export function duplicatePlaceholder(image: Described, same: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  const where = [same.name, same.turn !== null ? words.turn(same.turn) : words.thisTurn].filter(Boolean).join(words.separator);
  return `${heading(words, image, words.notRepeated)}\n${words.duplicate(same.id, where)}`;
}

// Put right before an image that is still sent, so the model can tell which id it is: Codex's own labels ("[Image #2]")
// start again in every message.
export function includedLabel(image: Described, lang: Lang = "zh"): string {
  return heading(WORDS[lang], image, WORDS[lang].included);
}

// v0.3: automatic selection.
export const autoNote = (lang: Lang) => WORDS[lang].autoNote;
export const fetchWords = (lang: Lang): FetchWords => WORDS[lang].fetch;
// v0.4: the same words for a Claude Code request (claude-rewrite.ts).
export const copyNote = (id: string, lang: Lang) => WORDS[lang].copy(id);
export const newImageWord = (lang: Lang) => WORDS[lang].newImage;

// v0.4, Claude Code only: the note also speaks of tool results, and a short note follows each message holding omitted
// images, naming them. Codex's words stay as they are.
export const claudeNote = (lang: Lang, auto = false) => `${auto ? WORDS[lang].autoNote : WORDS[lang].note}\n${WORDS[lang].toolNote}`;
export function hereNote(images: Described[], lang: Lang = "zh", auto = false): string {
  const words = WORDS[lang];
  const list = images.map((image) => words.listItem(image.id, image.name, words.kind[image.kind])).join(words.separator);
  return auto ? words.hereAuto(list) : words.here(list);
}

export function autoPlaceholder(image: Described, lang: Lang = "zh"): string {
  const words = WORDS[lang];
  return `${heading(words, image, words.omitted)}\n${words.autoPlain(image.id)}`;
}

// The line cam_view_image puts before each image it returns. Without Codex's own label ("[Image #3]"), which numbers
// images within their message and means nothing here: GPT-6 Luna once read it as the digit asked about.
export function fetchedLabel(image: Described, lang: Lang = "zh"): string {
  return heading(WORDS[lang], { ...image, label: null }, FETCHED_STATE[lang]);
}

export type RewriteOptions = {
  lang?: Lang;
  // Copies the model fetched in an earlier turn (key → the id they copy): left out in either mode.
  copies?: Map<string, string>;
  // Automatic selection: its wording; and a placeholder points to, and a label marks, only images of earlier turns
  // (the pinned ones), which stay sent through the turn, so a copy fetched mid-turn changes nothing before it.
  auto?: { currentTurn: number };
};

export function rewriteItems(
  items: Json[],
  describe: (ref: ImageRef) => Described | undefined,
  unchecked: Set<string>,
  pixelHash: (ref: ImageRef) => string | null,
  options: Lang | RewriteOptions = "zh",
): { items: Json[]; report: RewriteReport } {
  const { lang = "zh", copies = new Map<string, string>(), auto }: RewriteOptions = typeof options === "string" ? { lang: options } : options;
  const refs = findImages(items);
  const report: RewriteReport = { images: refs.length, replaced: [], locked: [], sentContentIds: [], copies: [] };
  const copied = refs.filter((ref) => copies.has(ref.key) && ref.part !== null);
  const drop = refs.filter((ref) => !copies.has(ref.key) && unchecked.has(ref.key) && ref.replaceable && describe(ref));
  for (const ref of refs) if (unchecked.has(ref.key) && !ref.replaceable) report.locked.push(describe(ref)?.id ?? ref.key);
  const sent = refs.filter((ref) => !drop.includes(ref) && !copied.includes(ref));
  report.sentContentIds = sent.map((ref) => ref.contentId);
  if (!drop.length && !copied.length) return { items, report };
  const earlier = (ref: ImageRef) => { const turn = describe(ref)?.turn; return auto !== undefined && turn !== null && turn !== undefined && turn < auto.currentTurn; };
  const lasting = auto ? sent.filter(earlier) : sent;

  const same = (a: ImageRef, b: ImageRef) => {
    if (a.contentId === b.contentId) return true;
    if (a.width !== b.width || a.height !== b.height) return false;
    const pixels = pixelHash(a);
    return pixels !== null && pixels === pixelHash(b);
  };
  // Each edit puts one text part at `at`, in place of `remove` parts (none for a label).
  const edits = new Map<number, Array<{ at: number; remove: number; text: string }>>();
  const edit = (item: number, at: number, remove: number, text: string) => edits.set(item, [...(edits.get(item) ?? []), { at, remove, text }]);
  let firstPlain: number | null = null;
  for (const ref of drop) {
    const image = describe(ref)!;
    const copy = lasting.find((other) => same(other, ref));
    const copyImage = copy ? describe(copy) ?? { id: WORDS[lang].newImage, name: copy.name, label: copy.label, kind: copy.kind, turn: null, width: copy.width, height: copy.height } : null;
    const text = copyImage ? duplicatePlaceholder(image, copyImage, lang) : auto ? autoPlaceholder(image, lang) : plainPlaceholder(image, lang);
    if (!copyImage && firstPlain === null) firstPlain = ref.item;
    report.replaced.push({ id: image.id, key: ref.key, kind: ref.kind, mode: copyImage ? "duplicate" : "plain", sameAs: copyImage?.id ?? null, base64Chars: ref.base64Chars });
    const at = ref.openTag ?? ref.part!;
    edit(ref.item, at, (ref.closeTag ?? ref.part!) - at + 1, text);
  }
  for (const ref of copied) {
    edit(ref.item, ref.part!, 1, WORDS[lang].copy(copies.get(ref.key)!));
    report.copies.push(copies.get(ref.key)!);
  }
  // v0.1-25: a checked image sits in its old place among placeholders, so every image still sent is marked with its id.
  for (const ref of lasting) {
    const image = ref.replaceable && ref.part !== null ? describe(ref) : undefined;
    if (image) edit(ref.item, ref.openTag ?? ref.part!, 0, includedLabel(image, lang));
  }
  const next = items.map((item, index) => {
    const list = edits.get(index);
    if (!list) return item;
    const field = item.type === "message" ? "content" : "output";
    const parts: Json[] = [...item[field]];
    for (const { at, remove, text } of list.sort((a, b) => b.at - a.at)) parts.splice(at, remove, { type: "input_text", text });
    return { ...item, [field]: parts };
  });
  // Only plain placeholders need the note (a duplicate's content is still in view). It goes before the user message
  // that opens that turn, so it never splits a tool call from its output.
  if (firstPlain !== null) {
    let at = firstPlain;
    while (at > 0 && !(next[at].type === "message" && next[at].role === "user")) at--;
    next.splice(at, 0, { type: "message", role: "developer", content: [{ type: "input_text", text: auto ? WORDS[lang].autoNote : WORDS[lang].note }] });
    report.noteAt = at;
  }
  return { items: next, report };
}
