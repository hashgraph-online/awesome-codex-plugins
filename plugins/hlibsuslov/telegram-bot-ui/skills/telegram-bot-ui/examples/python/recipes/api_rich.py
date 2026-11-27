"""Rich messages sent as JSON blocks (InputRichMessage.blocks), built with the tgkit.rich builders.

Run:  py -3 examples/python/recipes/api_rich.py        (offline; nothing is sent)
Written to payloads/api-rich.json by export_payloads.py. Ids are synthetic. A deploy bot streams a
draft (a thinking block, then the first finished section), sends the final report as blocks and
later edits it: the edit replaces the whole rich_message, so it rebuilds the document from the same
data with one checklist item checked. Every request passes validate_payload and validate_rich.
The same document as Rich HTML: tests/test_rich_blocks.py compares both forms.
"""
from __future__ import annotations

import os
import sys

import _common as c
from tgkit import rich as r
from tgkit.transport import FakeTransport

sys.path.insert(0, os.path.join(os.path.dirname(c.ROOT), "scripts"))
import validate_payload  # noqa: E402
import validate_rich  # noqa: E402

STATUS = "production"
CONTEXT = ("private chat with the user who started the deploy (drafts are private-only); the final message "
           "and its edit work in any chat where the bot may send messages")
STEP_CONTEXT = {
    "sendRichMessageDraft": "private chat only; no new uploads or URLs in a draft, media by file_id",
    "sendRichMessage": "any chat where the bot may send messages; a media block also needs the right to send it",
    "editMessageText": "a message the bot sent; rich_message replaces the whole document",
}

CHAT = 7001001                              # a private chat with the user
DRAFT = 4242                                # non-zero; reused so the updates animate
CHART = "AgACAgIAAxkBAAEBdeployChart0042"   # file_id of a chart sent earlier: drafts can't upload
RUNBOOK = "https://example.com/runbooks/payments-api"
SERVICES = [("payments-api", "212", "180"), ("ledger", "95", "97"), ("notifier", "40", "38")]


def summary_blocks() -> list[dict]:
    return [
        r.heading_block("Deploy 2026-11-25: payments-api 4.12", 1),
        r.paragraph_block(["Rolled out to ", r.bold("3 of 3"), " regions. p95 latency of ",
                           r.code("payments-api"), " fell by ", r.bold("15%"), "; see the ",
                           r.url("runbook", RUNBOOK), "."]),
    ]


def report_blocks(checked: set[str]) -> list[dict]:
    steps = ["Migrate the refunds table", "Switch traffic to the new pool", "Remove the old pool"]
    return summary_blocks() + [
        r.heading_block("Checklist", 2),
        r.list_block([r.list_item([r.paragraph_block(s)], has_checkbox=True, is_checked=s in checked)
                      for s in steps]),
        # The one document button here: a view switch right above the table it switches (the current period is
        # disabled). Roll back is the main action and lives on the keyboard; the runbook is a link in the text
        # (references/rich-message-buttons.md).
        r.buttons_block([r.message_button("24 h", disabled=True),
                         r.message_button("7 days", callback_data="deploy:4.12:period:7d")], align="left"),
        r.table(["Service", "p95 before, ms", "p95 after, ms"], [list(row) for row in SERVICES], compact=True,
                numeric_cols=frozenset({1, 2}), caption="Latency, 24 h before and after"),
        r.photo_block(CHART, r.block_caption("p95 latency, last 48 h", credit="Grafana, eu-west")),
        r.details_block("Migration log", [r.pre_block("ALTER TABLE refunds ADD COLUMN refund_id uuid;\n"
                                                      "-- 1 204 311 rows, 41 s", "sql")]),
        r.expandable_blockquote_block([r.paragraph_block("Error rate stayed under 0.1% during the switch.")],
                                      credit="On-call notes"),
        r.divider_block(),
        r.footer_block(["Started from ", r.code("/deploy payments-api 4.12"), " by the on-call engineer."]),
    ]


def send_rich_message_draft(t: FakeTransport) -> None:
    t.call("sendRichMessageDraft", {"chat_id": CHAT, "draft_id": DRAFT,
                                    "rich_message": {"blocks": [r.thinking_block("Collecting metrics")]}})
    t.call("sendRichMessageDraft", {"chat_id": CHAT, "draft_id": DRAFT, "rich_message": {
        "blocks": summary_blocks() + [r.thinking_block("Building the latency table")]}})


KEYBOARD = {"inline_keyboard": [[{"text": "Roll back", "callback_data": "deploy:4.12:rollback", "style": "danger"}]]}


def send_rich_message(t: FakeTransport) -> dict:
    return t.call("sendRichMessage", {"chat_id": CHAT, "reply_markup": KEYBOARD, "rich_message": {"blocks": report_blocks(
        {"Migrate the refunds table", "Switch traffic to the new pool"})}})


def edit_message_text(t: FakeTransport, msg: dict) -> None:
    t.call("editMessageText", {"chat_id": CHAT, "message_id": msg["message_id"], "rich_message": {
        "blocks": report_blocks({"Migrate the refunds table", "Switch traffic to the new pool",
                                 "Remove the old pool"})}})


def run_all() -> FakeTransport:
    t = FakeTransport()
    send_rich_message_draft(t)
    msg = send_rich_message(t)
    edit_message_text(t, msg)
    v = validate_payload.Validator(validate_payload.load_catalog(validate_payload.DATA_DIR))
    for method, params in t.calls:
        c.check(v.check_request(method, params).ok, f"{method}: structurally valid (validate_payload)")
        errors, warnings, _ = validate_rich.validate(params, draft=method.endswith("Draft"))  # drafts: no uploads
        c.check(not errors, f"{method}: blocks pass validate_rich {errors or ''}".rstrip())
        c.check(not [w for w in warnings if w.startswith("RICH_BUTTON_")], f"{method}: no misplaced document buttons")
    c.check(not any(b["type"] == "thinking" for b in t.params_of("sendRichMessage")[0]["rich_message"]["blocks"]),
            "the final message has no thinking block")
    c.check(sorted(t.methods()) == sorted(["sendRichMessageDraft"] * 2 + ["sendRichMessage", "editMessageText"]),
            "draft twice, send once, edit once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Rich messages as blocks")
