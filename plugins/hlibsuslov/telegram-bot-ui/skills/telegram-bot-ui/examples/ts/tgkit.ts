// tgkit.ts - the TypeScript twin of examples/python/tgkit (same invariants).
// Runs on Node >= 22.18 / 24 with built-in type stripping: no build, no deps.
// Verified against the Bot API docs on 2026-11-12 (Bot API 10.4).
import { deflateSync } from "node:zlib";

// Raw Bot API JSON. Its shape depends on the method, so it stays loosely typed here and is
// checked by the offline validators (scripts/validate_*.py) and the tests instead of zod:
// this harness deliberately has zero dependencies.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Params = Record<string, any>;
export type Call = { method: string; params: Params };

export class TelegramError extends Error {
  method: string; code: number; description: string; retryAfter?: number;
  constructor(method: string, code: number, description: string, retryAfter?: number) {
    super(`${method}: ${code} ${description}`);
    this.method = method; this.code = code; this.description = description; this.retryAfter = retryAfter;
  }
  get category(): string { return classify(this.code, this.description); }
}
export class OutcomeUnknown extends Error {
  method: string;
  constructor(method: string) { super(`${method}: outcome unknown`); this.method = method; }
}

export function classify(code: number, description: string): string {
  const d = description.toLowerCase();
  if (code === 429) return "rate_limited";
  if (code === 403) return "permission";
  if (code === 404) return "unsupported";
  if (code >= 500) return "server";
  if (d.includes("message is not modified")) return "not_modified";
  if (d.includes("query is too old")) return "query_too_old";
  if (/not enough rights|have no rights|chat_write_forbidden|bot was blocked/.test(d)) return "permission";
  if (/method not found|unknown method|unsupported|not supported/.test(d)) return "unsupported";
  return "validation";
}

type Scripted = unknown | "TIMEOUT" | ((m: string, p: Params) => unknown);
export class FakeTransport {
  calls: Call[] = [];
  private scripts = new Map<string, Scripted[]>();
  private nextId = 1000;
  script(method: string, ...results: Scripted[]): this {
    this.scripts.set(method, [...(this.scripts.get(method) ?? []), ...results]); return this;
  }
  async call(method: string, params: Params): Promise<any> {
    const wire = JSON.parse(JSON.stringify(params)); // what would really be sent
    this.calls.push({ method, params: wire });
    const queue = this.scripts.get(method);
    let r: any = queue && queue.length ? queue.shift() : this.fallback(method, wire);
    if (typeof r === "function") r = r(method, wire);
    if (r === "TIMEOUT") throw new OutcomeUnknown(method);
    if (r && typeof r === "object" && r.ok === false) throw new TelegramError(method, r.error_code, r.description, r.parameters?.retry_after);
    return r;
  }
  of(method: string): Params[] { return this.calls.filter((c) => c.method === method).map((c) => c.params); }
  private fallback(method: string, p: Params): any {
    if (method.startsWith("send") && !method.endsWith("Draft")) {
      const id = ++this.nextId;
      const msg: Params = { message_id: id, date: 0, chat: { id: p.chat_id } };
      if (p.ephemeral_message_parameters) { msg.message_id = 0; msg.ephemeral_message_id = id; }
      if (method === "sendWidget") msg.widget = { html: p.html, ...(p.is_shared ? { id: `77700${id}` } : {}) };
      return msg;
    }
    return true;
  }
}
export const err = (code: number, description: string, retry_after?: number) =>
  ({ ok: false, error_code: code, description, ...(retry_after ? { parameters: { retry_after } } : {}) });

const IDEMPOTENT = /^(edit|answer|get|delete|set)/;
export async function callWithPolicy(t: { call(m: string, p: Params): Promise<any> }, method: string, params: Params,
  opts: { maxAttempts?: number; sleep?: (s: number) => Promise<void> } = {}): Promise<any> {
  const max = opts.maxAttempts ?? 3;
  const sleep = opts.sleep ?? ((s: number) => new Promise((r) => setTimeout(r, s * 1000)));
  for (let attempt = 1; ; attempt++) {
    try { return await t.call(method, params); } catch (e) {
      if (e instanceof TelegramError) {
        if (e.category === "not_modified" && method.startsWith("edit")) return true;
        if (e.category === "rate_limited" && attempt < max) { await sleep(Math.max(e.retryAfter ?? 0, attempt)); continue; }
        if (e.category === "server" && IDEMPOTENT.test(method) && attempt < max) { await sleep(2 ** (attempt - 1)); continue; }
        throw e;
      }
      if (e instanceof OutcomeUnknown && IDEMPOTENT.test(method) && attempt < max) { await sleep(2 ** (attempt - 1)); continue; }
      throw e; // a send with unknown outcome is never repeated automatically
    }
  }
}

// ---- update routing -------------------------------------------------------
export class Router {
  handlers = new Map<string, (payload: any) => any>();
  unhandled: string[] = [];
  on(kind: string, fn: (payload: any) => any): this { this.handlers.set(kind, fn); return this; }
  allowedUpdates(): string[] { return [...this.handlers.keys()].sort(); }
  async dispatch(update: Params): Promise<any> {
    const kind = Object.keys(update).find((k) => k !== "update_id") ?? "<empty>";
    const fn = this.handlers.get(kind);
    if (!fn) { this.unhandled.push(kind); return undefined; }
    return fn(update[kind]);
  }
}

// ---- controlled generation (10.3) -----------------------------------------
export type Policy = "discard" | "keep_marked" | "offer_continue";
export const TERMINAL = new Set(["stopped", "completed", "failed", "timed_out"]);
export type Effect = { call?: string; params?: Params; final?: boolean; cancelUpstream?: boolean };
const LABELS: Record<string, string> = { start: "Starting…", search: "Searching the sources…", read: "Reading the documents…", write: "Writing the answer…" };

export class Generation {
  state = "started"; buffer = ""; flushed = 0; lastFlush: number | null = null; notBefore = 0;
  stage = "start"; stageDirty = true; dropped = 0; finalizations = 0; outcome: string | null = null;
  opId: string; chatId: number; draftId: number; threadId?: number; policy: Policy;
  minInterval = 1; minChars = 40; deadline: number; startedAt = 0;
  constructor(o: { opId: string; chatId: number; draftId: number; threadId?: number; policy?: Policy; deadline?: number }) {
    if (!o.draftId) throw new Error("draft_id must be non-zero");
    this.opId = o.opId; this.chatId = o.chatId; this.draftId = o.draftId; this.threadId = o.threadId;
    this.policy = o.policy ?? "keep_marked"; this.deadline = o.deadline ?? 120;
  }
  get terminal() { return TERMINAL.has(this.state); }
  key() { return `${this.chatId}:${this.threadId ?? 0}:${this.draftId}`; }
  start(now: number): Effect[] { this.startedAt = now; this.state = "generating"; return this.draft(now); }
  onStage(s: string, now: number): Effect[] { if (this.terminal) return []; this.stage = LABELS[s] ? s : "write"; this.stageDirty = true; return this.maybe(now); }
  onChunk(text: string, now: number): Effect[] {
    if (this.terminal || this.state === "stop_requested") { this.dropped++; return []; }
    this.buffer += text; return [...this.maybe(now), ...this.deadlineCheck(now)];
  }
  onTick(now: number): Effect[] { if (this.terminal) return []; const d = this.deadlineCheck(now); return d.length ? d : this.maybe(now); }
  onRateLimited(retryAfter: number, now: number) { this.notBefore = Math.max(this.notBefore, now + retryAfter); }
  onStop(now: number): Effect[] {
    if (this.terminal || this.state === "stop_requested") return [];
    this.state = "stop_requested";
    return [{ cancelUpstream: true }, ...this.finalize("stopped", this.buffer)];
  }
  onDone(now: number): Effect[] { if (this.terminal || this.state === "stop_requested") return []; return this.finalize("completed", this.buffer); }
  onError(now: number): Effect[] { if (this.terminal) return []; return [{ cancelUpstream: true }, ...this.finalize("failed", this.buffer)]; }
  private deadlineCheck(now: number): Effect[] {
    if (this.terminal || now - this.startedAt < this.deadline) return [];
    return [{ cancelUpstream: true }, ...this.finalize("timed_out", this.buffer)];
  }
  private maybe(now: number): Effect[] {
    const fresh = this.buffer.length - this.flushed;
    const wants = this.stageDirty || fresh >= this.minChars || (fresh > 0 && /[.!?…]\s*$/.test(this.buffer));
    if (!wants) return [];
    let earliest = this.notBefore;
    if (this.lastFlush !== null) earliest = Math.max(earliest, this.lastFlush + this.minInterval);
    return now < earliest ? [] : this.draft(now);
  }
  private addr(): Params { return { chat_id: this.chatId, ...(this.threadId ? { message_thread_id: this.threadId } : {}) }; }
  private draft(now: number): Effect[] {
    this.lastFlush = now; this.flushed = this.buffer.length; this.stageDirty = false;
    const blocks = [{ type: "thinking", text: LABELS[this.stage] ?? "Working…" }, ...paragraphs(this.buffer)];
    return [{ call: "sendRichMessageDraft", params: { ...this.addr(), draft_id: this.draftId, can_stop: true,
      keep_on_stop: this.policy === "keep_marked", rich_message: { blocks } } }];
  }
  private buttons(...kinds: string[]) {
    const names: Record<string, string> = { continue: "Continue", retry: "Try again" };
    return { inline_keyboard: [kinds.map((k) => ({ text: names[k], callback_data: `gen:${k}:${this.opId}` }))] };
  }
  private final(blocks: Params[], markup?: Params): Effect {
    return { call: "sendRichMessage", final: true, params: { ...this.addr(), rich_message: { blocks }, ...(markup ? { reply_markup: markup } : {}) } };
  }
  private finalize(outcome: string, text: string): Effect[] {
    this.finalizations++; this.outcome = outcome; this.state = outcome;
    if (outcome === "completed") return [this.final(paragraphs(text))];
    if (outcome === "stopped") {
      if (this.policy === "keep_marked" && text.trim())
        return [this.final([...paragraphs(text), { type: "footer", text: "Stopped by you — the answer is incomplete." }], this.buttons("continue", "retry"))];
      if (this.policy === "offer_continue" && text.trim())
        return [this.final([{ type: "paragraph", text: "Stopped. Continue from here or start over?" }], this.buttons("continue", "retry"))];
      return [this.final([{ type: "paragraph", text: "Stopped. Nothing was saved." }], this.buttons("retry"))];
    }
    return [this.final([{ type: "paragraph", text: outcome === "failed" ? "Couldn't finish the answer." : "This is taking too long, so I stopped." }], this.buttons("retry"))];
  }
}
export const paragraphs = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean).map((s) => ({ type: "paragraph", text: s }));

export async function execute(effects: Effect[], t: FakeTransport, g: Generation, now: number, cancel: () => void = () => {}) {
  for (const e of effects) {
    if (e.cancelUpstream) { cancel(); continue; }
    // Non-cancel effects always carry call + params (see Generation.draft/final).
    if (!e.final) {
      try { await t.call(e.call!, e.params!); } catch (x) {
        if (x instanceof TelegramError && x.category === "rate_limited") g.onRateLimited(x.retryAfter ?? 1, now);
      }
      continue;
    }
    await callWithPolicy(t, e.call!, e.params!, { sleep: async () => {} });
  }
}

// ---- ephemeral (10.3/10.4) ------------------------------------------------
export class AudienceViolation extends Error {}
export function ephemeralParams(cq: Params, api: "10.3" | "10.4" = "10.4", replaceOriginal = false): Params {
  const chat = cq.message?.chat;
  if (chat?.is_direct_messages) throw new AudienceViolation("no ephemeral callback replies in channel DM chats");
  if (replaceOriginal && cq.message?.ephemeral_message_id) throw new Error("edit the ephemeral message instead");
  const eph: Params = { callback_query_id: cq.id };
  const out: Params = {};
  if (api === "10.3") { if (!chat) throw new Error("10.3 needs chat_id"); eph.receiver_user_id = cq.from.id; out.chat_id = chat.id; }
  if (replaceOriginal) eph.replace_callback_query_message = true;
  return { ...out, ephemeral_message_parameters: eph };
}
export function guardAudience(method: string, p: Params, ownerId: number) {
  if (!method.startsWith("send")) return;
  const eph = p.ephemeral_message_parameters;
  if (eph) { if (eph.receiver_user_id !== undefined && eph.receiver_user_id !== ownerId) throw new AudienceViolation("receiver differs"); return; }
  if (p.chat_id === ownerId) return;
  throw new AudienceViolation(`${method} would publish personal content`);
}

// ---- widgets (10.4) -------------------------------------------------------
// Node's zlib can differ from the server's count by a few dozen bytes (Widgets
// guide). Near 4096, trust scripts/validate_widget.py (Python's zlib).
export const compressedSize = (html: string) => deflateSync(Buffer.from(html, "utf8"), { level: 9 }).length;
export function checkWidget(html: string, o: { caption?: string; chatData?: string; publicData?: string; context?: string; environment?: string } = {}) {
  const errors: string[] = []; const warnings: string[] = [];
  const raw = Buffer.byteLength(html, "utf8"); const packed = compressedSize(html);
  if (raw > 32768) errors.push(`html ${raw} bytes > 32768`);
  if (packed > 4096) errors.push(`html compresses to ${packed} bytes > 4096`);
  for (const [n, v] of [["chat_data", o.chatData], ["public_data", o.publicData]] as const)
    if (v !== undefined && Buffer.byteLength(v, "utf8") > 1024) errors.push(`${n} > 1024 UTF-8 bytes`);
  if ((o.environment ?? "production") === "production" && ["group", "supergroup", "inline", "forward"].includes(o.context ?? "private"))
    errors.push(`widgets in ${o.context} are test-server only`);
  if (!o.caption) warnings.push("no caption");
  if (/\bfetch\s*\(|XMLHttpRequest|WebSocket/.test(html)) warnings.push("network APIs are disabled in widgets");
  if (/<\s*(input|select|textarea)\b/i.test(html)) warnings.push("form controls are removed");
  return { ok: errors.length === 0, errors, warnings, raw, packed };
}

export type Rec = { state: Params; revision: number };
// Per-widget serialization: read -> decide -> edit -> commit must not interleave across awaits,
// or two concurrent increments both start from the same revision (lost update).
const widgetLocks = new Map<string, Promise<unknown>>();

export async function handleWidgetQuery(q: Params, store: Map<string, Rec>, answered: Set<string>, t: FakeTransport,
  decide: (q: Params, verb: string, arg: string, rec: Rec) => [Params | null, Params]): Promise<string> {
  // Reserve the id synchronously, before the first await: a redelivered update that
  // arrives while this one is in flight is a duplicate, not a second edit and answer.
  if (answered.has(q.id)) return "duplicate";
  answered.add(q.id);
  const key = q.inline_message_id ? `inline:${q.inline_message_id}` : q.chat ? `msg:${q.chat.id}:${q.message_id}` : `shared:${q.widget_id}`;
  const prev = widgetLocks.get(key) ?? Promise.resolve();
  const run = prev.then(() => processWidgetQuery(q, key, store, t, decide), () => processWidgetQuery(q, key, store, t, decide));
  widgetLocks.set(key, run);
  try { return await run; } finally { if (widgetLocks.get(key) === run) widgetLocks.delete(key); }
}

async function processWidgetQuery(q: Params, key: string, store: Map<string, Rec>, t: FakeTransport,
  decide: (q: Params, verb: string, arg: string, rec: Rec) => [Params | null, Params]): Promise<string> {
  const answer = async (data: Params, outcome: string) => {
    await t.call("answerWidgetQuery", { widget_query_id: q.id, data: JSON.stringify(data) });
    return outcome;
  };
  const bytes = Buffer.byteLength(q.data ?? "", "utf8");
  if (bytes < 1 || bytes > 64) return answer({ ok: false, err: "bad_request" }, "invalid");
  let rec = store.get(key) ?? { state: {}, revision: 0 };
  const [verb, arg = ""] = String(q.data).split(":");
  let next: Params | null; let reply: Params;
  try { [next, reply] = decide(q, verb, arg, rec); } catch { return answer({ ok: false, err: "not_allowed" }, "denied"); }
  if (next) {
    const cand = { state: next, revision: rec.revision + 1 };
    const payload = JSON.stringify({ ...cand.state, r: cand.revision });
    try {
      if (key.startsWith("shared:")) await t.call("editSharedWidgetData", { widget_id: q.widget_id, public_data: payload });
      else await t.call("editMessageWidgetData", { ...(q.inline_message_id ? { inline_message_id: q.inline_message_id } : { chat_id: q.chat.id, message_id: q.message_id }), chat_data: payload });
    } catch (e) {
      if (!(e instanceof TelegramError) || e.category !== "not_modified")
        return answer({ ok: false, err: e instanceof TelegramError && e.category === "rate_limited" ? "busy" : "failed", r: rec.revision }, "edit_failed");
    }
    store.set(key, cand); rec = cand; // commit after the edit
  }
  const { with_state, ...rest } = reply;
  return answer({ ok: true, ...rest, ...(with_state ? { s: { ...rec.state, r: rec.revision } } : {}), r: rec.revision }, "ok");
}

// ---- addressing -----------------------------------------------------------
export function addressOf(m: Params): Params {
  const p: Params = { chat_id: m.chat.id };
  if (m.chat.is_direct_messages) { if (m.direct_messages_topic) p.direct_messages_topic_id = m.direct_messages_topic.topic_id; return p; }
  if (m.is_topic_message && m.message_thread_id) p.message_thread_id = m.message_thread_id;
  if (m.business_connection_id) p.business_connection_id = m.business_connection_id;
  return p;
}
export const privateTopicLink = (bot: string, thread: number) => `https://t.me/${bot}/${thread}`;
