// onboarding.ts - TypeScript twin of examples/python/recipes/r23_onboarding.py (recipe 23).
// Deep-link payload grammar, 3 skippable steps, own-contact check, referral once, returning users.
import { FakeTransport, type Params } from "../tgkit.ts";
import { ScreenFlow, I18n, OnceStore, UpdateDedup, btn, kb, pack, b36, user, callback, textMessage, type Session } from "./flows.ts";

export const ALICE = user(111111111, "Alice", "en"), BOGDAN = user(222222222, "Богдан", "uk");
const START_PARAM = /^[A-Za-z0-9_-]{1,64}$/; // API: deep-link parameter alphabet and length

const EN: Record<string, string> = {
  lang_pick: "<b>Hi, {name}!</b> Which language should I use?", notify: "<b>Step 2 of 3 · Updates</b>",
  phone: "<b>Step 3 of 3 · Phone (optional)</b>", phone_kb_hint: "Tap “Share my phone” or “Skip”",
  phone_thanks: "Saved. The courier will call {phone}.", phone_not_yours: "That's someone else's contact.",
  home_empty: "<b>All set, {name}</b>", home: "<b>Welcome back, {name}</b>\nOrder {order} is on its way.",
  item_teaser: "<b>{title}</b> from your link is waiting in the cart.", ref_ok: "{name} invited you.",
  remove_kb: "Okay, no phone.", desc: "Fresh coffee beans.", short_desc: "Coffee beans.",
  cmd_start: "Open the shop", cmd_orders: "My orders", cmd_settings: "Language and notifications",
  btn_notify_on: "Notify me", btn_not_now: "Not now", btn_share_phone: "Share my phone", btn_skip: "Skip",
  btn_catalog: "Open the catalog", btn_orders: "My orders", btn_settings: "Settings", sys_stale: "This step is already done.",
  sys_not_yours: "This menu belongs to someone else.", sys_expired: "This menu has expired. Send /start.",
};
// The full uk catalog lives in the Python recipe; only strings that reach the wire as plain
// keyboard rows (and so are part of the protocol) are repeated here.
const I18N = new I18n({ en: EN, uk: { ...EN, btn_skip: "Пропустити" } });
const LANG_NAMES: Record<string, string> = { en: "English", uk: "Українська" };
const ITEMS: Record<string, string> = { eth: "Ethiopia Yirgacheffe" };
const REF_CODES: Record<string, number> = { alice7: ALICE.id };
const NAMES: Record<number, string> = { [ALICE.id]: "Alice" };
type Profile = { lang: string; onboarded: boolean; notify: boolean | null; phone: string | null; orders: string[] };

export async function deploySetup(t: FakeTransport) {
  for (const lang of Object.keys(I18N.catalog)) {
    const code = lang === I18N.fallback ? {} : { language_code: lang };
    await t.call("setMyCommands", { commands: ["start", "orders", "settings"].map((c) => ({ command: c, description: I18N.t(lang, `cmd_${c}`) })), ...code });
    await t.call("setMyDescription", { description: I18N.t(lang, "desc"), ...code });
    await t.call("setMyShortDescription", { short_description: I18N.t(lang, "short_desc"), ...code });
  }
}

export class Onboarding {
  t: FakeTransport; flow: ScreenFlow; users = new Map<number, Profile>(); referrals = new OnceStore(); updates = new UpdateDedup();
  constructor(t: FakeTransport) {
    this.t = t; this.flow = new ScreenFlow(t, "ob", I18N);
    const fl = this.flow;
    fl.screen("lang", (fl, s) => ({ text: fl.tr(s, "lang_pick", { name: s.data.name }), reply_markup: kb(...Object.entries(LANG_NAMES).map(([code, name]) =>
      [btn((code === s.lang ? "✓ " : "") + name, fl.cb(s, "lang", code), code === s.lang ? { style: "primary" } : {})])) }));
    fl.screen("notify", (fl, s) => ({ text: fl.tr(s, "notify"), reply_markup: kb([btn(fl.tr(s, "btn_notify_on"), fl.cb(s, "notify", 1), { style: "primary" }),
      btn(fl.tr(s, "btn_not_now"), fl.cb(s, "notify", 0))]) }));
    fl.screen("home", (fl, s) => {
      const p = this.profile(s.ownerId);
      let text = p.orders.length ? fl.tr(s, "home", { name: s.data.name, order: p.orders.at(-1) }) : fl.tr(s, "home_empty", { name: s.data.name });
      if (s.data.teaser) text += "\n\n" + fl.tr(s, "item_teaser", { title: ITEMS[s.data.teaser] });
      if (s.data.ref_by) text += "\n\n" + fl.tr(s, "ref_ok", { name: s.data.ref_by });
      return { text, reply_markup: kb([btn(fl.tr(s, "btn_catalog"), fl.cb(s, "noop", "catalog"), { style: "primary" })],
        [btn(fl.tr(s, "btn_orders"), fl.cb(s, "noop", "orders")), btn(fl.tr(s, "btn_settings"), fl.cb(s, "noop", "settings"))]) };
    });
    fl.action("lang", async (fl, s, [code]) => {
      if (!(code in I18N.catalog)) return "bad_lang";
      s.lang = this.profile(s.ownerId).lang = code;
      await fl.go(s, "notify");
      return "lang_set";
    });
    fl.action("notify", async (fl, s, [v]) => { this.profile(s.ownerId).notify = v === "1"; await this.askPhone(s); return `notify_${v === "1" ? "on" : "off"}`; });
    fl.action("noop", (fl, s, [where]) => `home_${where}`);
  }
  profile(id: number): Profile { return this.users.get(id) as Profile; } // created by /start before any callback
  async askPhone(s: Session) {
    this.flow.owners.delete(`${s.chatId}:${s.messageId}`);
    s.data.step = "phone";
    await this.t.call("sendMessage", { chat_id: s.chatId, parse_mode: "HTML", text: this.flow.tr(s, "phone"), reply_markup: {
      keyboard: [[{ text: this.flow.tr(s, "btn_share_phone"), request_contact: true }], [{ text: this.flow.tr(s, "btn_skip") }]],
      one_time_keyboard: true, resize_keyboard: true, input_field_placeholder: this.flow.tr(s, "phone_kb_hint").slice(0, 64) } });
  }
  async finish(s: Session, note: string) {
    this.profile(s.ownerId).onboarded = true; delete s.data.step;
    await this.t.call("sendMessage", { chat_id: s.chatId, text: note, reply_markup: { remove_keyboard: true } });
    s.messageId = undefined;
    await this.flow.open(s, "home");
    delete s.data.teaser; delete s.data.ref_by;
  }
  async onStart(m: Params): Promise<string> {
    const from = m.from, parts = String(m.text).split(/\s+/);
    let param = parts.length > 1 ? parts.slice(1).join(" ") : "";
    const malformed = !!param && !START_PARAM.test(param);
    if (malformed) param = "";
    const isNew = !this.users.has(from.id);
    if (isNew) this.users.set(from.id, { lang: I18N.langFor(from.language_code), onboarded: false, notify: null, phone: null, orders: [] });
    const prof = this.profile(from.id), s = this.flow.session(from.id, from.id, prof.lang);
    s.data.name = from.first_name ?? "";
    let outcome = isNew ? "start_new" : "start_returning";
    if (param.startsWith("item_") && param.slice(5) in ITEMS) { s.data.teaser = param.slice(5); outcome += "+item"; }
    else if (param.startsWith("ref_")) outcome += "+" + (await this.creditReferral(from.id, param.slice(4), isNew, s));
    else if (param) outcome += "+unknown_param";
    else if (malformed) outcome += "+malformed_param";
    await this.flow.open(s, prof.onboarded ? "home" : "lang", {}, true);
    return outcome;
  }
  async creditReferral(uid: number, code: string, isNew: boolean, s: Session): Promise<string> {
    const inviter = REF_CODES[code];
    if (inviter === undefined) return "ref_unknown";
    if (inviter === uid) return "ref_self";
    if (!isNew) return "ref_existing_user";
    const [, first] = await this.referrals.run(`ref:${uid}`, () => inviter);
    if (first) s.data.ref_by = NAMES[inviter] ?? "";
    return first ? "ref_credited" : "ref_duplicate";
  }
  async onMessage(m: Params): Promise<string> {
    const uid = m.from.id, s = this.flow.get(m.chat.id, uid);
    if (String(m.text ?? "").startsWith("/start")) return this.onStart(m);
    if (!s || s.data.step !== "phone") return "ignored";
    if (m.contact) {
      if (m.contact.user_id !== uid) { await this.t.call("sendMessage", { chat_id: s.chatId, text: this.flow.tr(s, "phone_not_yours") }); return "contact_not_own"; }
      this.profile(uid).phone = m.contact.phone_number;
      await this.finish(s, I18N.t(s.lang, "phone_thanks", { phone: m.contact.phone_number }));
      return "phone_saved";
    }
    if (m.text === this.flow.tr(s, "btn_skip")) { await this.finish(s, I18N.t(s.lang, "remove_kb")); return "phone_skipped"; }
    return "ignored";
  }
  async dispatch(u: Params): Promise<string> {
    if (!this.updates.firstTime(u)) return "duplicate_update";
    return u.callback_query ? this.flow.handle(u.callback_query) : this.onMessage(u.message);
  }
}

const contact = (from: Params, phone: string, name: string, userId: number) =>
  ({ message_id: 1, date: 0, from, chat: { id: from.id, type: "private" }, contact: { phone_number: phone, first_name: name, user_id: userId } });

export async function run() {
  const t = new FakeTransport();
  await deploySetup(t);
  const ob = new Onboarding(t), fl = ob.flow;
  let n = 0;
  const upd = (u: Params) => ({ update_id: 5000 + ++n, ...u });
  const sess = (who: Params) => fl.get(who.id, who.id) as Session; // /start ran first
  const tap = (who: Params, action: string, ...args: (string | number)[]) => {
    const s = sess(who), qid = `q${n}`;
    return ob.dispatch(upd({ callback_query: callback(qid, who, pack("ob", b36(s.version), action, ...args), who.id, s.messageId) }));
  };
  const out: string[] = [];
  const start = upd({ message: textMessage(BOGDAN, "/start ref_alice7") });
  out.push(await ob.dispatch(start), await ob.dispatch(start), await tap(BOGDAN, "lang", "uk"));
  const staleLang = pack("ob", b36(sess(BOGDAN).version - 1), "lang", "en");
  out.push(await tap(BOGDAN, "notify", 1));
  out.push(await ob.dispatch(upd({ message: contact(BOGDAN, "+380441112233", "Мама", 999999999) })));
  out.push(await ob.dispatch(upd({ message: contact(BOGDAN, "+380501234567", "Богдан", BOGDAN.id) })));
  out.push(await ob.dispatch(upd({ callback_query: callback("qs", BOGDAN, staleLang, BOGDAN.id, sess(BOGDAN).messageId) })));
  out.push(await ob.dispatch(upd({ message: textMessage(BOGDAN, "/start ref_alice7") })));
  out.push(await ob.dispatch(upd({ message: textMessage(ALICE, "/start item_eth") })));
  out.push(await tap(ALICE, "lang", "en"), await tap(ALICE, "notify", 0));
  out.push(await ob.dispatch(upd({ message: textMessage(ALICE, "Skip") })));
  out.push(await ob.dispatch(upd({ message: textMessage(ALICE, "/start ref_alice7") })));
  out.push(await ob.dispatch(upd({ message: textMessage(ALICE, "/start <script>alert(1)</script>") })));
  ob.profile(ALICE.id).orders.push("SH-1001");
  out.push(await ob.dispatch(upd({ message: textMessage(ALICE, "/start") })));
  return { t, ob, out };
}
