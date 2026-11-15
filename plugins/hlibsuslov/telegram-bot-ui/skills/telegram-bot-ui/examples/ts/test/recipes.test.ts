import { test } from "node:test";
import assert from "node:assert/strict";
import * as R from "../recipes.ts";
import { callWithPolicy, err, FakeTransport, OutcomeUnknown, ephemeralParams, guardAudience, AudienceViolation, checkWidget, handleWidgetQuery, type Rec } from "../tgkit.ts";

const finals = (t: FakeTransport) => t.calls.filter((c) => c.method === "sendRichMessage");

test("R01 stop: one final, late chunk dropped, upstream cancelled", async () => {
  for (const policy of ["keep_marked", "discard", "offer_continue"] as const) {
    const { t, g, cancelled, router } = await R.aiAssistant("stop", policy);
    assert.equal(g.outcome, "stopped"); assert.equal(finals(t).length, 1); assert.equal(cancelled, 1);
    assert.equal(g.dropped, 1); assert.ok(!JSON.stringify(finals(t)).includes("LATE"));
    assert.ok(t.of("sendRichMessageDraft").every((d) => d.can_stop && d.keep_on_stop === (policy === "keep_marked")));
    assert.deepEqual(router.allowedUpdates(), ["stopped_message_generation"]);
  }
  const race = await R.aiAssistant("race_done_first");
  assert.equal(race.g.outcome, "completed"); assert.equal(finals(race.t).length, 1);
});

test("R02 document: compact table, rich quote read when text is empty", async () => {
  const { t, asked } = await R.interactiveDocument();
  const blocks = t.of("sendRichMessage")[0].rich_message.blocks;
  assert.ok(blocks.some((b: { is_compact?: boolean }) => b.is_compact));
  assert.equal(asked, "Rotate the signing key every 90 days.");
});

test("R03 form: double Submit creates one order, force_reply kept on edit", async () => {
  const { t, orders } = await R.multiStepForm();
  assert.equal(orders, 1);
  assert.ok(t.of("editMessageText").every((e) => e.reply_markup.force_reply === true));
  assert.ok("disabled" in t.of("sendMessage")[0].reply_markup.inline_keyboard[1][0]);
});

test("R04 panels: per-user, 10.3 and 10.4 forms, failures stay private", async () => {
  const { t } = await R.personalPanels();
  const [a, b] = t.of("sendMessage");
  assert.ok(!("chat_id" in a) && b.ephemeral_message_parameters.receiver_user_id === 222222222);
  assert.ok(!a.text.includes("Pepperoni") && !b.text.includes("Margherita"));
  const failed = await R.personalPanels(true);
  assert.ok(failed.t.calls.every((c) => !c.method.startsWith("send") || c.params.ephemeral_message_parameters));
  assert.throws(() => guardAudience("sendMessage", { chat_id: -100, text: "x" }, 1), AudienceViolation);
  assert.throws(() => ephemeralParams(R.fixture("callback_channel_dm.json").callback_query), AudienceViolation);
});

test("R05 widget: answered once, failed edit not committed", async () => {
  const { store, outcomes, check, router } = await R.privateWidget();
  assert.ok(check.ok, check.errors.join());
  assert.deepEqual(outcomes, ["ok", "duplicate", "edit_failed"]);
  const rec = [...store.values()][0];
  assert.equal(rec.state.opt, "fast"); assert.equal(rec.state.st, "draft"); assert.equal(rec.revision, 1);
  assert.deepEqual(router.allowedUpdates(), ["widget_query"]);
  assert.ok(!checkWidget("<p>x</p>", { caption: "c", context: "group" }).ok);
  assert.ok(checkWidget("<p>x</p>", { caption: "c", context: "group", environment: "test" }).ok);
});

test("R06 shared widget: one vote per user, coalesced edits", async () => {
  const { t, votes } = await R.sharedWidget();
  assert.equal(votes.size, 2); assert.equal(t.of("editSharedWidgetData").length, 2);
  assert.equal(JSON.parse(t.of("editSharedWidgetData").at(-1)!.public_data).r, 3); // two writes exist (asserted above)
});

test("R07 wallet: awaiting until chain check, no 'from' in tx", async () => {
  const ok = await R.walletPayment(); assert.equal(ok.state, "paid"); assert.ok(!("from" in ok.tx));
  assert.equal(JSON.parse(ok.t.of("answerWidgetQuery")[1].data).state, "awaiting");
  assert.equal((await R.walletPayment("mismatch")).state, "mismatch");
});

test("R08 topics: Stop isolated by thread; DM topics use their own field", async () => {
  const { gens, link, dm } = await R.multiTopic();
  assert.deepEqual(gens.map((g) => g.outcome), ["completed", "stopped"]);
  assert.equal(link, "https://t.me/orders_demo_bot/12");
  assert.deepEqual(dm, { chat_id: -1002, direct_messages_topic_id: 222222222 });
});

test("429 is bounded and waits; unknown send outcome is not repeated", async () => {
  const slept: number[] = [];
  const t = new FakeTransport().script("sendMessage", err(429, "Too Many Requests", 4), err(429, "Too Many Requests", 4), err(429, "x", 4));
  await assert.rejects(callWithPolicy(t, "sendMessage", {}, { sleep: async (s) => { slept.push(s); } }));
  assert.equal(t.calls.length, 3); assert.deepEqual(slept, [4, 4]);
  const u = new FakeTransport().script("sendMessage", "TIMEOUT");
  await assert.rejects(callWithPolicy(u, "sendMessage", {}, { sleep: async () => {} }), OutcomeUnknown);
  assert.equal(u.calls.length, 1);
});

test("concurrent widget queries: no duplicate edits, no lost updates", async () => {
  // A transport that yields between calls, like a real network.
  const t = new FakeTransport().script("editMessageWidgetData", ...Array(10).fill(() => new Promise((r) => setTimeout(() => r(true), 5))));
  const store = new Map<string, Rec>([["msg:1:10", { state: { n: 0 }, revision: 0 }]]);
  const answered = new Set<string>();
  const q = (id: string) => ({ id, from: { id: 1 }, chat: { id: 1, type: "private" }, message_id: 10, data: "inc", type: { type: "data" } });
  const inc = (_q: unknown, _v: string, _a: string, rec: Rec): [Record<string, number>, Record<string, never>] => [{ n: rec.state.n + 1 }, {}];
  const out = await Promise.all([handleWidgetQuery(q("a"), store, answered, t, inc), handleWidgetQuery(q("a"), store, answered, t, inc),
    handleWidgetQuery(q("b"), store, answered, t, inc), handleWidgetQuery(q("c"), store, answered, t, inc)]);
  assert.deepEqual(out.sort(), ["duplicate", "ok", "ok", "ok"]);
  assert.equal(store.get("msg:1:10")!.state.n, 3); // set above, never removed
  assert.equal(t.of("answerWidgetQuery").length, 3);
});
