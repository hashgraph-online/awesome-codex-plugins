"""data-table: one page of a business report (today's orders) in a private chat.

Requests: "sync" (Refresh), "pg:<n>" -> the bot edits chat_data with page n of the report it
keeps, "rep" -> the bot sends the whole report as Rich Message tables split by whole rows with the
header repeated (tgkit.dataview.rich_table_parts) and answers how many parts went out.
The report lives in the bot's store; chat_data carries one page (<= 8 rows), so it stays small.
"""
from __future__ import annotations

from tgkit import dataview

from .core import Action, BadRequest, Ctx, Spec, load_demo

PAGE = 8
COLS = [["Order", "t"], ["Status", "s"], ["Items", "n", 1], ["Sum", "m:EUR"]]   # Items hides on narrow screens
STATUS = [(0, "Paid"), (0, "Paid"), (1, "Pending"), (0, "Paid"), (2, "Refunded"), (3, "Cancelled")]


def report(n: int = 29) -> list[list]:
    """Stand-in for the bot's order store: deterministic, so tests and payloads are stable."""
    return [[f"#{1040 + i}", list(STATUS[i % len(STATUS)]), 1 + i * 7 % 5, 1250 + i * 731 % 9000] for i in range(n)]


def page(rows: list[list], pg: int) -> list[list]:
    return rows[pg * PAGE:(pg + 1) * PAGE]


def totals(rows: list[list]) -> list:
    return ["Total", None, sum(r[2] for r in rows), sum(r[3] for r in rows if r[1][0] != 2)]


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "sync":
        return None, {}
    rows = report(state.get("n", 0)) if state else []
    if act.verb == "pg":
        pp = max(1, -(-len(rows) // PAGE))
        if not act.arg.isdigit() or not 0 <= int(act.arg) < pp:
            raise BadRequest(act.raw)
        pg = int(act.arg)
        if pg == state.get("pg"):
            return None, {}
        return {**state, "pg": pg, "pp": pp, "rw": page(rows, pg), "at": int(ctx.now)}, {}
    if act.verb == "rep":
        if not rows:
            raise BadRequest(act.raw)
        lang = ctx.lang if ctx.lang in ("en", "ru", "uk") else "en"
        cells = [[r[0], r[1][1], dataview.number(r[2], lang), dataview.money(r[3], "EUR", lang)] for r in rows]
        tot = totals(rows)
        parts = dataview.rich_table_parts(
            state["ti"], [c[0] for c in COLS], cells, numeric=frozenset({2, 3}), lang=lang,
            summary=f"{len(rows)} orders · {dataview.money(tot[3], 'EUR', lang)} paid",
            footer="Refunded orders are not in the total.")
        # The bot sends these in order with sendRichMessage (parts 2..n with disable_notification).
        ctx.memo["report_parts"] = parts
        return None, {"parts": len(parts)}
    raise BadRequest(act.raw)


SPEC = Spec(name="data-table", decide=decide, demo=load_demo("data-table"))
