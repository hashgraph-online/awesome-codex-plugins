// publish.ts - TypeScript twin of examples/python/tgkit/publish.py (core path).
// Content model -> text + entities, channel button rules, plan (text / album),
// idempotent Publisher with a write-ahead ledger, throttled fan-out.
// Node >= 22.18 (type stripping), no dependencies. Facts re-read 2026-11-15 (Bot API 10.4).
import { callWithPolicy, OutcomeUnknown, TelegramError, type Params } from "../tgkit.ts";

export type Inline = string | Inline[] | { bold?: Inline; italic?: Inline; code?: string; link?: string; text?: Inline };
export type Block =
  | { type: "heading" | "paragraph" | "footer"; text: Inline }
  | { type: "list"; items: (Inline | { text: Inline; done: boolean })[] }
  | { type: "quote"; text: Inline; expandable?: boolean; credit?: string };
export type Button = Params & { text: string };
export type Post = {
  blocks: Block[]; buttons?: Button[][]; media?: { type: string; ref: string; spoiler?: boolean }[];
  linkPreview?: { url?: string; large?: boolean; above?: boolean; disabled?: boolean };
  silent?: boolean; protect?: boolean; followupText?: string;
};

const SCHEMES = ["http://", "https://", "tg://"];
export function checkUrl(url: string): string {
  if (!SCHEMES.some((s) => url.startsWith(s)) || /\s/.test(url)) throw new Error(`refusing link URL ${url}`);
  return url;
}

// JS strings are UTF-16, so .length is exactly the MessageEntity unit.
export function toEntities(blocks: Block[]): { text: string; entities: Params[] } {
  let text = "";
  const entities: Params[] = [];
  const span = (type: string, start: number, extra: Params = {}) => {
    if (text.length > start) entities.push({ type, offset: start, length: text.length - start, ...extra });
  };
  const inline = (node: Inline | undefined): void => {
    if (node === undefined) return;
    if (typeof node === "string") { text += node; return; }
    if (Array.isArray(node)) { node.forEach(inline); return; }
    const start = text.length;
    if (node.link !== undefined) { checkUrl(node.link); inline(node.text ?? node.link); span("text_link", start, { url: node.link }); }
    else if (node.code !== undefined) { text += node.code; span("code", start); }
    else if (node.bold !== undefined) { inline(node.bold); span("bold", start); }
    else if (node.italic !== undefined) { inline(node.italic); span("italic", start); }
    else throw new Error("unknown inline span");
  };
  blocks.forEach((b, i) => {
    if (i) text += "\n\n";
    const start = text.length;
    if (b.type === "heading") { inline(b.text); span("bold", start); }
    else if (b.type === "paragraph") inline(b.text);
    else if (b.type === "footer") { inline(b.text); span("italic", start); }
    else if (b.type === "list") b.items.forEach((it, n) => {
      if (n) text += "\n";
      const done = typeof it === "object" && !Array.isArray(it) && "done" in it;
      text += done ? ((it as { done: boolean }).done ? "☑ " : "☐ ") : "• ";
      inline(done ? (it as { text: Inline }).text : (it as Inline));
    });
    else if (b.type === "quote") {
      inline(b.text);
      if (b.credit) text += `\n— ${b.credit}`;
      span(b.expandable ? "expandable_blockquote" : "blockquote", start);
    }
  });
  return { text, entities };
}

const NOT_IN_CHANNEL: Record<string, string> = {
  web_app: "private chats only", switch_inline_query_current_chat: "not supported in channels",
  switch_inline_query: "avoid in channels", pay: "invoices only", callback_game: "games only",
};
const ACTIONS = ["url", "callback_data", "web_app", "login_url", "switch_inline_query", "switch_inline_query_current_chat",
  "switch_inline_query_chosen_chat", "copy_text", "callback_game", "pay", "disabled"];

export function checkButtons(rows: Button[][], context = "channel", customEmojiOk = false): string[] {
  const errors: string[] = [];
  for (const b of rows.flat()) {
    const acts = ACTIONS.filter((a) => a in b);
    if (acts.length !== 1) { errors.push(`${b.text}: exactly one action, got ${acts.join(",")}`); continue; }
    if (context === "channel" && acts[0] in NOT_IN_CHANNEL) errors.push(`${b.text}: ${acts[0]} ${NOT_IN_CHANNEL[acts[0]]}`);
    if (acts[0] === "callback_data" && !(Buffer.byteLength(b.callback_data, "utf8") >= 1 && Buffer.byteLength(b.callback_data, "utf8") <= 64))
      errors.push(`${b.text}: callback_data must be 1-64 bytes`);
    if (b.icon_custom_emoji_id && context === "channel" && !customEmojiOk) errors.push(`${b.text}: custom emoji needs a Fragment-username bot in channels`);
  }
  return errors;
}

const keyboard = (rows?: Button[][]) => (rows && rows.length ? { inline_keyboard: rows } : undefined);

export function plan(post: Post, chatId: number | string): [string, Params][] {
  const common: Params = { ...(post.silent ? { disable_notification: true } : {}), ...(post.protect ? { protect_content: true } : {}) };
  const { text, entities } = toEntities(post.blocks);
  const markup = keyboard(post.buttons);
  if ((post.media?.length ?? 0) >= 2) {
    if (text.length > 1024) throw new Error("album caption over 1024 characters: split it (see the Python twin)");
    const media = (post.media ?? []).map((m, i) => ({
      type: m.type, media: m.ref,
      ...(i === 0 && text ? { caption: text, ...(entities.length ? { caption_entities: entities } : {}) } : {}),
      ...(m.spoiler ? { has_spoiler: true } : {}),
    }));
    const reqs: [string, Params][] = [["sendMediaGroup", { chat_id: chatId, media, ...common }]];
    if (markup) reqs.push(["sendMessage", { chat_id: chatId, text: post.followupText ?? "Links:", ...common, disable_notification: true, reply_markup: markup }]);
    return reqs;
  }
  if (text.length > 4096) throw new Error("text over 4096 characters: use a rich message (see the Python twin)");
  const p: Params = { chat_id: chatId, text, ...(entities.length ? { entities } : {}) };
  const lp = post.linkPreview;
  if (lp) p.link_preview_options = lp.disabled ? { is_disabled: true }
    : { ...(lp.url ? { url: checkUrl(lp.url) } : {}), ...(lp.large ? { prefer_large_media: true } : {}), ...(lp.above ? { show_above_text: true } : {}) };
  Object.assign(p, common);
  if (markup) p.reply_markup = markup;
  return [["sendMessage", p]];
}

type Transport = { call(m: string, p: Params): Promise<unknown> };
export type Rec = { state: "pending" | "sent" | "unknown" | "failed"; chatId: number | string; messageIds: number[]; fingerprint: string };
export const fingerprint = (x: unknown) => JSON.stringify(x);

const idsOf = (r: unknown): number[] => Array.isArray(r) ? r.map((m: Params) => m.message_id)
  : r && typeof r === "object" && "message_id" in r ? [(r as Params).message_id] : [];

export class Publisher {
  ledger = new Map<string, Rec>();
  private t: Transport;
  private sleep: (s: number) => Promise<void>;
  constructor(t: Transport, sleep: (s: number) => Promise<void> = async () => {}) { this.t = t; this.sleep = sleep; }

  async publish(post: Post, chatId: number | string, key: string): Promise<{ status: string; messageIds: number[] }> {
    const rec = this.ledger.get(key);
    if (rec?.state === "sent") return { status: "already_sent", messageIds: rec.messageIds };
    if (rec && (rec.state === "pending" || rec.state === "unknown")) return { status: "unknown", messageIds: rec.messageIds };
    const errors = checkButtons(post.buttons ?? []);
    if (errors.length) throw new Error(errors.join("; "));
    const reqs = plan(post, chatId);
    const r: Rec = { state: "pending", chatId, messageIds: [], fingerprint: fingerprint(post) };
    this.ledger.set(key, r);                                       // write-ahead, before the request leaves
    for (const [method, params] of reqs) {
      try { r.messageIds.push(...idsOf(await callWithPolicy(this.t, method, params, { sleep: this.sleep }))); }
      catch (e) {
        if (e instanceof OutcomeUnknown) { r.state = "unknown"; return { status: "unknown", messageIds: r.messageIds }; }
        if (e instanceof TelegramError && !r.messageIds.length) { r.state = "failed"; return { status: "failed", messageIds: [] }; }
        r.state = "unknown"; return { status: "partial", messageIds: r.messageIds };
      }
    }
    r.state = "sent";
    return { status: "sent", messageIds: r.messageIds };
  }

  reconcile(key: string, foundMessageIds: number[]): string {
    const rec = this.ledger.get(key);
    if (!rec) throw new Error(`no record ${key}`);
    if (foundMessageIds.length) { rec.state = "sent"; rec.messageIds = foundMessageIds; return "sent"; }
    this.ledger.delete(key);
    return "absent";
  }

  async edit(key: string, post: Post): Promise<string> {
    const rec = this.ledger.get(key);
    if (rec?.state !== "sent") throw new Error(`${key} is not sent`);
    if (fingerprint(post) === rec.fingerprint) return "unchanged";   // no request at all
    const reqs = plan(post, rec.chatId);
    if (reqs.length !== 1 || reqs[0][0] !== "sendMessage") return "repost_required";
    const { chat_id, text, entities, link_preview_options, reply_markup } = reqs[0][1];
    await callWithPolicy(this.t, "editMessageText", { chat_id, message_id: rec.messageIds[0], text,
      ...(entities ? { entities } : {}), ...(link_preview_options ? { link_preview_options } : {}), ...(reply_markup ? { reply_markup } : {}) });
    rec.fingerprint = fingerprint(post);
    return "edited";
  }
}

export async function fanOut(t: Transport, jobs: [string, [string, Params][]][],
  o: { perSecond?: number; sleep?: (s: number) => Promise<void>; done?: Set<string> } = {}) {
  const sleep = o.sleep ?? (async () => {});
  const interval = 1 / (o.perSecond ?? 25);
  const done = o.done ?? new Set<string>();
  const report = { sent: [] as string[], blocked: [] as string[], invalid: [] as string[], unknown: [] as string[], skipped: [] as string[] };
  let first = true;
  for (const [rid, reqs] of jobs) {
    if (done.has(rid)) { report.skipped.push(rid); continue; }
    try {
      for (const [m, p] of reqs) { if (!first) await sleep(interval); first = false; await callWithPolicy(t, m, p, { sleep }); }
      done.add(rid); report.sent.push(rid);
    } catch (e) {
      if (e instanceof OutcomeUnknown) report.unknown.push(rid);
      else if (e instanceof TelegramError && e.category === "permission") report.blocked.push(rid);
      else if (e instanceof TelegramError && e.category === "rate_limited") throw e;   // let the caller reschedule
      else report.invalid.push(rid);
    }
  }
  return report;
}
