"""R02 - Interactive document: compact table, expandable quote, attached document,
buttons inside rich content, and replying with a quote of a selected fragment.

Run:  py -3 examples/python/recipes/r02_interactive_document.py
"""
from __future__ import annotations

import _common as c
from tgkit import rich
from tgkit.transport import FakeTransport

CHAT = 111111111


STATUS = {"production": [["signing", "Platform", "12"], ["webhook", "Bots team", "48"], ["backup", "SRE", "85"]],
          "staging": [["signing", "Platform", "40"], ["webhook", "Bots team", "61"]]}
STEPS = [("gen", "Generate the new signing key"), ("deploy", "Deploy it next to the old one"),
         ("revoke", "Revoke the old key after 24 hours")]


def build_document(spec_file_id: str, *, view: str = "production", done: frozenset[str] = frozenset()) -> dict:
    """The document only holds what changes THIS message (references/rich-message-buttons.md): a view switch over
    the table it switches, and a "Done" link after each checklist step. Approve (the main action) is on the
    keyboard (`keyboard()`), the owner is a link in the sentence, the checklist id is <code> (tap to copy)."""
    switch = rich.button_row([rich.rich_button(name.title(), disabled=True) if name == view
                              else rich.rich_button(name.title(), callback_data=f"doc:view:{name}")
                              for name in ("production", "staging")])

    def step(sid: str, text: str) -> dict:
        if sid in done:
            line = [f"✓ {text} · ", rich.button(rich.rich_button("Undo", callback_data=f"doc:undo:{sid}", style="link"))]
        else:
            line = rich.inline_button_text(f"{text} · ", rich.rich_button("Done", callback_data=f"doc:done:{sid}", style="link"))
        return {"blocks": [{"type": "paragraph", "text": line}]}

    return {"blocks": [
        {"type": "heading", "size": 2, "text": "Key rotation policy v3"},
        {"type": "paragraph", "text": ["Rotate the ", {"type": "bold", "text": "signing key"}, " every 90 days. Questions: ",
                                       rich.url("the key owner", "https://t.me/orders_demo_bot?start=ask_rotation"),
                                       ". Checklist id ", rich.code("ROT-2026-v3"), "."]},
        switch,  # a view switch sits right above the block it switches; the current view is disabled
        rich.table(["Key", "Owner", "Days left"], STATUS[view],
                   compact=True, numeric_cols=frozenset({2}), caption=f"{view.title()} on 12 Nov 2026"),
        {"type": "heading", "size": 3, "text": f"Rotation steps · {len(done)} of {len(STEPS)}"},
        {"type": "list", "items": [step(sid, text) for sid, text in STEPS]},
        # 10.5: an expandable quote holds blocks, so the auditor's checklist stays a real list.
        rich.expandable_quote(blocks=[
            {"type": "paragraph", "text": "Auditor note: every rotation is logged with"},
            {"type": "list", "items": [{"blocks": [{"type": "paragraph", "text": item}]} for item in (
                "the operator's id", "the old and the new key fingerprint", "the time")]},
            {"type": "paragraph", "text": "Logs are kept for one year."}], credit="Audit 2026-10"),
        rich.document_block(spec_file_id, caption="Full procedure (PDF)"),
    ]}


def keyboard(approved: bool = False) -> dict:
    """The main action stays on the keyboard; once taken it becomes a disabled status there."""
    return {"inline_keyboard": [[{"text": "Approved", "disabled": {}} if approved
                                 else {"text": "Approve policy", "callback_data": "doc:approve:v3", "style": "success"}]]}


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    # 1) The PDF is uploaded once elsewhere; reuse its file_id. In Rich Markdown /
    #    HTML the same file would be referenced as tg://document?id=spec + media[].
    doc = build_document("BQACAgIAAxkBAAIBdemoFileId")
    msg = t.call("sendRichMessage", {"chat_id": CHAT, "rich_message": doc, "reply_markup": keyboard()})
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

    # 4) A document button: "Done" after step 1 re-renders this message (the whole document; the keyboard is
    #    repeated as it was). Then the view switch: the table shows staging, the switch marks it current.
    t.call("answerCallbackQuery", {"callback_query_id": "q-done"})
    t.call("editMessageText", {"chat_id": CHAT, "message_id": msg["message_id"], "reply_markup": keyboard(),
                               "rich_message": build_document("BQACAgIAAxkBAAIBdemoFileId", done=frozenset({"gen"}))})
    t.call("answerCallbackQuery", {"callback_query_id": "q-view"})
    t.call("editMessageText", {"chat_id": CHAT, "message_id": msg["message_id"], "reply_markup": keyboard(),
                               "rich_message": build_document("BQACAgIAAxkBAAIBdemoFileId", view="staging",
                                                              done=frozenset({"gen"}))})
    # 5) "Approve policy" on the keyboard: answer, then only the keyboard changes (no document re-render).
    t.call("answerCallbackQuery", {"callback_query_id": "q-approve", "text": "Approved"})
    t.call("editMessageReplyMarkup", {"chat_id": CHAT, "message_id": msg["message_id"], "reply_markup": keyboard(approved=True)})
    addresses = rich.find_ton_addresses(received["blocks"][0]["text"])
    return t, asked_about, fragment, addresses


def main() -> None:
    t, asked, fragment, addresses = run()
    c.dump(t, "Interactive document")
    doc = t.params_of("sendRichMessage")[0]["rich_message"]["blocks"]
    tbl = next(b for b in doc if b["type"] == "table")
    c.check(tbl.get("is_compact") is True and all(x.get("is_header") for x in tbl["cells"][0]),
            "compact table with real header cells")
    quote = next(b for b in doc if b["type"] == "expandable_blockquote")
    c.check("text" not in quote and [b["type"] for b in quote["blocks"]] == ["paragraph", "list", "paragraph"],
            "long note collapsed by default; 10.5 quote holds blocks (a real list), not text")
    c.check(any(b["type"] == "document" and b["document"]["type"] == "document" for b in doc),
            "document block wraps an InputMediaDocument")
    c.check(asked == "Rotate the signing key every 90 days.", "quote read from rich_texts when text is empty")
    c.check(fragment == [{"type": "bold", "text": "signing key"}], "quoted fragment keeps its formatting")
    c.check(addresses == ["UQAsampleMerchant00000000000000000000000000000005"],
            "TON address read from RichTextTonAddress, not from the shortened text")
    first, second = (p["rich_message"]["blocks"] for p in t.params_of("editMessageText"))
    steps = next(b for b in first if b["type"] == "list")["items"]
    c.check(steps[0]["blocks"][0]["text"][1]["button"]["callback_data"] == "doc:undo:gen"
            and steps[1]["blocks"][0]["text"][1]["button"]["style"] == "link",
            "a document button changes its own step in place: Done -> ✓ and Undo, quiet link style")
    c.check(next(b for b in second if b["type"] == "buttons")["buttons"][1] == {"text": "Staging", "disabled": {}},
            "the view switch marks the current view, right above the table it switches")
    c.check(t.params_of("editMessageReplyMarkup")[0]["reply_markup"]["inline_keyboard"] == [[{"text": "Approved", "disabled": {}}]]
            and not any(b.get("style") in ("primary", "success", "danger")
                        for b in rich_buttons(doc)), "the main action is on the keyboard; no filled button in the document")


def rich_buttons(blocks) -> list[dict]:
    out: list[dict] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            if node.get("type") == "buttons":
                out.extend(node["buttons"])
            if node.get("type") == "button":
                out.append(node["button"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(blocks)
    return out


if __name__ == "__main__":
    main()
