#!/usr/bin/env python3
"""Layout rules for Mini App screens: recommend a layout for a content type, review a screen description.

  py -3 scripts/miniapp_layout.py entities                 # content types: book, trainer, workout, product, plan...
  py -3 scripts/miniapp_layout.py show book                # recommended card, list variant, detail order, markup skeleton
  py -3 scripts/miniapp_layout.py rules                    # L01-L25
  py -3 scripts/miniapp_layout.py review screen.json       # findings with rule ids and fixes (--json)
  py -3 scripts/miniapp_layout.py schema                   # every key and value a screen description may use
  py -3 scripts/miniapp_layout.py example catalog          # a screen description to start from

A screen description is a small JSON an agent writes from a design, a screenshot or code before changing it:

  {"screen": "catalog", "entity": "book", "width": 390,
   "layout": {"variant": "tile", "columns": 2},
   "card": {"image": {"ratio": "1:1", "fit": "cover", "position": "top"},
            "slots": ["image", "price", "title", "author"], "title_lines": 3, "tags": 2,
            "actions": ["favourite", "add"], "rating": "stars", "price": {"style": "pill"}, "text_on_image": false},
   "primary_action": "in-card", "carousels": 1, "filters": {"count": 7, "placement": "top"}, "search": "top",
   "unavailable": "hidden"}

Screens: catalog, detail, booking, form, plans, dashboard, gallery. Every key is optional; only what is described
is checked, so describe every list and detail screen fully. Unknown keys and values are errors (exit 2): a typo
must not pass as "0 findings". The rules are this skill's heuristics (data/mini-apps/layouts.json, references/mini-apps/layout-rules.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SKILL, "data", "mini-apps", "layouts.json")
TEXT_SLOTS_ORDER = ["title", "name", "author", "meta", "specialty", "date", "venue", "rating", "price"]
EXAMPLES = {
    "catalog": {"screen": "catalog", "entity": "book", "width": 390, "layout": {"variant": "tile", "columns": 2},
                "card": {"image": {"ratio": "2:3", "fit": "contain", "position": "top"},
                         "slots": ["image", "title", "author", "price", "format"], "title_lines": 2, "tags": 1,
                         "actions": [], "rating": "short", "price": {"style": "plain"}, "text_on_image": False},
                "primary_action": "main-button", "carousels": 1, "filters": {"count": 4, "placement": "top"},
                "search": "top", "unavailable": "dimmed"},
    "booking": {"screen": "booking", "entity": "trainer", "primary_action": "main-button",
                "booking": {"days": "strip", "slots_columns": 4, "unavailable": "disabled", "summary": True,
                            "main_button_names_slot": True}},
    "detail": {"screen": "detail", "entity": "product", "primary_action": "main-button",
               "sections": ["gallery", "title", "price", "variant selectors", "availability", "description", "details",
                            "reviews", "related"], "gallery": "carousel", "carousels": 1},
    "plans": {"screen": "plans", "entity": "plan", "width": 390, "primary_action": "main-button",
              "plans": {"layout": "stacked", "count": 3, "features_max": 5, "recommended": 1}},
}


# The screen description: key -> allowed values (a tuple), a type, or a nested schema (dict).
SCHEMA: dict = {
    "screen": ("catalog", "detail", "booking", "form", "plans", "dashboard", "gallery"),
    "entity": str, "width": int, "max_width": int,
    "layout": {"variant": ("row", "tile", "media-card", "scroller-card", "plan-card"), "columns": int},
    "card": {
        "image": {"ratio": str, "fit": ("cover", "contain"), "position": ("top", "start", "end", "both", "none")},
        "slots": list, "title_lines": int, "description_lines": int, "tags": int, "ribbon": bool,
        "actions": list, "rating": ("none", "short", "stars", "five-stars"),
        "price": {"style": ("plain", "pill", "badge", "accent"), "on_image": bool, "figures": ("tabular", "proportional")},
        "text_on_image": bool, "alt": str,
    },
    "primary_action": ("main-button", "none", "in-card", "fixed-button", "several"),
    "carousels": int, "main_list": ("list", "grid", "carousel"),
    "filters": {"count": int, "placement": ("top", "sheet", "side"), "result_count": bool},
    "search": ("top", "bottom", "hidden", "none"),
    "unavailable": ("dimmed", "disabled", "hidden", "colour-only", "color-only", "labelled"),
    "sections": list, "gallery": ("carousel", "grid", "viewer", "masonry", "autoplay"),
    "form": {"columns": int, "labels": ("above", "floating", "placeholder", "none")},
    "booking": {"days": ("strip", "calendar", "dropdown", "list"), "slots_columns": int,
                "unavailable": ("disabled", "hidden", "dimmed"), "summary": bool, "main_button_names_slot": bool},
    "plans": {"layout": ("stacked", "side-by-side", "table"), "count": int, "features_max": int,
              "recommended": int, "table": bool},
    "states": {"skeleton": ("card-shaped", "spinner", "none"), "empty": bool, "error": bool},
}


def validate(spec, schema: dict = SCHEMA, at: str = "") -> list[str]:
    """Schema errors: unknown keys, values outside the allowed set, wrong types."""
    errors = []
    if not isinstance(spec, dict):
        return [f"{at or 'the description'} must be an object"]
    for key, value in spec.items():
        path = f"{at}.{key}" if at else key
        if key.startswith("$") or key == "notes":
            continue
        if key not in schema:
            errors.append(f"unknown key {path!r}; allowed here: {', '.join(sorted(schema))}")
            continue
        rule = schema[key]
        if isinstance(rule, dict):
            errors += validate(value, rule, path)
        elif isinstance(rule, tuple):
            if value not in rule:
                errors.append(f"{path} = {value!r}; allowed: {', '.join(rule)}")
        elif rule is int and (not isinstance(value, int) or isinstance(value, bool)):
            errors.append(f"{path} must be a whole number, got {value!r}")
        elif rule is not int and not isinstance(value, rule):
            errors.append(f"{path} must be {rule.__name__}, got {type(value).__name__}")
    return errors


def schema_text(schema: dict = SCHEMA, indent: str = "") -> str:
    lines = []
    for key, rule in schema.items():
        if isinstance(rule, dict):
            lines.append(f"{indent}{key}:")
            lines.append(schema_text(rule, indent + "  "))
        elif isinstance(rule, tuple):
            lines.append(f"{indent}{key}: {' | '.join(rule)}")
        else:
            lines.append(f"{indent}{key}: {rule.__name__}")
    return "\n".join(lines)


def load() -> dict:
    with open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


def ratio_of(text: str | None) -> str | None:
    m = re.search(r"(\d+)\s*[:x×/]\s*(\d+)", text or "")
    return f"{m.group(1)}:{m.group(2)}" if m else None


def finding(data: dict, rule: str, message: str) -> dict:
    r = data["rules"][rule]
    return {"rule": rule, "severity": r["severity"], "title": r["title"], "message": message, "fix": r["fix"]}


def review(spec: dict, data: dict) -> list[dict]:
    out: list[dict] = []
    add = lambda rule, msg: out.append(finding(data, rule, msg))  # noqa: E731
    ent = data["entities"].get(spec.get("entity", ""))
    if spec.get("entity") and not ent:
        add("L02", f"unknown entity {spec['entity']!r}; known: {', '.join(data['entities'])}")
    screen = spec.get("screen", "catalog")
    card = spec.get("card", {})
    image = card.get("image", {})

    # L01 primary action
    pa = spec.get("primary_action")
    if pa in ("in-card", "fixed-button", "several") and screen in ("detail", "booking", "form", "plans"):
        add("L01", f"primary action is {pa!r} on a {screen} screen")
    if pa == "fixed-button":
        add("L01", "an own fixed bottom button duplicates Telegram's bottom bar")
    if screen == "catalog" and pa == "in-card" and card.get("actions") and len(card["actions"]) > 1:
        add("L19", f"{len(card['actions'])} actions on every card ({', '.join(card['actions'])})")

    # L02-L04 image
    if ent and image.get("ratio"):
        want = ratio_of(ent["ratio"])
        if want and ratio_of(image["ratio"]) != want and spec.get("layout", {}).get("variant", ent["list_variant"]) != "row":
            add("L02", f"{ent['title']} images are {want}, the card uses {image['ratio']}")
    if ent and image.get("fit"):
        want_contain = ent["fit"].startswith("contain")
        if want_contain and image["fit"] == "cover":
            add("L03", f"{ent['title']} images are cropped by cover; covers and packshots must stay whole")
    variant = spec.get("layout", {}).get("variant") or (ent or {}).get("list_variant")
    pos = image.get("position")
    if pos:
        if variant in ("tile", "media-card", "scroller-card") and pos != "top":
            add("L04", f"a {variant} puts its image {pos}, not on top")
        if variant == "row" and pos == "top":
            add("L04", "a row with a full-width image is a media card: use a thumbnail at the start")
        if pos == "both":
            add("L04", "images on both sides of a row")

    # L05 order and clamping
    slots = [s for s in card.get("slots", []) if s != "image"]
    text_slots = [s for s in slots if s in TEXT_SLOTS_ORDER]
    if text_slots and text_slots[0] not in ("title", "name", "date", "time") and ent and ent.get("list_variant") != "plan-card" \
            and spec.get("entity") != "listing":
        add("L05", f"the card text starts with {text_slots[0]!r}, not the title")
    if "price" in text_slots and "title" in text_slots and text_slots.index("price") < text_slots.index("title") \
            and spec.get("entity") != "listing":
        add("L06", "price above the title (listings are the exception: price leads)")
    lines = card.get("title_lines")
    if lines and ((variant == "row" and lines > 1 and spec.get("entity") != "article") or lines > 2 and spec.get("entity") != "article"):
        add("L05", f"title takes {lines} lines in a {variant}")

    # L06 price
    price = card.get("price", {})
    if price.get("style") in ("pill", "badge", "accent"):
        add("L06", f"price drawn as a {price['style']}")
    if price.get("on_image"):
        add("L06", "price placed on the image")
    if price.get("figures") == "proportional":
        add("L21", "prices in proportional figures do not line up")

    # L07 rating, L08 availability, L17-L20
    if card.get("rating") in ("stars", "five-stars"):
        add("L07", "a row of stars on every card")
    if spec.get("unavailable") in ("hidden", "colour-only", "color-only"):
        add("L08", f"unavailable items are {spec['unavailable']}")
    if (card.get("description_lines") or 0) > 1:
        add("L17", f"{card['description_lines']} description lines in a card")
    if (card.get("tags") or 0) > 1 or card.get("ribbon"):
        add("L18", f"{card.get('tags', 0)} tags{' and a ribbon' if card.get('ribbon') else ''} on a card")
    if len(card.get("actions", [])) > 1 and not (screen == "catalog" and pa == "in-card"):
        add("L19", f"{len(card['actions'])} controls on one card")
    if card.get("text_on_image"):
        add("L20", "text drawn over the image")
    if card.get("alt") in (None, "", "missing") and "image" in card.get("slots", []) and "alt" in card:
        add("L22", "images without alt text")

    # L09 columns, L10 carousels, L24 width
    width = spec.get("width")
    cols = spec.get("layout", {}).get("columns")
    if width and cols and variant == "tile":
        want = 2 if width < 560 else 3
        if cols != want:
            add("L09", f"{cols} columns at {width} px")
    if variant == "tile" and width and width >= 600 and not spec.get("max_width"):
        add("L24", "a wide client stretches the grid; cap the content at ~600 px")
    if (spec.get("carousels") or 0) > 1:
        add("L10", f"{spec['carousels']} horizontal scrollers on one screen")
    if spec.get("main_list") == "carousel":
        add("L10", "the main catalogue is a horizontal scroller")

    # L11 detail order, L12 gallery
    sections = spec.get("sections")
    if sections and ent:
        expected = [s for s in ent["detail"]]
        first_media = expected[0]
        if sections and sections[0] not in (first_media, "gallery", "cover", "portrait", "video", "photo", "media"):
            add("L11", f"the detail screen starts with {sections[0]!r} instead of the media")
        if "reviews" in sections and "description" in sections and sections.index("reviews") < sections.index("description"):
            add("L11", "reviews before the description")
    if spec.get("gallery") in ("masonry", "autoplay"):
        add("L12", f"a {spec['gallery']} gallery")

    # L13-L16
    filters = spec.get("filters", {})
    if (filters.get("count") or 0) > 5 and filters.get("placement") != "sheet":
        add("L13", f"{filters['count']} filters in a row")
    if filters and filters.get("result_count") is False:
        add("L13", "no result count after filtering")
    if spec.get("search") in ("bottom", "hidden") and screen == "catalog":
        add("L14", f"search is {spec['search']}")
    form = spec.get("form", {})
    if form.get("columns", 1) > 1:
        add("L15", f"a {form['columns']}-column form")
    if form.get("labels") in ("placeholder", "none"):
        add("L15", "placeholders used as labels")
    booking = spec.get("booking", {})
    if booking:
        if booking.get("unavailable") == "hidden":
            add("L16", "taken slots are hidden")
        if booking.get("days") not in (None, "strip"):
            add("L16", f"days picked with a {booking['days']}")
        if booking.get("slots_columns") and not 3 <= booking["slots_columns"] <= 4:
            add("L16", f"{booking['slots_columns']} slot columns")
        if booking.get("summary") is False:
            add("L16", "no summary of the chosen slot")
        if booking.get("main_button_names_slot") is False:
            add("L16", "the MainButton does not name the slot and price")
    plans = spec.get("plans", {})
    if plans:
        if plans.get("layout") == "side-by-side" and (width or 390) < 600:
            add("L25", "plans side by side on a phone")
        if (plans.get("features_max") or 0) > 6 or (plans.get("count") or 0) > 3 and not plans.get("table"):
            add("L25", "many plans or features without a comparison table")
        if (plans.get("recommended") or 0) > 1:
            add("L25", f"{plans['recommended']} recommended plans")
    if spec.get("states", {}).get("skeleton") == "spinner":
        add("L23", "a spinner instead of skeletons in the card's shape")
    return out


def show(name: str, data: dict) -> str:
    e = data["entities"][name]
    v = data["variants"][e["list_variant"]]
    lines = [f"{name}: {e['title']}",
             f"  list: {e['list_variant']} ({v['what']}; kit {v['kit']}), columns {e['columns']}",
             f"  image: {e['ratio']}, fit {e['fit']}",
             f"  card slots in order: {', '.join(e['card'])}",
             f"  meta line: {e['meta']}" + (f"; rating: {e['rating']}" if e.get('rating') else ""),
             f"  card control: {e['card_action']}",
             f"  primary action (MainButton): {e['primary']}",
             f"  detail order: {' -> '.join(e['detail'])}"]
    if e.get("row"):
        lines.append(f"  as a row: {e['row']}")
    ratio = ratio_of(e["ratio"]) or "1:1"
    fit = "is-contain" if e["fit"].startswith("contain") else ""
    if e["list_variant"] == "tile":
        markup = (f'<div class="tma-grid">\n  <a class="tma-tile" href="#">\n    <figure class="tma-media {fit}" style="--tma-ratio:{ratio.replace(":", " / ")}">'
                  f'<img src="..." alt="Title, variant" loading="lazy"></figure>\n    <span class="tma-tile__title">Title</span>\n'
                  f'    <span class="tma-meta">{e["meta"]}</span>\n    <span class="tma-price">€12.90</span>\n  </a>\n</div>')
    elif e["list_variant"] in ("media-card", "scroller-card"):
        markup = (f'<a class="tma-tile is-wide" href="#">\n  <figure class="tma-media" style="--tma-ratio:{ratio.replace(":", " / ")}">'
                  f'<img src="..." alt="..." loading="lazy"><span class="tma-media__badge">32 min</span></figure>\n'
                  f'  <span class="tma-tile__title">Title</span>\n  <span class="tma-meta">{e["meta"]}</span>\n</a>')
    elif e["list_variant"] == "plan-card":
        markup = ('<section class="tma-card tma-plan">\n  <p class="tma-headline">Team</p>\n  <p class="tma-price is-lg">€12 <span class="tma-price__period">/ month</span></p>\n'
                  '  <ul class="tma-checks"><li>Up to 10 seats</li></ul>\n</section>')
    elif e["card"] and e["card"][0] == "time":
        markup = ('<ul class="tma-list">\n  <li><a class="tma-cell is-2" href="#"><span class="tma-cell__time">07:00</span>\n'
                  f'    <span class="tma-cell__body"><span class="tma-cell__title">Title</span><span class="tma-cell__subtitle">{e["meta"]} · 3 spots left</span></span>\n'
                  '    <svg class="tma-cell__chevron" aria-hidden="true"><use href="icons.svg#i-chevron-right"/></svg></a></li>\n'
                  '  <!-- a full one stays listed: aria-disabled="true" dims it, the reason is in the subtitle -->\n</ul>')
    elif "avatar" not in e["ratio"] and (ratio_of(e["ratio"]) or "thumbnail" in e["ratio"] or "photo" in e["ratio"]):
        end = "end" in e["ratio"]
        thumb = '<span class="tma-row-thumb"><img src="..." alt="Title"></span>'
        markup = ('<ul class="tma-list">\n  <li><a class="tma-cell is-2" href="#">' + ("" if end else thumb) + '\n'
                  f'    <span class="tma-cell__body"><span class="tma-cell__title">Title</span><span class="tma-cell__subtitle">{e["meta"]}</span></span>\n'
                  '    ' + (thumb if end else '<span class="tma-cell__after tma-price">€12.90</span>') + '</a></li>\n</ul>')
    elif "avatar" in e["ratio"]:
        markup = ('<ul class="tma-list">\n  <li><a class="tma-cell is-2" href="#"><img class="tma-avatar is-48" src="..." alt="Name">\n'
                  f'    <span class="tma-cell__body"><span class="tma-cell__title">Name</span><span class="tma-cell__subtitle">{e["meta"]}</span></span>\n'
                  '    <span class="tma-cell__after">from €30</span></a></li>\n</ul>')
    else:
        markup = ('<ul class="tma-list">\n  <li><div class="tma-cell is-2">\n'
                  f'    <span class="tma-cell__body"><span class="tma-cell__title">Name</span><span class="tma-cell__subtitle">{e["meta"]}</span></span>\n'
                  '    <span class="tma-cell__after tma-num">1,250</span></div></li>\n</ul>')
    return "\n".join(lines) + "\n\nMarkup (kit classes):\n" + markup


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Mini App layout rules")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("entities")
    sub.add_parser("rules")
    sub.add_parser("show").add_argument("entity")
    sub.add_parser("review").add_argument("spec")
    sub.add_parser("example").add_argument("screen", choices=sorted(EXAMPLES))
    sub.add_parser("schema")
    args = ap.parse_args(argv)
    data = load()
    if args.cmd == "entities":
        for k, e in data["entities"].items():
            print(f"{k:<11} {e['title']:<34} {e['list_variant']:<11} image {e['ratio']}")
    elif args.cmd == "rules":
        for k, r in data["rules"].items():
            print(f"{k} {r['title']}\n    fix: {r['fix']}")
    elif args.cmd == "show":
        if args.entity not in data["entities"]:
            print(f"unknown entity {args.entity}; known: {', '.join(data['entities'])}")
            return 1
        print(json.dumps(data["entities"][args.entity], ensure_ascii=False, indent=1) if args.json else show(args.entity, data))
    elif args.cmd == "example":
        print(json.dumps(EXAMPLES[args.screen], ensure_ascii=False, indent=1))
    elif args.cmd == "schema":
        print(schema_text())
    else:
        with open(args.spec, encoding="utf-8") as fh:
            spec = json.load(fh)
        errors = validate(spec)
        if errors:
            for e in errors:
                print(f"SCHEMA {e}")
            print(f"{len(errors)} schema error(s): fix the description (py -3 scripts/miniapp_layout.py schema); nothing was reviewed")
            return 2
        found = review(spec, data)
        if args.json:
            print(json.dumps({"findings": found, "ok": not any(f["severity"] == "error" for f in found)}, ensure_ascii=False, indent=1))
        else:
            for f in found:
                print(f"{'ERROR' if f['severity'] == 'error' else 'WARN '} {f['rule']} {f['title']}: {f['message']}\n      fix: {f['fix']}")
            print(f"{len(found)} finding(s). Rules: references/mini-apps/layout-rules.md")
        return 1 if any(f["severity"] == "error" for f in found) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
