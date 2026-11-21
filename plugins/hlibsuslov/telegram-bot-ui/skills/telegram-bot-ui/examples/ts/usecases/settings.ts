// settings.ts - TypeScript twin of examples/python/recipes/r24_settings.py (recipe 24).
// One message + back stack, state-shaped toggles, confirm + undo window, group redirect.
import { FakeTransport, type Params } from "../tgkit.ts";
import { ScreenFlow, I18n, OnceStore, Scheduler, btn, kb, pack, b36, user, callback, textMessage, type Session } from "./flows.ts";

export const ALICE = user(111111111, "Alice", "en"), BOGDAN = user(222222222, "Богдан", "ru");
const BOT = "coffee_demo_bot", GROUP = -1001234567890, UNDO_SECONDS = 30;
const EN: Record<string, string> = {
  root: "<b>Settings</b>\nLanguage: {lang} · Notifications: {notif}", notif: "<b>Notifications</b>",
  quiet: "<b>Quiet hours</b> from {start}:00", lang: "<b>Language</b>", privacy: "<b>Privacy</b>: {shown}",
  confirm_delete: "<b>Delete all your data?</b>", deleting: "<b>Deleting in {sec} s</b>", deleted: "<b>Your data was deleted.</b>",
  undone: "Deletion cancelled.", too_late: "Too late — the data is already deleted.", group_hint: "Settings open in our private chat.",
  shown: "yes", hidden: "no", btn_lang: "Language: {lang}", btn_notif: "Notifications", btn_privacy: "Privacy",
  btn_delete: "Delete my data", btn_delete_yes: "Delete everything", btn_cancel: "Cancel", btn_undo: "Undo", btn_back: "← Back",
  btn_toggle: "{mark} {label}", btn_quiet: "Quiet hours: from {start}:00", btn_open_private: "Open settings", btn_start_again: "Start again",
  t_shipping: "Shipping updates", t_promos: "Offers and news", t_digest: "Weekly digest",
  sys_stale: "This screen has changed.", sys_not_yours: "These are someone else's settings.", sys_expired: "This menu has expired.",
};
const I18N = new I18n({ en: EN, ru: EN }); // full ru copy: Python recipe
const LANG_NAMES: Record<string, string> = { en: "English", ru: "Русский" };
const TOGGLES = ["shipping", "promos", "digest"] as const;
const DEFAULTS: Params = { shipping: true, promos: false, digest: true, quiet: 22, public: false };

export class Settings {
  t: FakeTransport; flow: ScreenFlow; jobs = new Scheduler(); deletions = new OnceStore(); deleted = new Set<number>(); now = 0;
  constructor(t: FakeTransport) {
    this.t = t; this.flow = new ScreenFlow(t, "st", I18N);
    const fl = this.flow, back = (s: Session) => btn(fl.tr(s, "btn_back"), fl.cb(s, "back"));
    const prefs = (s: Session): Params => (s.data.prefs ??= { ...DEFAULTS });
    fl.screen("root", (fl, s) => ({ text: fl.tr(s, "root", { lang: LANG_NAMES[s.lang], notif: `${TOGGLES.filter((k) => prefs(s)[k]).length}/${TOGGLES.length}` }),
      reply_markup: kb([btn(fl.tr(s, "btn_lang", { lang: LANG_NAMES[s.lang] }), fl.cb(s, "go", "lang"))],
        [btn(fl.tr(s, "btn_notif"), fl.cb(s, "go", "notif")), btn(fl.tr(s, "btn_privacy"), fl.cb(s, "go", "privacy"))],
        [btn(fl.tr(s, "btn_delete"), fl.cb(s, "go", "confirm_delete"), { style: "danger" })]) }));
    fl.screen("notif", (fl, s) => ({ text: fl.tr(s, "notif"), reply_markup: kb(
      ...TOGGLES.map((k) => [btn(fl.tr(s, "btn_toggle", { mark: prefs(s)[k] ? "✓" : "✗", label: fl.tr(s, `t_${k}`) }), fl.cb(s, "tog", k))]),
      [btn(fl.tr(s, "btn_quiet", { start: prefs(s).quiet }), fl.cb(s, "go", "quiet"))], [back(s)]) }));
    fl.screen("quiet", (fl, s) => ({ text: fl.tr(s, "quiet", { start: prefs(s).quiet }), reply_markup: kb(
      [20, 21, 22, 23].map((h) => h === prefs(s).quiet ? btn(`${h}:00`, undefined, { disabled: true }) : btn(`${h}:00`, fl.cb(s, "quiet", h))), [back(s)]) }));
    fl.screen("lang", (fl, s) => ({ text: fl.tr(s, "lang"), reply_markup: kb(
      ...Object.entries(LANG_NAMES).map(([c, name]) => [btn((c === s.lang ? "✓ " : "") + name, fl.cb(s, "lang", c))]), [back(s)]) }));
    fl.screen("privacy", (fl, s) => ({ text: fl.tr(s, "privacy", { shown: fl.tr(s, prefs(s).public ? "shown" : "hidden") }), reply_markup: kb(
      [btn(fl.tr(s, "btn_toggle", { mark: prefs(s).public ? "✓" : "✗", label: fl.tr(s, "btn_privacy") }), fl.cb(s, "tog", "public"))], [back(s)]) }));
    fl.screen("confirm_delete", (fl, s) => ({ text: fl.tr(s, "confirm_delete"), reply_markup: kb(
      [btn(fl.tr(s, "btn_cancel"), fl.cb(s, "back"))], [btn(fl.tr(s, "btn_delete_yes"), fl.cb(s, "delete"), { style: "danger" })]) }));
    fl.screen("deleting", (fl, s) => ({ text: fl.tr(s, "deleting", { sec: UNDO_SECONDS }), reply_markup: kb([btn(fl.tr(s, "btn_undo"), fl.cb(s, "undo"), { style: "primary" })]) }));
    fl.screen("deleted", (fl, s) => ({ text: fl.tr(s, "deleted"), reply_markup: kb([btn(fl.tr(s, "btn_start_again"), undefined, { url: `https://t.me/${BOT}?start=new` })]) }));
    fl.action("go", async (fl, s, [screen]) => { await fl.go(s, screen); });
    fl.action("back", async (fl, s) => { await fl.back(s); });
    fl.action("tog", async (fl, s, [k]) => {
      if (typeof DEFAULTS[k] !== "boolean") return "bad_toggle";
      prefs(s)[k] = !prefs(s)[k]; await fl.refresh(s);
      return `${k}=${prefs(s)[k] ? "on" : "off"}`;
    });
    fl.action("quiet", async (fl, s, [h]) => { prefs(s).quiet = Number(h); await fl.back(s); return "quiet_set"; });
    fl.action("lang", async (fl, s, [c]) => { if (c in I18N.catalog) s.lang = c; await fl.back(s); return `lang_${s.lang}`; });
    fl.action("delete", async (fl, s) => {
      const [, first] = await this.deletions.run(`del:${s.ownerId}:${s.data.del_round ?? 0}`, () => {
        this.jobs.at(this.now + UNDO_SECONDS, `del:${s.ownerId}`, { user: s.ownerId }); return true; });
      await fl.open(s, "deleting");
      return first ? "deletion_scheduled" : "deletion_already_scheduled";
    });
    fl.action("undo", async (fl, s, _a, cq) => {
      if (this.deleted.has(s.ownerId)) { await fl.answer(cq, fl.tr(s, "too_late"), true); return "too_late"; }
      this.jobs.cancel(`del:${s.ownerId}`); s.data.del_round = (s.data.del_round ?? 0) + 1;
      await fl.answer(cq, fl.tr(s, "undone")); await fl.open(s, "root");
      return "undone";
    });
  }
  async tick(now: number): Promise<string[]> {
    this.now = now;
    const done: string[] = [];
    for (const job of this.jobs.due(now)) {
      const uid = job.payload.user as number, s = this.flow.get(uid, uid) as Session; // jobs exist only for open sessions
      this.deleted.add(uid); s.data = {};
      await this.flow.open(s, "deleted");
      done.push(`deleted:${uid}`);
    }
    return done;
  }
  async onCommand(m: Params): Promise<string> {
    const lang = I18N.langFor(m.from.language_code);
    if (m.chat.type !== "private") {
      await this.t.call("sendMessage", { chat_id: m.chat.id, text: I18N.t(lang, "group_hint"), reply_parameters: { message_id: m.message_id },
        reply_markup: kb([btn(I18N.t(lang, "btn_open_private"), undefined, { url: `https://t.me/${BOT}?start=settings` })]) });
      return "group_redirect";
    }
    await this.flow.open(this.flow.session(m.chat.id, m.from.id, lang), "root", {}, true);
    return "root";
  }
}

export async function run() {
  const t = new FakeTransport(), st = new Settings(t), fl = st.flow;
  let n = 0;
  const sess = () => fl.get(BOGDAN.id, BOGDAN.id) as Session; // opened by /settings first
  const tap = (action: string, args: (string | number)[] = [], old = 0) =>
    fl.handle(callback(`q${++n}`, BOGDAN, pack("st", b36(sess().version - old), action, ...args), BOGDAN.id, sess().messageId));
  const out: string[] = [await st.onCommand(textMessage(BOGDAN, "/settings", { chatId: GROUP, chatType: "supergroup", messageId: 9 }))];
  out.push(await st.onCommand(textMessage(BOGDAN, "/settings")));
  out.push(await tap("go", ["notif"]), await tap("tog", ["promos"]), await tap("tog", ["promos"], 1), await tap("go", ["quiet"]),
    await tap("quiet", [23]), await tap("back"), await tap("go", ["lang"]), await tap("lang", ["en"]), await tap("go", ["confirm_delete"]),
    await tap("back"), await tap("go", ["confirm_delete"]), await tap("delete"), await tap("undo"), await tap("go", ["confirm_delete"]), await tap("delete"));
  const undo = pack("st", b36(sess().version), "undo");
  out.push(...(await st.tick(UNDO_SECONDS + 1)));
  out.push(await fl.handle(callback("q-late", BOGDAN, undo, BOGDAN.id, sess().messageId)));
  out.push(await fl.handle(callback("q-alice", ALICE, pack("st", b36(sess().version), "tog", "promos"), BOGDAN.id, sess().messageId)));
  return { t, st, out };
}
