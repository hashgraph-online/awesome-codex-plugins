#!/usr/bin/env python3
"""The icon plan: choose custom emoji packs and the best STATIC emoji for every button and title, in stages,
with a score breakdown, alternatives and a decision record. The playbook the agent follows is
references/emoji-packs.md "The icon plan"; this module does the measurable part of it.

  0 gate      eligibility route (Fragment / owner Premium / none), channels, and whether icons pay off at all
  1 inventory every place that may carry an icon (button labels per locale, titles) mapped to a slot meaning;
              keyboards are all icons or none; Back / Forward / Close stay words by default
  2 brief     the look asked of a pack: the style profile, else the Mini App kit's line icons (outline,
              monochrome, adaptive), so the bot and its Mini App read as one identity
  3 packs     candidate packs: library search votes + facet fit; per pack static coverage of the slots,
              theme safety, legibility of its look; the main pack and its compatible siblings
  4 slots     per slot every static candidate of the family pool, scored: meaning, family, style, theme,
              legibility (weights in WEIGHTS), with the reasons
  5 assemble  the main pack first; a sibling only when it says the meaning clearly better; one id one meaning;
              locked slots kept; a slot nothing says well stays label-only; a keyboard with a gap goes label-only
  6 review    review_html(): each choice and its alternatives at button size on light and dark, a verdict per slot
  7 record    the plan document (format bot-ui-icon-plan/v1), kept in a bot-ui project as emoji/icon-plan.json
  8 validate  bot-ui validate (BUTTON_EMOJI_ANIMATED, ICON_MEANING_MISMATCH), audit_icons, a real-client check

Network: only through emoji_packs.LibraryClient (search words and pack names leave the machine). Offline: saved
answers (`--library-json`); the catalog export has no fallback emoji, so it cannot say what an emoji means.
"""
from __future__ import annotations

import datetime
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from bot_ui.emoji import PLACEHOLDER_RE, WORD_RE, _phrases, _says  # noqa: E402
from emoji_packs import GROUP_ROLE, emoji_key, normalize_brief, rank_by_facets  # noqa: E402

FORMAT = "bot-ui-icon-plan/v1"
# The Mini App kit draws line icons: stroke 1.8, round caps, one colour (data/mini-apps/icons.json). Without a
# style profile the bot's custom emoji are asked to look the same way.
KIT_BRIEF = {"topic": ["interface"], "style": ["outline"], "palette": ["monochrome"], "fit": ["adaptive"]}
CONTROLS = {"back", "forward", "close"}       # words read faster; an icon here only when the family does it everywhere
WEIGHTS = {"meaning": 0.40, "family": 0.20, "style": 0.15, "theme": 0.10, "legibility": 0.15}
MEANING_MIN = 0.6         # below: not a candidate for the slot at all
LEGIBLE_MIN = 0.4         # below: unreadable at 20 px, never chosen
FAMILY_MIN = 0.8          # a sibling pack fills a gap only when the library rates it at least this similar
SWITCH_MEANING = 0.2      # a sibling replaces the main pack's emoji only when it says the meaning this much better
SWITCH_TOTAL = 0.12       # ... or scores this much higher overall
ALTERNATIVES = 3
WORTH_MIN = 3             # fewer icon slots than this across the bot: icons rarely pay for a second pack and a route
HARD_STYLES = {"3d", "glossy", "realistic", "mosaic", "pixel", "gradient", "neon", "cartoon"}
EMOJI_TH = 0.5            # the library's emoji-level tag threshold


# ------------------------------------------------------------------ stage 0: gate

def gate(route: str | None, slots: int, audiences: list[str] | None = None) -> dict:
    """Whether this bot should carry custom emoji icons at all, and what that depends on."""
    route = route or "none"
    reasons, ok = [], True
    if route == "none":
        ok = False
        reasons.append("no route: the bot has no Fragment username and the owner's Premium is not declared "
                       "(capabilities.customEmoji); Telegram strips custom emoji silently - keep words or Unicode")
    if route == "owner_premium" and "channel" in (audiences or []):
        reasons.append("channel screens need Fragment usernames: owner Premium does not reach channels")
    if route == "owner_premium":
        reasons.append("owner Premium: if it lapses Telegram drops the icons silently; keep labels that read alone")
    if slots < WORTH_MIN:
        reasons.append(f"{slots} icon slot(s): too few to be worth a pack; consider label-only buttons")
    return {"ok": ok, "route": route, "reasons": reasons}


# ------------------------------------------------------------------ stage 1: inventory

def label_slot(label: str, vocab: dict) -> str | None:
    """The one slot a label says: the longest phrase wins ("Order status" -> status over order when both match)."""
    tokens = [t.lower() for t in WORD_RE.findall(PLACEHOLDER_RE.sub(" ", label or ""))]
    best: tuple[int, str] | None = None
    for slot, entry in vocab.items():
        if not entry.get("words"):
            continue
        for phrase in _phrases(entry):
            if _says(tokens, phrase) and (best is None or len(phrase) > best[0] or (len(phrase) == best[0] and slot < best[1])):
                best = (len(phrase), slot)
    return best[1] if best else None


def lead_slot(lead: str | None, vocab: dict) -> str | None:
    """The slot whose first choice (else any choice) is this emoji."""
    if not lead:
        return None
    key = emoji_key(lead)
    first = next((s for s, v in vocab.items() if [emoji_key(u) for u in (v.get("unicode") or [])][:1] == [key]), None)
    return first or next((s for s, v in vocab.items() if key in {emoji_key(u) for u in v.get("unicode") or []}), None)


def inventory(places: list[dict], vocab: dict) -> dict:
    """places: [{where, kind: button|title, labels: {locale: text}, keyboard: id|None, lead: emoji|None, icon: id|None}]
    -> {slots: {slot: {use, labels, places, control}}, unmatched: [...], keyboards: {id: [{where, slot, control}]}}.
    The label's words decide the meaning; a leading emoji only breaks a tie or speaks for a title without words."""
    slots: dict[str, dict] = {}
    unmatched, keyboards = [], {}
    for p in places:
        texts = [t for t in (p.get("labels") or {}).values() if isinstance(t, str) and t.strip()]
        said = Counter(s for t in texts if (s := label_slot(t, vocab)))
        lead = lead_slot(p.get("lead"), vocab)
        kind = p.get("kind", "button")
        if kind == "title" and lead:
            slot = lead          # a title's emoji is its icon; its words are the screen's subject, not a slot
        else:
            slot = (lead if lead in said else said.most_common(1)[0][0]) if said else lead
        if kind == "button" and p.get("keyboard"):
            keyboards.setdefault(p["keyboard"], []).append({"where": p["where"], "slot": slot, "control": slot in CONTROLS})
        if not slot:
            unmatched.append({"where": p["where"], "labels": p.get("labels") or {}})
            continue
        row = slots.setdefault(slot, {"use": [], "labels": [], "places": [], "control": slot in CONTROLS})
        if kind not in row["use"]:
            row["use"].append(kind)
        row["labels"] += [t for t in texts if t not in row["labels"]]
        row["places"].append(p["where"])
    return {"slots": slots, "unmatched": unmatched, "keyboards": keyboards}


# ------------------------------------------------------------------ stage 2: brief

def brief_for(profile_brief: dict | None) -> tuple[dict, str]:
    """The profile's brief, completed by the kit's defaults where it is silent; (brief, where it came from)."""
    if not profile_brief:
        return dict(KIT_BRIEF), "the Mini App kit's line icons (no style profile)"
    out = {**KIT_BRIEF, **{k: v for k, v in profile_brief.items() if v}}
    return out, "the style profile, completed by the kit's defaults"


# ------------------------------------------------------------------ stage 4: scoring one emoji for one slot

def _tags(facets: dict | None, facet: str, th: float = EMOJI_TH) -> dict[str, float]:
    return {v: c for v, c in ((facets or {}).get(facet) or []) if isinstance(c, (int, float)) and c >= th}


def meaning_score(e: dict, slot: str, vocab: dict, needed: set[str]) -> tuple[float, list[str]]:
    """1.0 for the slot's first emoji, less for its later equivalents, 0 when the emoji is not one of them;
    + the emoji's interface role, - decoration, - a picture that is another needed slot's first emoji."""
    keys = [emoji_key(u) for u in (vocab.get(slot) or {}).get("unicode") or []]
    fb = emoji_key(e.get("fallback") or "")
    if not fb or fb not in keys:
        return 0.0, []
    i = keys.index(fb)
    score, why = max(0.6, 1.0 - 0.12 * i), [f"{e.get('fallback')} is the slot's {'first' if i == 0 else f'#{i + 1}'} emoji"]
    roles = _tags(e.get("facets"), "role")
    want = GROUP_ROLE.get((vocab.get(slot) or {}).get("group"))
    if want and want in roles:
        score += 0.1
        why.append(f"tagged as a {want} icon")
    if "decoration" in roles:
        score -= 0.15
        why.append("tagged as decoration")
    other = [s for s in needed if s != slot and [emoji_key(u) for u in (vocab.get(s) or {}).get("unicode") or []][:1] == [fb]]
    if other:
        score -= 0.2
        why.append(f"the same picture is the first emoji of {', '.join(sorted(other))}: it may read as that")
    return round(min(1.0, max(0.0, score)), 3), why


def theme_score(e: dict, theme: str) -> tuple[float, str]:
    if e.get("adaptive"):
        return 1.0, "adaptive: drawn in the text colour, right in light and dark"
    fit = _tags(e.get("facets"), "fit")
    if theme == "both":
        if "both" in fit:
            return 0.75, "fixed colours that read on light and dark"
        if fit.keys() & {"light", "dark"}:
            return 0.3, f"fixed colours for {'/'.join(sorted(fit.keys() & {'light', 'dark'}))} only"
        return 0.5, "fixed colours, theme fit untagged: check both themes"
    if theme in fit or "both" in fit:
        return 0.9, f"fits {theme}"
    return 0.5, "fixed colours, theme fit untagged"


def style_score(e: dict, pack: dict, brief: dict) -> tuple[float, str]:
    wanted = brief.get("style") or []
    if not wanted:
        return 0.7, "no style asked"
    own = _tags(e.get("facets"), "style")
    if own:
        best = max((own.get(w, 0.0) for w in wanted), default=0.0)
        if best:
            return round(best, 3), f"drawn {'/'.join(wanted)} ({best:.2f})"
        return 0.2, f"drawn {max(own, key=own.get)}, asked {'/'.join(wanted)}"
    pk = _tags(pack.get("facets"), "style", 0.3)
    best = max((pk.get(w, 0.0) for w in wanted), default=0.0)
    if best:
        return round(0.9 * best, 3), f"pack drawn {'/'.join(wanted)} ({best:.2f})"
    return (0.3, f"pack drawn {max(pk, key=pk.get)}, asked {'/'.join(wanted)}") if pk else (0.5, "style untagged: look at it")


def legibility_score(e: dict, pack: dict) -> tuple[float, list[str]]:
    """How well the picture reads at button size (about 20 px): one simple glyph beats a scene."""
    score, why = 1.0, []
    hard = _tags(e.get("facets"), "style").keys() & HARD_STYLES
    if hard:
        score -= 0.35
        why.append(f"{'/'.join(sorted(hard))}: detail that blurs at 20 px")
    if _tags(e.get("facets"), "topic").keys() & {"characters", "faces"}:
        score -= 0.3
        why.append("a face or character: reads as a sticker, not an icon")
    if "multicolor" in _tags(e.get("facets"), "palette"):
        score -= 0.15
        why.append("many colours")
    look = pack.get("look") or {}
    for key, bad, cut, text in (("line_weight", {"hairline"}, 0.2, "hairline strokes vanish small"),
                                ("fill", {"photo", "textured"}, 0.3, "photo or textured fill"),
                                ("fill", {"gradient"}, 0.1, "gradient fill"),
                                ("shadows", {"glow", "hard"}, 0.15, "glow or hard shadows"),
                                ("perspective", {"three-quarter"}, 0.1, "three-quarter perspective")):
        if look.get(key) in bad:
            score -= cut
            why.append(text)
    return round(max(0.0, score), 3), why


def score_candidate(e: dict, slot: str, vocab: dict, needed: set[str], pack: dict, family: float, brief: dict,
                    theme: str) -> dict | None:
    """One emoji as a candidate for one slot, or None when it does not say the slot at all."""
    meaning, mwhy = meaning_score(e, slot, vocab, needed)
    if meaning < MEANING_MIN:
        return None
    t, twhy = theme_score(e, theme)
    s, swhy = style_score(e, pack, brief)
    leg, lwhy = legibility_score(e, pack)
    parts = {"meaning": meaning, "family": round(family, 3), "style": s, "theme": t, "legibility": leg}
    total = round(sum(WEIGHTS[k] * v for k, v in parts.items()), 3)
    return {"id": str(e["id"]), "pack": pack["name"], "fallback": e.get("fallback") or "", "format": e.get("format"),
            "adaptive": bool(e.get("adaptive")), "preview": e.get("preview"), "score": total, "breakdown": parts,
            "why": mwhy + [swhy, twhy] + lwhy}


# ------------------------------------------------------------------ stage 3: packs

def _static(e: dict) -> bool:
    return e.get("format") == "static"


def candidate_packs(slots: list[str], vocab: dict, client, brief: dict, doc: dict | None,
                    candidates: int) -> tuple[list[str], dict, list[str]]:
    """Pack names to fetch: library search votes (static hits of a slot's emoji) and the best facet fits (`doc`:
    the library's facets answer, None when it has no tags)."""
    votes: Counter = Counter()
    for slot in slots:
        keys = {emoji_key(u) for u in vocab[slot].get("unicode") or []}
        query = (vocab[slot].get("unicode") or [vocab[slot].get("label", slot)])[0]
        seen = set()
        for hit in client.search(query).get("emoji") or []:
            if _static(hit) and emoji_key(hit.get("fallback") or "") in keys and hit.get("pack") not in seen:
                votes[hit["pack"]] += 1
                seen.add(hit["pack"])
    notes: list[str] = []
    fit: dict[str, float] = {}
    catalog: dict[str, dict] = {}
    if doc is None:
        notes.append("the library has no tags yet: packs ranked by coverage only")
    else:
        catalog = {p["name"]: p for p in doc.get("packs") or [] if isinstance(p, dict) and "name" in p}
        ranked = rank_by_facets(doc, brief, top=len(catalog) or 1)
        fit = {r["name"]: r["score"] for r in ranked["packs"]}
        notes += ranked["problems"]
    pool = dict(votes)
    for name, score in sorted(fit.items(), key=lambda kv: (-kv[1], kv[0]))[:candidates]:
        if score > 0:
            pool.setdefault(name, 0)
    order = sorted(pool, key=lambda n: (-(pool[n] / max(1, len(slots)) + 0.5 * fit.get(n, 0.0)), n))
    return order[:candidates], {"fit": fit, "votes": dict(votes), "catalog": catalog}, notes


def _pack_doc(client, name: str, catalog: dict) -> dict:
    doc = client.pack(name)
    meta = catalog.get(name) or {}
    return {"name": name, "title": doc.get("title") or meta.get("title") or name,
            "emoji": [e for e in doc.get("emoji") or [] if isinstance(e, dict) and str(e.get("id", "")).isdigit()],
            "facets": doc.get("facets") or meta.get("facets") or {}, "look": doc.get("look") or meta.get("look") or {},
            "compatible": doc.get("compatible") or meta.get("compatible") or [],
            "link": doc.get("telegramUrl") or f"https://t.me/addemoji/{name}"}


def pack_row(pack: dict, slots: dict, vocab: dict, brief: dict, theme: str, facet_fit: float) -> dict:
    """How well one pack alone serves the slots: weighted static coverage, meaning, theme, legibility, facet fit."""
    needed = set(slots)
    best: dict[str, dict] = {}
    for slot in slots:
        for e in pack["emoji"]:
            if not _static(e):
                continue
            c = score_candidate(e, slot, vocab, needed, pack, 1.0, brief, theme)
            if c and (slot not in best or c["score"] > best[slot]["score"]):
                best[slot] = c
    weight = {s: (1.0 if "button" in r["use"] else 0.5) for s, r in slots.items()}
    total_w = sum(weight.values()) or 1.0
    coverage = sum(weight[s] for s in best) / total_w
    mean = lambda k: sum(c["breakdown"][k] for c in best.values()) / len(best) if best else 0.0  # noqa: E731
    score = 0.45 * coverage + 0.1 * mean("meaning") + 0.15 * mean("theme") + 0.1 * mean("legibility") + 0.2 * facet_fit
    missing = [s for s in slots if s not in best]
    return {"name": pack["name"], "title": pack["title"], "link": pack["link"], "score": round(score, 3),
            "coverage": round(coverage, 3), "covers": sorted(best), "missing": missing,
            "adaptive_share": round(sum(c["adaptive"] for c in best.values()) / max(1, len(best)), 2),
            "facet_fit": round(facet_fit, 3), "look": pack.get("look") or {},
            "why": f"{pack['name']}: static emoji for {len(best)}/{len(slots)} slots"
                   + (f" (missing {', '.join(missing)})" if missing else "")
                   + f"; meaning {mean('meaning'):.2f}, theme {mean('theme'):.2f}, legibility {mean('legibility'):.2f}, "
                     f"brief fit {facet_fit:.2f}"}


# ------------------------------------------------------------------ stages 3-5: the plan

def plan_icons(inv: dict, vocab: dict, client, *, brief: dict | None = None, brief_source: str = "",
               theme: str = "both", locks: dict | None = None, gate_info: dict | None = None,
               candidates: int = 6, controls: bool = False) -> dict:
    """The whole plan for an inventory: packs ranked, the family pool, per slot the choice, the alternatives and the
    reasons; keyboards all-or-none; the decision record (FORMAT). `locks`: {slot: {id, ...}} the user chose."""
    brief = brief or dict(KIT_BRIEF)
    facets_doc = client.facets()
    wanted, problems = normalize_brief(brief, facets_doc)
    locks = {s: dict(i) for s, i in (locks or {}).items() if isinstance(i, dict) and i.get("id")}
    slots = {s: r for s, r in inv["slots"].items() if s in vocab}
    to_pick = [s for s, r in slots.items() if s not in locks and (controls or not r["control"])]
    notes = list(problems)
    names, info, more = candidate_packs(to_pick, vocab, client, wanted, facets_doc, candidates) if to_pick else ([], {"fit": {}, "catalog": {}}, [])
    notes += more
    packs = {n: _pack_doc(client, n, info["catalog"]) for n in names}
    rows = sorted((pack_row(p, {s: slots[s] for s in to_pick}, vocab, wanted, theme, info["fit"].get(n, 0.0))
                   for n, p in packs.items()), key=lambda r: (-r["score"], r["name"]))
    rows = [r for r in rows if r["covers"]]
    main = rows[0]["name"] if rows else None
    family = {main: 1.0} if main else {}
    if main:
        for sib, sim in packs[main]["compatible"]:
            if isinstance(sim, (int, float)) and sim >= FAMILY_MIN and len(family) < 4:
                family[sib] = float(sim)
                if sib not in packs:
                    packs[sib] = _pack_doc(client, sib, info["catalog"])
    needed = set(slots)
    used: dict[str, str] = {i["id"]: s for s, i in locks.items()}
    out_slots: dict[str, dict] = {}
    order = sorted(slots, key=lambda s: (s not in locks, "button" not in slots[s]["use"], -len(slots[s]["places"]), s))
    for slot in order:
        row = {"use": slots[slot]["use"], "labels": slots[slot]["labels"], "places": slots[slot]["places"],
               "choice": None, "alternatives": [], "reasons": [], "verdict": None}
        if slot in locks:
            row.update(status="locked", choice={**locks[slot], "by": locks[slot].get("by", "user")},
                       reasons=["chosen by the user: kept as is"])
            out_slots[slot] = row
            continue
        if slots[slot]["control"] and not controls:
            row.update(status="label-only", reasons=[f"{slot} is a control: the word reads faster than an arrow or a cross"])
            out_slots[slot] = row
            continue
        cands = []
        for name, sim in family.items():
            for e in packs[name]["emoji"]:
                if not _static(e) or str(e["id"]) in used:
                    continue
                c = score_candidate(e, slot, vocab, needed, packs[name], sim, wanted, theme)
                if c and c["breakdown"]["legibility"] >= LEGIBLE_MIN:
                    cands.append(c)
        cands.sort(key=lambda c: (-c["score"], c["pack"] != main, c["id"]))
        own = next((c for c in cands if c["pack"] == main), None)
        other = next((c for c in cands if c["pack"] != main), None)
        pick, reasons = own, []
        if own and other and (other["breakdown"]["meaning"] >= own["breakdown"]["meaning"] + SWITCH_MEANING
                              or other["score"] >= own["score"] + SWITCH_TOTAL):
            pick = other
            reasons.append(f"{other['pack']} (similarity {family[other['pack']]:.2f}) says it clearly better than {main}")
        elif not own and other:
            pick = other
            reasons.append(f"{main} has no static emoji for it; {other['pack']} is drawn alike "
                           f"(similarity {family[other['pack']]:.2f})")
        elif own:
            reasons.append(f"from the main pack {main}")
        if pick is None:
            row.update(status="label-only", reasons=["no static emoji in the family says this meaning well: keep the word"])
        else:
            used[pick["id"]] = slot
            row.update(status="chosen", choice=pick, reasons=reasons + pick["why"])
        row["alternatives"] = [c for c in cands if c is not pick][:ALTERNATIVES]
        out_slots[slot] = row
    # keyboards: all icons or none
    keyboards = {}
    for kb, buttons in inv.get("keyboards", {}).items():
        content = [b for b in buttons if not (b["control"] and not controls)]
        gaps = [b["where"] for b in content if not b["slot"] or (out_slots.get(b["slot"]) or {}).get("status") == "label-only"]
        keyboards[kb] = {"icons": not gaps and bool(content), "gaps": gaps}
    for slot, row in out_slots.items():
        if row["status"] != "chosen":
            continue
        kbs = [kb for kb, bs in inv.get("keyboards", {}).items() if any(b["slot"] == slot for b in bs)]
        if kbs and not any(keyboards[kb]["icons"] for kb in kbs) and "title" not in row["use"]:
            row["status"] = "label-only"
            row["reasons"].insert(0, f"its keyboard{'s' if len(kbs) > 1 else ''} {', '.join(kbs)} cannot be all icons "
                                     f"(a button there has none): a keyboard is all icons or none")
    used_packs = Counter((r["choice"] or {}).get("pack") for r in out_slots.values() if r["status"] in ("chosen", "locked"))
    used_packs.pop(None, None)
    if len(used_packs) > 2:
        notes.append(f"{len(used_packs)} packs in use: look hard at the review sheet for mismatched weight and fill")
    g = gate_info or {"ok": True, "route": "unknown", "reasons": []}
    chosen = sum(r["status"] == "chosen" for r in out_slots.values())
    return {
        "format": FORMAT, "generated": datetime.date.today().isoformat(), "theme": theme,
        "gate": g, "brief": wanted, "briefSource": brief_source or "given",
        "packs": {"main": main, "family": [{"name": n, "similarity": round(s, 2)} for n, s in family.items()],
                  "ranking": rows[:5], "used": dict(used_packs)},
        "slots": out_slots, "keyboards": keyboards, "unmatched": inv.get("unmatched", []),
        "summary": {"slots": len(out_slots), "chosen": chosen, "locked": sum(r["status"] == "locked" for r in out_slots.values()),
                    "labelOnly": sum(r["status"] == "label-only" for r in out_slots.values())},
        "notes": notes,
        "next": ["Look at the review sheet: every choice at button size on light and dark (stage 6).",
                 "Record a verdict per chosen slot: ok, an alternative, or reject (label-only).",
                 "Apply only slots with an ok verdict; run bot-ui validate and audit_icons; check on a real client."],
    }


# ------------------------------------------------------------------ stage 6: the review sheet

def review_html(plan: dict, site: str | None = None, pictures: dict[str, str] | None = None) -> str:
    """Each slot: its labels, the choice at 20 px (button size) and 40 px on a light and a dark tile, the
    alternatives, the score breakdown, the reasons and how to record the verdict. `site` resolves the library's
    relative preview paths; `pictures` maps id -> data: URL (a bot-ui project's cached previews)."""
    from html import escape as esc

    def pic(c: dict | None, size: int, dark: bool) -> str:
        if not c:
            return '<span class="none">-</span>'
        src = (pictures or {}).get(c.get("id")) or (f"{site.rstrip('/')}{c['preview']}" if site and c.get("preview") else None)
        tint = (" adaptive dark" if dark else " adaptive") if c.get("adaptive") else ""
        if src:
            return f'<img class="ic{tint}" src="{esc(src)}" width="{size}" height="{size}" alt="{esc(c.get("fallback") or "")}">'
        return f'<span class="fb" style="font-size:{size}px">{esc(c.get("fallback") or "?")}</span>'

    def tile(c: dict | None, label: str, dark: bool) -> str:
        return (f'<div class="btn{" d" if dark else ""}">{pic(c, 20, dark)}<span>{esc(label)}</span></div>'
                f'<div class="big{" d" if dark else ""}">{pic(c, 40, dark)}</div>')

    rows = []
    for slot, r in plan["slots"].items():
        label = (r["labels"] or [slot])[0]
        c = r.get("choice")
        bd = c.get("breakdown") if c else None
        score = (f"<b>{c.get('score', '')}</b><br>" + " · ".join(f"{k} {v}" for k, v in bd.items())) if bd else ""
        alts = "".join(f'<figure>{pic(a, 28, False)}{pic(a, 28, True)}<figcaption>#{n} {esc(a["pack"])} {a["score"]}'
                       f"</figcaption></figure>" for n, a in enumerate(r.get("alternatives") or [], 1))
        verdict = r.get("verdict") or ("record: bot-ui emoji verdict --slot " + esc(slot) + " --ok | --alt N | --reject REASON"
                                       if r["status"] == "chosen" else "")
        rows.append(f'<tr class="{esc(r["status"])}"><th>{esc(slot)}<br><small>{esc(", ".join(r["labels"][:3]))}</small></th>'
                    f'<td>{esc(r["status"])}{"<br>" + esc(c["pack"]) + " " + esc(c.get("format") or "") if c and c.get("pack") else ""}</td>'
                    f'<td class="tiles">{tile(c, label, False)}{tile(c, label, True)}</td><td>{score}</td>'
                    f'<td class="alts">{alts}</td><td>{"<br>".join(esc(x) for x in r["reasons"][:6])}</td>'
                    f"<td><code>{verdict}</code></td></tr>")
    g = plan.get("gate") or {}
    head = (f"<p>Main pack <b>{esc(str(plan['packs'].get('main')))}</b>; family "
            f"{esc(', '.join(f['name'] for f in plan['packs'].get('family') or []))}; brief {esc(str(plan.get('brief')))} "
            f"({esc(plan.get('briefSource') or '')}); route {esc(str(g.get('route')))}{'' if g.get('ok', True) else ' - BLOCKED'}."
            f"</p><p>Look at every row at the 20 px size: does the picture say the label, does it read on light and dark, "
            f"does it match its neighbours in fill, weight and colour? Adaptive emoji are tinted here like Telegram does "
            f"(an approximation).</p>")
    return ("<!doctype html><meta charset=utf-8><title>Icon plan review</title><style>"
            "body{font:14px system-ui;margin:24px;color:#222}table{border-collapse:collapse;width:100%}"
            "td,th{border-bottom:1px solid #ddd;padding:8px;text-align:start;vertical-align:middle}"
            ".tiles{display:grid;grid-template-columns:auto auto;gap:6px;align-items:center}"
            ".btn{display:flex;gap:6px;align-items:center;justify-content:center;min-width:150px;padding:8px 12px;border-radius:10px;"
            "background:#eef1f5;color:#111}.btn.d{background:#2b3441;color:#fff}.big{padding:6px;border-radius:10px;background:#fff;"
            "border:1px solid #ddd}.big.d{background:#17212b;border-color:#17212b}.adaptive{filter:brightness(0)}"
            ".adaptive.dark{filter:brightness(0) invert(1)}.alts{display:flex;gap:8px}figure{margin:0;text-align:center}"
            "figcaption{font-size:11px;color:#666}.label-only{background:#fafafa;color:#666}.locked{background:#f3f8ff}"
            "</style><h1>Icon plan review</h1>" + head +
            "<table><tr><th>slot</th><th>status</th><th>at button size</th><th>score</th><th>alternatives</th>"
            "<th>why</th><th>verdict</th></tr>" + "".join(rows) + "</table>")


# ------------------------------------------------------------------ stage 6-7: verdicts on the record

def set_verdict(plan: dict, slot: str, *, ok: bool = False, alt: int | None = None, reject: str | None = None,
                note: str | None = None) -> dict:
    """ok: the choice was looked at and fits. alt N: the Nth alternative becomes the choice (look again, then ok).
    reject: the slot goes label-only, with the reason."""
    row = (plan.get("slots") or {}).get(slot)
    if row is None:
        raise ValueError(f"no slot {slot!r} in the plan")
    if row["status"] == "locked":
        raise ValueError(f"{slot} is locked: the user chose it")
    if alt is not None:
        alts = row.get("alternatives") or []
        if not 1 <= alt <= len(alts):
            raise ValueError(f"{slot} has {len(alts)} alternative(s)")
        new = alts.pop(alt - 1)
        if row.get("choice"):
            alts.insert(0, row["choice"])
        row.update(choice=new, status="chosen", verdict=None)
        row["reasons"] = [f"alternative #{alt} taken after the review"] + new.get("why", [])
        return row
    if reject is not None:
        row.update(status="label-only", verdict={"value": "reject", "note": reject})
        return row
    if ok:
        if row["status"] != "chosen":
            raise ValueError(f"{slot} has no choice to accept (status {row['status']})")
        row["verdict"] = {"value": "ok", "note": note or ""}
        return row
    raise ValueError("pass ok, alt or reject")


def accepted(plan: dict) -> dict[str, dict]:
    """The icons the review accepted: slot -> choice (verdict ok)."""
    return {s: r["choice"] for s, r in (plan.get("slots") or {}).items()
            if r.get("status") == "chosen" and (r.get("verdict") or {}).get("value") == "ok" and r.get("choice")}
