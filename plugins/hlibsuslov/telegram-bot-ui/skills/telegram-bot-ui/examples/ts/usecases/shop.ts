// shop.ts - TypeScript twin of examples/python/recipes/r20_shop.py (recipe 20).
// Same protocol: one invoice per order+method, server-side pre-checkout re-check,
// fulfilment once per telegram_payment_charge_id, disabled sold-out items, stale/owner guards.
import { readFileSync } from "node:fs";
import { FakeTransport, type Params } from "../tgkit.ts";
import { ScreenFlow, I18n, Raw, OnceStore, UpdateDedup, btn, kb, pack, b36, user, callback, textMessage, type Session } from "./flows.ts";

const fixture = (name: string) => JSON.parse(readFileSync(new URL(`../../fixtures/${name}`, import.meta.url), "utf8"));
export const ALICE = user(111111111, "Alice", "en"), OLENA = user(333333333, "Олена", "uk");
const PROVIDER_TOKEN = "PROVIDER_TOKEN_FROM_ENV"; // live: env SHOP_PROVIDER_TOKEN

// English only here: the Python recipe carries the full en/uk catalog; the twin proves the protocol.
const I18N = new I18n({ en: {
  catalog: "<b>Coffee beans</b>\nPick a coffee:", product: "<b>{title}</b>\nPrice: ⭐ {stars} · €{eur}\nIn your cart: {qty}",
  cart: "<b>Your cart</b>\n{lines}\n\nTotal: ⭐ {stars} · €{eur}", cart_empty: "<b>Your cart is empty</b>",
  pay: "<b>Checkout</b> · order {order}\nTotal: ⭐ {stars} · €{eur}", invoice_sent: "Your invoice is below ↓",
  sold_out: "Sold out. We'll restock on Monday.", added: "Added to cart", pc_changed: "Your cart changed after this invoice.",
  pc_stock: "Sorry, {title} just sold out.", invoice_title: "Order {order}", invoice_desc: "{count} bag(s) of coffee",
  receipt_title: "Paid · order {order}", receipt_note: "We'll message you when it ships.",
  btn_cart: "Cart ({qty})", btn_add: "Add to cart", btn_back: "← Back", btn_checkout: "Checkout", btn_stars: "Pay ⭐ {stars}",
  btn_card: "Pay by card · €{eur}", btn_clear: "Empty the cart", btn_catalog: "Catalog" } });

type Product = { title: string; stars: number; cents: number; stock: number };
const PRODUCTS: Record<string, Product> = {
  eth: { title: "Ethiopia Yirgacheffe", stars: 250, cents: 920, stock: 5 },
  col: { title: "Colombia Huila", stars: 220, cents: 840, stock: 0 },
  ken: { title: "Kenya Nyeri AA", stars: 300, cents: 1100, stock: 1 },
};
const eur = (c: number) => `${Math.floor(c / 100)}.${String(c % 100).padStart(2, "0")}`;
type Order = { id: string; user: number; chat: number; lang: string; items: Record<string, number>; stars: number; cents: number;
  count: number; status: "pending" | "superseded" | "paid"; method?: string; charge?: string };

export class Shop {
  flow: ScreenFlow; stock: Record<string, number>; orders = new Map<string, Order>(); byCart = new Map<string, string>();
  invoices = new OnceStore(); payments = new OnceStore(); updates = new UpdateDedup(); next = 1001;
  t: FakeTransport;
  constructor(t: FakeTransport) {
    this.t = t;
    this.flow = new ScreenFlow(t, "sh", I18N);
    this.stock = Object.fromEntries(Object.entries(PRODUCTS).map(([k, p]) => [k, p.stock]));
    this.screens();
  }
  cart(s: Session): Record<string, number> { return (s.data.cart ??= {}); }
  totals(c: Record<string, number>) {
    const e = Object.entries(c);
    return { stars: e.reduce((a, [k, q]) => a + PRODUCTS[k].stars * q, 0), cents: e.reduce((a, [k, q]) => a + PRODUCTS[k].cents * q, 0),
      count: e.reduce((a, [, q]) => a + q, 0) };
  }
  bump(s: Session) { s.data.cart_rev = (s.data.cart_rev ?? 0) + 1; }
  orderForCart(s: Session): Order {
    const key = `${s.ownerId}:${s.data.cart_rev ?? 0}`;
    const known = this.byCart.get(key);
    if (known) return this.orders.get(known) as Order; // byCart only stores ids it inserted
    for (const o of this.orders.values()) if (o.user === s.ownerId && o.status === "pending") o.status = "superseded";
    const id = `SH-${this.next++}`, tot = this.totals(this.cart(s));
    const o: Order = { id, user: s.ownerId, chat: s.chatId, lang: s.lang, items: { ...this.cart(s) }, ...tot, status: "pending" };
    this.orders.set(id, o); this.byCart.set(key, id);
    return o;
  }
  private screens() {
    const fl = this.flow;
    fl.screen("catalog", (fl, s) => {
      const rows = Object.entries(PRODUCTS).map(([k, p]) => [this.stock[k] <= 0
        ? btn(`${p.title} · ⭐ ${p.stars}`, undefined, { disabled: true }) : btn(`${p.title} · ⭐ ${p.stars}`, fl.cb(s, "item", k))]);
      const qty = Object.values(this.cart(s)).reduce((a, b) => a + b, 0);
      return { text: fl.tr(s, "catalog"), reply_markup: kb(...rows, [btn(fl.tr(s, "btn_cart", { qty }), fl.cb(s, "cart"))]) };
    });
    fl.screen("item", (fl, s) => {
      const k = s.args.key as string, p = PRODUCTS[k], qty = this.cart(s)[k] ?? 0;
      const total = Object.values(this.cart(s)).reduce((a, b) => a + b, 0);
      const minus = qty ? btn("−", fl.cb(s, "qty", k, -1)) : btn("−", undefined, { disabled: true });
      const plus = qty < this.stock[k] ? btn("+", fl.cb(s, "qty", k, 1)) : btn("+", undefined, { disabled: true });
      const add = !qty ? btn(fl.tr(s, "btn_add"), fl.cb(s, "qty", k, 1), { style: "primary" })
        : btn(fl.tr(s, "btn_cart", { qty: total }), fl.cb(s, "cart"), { style: "primary" });
      return { text: fl.tr(s, "product", { title: p.title, stars: p.stars, eur: eur(p.cents), qty }),
        reply_markup: kb([minus, btn(String(qty), undefined, { disabled: true }), plus], [add], [btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]) };
    });
    fl.screen("cart", (fl, s) => {
      const items = this.cart(s);
      if (!Object.keys(items).length) return { text: fl.tr(s, "cart_empty"), reply_markup: kb([btn(fl.tr(s, "btn_catalog"), fl.cb(s, "home"))]) };
      const tot = this.totals(items);
      const lines = Object.entries(items).map(([k, q]) => `• ${PRODUCTS[k].title} × ${q}`).join("\n");
      return { text: fl.tr(s, "cart", { lines: new Raw(lines), stars: tot.stars, eur: eur(tot.cents) }),
        reply_markup: kb([btn(fl.tr(s, "btn_checkout"), fl.cb(s, "checkout"), { style: "primary" })],
          [btn(fl.tr(s, "btn_clear"), fl.cb(s, "clear"), { style: "danger" })], [btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]) };
    });
    fl.screen("pay", (fl, s) => {
      const o = this.orders.get(s.args.order as string) as Order; // set by the checkout action
      return { text: fl.tr(s, "pay", { order: o.id, stars: o.stars, eur: eur(o.cents) }), reply_markup: kb(
        [btn(fl.tr(s, "btn_stars", { stars: o.stars }), fl.cb(s, "inv", o.id, "xtr"), { style: "primary" })],
        [btn(fl.tr(s, "btn_card", { eur: eur(o.cents) }), fl.cb(s, "inv", o.id, "card"))], [btn(fl.tr(s, "btn_back"), fl.cb(s, "back"))]) };
    });
    fl.action("item", (fl, s, a) => { fl.go(s, "item", { key: a[0] }); });
    fl.action("qty", async (fl, s, a, cq) => {
      const k = a[0], d = Number(a[1]), items = this.cart(s), n = (items[k] ?? 0) + d;
      if (!(k in PRODUCTS) || n > this.stock[k]) { await fl.answer(cq, fl.tr(s, "sold_out"), true); return "sold_out"; }
      if (n <= 0) delete items[k]; else items[k] = n;
      this.bump(s);
      if (d > 0 && n === 1) await fl.answer(cq, fl.tr(s, "added"));
      await fl.refresh(s);
      return "cart_changed";
    });
    fl.action("cart", async (fl, s) => { await fl.go(s, "cart"); });
    fl.action("home", async (fl, s) => { await fl.open(s, "catalog"); });
    fl.action("back", async (fl, s) => { await fl.back(s); });
    fl.action("clear", async (fl, s) => { for (const k of Object.keys(this.cart(s))) delete this.cart(s)[k]; this.bump(s); await fl.refresh(s); });
    fl.action("checkout", async (fl, s) => { await fl.go(s, "pay", { order: this.orderForCart(s).id }); });
    fl.action("inv", async (fl, s, [oid, method], cq) => {
      const o = this.orders.get(oid);
      if (!o || o.user !== s.ownerId || o.status !== "pending") { await fl.answer(cq, fl.tr(s, "pc_changed"), true); return "order_gone"; }
      const [, first] = await this.invoices.run(`${oid}:${method}`, () => this.sendInvoice(o, method));
      if (!first) { await fl.answer(cq, fl.tr(s, "invoice_sent")); return "invoice_already_sent"; }
      return "invoice_sent";
    });
  }
  async sendInvoice(o: Order, method: string) {
    const base = { chat_id: o.chat, title: I18N.t(o.lang, "invoice_title", { order: o.id }),
      description: I18N.t(o.lang, "invoice_desc", { count: o.count }), payload: `o:${o.id}` };
    const params: Params = method === "xtr"
      ? { ...base, provider_token: "", currency: "XTR", prices: [{ label: base.title, amount: o.stars }] }
      : { ...base, provider_token: PROVIDER_TOKEN, currency: "EUR", need_name: true,
          prices: Object.entries(o.items).map(([k, q]) => ({ label: `${PRODUCTS[k].title} × ${q}`, amount: PRODUCTS[k].cents * q })) };
    o.method = method;
    return (await this.t.call("sendInvoice", params)).message_id;
  }
  async onPreCheckout(q: Params): Promise<boolean> {
    const o = this.orders.get(String(q.invoice_payload).replace(/^o:/, ""));
    let error: string | undefined;
    if (!o || o.status !== "pending" || o.user !== q.from.id) error = I18N.t("en", "pc_changed");
    else if (q.total_amount !== (q.currency === "XTR" ? o.stars : o.cents) || !["XTR", "EUR"].includes(q.currency)) error = I18N.t("en", "pc_changed");
    else { const short = Object.entries(o.items).find(([k, n]) => this.stock[k] < n); if (short) error = I18N.t("en", "pc_stock", { title: PRODUCTS[short[0]].title }); }
    await this.t.call("answerPreCheckoutQuery", { pre_checkout_query_id: q.id, ok: !error, ...(error ? { error_message: error } : {}) });
    return !error;
  }
  async onSuccessfulPayment(m: Params): Promise<string> {
    const sp = m.successful_payment;
    const [, first] = await this.payments.run(sp.telegram_payment_charge_id, async () => {
      const o = this.orders.get(String(sp.invoice_payload).replace(/^o:/, "")) as Order; // pre-checkout accepted it
      o.status = "paid"; o.charge = sp.telegram_payment_charge_id;
      for (const [k, n] of Object.entries(o.items)) this.stock[k] -= n;
      const s = this.flow.get(o.chat, o.user);
      if (s) { s.data.cart = {}; this.bump(s); }
      const rows = Object.entries(o.items).map(([k, q]) => [cell(PRODUCTS[k].title), cell(String(q), "right")]);
      rows.push([cell({ type: "bold", text: "Total" }), cell(o.method === "xtr" ? `⭐ ${o.stars}` : `€${eur(o.cents)}`, "right")]);
      await this.t.call("sendRichMessage", { chat_id: o.chat, rich_message: { blocks: [
        { type: "heading", size: 2, text: I18N.t(o.lang, "receipt_title", { order: o.id }) },
        { type: "table", cells: [[cell("Coffee", "left", true), cell("Qty", "right", true)], ...rows], is_bordered: true, is_compact: true },
        { type: "paragraph", text: I18N.t(o.lang, "receipt_note") }] } });
      return o.id;
    });
    return first ? "fulfilled" : "duplicate_payment";
  }
  async dispatch(u: Params): Promise<string> {
    if (!this.updates.firstTime(u)) return "duplicate_update";
    if (u.pre_checkout_query) return (await this.onPreCheckout(u.pre_checkout_query)) ? "pc_ok" : "pc_refused";
    if (u.callback_query) return this.flow.handle(u.callback_query);
    if (u.message.successful_payment) return this.onSuccessfulPayment(u.message);
    const s = this.flow.session(u.message.chat.id, u.message.from.id, I18N.langFor(u.message.from.language_code));
    await this.flow.open(s, "catalog", {}, true);
    return "catalog";
  }
}
const cell = (text: unknown, align = "left", header = false) => ({ text, align, valign: "middle", ...(header ? { is_header: true } : {}) });

export async function run() {
  const t = new FakeTransport(), shop = new Shop(t), fl = shop.flow;
  let n = 0;
  const tap = (who: Params, action: string, args: (string | number)[] = [], old = 0) => {
    const s = fl.get(who.id, who.id) as Session; // opened by /start before any tap
    n++;
    return shop.dispatch({ update_id: 1000 + n, callback_query: callback(`cq${n}`, who, pack("sh", b36(s.version - old), action, ...args), who.id, s.messageId) });
  };
  const out: string[] = [await shop.dispatch({ update_id: 1, message: textMessage(ALICE, "/start") })];
  out.push(await tap(ALICE, "qty", ["col", 1]), await tap(ALICE, "item", ["eth"]), await tap(ALICE, "qty", ["eth", 1]),
    await tap(ALICE, "qty", ["eth", 1], 1), await tap(ALICE, "qty", ["eth", 1]), await tap(ALICE, "cart"), await tap(ALICE, "checkout"));
  const oid = (fl.get(ALICE.id, ALICE.id) as Session).args.order as string;
  out.push(await tap(ALICE, "inv", [oid, "xtr"]), await tap(ALICE, "back"), await tap(ALICE, "checkout"), await tap(ALICE, "inv", [oid, "xtr"]));
  out.push(await shop.dispatch(fixture("usecase_pre_checkout_stars.json")));
  const pay = fixture("usecase_successful_payment_stars.json");
  out.push(await shop.dispatch(pay), await shop.dispatch(pay), await shop.dispatch({ ...pay, update_id: 920099 }));
  out.push(await shop.dispatch({ update_id: 2, message: textMessage(OLENA, "/start") }));
  out.push(await tap(OLENA, "item", ["ken"]), await tap(OLENA, "qty", ["ken", 1]), await tap(OLENA, "cart"), await tap(OLENA, "checkout"));
  const oid2 = (fl.get(OLENA.id, OLENA.id) as Session).args.order as string;
  shop.stock.ken = 0;
  out.push(await tap(OLENA, "inv", [oid2, "card"]));
  out.push(await shop.dispatch(fixture("usecase_pre_checkout_card.json")));
  const a = fl.get(ALICE.id, ALICE.id) as Session;
  out.push(await shop.dispatch({ update_id: 3, callback_query: callback("cqx", OLENA, pack("sh", b36(a.version), "clear"), ALICE.id, a.messageId) }));
  return { t, shop, out };
}
