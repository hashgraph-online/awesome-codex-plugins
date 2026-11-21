// The eight end-to-end recipes in TypeScript, sharing fixtures and payload shapes with
// the Python versions (examples/fixtures, examples/widgets). Offline by default.
// Run: node examples/ts/recipes.ts        Test: cd examples/ts && npm test
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  FakeTransport, Generation, Router, execute, ephemeralParams, guardAudience, checkWidget, handleWidgetQuery,
  addressOf, privateTopicLink, err, TelegramError, type Params, type Rec,
} from "./tgkit.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const fixture = (n: string): Params => JSON.parse(readFileSync(join(ROOT, "fixtures", n), "utf8"));
export const widgetHtml = (n: string) => readFileSync(join(ROOT, "widgets", n), "utf8");
const CHAT = 111111111;

// R01 - AI answer with Stop
export async function aiAssistant(ending: "stop" | "complete" | "race_done_first" = "stop", policy: "keep_marked" | "discard" | "offer_continue" = "keep_marked") {
  const t = new FakeTransport(); let cancelled = 0;
  const g = new Generation({ opId: "a1b2c3", chatId: CHAT, draftId: 48127, policy });
  const ops = new Map([[g.key(), g]]);
  const router = new Router().on("stopped_message_generation", async (s: Params) => {
    const op = ops.get(`${s.chat.id}:${s.message_thread_id ?? 0}:${s.draft_id}`);
    if (op) await execute(op.onStop(now), t, op, now, () => cancelled++);
  });
  let now = 0;
  const at = async (ts: number, eff: ReturnType<Generation["start"]>) => { now = ts; await execute(eff, t, g, ts, () => cancelled++); };
  await at(0, g.start(0));
  await at(1.2, g.onStage("search", 1.2));
  await at(1.5, g.onChunk("Telegram added a Stop button to drafts. ", 1.5));
  await at(2.6, g.onChunk("\n\nkeep_on_stop keeps the partial draft for a short time", 2.6));
  if (ending === "stop") {
    await router.dispatch(fixture("stopped_message_generation.json"));
    await at(3, g.onChunk(" LATE", 3));
    await router.dispatch(fixture("stopped_message_generation.json"));
    await at(3.5, g.onDone(3.5));
  } else if (ending === "race_done_first") {
    await at(3, g.onDone(3)); await router.dispatch(fixture("stopped_message_generation.json"));
  } else await at(3, g.onDone(3));
  return { t, g, cancelled, router };
}

// R02 - interactive document
export async function interactiveDocument() {
  const t = new FakeTransport();
  const doc = { blocks: [
    { type: "heading", size: 2, text: "Key rotation policy v3" },
    { type: "table", is_bordered: true, is_compact: true, cells: [
      [{ text: "Key", is_header: true, align: "left", valign: "middle" }, { text: "Days left", is_header: true, align: "right", valign: "middle" }],
      [{ text: "signing", align: "left", valign: "middle" }, { text: "12", align: "right", valign: "middle" }]] },
    { type: "expandable_blockquote", text: "Auditor note: rotation must be logged…", credit: "Audit 2026-10" },
    { type: "document", document: { type: "document", media: "BQACAgIAAxkBAAIBdemoFileId" }, caption: { text: "Full procedure (PDF)" } },
    { type: "buttons", align: "left", buttons: [{ text: "Approve", callback_data: "doc:approve:v3", style: "success" }, { text: "Copy id", copy_text: { text: "ROT-2026-v3" } }] },
  ] };
  await t.call("sendRichMessage", { chat_id: CHAT, rich_message: doc });
  const quote = fixture("message_quote_rich.json").message.quote;
  const plain = (rt: unknown): string => typeof rt === "string" ? rt : Array.isArray(rt) ? rt.map(plain).join("")
    : rt && typeof rt === "object" ? plain((rt as Params).text) : "";
  const asked = quote.text || quote.rich_texts.map(plain).join("\n");   // 10.4: text may be ""
  await t.call("sendMessage", { chat_id: CHAT, text: "Because a leaked key stops working within 90 days.",
    reply_parameters: { message_id: 600, quote_rich_texts: [{ type: "bold", text: "signing key" }] } });
  return { t, asked };
}

// R03 - form with force_reply + disabled Submit
export async function multiStepForm() {
  const t = new FakeTransport(); const submitted = new Set<string>(); let orders = 0;
  const kb = (complete: boolean) => ({ force_reply: true, inline_keyboard: [
    [{ text: "S", callback_data: "f:F7:0:o:0" }, { text: "M", callback_data: "f:F7:0:o:1" }],
    [complete ? { text: "Submit", callback_data: "f:F7:submit", style: "success" } : { text: "Submit", disabled: {} }]] });
  await t.call("sendMessage", { chat_id: CHAT, text: "Step 1 of 1. Choose a size or type it.", reply_markup: kb(false) });
  await t.call("sendMessage", { chat_id: CHAT, text: "Size: M. Ready to send.", reply_markup: kb(true) });
  const submit = async (qid: string) => {
    if (submitted.has("F7")) return t.call("answerCallbackQuery", { callback_query_id: qid, text: "Already sent." });
    submitted.add("F7"); orders++;
    await t.call("answerCallbackQuery", { callback_query_id: qid });
    // force_reply can't change on edit: repeat it.
    await t.call("editMessageText", { chat_id: CHAT, message_id: 1002, text: "Sent. Reference: ORD-1042",
      reply_markup: { force_reply: true, inline_keyboard: [[{ text: "Sent", disabled: {} }]] } });
  };
  await submit("q1"); await submit("q2");
  return { t, orders };
}

// R04 - shared card, personal panels
export async function personalPanels(failFirst = false) {
  const t = new FakeTransport();
  if (failFirst) t.script("sendMessage", err(400, "Bad Request: EPHEMERAL_REPLY_UNAVAILABLE"));
  const data: Record<number, string> = { 111111111: "Margherita — $9.50", 222222222: "Pepperoni — $12.00" };
  for (const [name, api] of [["callback_card_user_a.json", "10.4"], ["callback_card_user_b.json", "10.3"]] as const) {
    const cq = fixture(name).callback_query; const text = `Your order: ${data[cq.from.id]}`;
    const p = { ...ephemeralParams(cq, api), text };
    guardAudience("sendMessage", p, cq.from.id);
    try { await t.call("sendMessage", p); await t.call("answerCallbackQuery", { callback_query_id: cq.id }); }
    catch { await t.call("answerCallbackQuery", { callback_query_id: cq.id, text, show_alert: true }); } // still private
  }
  return { t };
}

// R05 - private widget
export async function privateWidget() {
  const t = new FakeTransport(); const store = new Map<string, Rec>(); const answered = new Set<string>();
  const html = widgetHtml("order-card.html");
  const order = { o: "1042", items: [{ q: 2, n: "Margherita", p: 950 }], opt: "std", st: "draft" };
  const check = checkWidget(html, { caption: "Order #1042", chatData: JSON.stringify({ ...order, r: 0 }) });
  const msg = await t.call("sendWidget", { chat_id: CHAT, html, caption: "Order #1042 · $23.50", allow_queries: true, chat_data: JSON.stringify({ ...order, r: 0 }) });
  store.set(`msg:${CHAT}:${msg.message_id}`, { state: order, revision: 0 });
  const decide = (_q: Params, verb: string, arg: string, rec: Rec): [Params | null, Params] => {
    if (verb === "sync") return [null, { with_state: true }];
    if (rec.state.st !== "draft") return [null, { msg: "Already confirmed", with_state: true }];
    if (verb === "ship") return [{ ...rec.state, opt: arg }, { with_state: true }];
    if (verb === "confirm") return [{ ...rec.state, st: "confirmed" }, { with_state: true }];
    return [null, { msg: "Unknown" }];
  };
  const router = new Router().on("widget_query", (q: Params) => handleWidgetQuery({ ...q, message_id: msg.message_id }, store, answered, t, decide));
  const outcomes = [await router.dispatch(fixture("widget_query_ship.json")), await router.dispatch(fixture("widget_query_ship.json"))];
  t.script("editMessageWidgetData", err(429, "Too Many Requests: retry after 3", 3));
  outcomes.push(await router.dispatch(fixture("widget_query_confirm.json")));
  return { t, store, outcomes, check, router };
}

// R06 - shared widget (forward/inline parts are test-server only)
export async function sharedWidget() {
  const t = new FakeTransport(); const votes = new Map<number, number>(); let rev = 0; let lastWrite = -Infinity; let pending: string | null = null;
  const first = await t.call("sendWidget", { chat_id: 555555555, html: widgetHtml("shared-poll.html"), is_shared: true, allow_queries: true, caption: "Poll: Lunch?" });
  const id = first.widget.id;
  await t.call("sendSharedWidget", { chat_id: CHAT, widget_id: id, caption: "Poll: Lunch?" });
  const flush = async (now: number) => { if (pending && now - lastWrite >= 1) { await t.call("editSharedWidgetData", { widget_id: id, public_data: pending }); pending = null; lastWrite = now; } };
  const onVote = async (q: Params, now: number) => {
    votes.set(q.from.id, Number(q.data.split(":")[1])); rev++;
    const counts = [0, 0, 0]; for (const v of votes.values()) counts[v]++;
    const state = { q: "Lunch?", opts: ["Pizza", "Sushi", "Salad"], v: counts, r: rev };
    await t.call("answerWidgetQuery", { widget_query_id: q.id, data: JSON.stringify({ ok: true, s: state, r: rev }) });
    pending = JSON.stringify(state); await flush(now);
  };
  await onVote({ ...fixture("widget_query_vote.json").widget_query, widget_id: id }, 10);
  await onVote({ ...fixture("shared_widget_query_vote.json").shared_widget_query, widget_id: id }, 10.4);
  await onVote({ ...fixture("widget_query_inline_vote.json").widget_query, widget_id: id }, 10.7);
  await flush(11.2);
  return { t, votes };
}

// R07 - wallet
export async function walletPayment(verdict: "confirmed" | "mismatch" = "confirmed") {
  const t = new FakeTransport(); let state = "new";
  const data = fixture("widget_query_wallet_data.json").widget_query;
  const tx = { valid_until: 1762900300, messages: [{ address: "UQAsampleMerchant00000000000000000000000000000005", amount: "1250000000" }] };
  await t.call("answerWidgetQuery", { widget_query_id: data.id, data: JSON.stringify({ ok: true, tx }) });
  const sent = fixture("widget_query_sent_transaction.json").widget_query;
  state = "awaiting";                          // a notification, not proof
  await t.call("answerWidgetQuery", { widget_query_id: sent.id, data: JSON.stringify({ ok: true, state }) });
  state = verdict === "confirmed" ? "paid" : "mismatch"; // after YOUR on-chain check
  await t.call("editMessageWidgetData", { chat_id: CHAT, message_id: sent.message_id, chat_data: JSON.stringify({ o: "42", st: state, r: 2 }) });
  return { t, state, tx };
}

// R08 - topics
export async function multiTopic() {
  const t = new FakeTransport();
  const gens = [11, 12].map((th, i) => new Generation({ opId: `t${th}`, chatId: CHAT, draftId: 50000 + i, threadId: th }));
  for (const g of gens) { await execute(g.start(0), t, g, 0); await execute(g.onChunk(`Answer for topic ${g.threadId}. `, 1.5), t, g, 1.5); }
  const s = fixture("stopped_message_generation_topic.json").stopped_message_generation;
  const target = gens.find((g) => g.key() === `${s.chat.id}:${s.message_thread_id ?? 0}:${s.draft_id}`)!; // fixture targets topic 12
  await execute(target.onStop(2), t, target, 2);
  await execute(gens[0].onDone(3), t, gens[0], 3);
  const dm = addressOf({ chat: { id: -1002, is_direct_messages: true }, message_thread_id: 9, direct_messages_topic: { topic_id: 222222222 } });
  return { t, gens, link: privateTopicLink("orders_demo_bot", 12), dm };
}

if (import.meta.url === `file://${process.argv[1]?.replace(/\\/g, "/").replace(/^\/?/, "/")}` || process.argv[1]?.endsWith("recipes.ts")) {
  for (const [name, fn] of Object.entries({ aiAssistant, interactiveDocument, multiStepForm, personalPanels, privateWidget, sharedWidget, walletPayment, multiTopic })) {
    const { t } = await (fn as () => Promise<{ t: FakeTransport }>)();
    console.log(`\n== ${name} ==`);
    for (const c of t.calls) console.log(c.method, JSON.stringify(c.params).slice(0, 140));
  }
}
void TelegramError;
