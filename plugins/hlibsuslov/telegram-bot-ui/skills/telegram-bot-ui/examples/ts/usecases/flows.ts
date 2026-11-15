// flows.ts - TypeScript twin of examples/python/tgkit/flows.py (same invariants).
// Node >= 22.18 type stripping, no dependencies. Verified against Bot API 10.4 on 2026-11-15.
import { FakeTransport, TelegramError, type Params } from "../tgkit.ts";

export const MAX_CALLBACK_BYTES = 64; // API: callback_data 1-64 bytes

export function pack(...parts: (string | number)[]): string {
  const items = parts.map(String);
  if (items.some((p) => p.includes(":"))) throw new Error("callback part contains ':'");
  const data = items.join(":");
  const size = Buffer.byteLength(data, "utf8");
  if (size < 1 || size > MAX_CALLBACK_BYTES) throw new RangeError(`callback_data is ${size} bytes (1-64 allowed)`);
  return data;
}
export const b36 = (n: number) => n.toString(36);

export function btn(text: string, data?: string, o: { style?: string; disabled?: boolean; url?: string } = {}): Params {
  const b: Params = { text };
  if (o.disabled) b.disabled = {};
  else if (data !== undefined) b.callback_data = data;
  else if (o.url) b.url = o.url;
  else throw new Error("a button needs exactly one action");
  if (o.style) b.style = o.style;
  return b;
}
export const kb = (...rows: (Params[] | null | undefined)[]) => ({ inline_keyboard: rows.filter((r) => r && r.length) });

const escapeHtml = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
export class Raw { text: string; constructor(text: string) { this.text = text; } }

export class I18n {
  catalog: Record<string, Record<string, string>>; fallback: string;
  constructor(catalog: Record<string, Record<string, string>>, fallback = "en") { this.catalog = catalog; this.fallback = fallback; }
  langFor(code?: string): string { const c = (code ?? "").split("-")[0].toLowerCase(); return c in this.catalog ? c : this.fallback; }
  t(lang: string, key: string, values: Record<string, unknown> = {}): string {
    const tpl = this.catalog[lang]?.[key] ?? this.catalog[this.fallback][key];
    if (tpl === undefined) throw new Error(`missing copy key ${key}`);
    return tpl.replace(/\{(\w+)\}/g, (_, k) => { const v = values[k]; return v instanceof Raw ? v.text : escapeHtml(String(v)); });
  }
  missing(): Record<string, string[]> {
    const all = new Set(Object.values(this.catalog).flatMap((t) => Object.keys(t)));
    const out: Record<string, string[]> = {};
    for (const [lang, t] of Object.entries(this.catalog)) { const m = [...all].filter((k) => !(k in t)); if (m.length) out[lang] = m.sort(); }
    return out;
  }
}

export type Session = {
  ownerId: number; chatId: number; lang: string; screen: string; stack: [string, Params][];
  args: Params; data: Params; version: number; messageId?: number; kind: string;
};
type Render = (fl: ScreenFlow, s: Session) => Params;
type Action = (fl: ScreenFlow, s: Session, args: string[], cq: Params) => Promise<string | void> | string | void;

export class ScreenFlow {
  screens = new Map<string, Render>();
  actions = new Map<string, Action>();
  sessions = new Map<string, Session>();
  owners = new Map<string, number>();
  private answered = new Set<string>();
  texts: Record<string, string> = { stale: "This screen has changed. Use the latest message.",
    not_yours: "This menu belongs to someone else. Open your own with /start.", expired: "This menu has expired. Send /start to open a new one." };
  t: FakeTransport; app: string; i18n?: I18n;
  constructor(t: FakeTransport, app: string, i18n?: I18n) { this.t = t; this.app = app; this.i18n = i18n; }

  screen(name: string, fn: Render) { this.screens.set(name, fn); }
  action(name: string, fn: Action) { this.actions.set(name, fn); }
  session(chatId: number, userId: number, lang = "en"): Session {
    const key = `${chatId}:${userId}`;
    if (!this.sessions.has(key)) this.sessions.set(key, { ownerId: userId, chatId, lang, screen: "", stack: [], args: {}, data: {}, version: 0, kind: "" });
    return this.sessions.get(key)!;
  }
  get(chatId: number, userId: number) { return this.sessions.get(`${chatId}:${userId}`); }
  cb(s: Session, action: string, ...args: (string | number)[]) { return pack(this.app, b36(s.version), action, ...args); }
  tr(s: Session, key: string, values: Record<string, unknown> = {}) { return this.i18n!.t(s.lang, key, values); }

  open(s: Session, screen: string, args: Params = {}, newMessage = false) { s.stack = []; return this.show(s, screen, args, newMessage); }
  go(s: Session, screen: string, args: Params = {}) { if (s.screen) s.stack.push([s.screen, { ...s.args }]); return this.show(s, screen, args); }
  back(s: Session) { const prev = s.stack.pop(); return prev ? this.show(s, prev[0], prev[1]) : this.show(s, s.screen, s.args); }
  refresh(s: Session) { return this.show(s, s.screen, s.args); }

  private async show(s: Session, screen: string, args: Params, newMessage = false) {
    s.screen = screen; s.args = { ...args }; s.version += 1;
    const out = this.screens.get(screen)!(this, s);
    const params: Params = { ...out };
    if ("text" in params && !("parse_mode" in params)) params.parse_mode = "HTML";
    const kind = "rich_message" in params ? "rich" : "text";
    if (s.messageId === undefined || newMessage || kind !== s.kind) {
      if (s.messageId !== undefined) this.owners.delete(`${s.chatId}:${s.messageId}`);
      const msg = await this.t.call(kind === "rich" ? "sendRichMessage" : "sendMessage", { chat_id: s.chatId, ...params });
      s.messageId = msg.message_id; s.kind = kind;
      this.owners.set(`${s.chatId}:${s.messageId}`, s.ownerId);
      return msg;
    }
    try { return await this.t.call("editMessageText", { chat_id: s.chatId, message_id: s.messageId, ...params }); } catch (e) {
      if (e instanceof TelegramError && e.category === "not_modified") return true;
      throw e;
    }
  }

  async answer(cq: Params, text?: string, alert = false) {
    if (this.answered.has(cq.id)) return;
    this.answered.add(cq.id);
    const p: Params = { callback_query_id: cq.id };
    if (text) { p.text = text.slice(0, 200); if (alert) p.show_alert = true; }
    await this.t.call("answerCallbackQuery", p);
  }
  sysText(status: string, cq: Params, s?: Session): string {
    if (this.i18n && `sys_${status}` in this.i18n.catalog[this.i18n.fallback])
      return this.i18n.t(s ? s.lang : this.i18n.langFor(cq.from.language_code), `sys_${status}`);
    return this.texts[status];
  }
  async handle(cq: Params): Promise<string> {
    const parts = String(cq.data ?? "").split(":");
    if (parts.length < 3 || parts[0] !== this.app) return "foreign";
    const chat = cq.message?.chat?.id, mid = cq.message?.message_id, user = cq.from.id;
    const owner = this.owners.get(`${chat}:${mid}`);
    let status = "ok";
    const s = this.get(chat, user);
    if (owner !== undefined && owner !== user) status = "not_yours";
    else if (!s || owner === undefined) status = "expired";
    if (status !== "ok") { await this.answer(cq, this.sysText(status, cq), status === "not_yours"); return status; }
    const fn = this.actions.get(parts[2]);
    if (parts[1] !== b36(s!.version) || !fn) { await this.answer(cq, this.sysText("stale", cq, s)); return "stale"; }
    const r = await fn(this, s!, parts.slice(3), cq);
    await this.answer(cq);
    return typeof r === "string" ? r : "ok";
  }
}

export class OnceStore {
  done = new Map<string, unknown>(); runs = 0;
  async run<T>(key: string, fn: () => Promise<T> | T): Promise<[T, boolean]> {
    if (this.done.has(key)) return [this.done.get(key) as T, false];
    this.runs++; const r = await fn(); this.done.set(key, r); return [r, true];
  }
}
export class UpdateDedup {
  seen = new Set<number>();
  firstTime(u: Params) { if (this.seen.has(u.update_id)) return false; this.seen.add(u.update_id); return true; }
}
export class Scheduler {
  jobs = new Map<string, { at: number; key: string; payload: Params }>();
  at(when: number, key: string, payload: Params = {}) { this.jobs.set(key, { at: when, key, payload }); }
  cancel(prefix: string) { let n = 0; for (const k of [...this.jobs.keys()]) if (k.startsWith(prefix)) { this.jobs.delete(k); n++; } return n; }
  due(now: number) {
    const ready = [...this.jobs.values()].filter((j) => j.at <= now).sort((a, b) => a.at - b.at || a.key.localeCompare(b.key));
    for (const j of ready) this.jobs.delete(j.key);
    return ready;
  }
}

export const user = (id: number, name = "User", lang = "en") => ({ id, is_bot: false, first_name: name, language_code: lang });
export const callback = (id: string, from: Params, data: string, chatId: number, messageId?: number, chatType = "private") =>
  ({ id, from, chat_instance: "-1", data, message: { message_id: messageId, date: 0, chat: { id: chatId, type: chatType } } });
export const textMessage = (from: Params, text: string, o: { chatId?: number; chatType?: string; messageId?: number } = {}) =>
  ({ message_id: o.messageId ?? 1, date: 0, from, chat: { id: o.chatId ?? from.id, type: o.chatType ?? "private" }, text });

// Shape of a request sequence without human-language text: what a twin must reproduce exactly.
const TEXT_KEYS = new Set(["text", "title", "description", "label", "error_message", "short_description",
  "input_field_placeholder", "message_text"]);
export function protocol(calls: { method: string; params: Params }[]) {
  const strip = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(strip);
    if (v && typeof v === "object") {
      const o: Params = {};
      for (const [k, x] of Object.entries(v)) if (!TEXT_KEYS.has(k)) o[k] = strip(x);
      return o;
    }
    return v;
  };
  return calls.map((c) => ({ method: c.method, params: strip(c.params) }));
}
