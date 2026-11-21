// Run: node --test examples/ts/publishing/publish.test.ts   (Node >= 22.18)
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { err, FakeTransport } from "../tgkit.ts";
import { checkButtons, fanOut, plan, Publisher, toEntities, type Post } from "./publish.ts";

const CH = -1001500000001;
const newsPost = (): Post => {
  const url = "https://example.com/news/4821?utm=feed&ref=\"tg\"";
  return {
    blocks: [{ type: "heading", text: "Tram line 4 <reopens> & runs until 01:00" },
      { type: "paragraph", text: "Repairs on Bridge Street are finished two weeks early. Night trams start on Friday." },
      { type: "paragraph", text: ["Source: ", { link: url, text: "City Transport Office" }] }],
    buttons: [[{ text: "Read the full story", url }]], linkPreview: { url, large: true },
  };
};

test("same wire payload as the Python recipe R30", () => {
  const golden = JSON.parse(readFileSync(new URL("../../payloads/r30-news-autoposter.json", import.meta.url), "utf8"));
  const [[method, params]] = plan(newsPost(), CH);
  assert.equal(method, golden.steps[0].method);
  assert.deepEqual(params, golden.steps[0].params);
});

test("timeout never double-posts; reconcile unlocks", async () => {
  const t = new FakeTransport().script("sendMessage", "TIMEOUT");
  const pub = new Publisher(t);
  assert.equal((await pub.publish(newsPost(), CH, "k")).status, "unknown");
  assert.equal((await pub.publish(newsPost(), CH, "k")).status, "unknown");
  assert.equal(t.calls.length, 1);
  assert.equal(pub.reconcile("k", [5001]), "sent");
  assert.equal((await pub.publish(newsPost(), CH, "k")).status, "already_sent");
  assert.equal(t.calls.length, 1);
});

test("unchanged edit sends nothing; changed edit is editMessageText", async () => {
  const t = new FakeTransport();
  const pub = new Publisher(t);
  await pub.publish(newsPost(), CH, "k");
  assert.equal(await pub.edit("k", newsPost()), "unchanged");
  assert.equal(t.calls.length, 1);
  const changed = newsPost(); changed.blocks[1] = { type: "paragraph", text: "Night trams start on Saturday." };
  assert.equal(await pub.edit("k", changed), "edited");
  assert.equal(t.calls[1].method, "editMessageText");
});

test("album: no reply_markup on the group, buttons in a silent follow-up", () => {
  const reqs = plan({ blocks: [{ type: "paragraph", text: "Market" }], media: [{ type: "photo", ref: "A" }, { type: "photo", ref: "B", spoiler: true }],
    buttons: [[{ text: "Map", url: "https://example.com/m" }]] }, CH);
  assert.deepEqual(reqs.map((r) => r[0]), ["sendMediaGroup", "sendMessage"]);
  assert.ok(!("reply_markup" in reqs[0][1]) && reqs[1][1].disable_notification === true);
});

test("hostile text stays literal; UTF-16 offsets", () => {
  const { text, entities } = toEntities([{ type: "paragraph", text: ["👩‍👩‍👧 ", { bold: "<b>_*" }] }]);
  assert.equal(text, "👩‍👩‍👧 <b>_*");
  assert.deepEqual(entities, [{ type: "bold", offset: 9, length: 5 }]);
  assert.throws(() => toEntities([{ type: "paragraph", text: { link: "javascript:alert(1)", text: "x" } }]));
});

test("channel button rules", () => {
  assert.equal(checkButtons([[{ text: "Like", callback_data: "like" }], [{ text: "Code", copy_text: { text: "X" } }]]).length, 0);
  assert.equal(checkButtons([[{ text: "App", web_app: { url: "https://e.com" } }]]).length, 1);
  assert.equal(checkButtons([[{ text: "x", url: "https://e.com", icon_custom_emoji_id: "1" }]]).length, 1);
});

test("fan-out: 429 waits retry_after, 403 does not stop the batch", async () => {
  const sleeps: number[] = [];
  const t = new FakeTransport().script("sendMessage", { message_id: 1 }, err(403, "Forbidden: bot was blocked by the user"),
    err(429, "Too Many Requests", 3), { message_id: 2 });
  const jobs = [1, 2, 3].map((id) => [String(id), plan({ blocks: [{ type: "paragraph", text: "hi" }] }, id)] as [string, [string, Record<string, unknown>][]]);
  const report = await fanOut(t, jobs, { sleep: async (s) => { sleeps.push(s); } });
  assert.deepEqual(report.sent, ["1", "3"]);
  assert.deepEqual(report.blocked, ["2"]);
  assert.ok(sleeps.includes(3));
  assert.equal(t.calls.length, 4);
});
