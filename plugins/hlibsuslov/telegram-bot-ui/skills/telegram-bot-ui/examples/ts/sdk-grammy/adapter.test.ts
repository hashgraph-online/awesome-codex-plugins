// Offline contract test against the real grammy@1.46.0 package: no token, no network.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import grammy from "grammy";

const { Bot } = grammy;
import { ALLOWED_UPDATES, DEFAULT_UPDATE_TYPES, installWidgetRouting, widgetApi } from "./adapter.ts";

const fixture = (n: string) => JSON.parse(readFileSync(new URL(`../../fixtures/${n}`, import.meta.url), "utf8"));
const BOT_INFO = { id: 999000111, is_bot: true as const, first_name: "OrdersBot", username: "orders_demo_bot",
  can_join_groups: true, can_read_all_group_messages: false, supports_inline_queries: false,
  can_connect_to_business: false, has_main_web_app: false };

function offlineBot() {
  const bot = new Bot("123456:" + "A".repeat(35), { botInfo: BOT_INFO as never });
  const calls: { method: string; payload: unknown }[] = [];
  bot.api.config.use(async (_prev, method, payload) => {
    calls.push({ method, payload });
    return { ok: true, result: (method.startsWith("send") ? { message_id: 1, date: 0, chat: { id: 1, type: "private" } } : true) } as never;
  });
  return { bot, calls };
}

test("default subscription omits widget updates; adapter adds them", () => {
  assert.ok(!DEFAULT_UPDATE_TYPES.includes("widget_query"));
  assert.ok(DEFAULT_UPDATE_TYPES.includes("stopped_message_generation"), "10.3 is known");
  assert.ok(ALLOWED_UPDATES.includes("widget_query") && ALLOWED_UPDATES.includes("shared_widget_query"));
});

test("widget_query reaches the handler and 10.4 methods reach the wire", async () => {
  const { bot, calls } = offlineBot();
  const seen: string[] = [];
  installWidgetRouting(bot, async (kind, q, api) => {
    seen.push(`${kind}:${q.id}`);
    await api.answerWidgetQuery({ widget_query_id: q.id, data: '{"ok":true}' });
  });
  bot.on("message", () => { seen.push("message"); });
  await bot.handleUpdate(fixture("widget_query_ship.json"));
  const fwd = fixture("shared_widget_query_vote.json"); delete fwd._test_server_only;
  await bot.handleUpdate(fwd);
  assert.deepEqual(seen, ["widget_query:8123456789012345678", "shared_widget_query:8123456789012340101"]);
  await widgetApi(bot).sendWidget({ chat_id: 111111111, html: "<p>x</p>", caption: "c", allow_queries: true });
  assert.deepEqual(calls.map((c) => c.method), ["answerWidgetQuery", "answerWidgetQuery", "sendWidget"]);
  assert.deepEqual(calls[2].payload, { chat_id: 111111111, html: "<p>x</p>", caption: "c", allow_queries: true });
});

test("10.3 fields serialize through grammY unchanged", async () => {
  const { bot, calls } = offlineBot();
  const kb = { inline_keyboard: [[{ text: "Sold out", disabled: {} }]], force_reply: true };
  await bot.api.sendMessage(1, "Pick a size", { reply_markup: kb as never });
  await bot.api.raw.sendMessageDraft({ chat_id: 1, draft_id: 7, text: "", can_stop: true, keep_on_stop: true } as never);
  assert.deepEqual((calls[0].payload as { reply_markup: unknown }).reply_markup, kb);
  assert.equal((calls[1].payload as { can_stop: boolean }).can_stop, true);
});
