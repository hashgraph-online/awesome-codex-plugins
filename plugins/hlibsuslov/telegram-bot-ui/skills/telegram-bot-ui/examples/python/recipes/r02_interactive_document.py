"""R02 - Interactive document: compact table, expandable quote, attached document,
buttons inside rich content, and replying with a quote of a selected fragment.

Run:  py -3 examples/python/recipes/r02_interactive_document.py
"""
from __future__ import annotations

import _common as c
from tgkit import rich
from tgkit.transport import FakeTransport

CHAT = 111111111


def build_document(spec_file_id: str, approved: bool = False) -> dict:
    approve = (rich.rich_button("Approved", disabled=True) if approved
               else rich.rich_button("Approve", callback_data="doc:approve:v3", style="success"))
    return {"blocks": [
        {"type": "heading", "size": 2, "text": "Key rotation policy v3"},
        {"type": "paragraph", "text": ["Rotate the ", {"type": "bold", "text": "signing key"}, " every 90 days."]},
        rich.table(["Key", "Owner", "Days left"],
                   [["signing", "Platform", "12"], ["webhook", "Bots team", "48"], ["backup", "SRE", "85"]],
                   compact=True, numeric_cols=frozenset({2}), caption="Status on 12 Nov 2026"),
        rich.expandable_quote(
            "Auditor note: rotation must be logged with the operator's id, the old key fingerprint, "
            "the new key fingerprint and the time. Logs are kept for one year.", credit="Audit 2026-10"),
        rich.document_block(spec_file_id, caption="Full procedure (PDF)"),
        {"type": "paragraph", "text": rich.inline_button_text(
            "Questions? ", rich.rich_button("Ask the owner", url="https://t.me/orders_demo_bot?start=ask_rotation", style="primary"))},
        rich.button_row([approve, rich.rich_button("Copy checklist id", copy_text="ROT-2026-v3")]),
    ]}


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    # 1) The PDF is uploaded once elsewhere; reuse its file_id. In Rich Markdown /
    #    HTML the same file would be referenced as tg://document?id=spec + media[].
    doc = build_document("BQACAgIAAxkBAAIBdemoFileId")
    msg = t.call("sendRichMessage", {"chat_id": CHAT, "rich_message": doc})
    # Markdown form of the same attachment (10.3 tg://document?id=):
    t.call("sendRichMessage", {"chat_id": CHAT, "rich_message": {
        "markdown": "## Attachments\n\n![](tg://document?id=spec \"Full procedure (PDF)\")",
        "media": [{"id": "spec", "media": {"type": "document", "media": "BQACAgIAAxkBAAIBdemoFileId"}}]}})

    # 2) A user replies quoting a fragment of the rich message: quote.text is "".
    upd = c.fixture("message_quote_rich.json")["message"]
    asked_about = rich.quote_text(upd["quote"])

    # 3) The bot answers, quoting the exact fragment back (10.4 quote_rich_texts).
    received = c.fixture("rich_message_received.json")["message"]["rich_message"]
    para = received["blocks"][1]["text"]
    fragment = rich.quote_from_paragraph(para, len("Rotate the "), len("Rotate the signing key"))
    t.call("sendMessage", {"chat_id": CHAT, "text": "Because a leaked key stops working within 90 days.",
                           "reply_parameters": {"message_id": 600, "quote_rich_texts": fragment}})

    # 4) "Approve" pressed: answer, then re-render with the button disabled.
    t.call("answerCallbackQuery", {"callback_query_id": "q-approve", "text": "Approved"})
    t.call("editMessageText", {"chat_id": CHAT, "message_id": msg["message_id"],
                               "rich_message": build_document("BQACAgIAAxkBAAIBdemoFileId", approved=True)})
    addresses = rich.find_ton_addresses(received["blocks"][0]["text"])
    return t, asked_about, fragment, addresses


def main() -> None:
    t, asked, fragment, addresses = run()
    c.dump(t, "Interactive document")
    doc = t.params_of("sendRichMessage")[0]["rich_message"]["blocks"]
    tbl = next(b for b in doc if b["type"] == "table")
    c.check(tbl.get("is_compact") is True and all(x.get("is_header") for x in tbl["cells"][0]),
            "compact table with real header cells")
    c.check(any(b["type"] == "expandable_blockquote" for b in doc), "long note collapsed by default")
    c.check(any(b["type"] == "document" and b["document"]["type"] == "document" for b in doc),
            "document block wraps an InputMediaDocument")
    c.check(asked == "Rotate the signing key every 90 days.", "quote read from rich_texts when text is empty")
    c.check(fragment == [{"type": "bold", "text": "signing key"}], "quoted fragment keeps its formatting")
    c.check(addresses == ["UQAsampleMerchant00000000000000000000000000000005"],
            "TON address read from RichTextTonAddress, not from the shortened text")
    edited = t.params_of("editMessageText")[0]["rich_message"]["blocks"][-1]["buttons"][0]
    c.check(edited == {"text": "Approved", "disabled": {}}, "approved button disabled, no action left")


if __name__ == "__main__":
    main()
