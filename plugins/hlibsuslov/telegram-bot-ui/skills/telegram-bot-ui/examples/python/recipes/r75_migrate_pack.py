"""R75 - Migrate from one pack to another without touching handlers.

Handlers ask for SLOTS (`icons.button("Cart", "cart")`), never for ids, so a migration is
data only: resolve the new family for the slots in use, check coverage, verify the ids
with getCustomEmojiStickers, audit the new map (one family, static), then swap the map. A
slot the new pack does not cover blocks the switch (or goes label-only on purpose) - it
never borrows an icon from the old family.

Run:  py -3 examples/python/recipes/r75_migrate_pack.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, audit_map, resolve, sticker_lookup
from tgkit.icons import Eligibility, IconSystem, SendContext, verify_ids
from tgkit.transport import FakeTransport

CHAT = 111111111
SLOTS = ["home", "cart", "search", "settings", "done", "back"]


def shop_menu(icons: IconSystem) -> dict:               # the handler: unchanged across packs
    return {"chat_id": CHAT, "parse_mode": "HTML", "text": icons.title("home", "Shop"),
            "reply_markup": {"inline_keyboard": [
                [icons.button("Cart", "cart", style="primary", callback_data="cart"),
                 icons.button("Search", "search", callback_data="search")],
                [icons.button("Settings", "settings", callback_data="settings")],
                [icons.button("Back", "back", callback_data="back")]]}}


def run():
    t = FakeTransport().script("getCustomEmojiStickers", sticker_lookup(["demo_solid_icons"]))
    old_map, _ = resolve(["demo_line_icons"], SLOTS, family="demo-line")
    new_map, report = resolve(["demo_solid_icons"], SLOTS, family="demo-solid")
    eligibility = Eligibility(owner_premium=True)
    icons = IconSystem(old_map["icons"], vocabulary=VOCAB, eligibility=eligibility)
    icons.send(t, "sendMessage", shop_menu(icons), SendContext("private"))
    found, missing = verify_ids(t, [i["id"] for i in new_map["icons"].values()])
    errors, warnings = audit_map(new_map, allow_fixture_ids=True)
    switched = report["coverage"] == 1.0 and not missing and not errors and not warnings
    if switched:
        icons = IconSystem(new_map["icons"], vocabulary=VOCAB, eligibility=eligibility)
    icons.send(t, "sendMessage", shop_menu(icons), SendContext("private"))
    return t, old_map, new_map, report, switched


def _shape(params: dict) -> list:
    return [[{k: v for k, v in b.items() if k != "icon_custom_emoji_id"} for b in row]
            for row in params["reply_markup"]["inline_keyboard"]]


def main() -> None:
    t, old_map, new_map, report, switched = run()
    c.dump(t, "Migrate to another pack")
    before, after = t.params_of("sendMessage")
    c.check(switched and report["coverage"] == 1.0, "new family covers every slot in use, verified and audited")
    c.check(_shape(before) == _shape(after), "same handler output: labels, actions and styles unchanged")
    ids_after = {b["icon_custom_emoji_id"] for row in after["reply_markup"]["inline_keyboard"] for b in row}
    c.check(ids_after == {new_map["icons"][s]["id"] for s in ("cart", "search", "settings", "back")}
            and not ids_after & {i["id"] for i in old_map["icons"].values()}, "only the ids changed - none left from the old pack")
    _, partial = resolve(["demo_solid_icons"], SLOTS + ["gift"], family="demo-solid")
    c.check(partial["uncovered"] == ["gift"], "a slot the new pack lacks is reported before the switch, not filled from the old family")


if __name__ == "__main__":
    main()
