// inline.ts - TypeScript twin of examples/python/recipes/r60_inline_mode.py (recipe 60).
// Articles always carry a keyboard (so chosen_inline_result has inline_message_id), paging by
// next_offset, "nothing found" = no fake cards + a button, votes keyed by inline_message_id.
import { readFileSync } from "node:fs";
import { FakeTransport, TelegramError, type Params } from "../tgkit.ts";
import { I18n, Raw, UpdateDedup, btn, kb, pack, user } from "./flows.ts";

const fixture = (name: string) => JSON.parse(readFileSync(new URL(`../../fixtures/${name}`, import.meta.url), "utf8"));
const APP = "pl", BOT = "placecards_bot", PAGE = 3;
export const ALICE = user(111111111, "Alice", "en"), BOGDAN = user(222222222, "Богдан", "uk"), EVE = user(333333333, "Eve <script>", "en");
const EN: Record<string, string> = {
  card: "<b>{title}</b>\n{area} · {note}\n\n{going}", desc: "{area} · {note}", going_none: "Who is in? Tap the button.",
  going_some: "Going ({n}): {names}", toast_in: "You are in ✓", toast_out: "Removed: you are not going",
  btn_in: "👍 I'm in", btn_in_n: "👍 I'm in · {n} going", btn_open: "Open in the bot", btn_more: "Open the bot for more",
  btn_none: "Nothing found: open the bot", sys_stale: "This card is out of date.", sys_expired: "This card is no longer tracked.",
};
const I18N = new I18n({ en: EN, uk: EN }); // full uk copy: Python recipe
const PLACES: Record<string, { pop: number; tags: string; title: string; area: string; note: string }> = {
  kaffa: { pop: 1, tags: "coffee кава", title: "Kaffa Roasters", area: "Podil", note: "Filter coffee, oat milk" },
  pie: { pop: 2, tags: "bakery випічка", title: "Pie Lab", area: "Podil", note: "Apple pie" },
  tea: { pop: 3, tags: "tea чай", title: "Tea Room", area: "Lukianivka", note: "Oolong, quiet tables" },
  jam: { pop: 4, tags: "coffee кава", title: "Jam Espresso", area: "Centre", note: "Espresso bar, open late" },
  bean: { pop: 5, tags: "coffee кава", title: "Bean There", area: "Pechersk", note: "Pour-over flights" },
  mono: { pop: 6, tags: "coffee кава bakery", title: "Mono Cup", area: "Obolon", note: "Cardamom bun" },
  nut: { pop: 7, tags: "bakery випічка", title: "Nut Oven", area: "Centre", note: "Rye bread" },
};
// The Python haystack also contains the Ukrainian titles; the twin searches tags + English titles,
// which is enough for the fixture queries ("coffee", "кава", nothing-found).
const RANKED = Object.keys(PLACES).sort((a, b) => PLACES[a].pop - PLACES[b].pop);
const haystack = (k: string) => `${PLACES[k].title} ${PLACES[k].tags}`.toLowerCase();
type Tracked = { item: string; lang: string; voters: Map<number, string> };

export class PlaceBot {
  t: FakeTransport; msgs = new Map<string, Tracked>(); updates = new UpdateDedup();
  constructor(t: FakeTransport) { this.t = t; }
  keyboard(lang: string, key: string, n: number) {
    return kb([btn(n ? I18N.t(lang, "btn_in_n", { n }) : I18N.t(lang, "btn_in"), pack(APP, "vote", key), { style: "primary" })],
      [btn(I18N.t(lang, "btn_open"), undefined, { url: `https://t.me/${BOT}?start=place_${key}` })]);
  }
  card(lang: string, key: string, voters: Map<number, string>) {
    const p = PLACES[key], esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const going = voters.size ? I18N.t(lang, "going_some", { n: voters.size, names: new Raw([...voters.values()].map(esc).join(", ")) })
      : I18N.t(lang, "going_none");
    return I18N.t(lang, "card", { title: p.title, area: p.area, note: p.note, going: new Raw(going) });
  }
  article(lang: string, key: string) {
    const p = PLACES[key];
    return { type: "article", id: key, title: p.title, description: I18N.t(lang, "desc", { area: p.area, note: p.note }),
      input_message_content: { message_text: this.card(lang, key, new Map()), parse_mode: "HTML" }, reply_markup: this.keyboard(lang, key, 0) };
  }
  async onInlineQuery(iq: Params): Promise<string> {
    const lang = I18N.langFor(iq.from.language_code), q = String(iq.query).trim().toLowerCase();
    const offset = /^\d+$/.test(iq.offset) ? Number(iq.offset) : 0;
    const params: Params = { inline_query_id: iq.id, is_personal: true, cache_time: 60 };
    let page: string[], nextOffset = "", state: string;
    if (!q) {
      page = RANKED.slice(0, PAGE); state = "popular";
      params.button = { text: I18N.t(lang, "btn_more"), start_parameter: "search" };
    } else {
      const hits = RANKED.filter((k) => haystack(k).includes(q));
      page = hits.slice(offset, offset + PAGE);
      nextOffset = offset + PAGE < hits.length ? String(offset + PAGE) : ""; state = "results";
      if (!hits.length) { state = "none"; params.button = { text: I18N.t(lang, "btn_none"), start_parameter: "search" }; }
    }
    params.results = page.map((k) => this.article(lang, k));
    params.next_offset = nextOffset;
    await this.t.call("answerInlineQuery", params);
    return state;
  }
  onChosen(cr: Params): string {
    const imid = cr.inline_message_id;
    if (!(cr.result_id in PLACES) || !imid) return "ignored";
    if (this.msgs.has(imid)) return "duplicate";
    this.msgs.set(imid, { item: cr.result_id, lang: I18N.langFor(cr.from.language_code), voters: new Map() });
    return "tracked";
  }
  async onCallback(cq: Params): Promise<string> {
    const parts = String(cq.data ?? "").split(":");
    if (parts[0] !== APP || parts.length !== 3) return "foreign";
    const lang = I18N.langFor(cq.from.language_code), m = this.msgs.get(cq.inline_message_id);
    if (!m) { await this.t.call("answerCallbackQuery", { callback_query_id: cq.id, text: I18N.t(lang, "sys_expired") }); return "expired"; }
    if (parts[1] !== "vote" || parts[2] !== m.item || !(parts[2] in PLACES)) {
      await this.t.call("answerCallbackQuery", { callback_query_id: cq.id, text: I18N.t(lang, "sys_stale") }); return "stale";
    }
    const joined = !m.voters.has(cq.from.id);
    if (joined) m.voters.set(cq.from.id, cq.from.first_name); else m.voters.delete(cq.from.id);
    try {
      await this.t.call("editMessageText", { inline_message_id: cq.inline_message_id, text: this.card(m.lang, m.item, m.voters),
        parse_mode: "HTML", reply_markup: this.keyboard(m.lang, m.item, m.voters.size) });
    } catch (e) { if (!(e instanceof TelegramError && e.category === "not_modified")) throw e; }
    await this.t.call("answerCallbackQuery", { callback_query_id: cq.id, text: I18N.t(lang, joined ? "toast_in" : "toast_out") });
    return joined ? "joined" : "left";
  }
  async dispatch(u: Params): Promise<string> {
    if (!this.updates.firstTime(u)) return "duplicate_update";
    if (u.inline_query) return this.onInlineQuery(u.inline_query);
    if (u.chosen_inline_result) return this.onChosen(u.chosen_inline_result);
    return this.onCallback(u.callback_query);
  }
}

const inlineCallback = (id: string, from: Params, data: string, imid: string) => ({ id, from, chat_instance: "-1", data, inline_message_id: imid });

export async function run() {
  const t = new FakeTransport(), bot = new PlaceBot(t);
  const chosen = fixture("usecase_chosen_inline_result.json"), imid = chosen.chosen_inline_result.inline_message_id as string;
  let n = 100;
  const tap = (who: Params, data = pack(APP, "vote", "kaffa"), at = imid) => { n++; return bot.dispatch({ update_id: 961000 + n, callback_query: inlineCallback(`cq${n}`, who, data, at) }); };
  const out: string[] = [];
  for (const f of ["empty", "text", "page2", "none"]) out.push(await bot.dispatch(fixture(`usecase_inline_query_${f}.json`)));
  out.push(await bot.dispatch(chosen), await bot.dispatch({ ...chosen, update_id: 960055 }));
  out.push(await bot.dispatch({ update_id: 960006, chosen_inline_result: { ...chosen.chosen_inline_result, result_id: "removed", inline_message_id: "AQAAOTHER" } }));
  out.push(await tap(ALICE), await tap(BOGDAN), await tap(EVE), await tap(ALICE), await tap(BOGDAN, undefined, "AQAAUNKNOWN"),
    await tap(ALICE, pack(APP, "vote", "closed")));
  const again = { update_id: 961777, callback_query: inlineCallback("cqdup", BOGDAN, pack(APP, "vote", "kaffa"), imid) };
  out.push(await bot.dispatch(again), await bot.dispatch(again));
  return { t, bot, out };
}
