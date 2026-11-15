// Twins replay the Python recipes: same methods, same order, same callback scheme, same
// structure (human-language text is normalized away; the catalogs live in the Python recipes).
// Run: node --test examples/ts/usecases/usecases.test.ts   (Node >= 22.18)
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { protocol, pack, I18n } from "./flows.ts";
import * as shop from "./shop.ts";
import * as onboarding from "./onboarding.ts";
import * as settings from "./settings.ts";
import * as inline from "./inline.ts";

const payload = (name: string) =>
  JSON.parse(readFileSync(new URL(`../../payloads/${name}.json`, import.meta.url), "utf8")).steps as { method: string; params: Record<string, unknown> }[];

const twins: [string, () => Promise<{ t: { calls: { method: string; params: Record<string, unknown> }[] }; out: string[] }>][] = [
  ["r20-shop", shop.run], ["r23-onboarding", onboarding.run], ["r24-settings", settings.run], ["r60-inline-mode", inline.run],
];

for (const [name, run] of twins) {
  test(`${name}: the twin sends the same protocol as the Python recipe`, async () => {
    const { t } = await run();
    assert.deepEqual(protocol(t.calls), protocol(payload(name)));
  });
}

test("shop: one invoice per order, fulfilment once, sold-out and foreign taps refused", async () => {
  const { t, out, shop: s } = await shop.run();
  assert.equal(t.calls.filter((c) => c.method === "sendInvoice").length, 2);
  assert.deepEqual(out.slice(12, 16), ["pc_ok", "fulfilled", "duplicate_update", "duplicate_payment"]);
  assert.equal(out[1], "sold_out"); assert.equal(out[4], "stale"); assert.equal(out.at(-1), "not_yours");
  assert.equal(s.stock.eth, 3);
});

test("callback_data is limited in bytes, Cyrillic included", () => {
  assert.equal(Buffer.byteLength(pack("x", "п".repeat(31))), 64);
  assert.throws(() => pack("xy", "п".repeat(31)), RangeError);
});

test("i18n escapes values and reports missing keys", () => {
  const i = new I18n({ en: { hi: "<b>{n}</b>", x: "1" }, uk: { hi: "<b>{n}</b>" } });
  assert.equal(i.t("uk", "hi", { n: "<i>" }), "<b>&lt;i&gt;</b>");
  assert.deepEqual(i.missing(), { uk: ["x"] });
});
