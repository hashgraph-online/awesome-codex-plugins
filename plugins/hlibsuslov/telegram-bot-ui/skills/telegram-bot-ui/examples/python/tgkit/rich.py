"""Rich-message builders and readers.

Input side: one builder per InputRichBlock* member, per RichText* member and per
object those hold (list item, table cell, block caption, button), so a rich
message can be sent as `InputRichMessage.blocks` without HTML or escaping.
Parameter names are the catalog field names and a parameter without a default is
a required field; tests/test_rich_blocks.py compares both with
data/bot-api/catalog.json. Builders return plain dicts and leave limits to
scripts/validate_rich.py. RichText is shared by sent and received messages (the
catalog has no InputRichText), so the RichText* builders serve both.

Conveniences: compact tables, expandable quotations, document blocks, button rows.
Output side (RichText / TextQuote): flattening rich texts, reading TON addresses,
building quote_rich_texts for a reply.
"""
from __future__ import annotations

import functools
from typing import Any, Callable

RichText = Any  # str | list | dict - the Bot API RichText union
Block = dict[str, Any]

# Rich Message Limits (Bot API, "Rich Message Limits", verified 2026-11-12).
LIMITS = {"chars": 32768, "blocks": 500, "depth": 16, "media": 50, "table_columns": 20}
BUTTON_ROW_MAX = 8      # InputRichBlockButtons.buttons: 1-8
QUOTE_MAX_TEXTS = 32
QUOTE_MAX_CHARS = 1024
BUTTON_ACTIONS = ("url", "callback_data", "web_app", "login_url", "switch_inline_query",
                  "switch_inline_query_current_chat", "switch_inline_query_chosen_chat", "copy_text", "disabled")


def _renamed(**aliases: str) -> Callable[[Callable[..., Block]], Callable[..., Block]]:
    """Accept an old keyword (old=new) for a builder whose parameters now mirror the catalog. The
    signature stays the catalog's (inspect follows __wrapped__); passing both names is a TypeError."""
    def wrap(fn: Callable[..., Block]) -> Callable[..., Block]:
        @functools.wraps(fn)
        def builder(*args: Any, **kwargs: Any) -> Block:
            for old, new in aliases.items():
                if old in kwargs:
                    if new in kwargs or args:
                        raise TypeError(f"{fn.__name__}() got both {old!r} (old name) and {new!r}")
                    kwargs[new] = kwargs.pop(old)
            return fn(*args, **kwargs)
        return builder
    return wrap


def _obj(type_: str | None, **fields: Any) -> dict[str, Any]:
    """A Bot API object: the `type` constant first, then the given fields. None and False are left out
    (the flags here are of type True: "omit the field for false")."""
    out: dict[str, Any] = {"type": type_} if type_ else {}
    out.update({k: v for k, v in fields.items() if v is not None and v is not False})
    return out


def _media(kind: str, value: str | dict[str, Any]) -> dict[str, Any]:
    """InputMedia* from a file_id, an HTTP URL or attach://<name>; an InputMedia object is kept as is."""
    return {"type": kind, "media": value} if isinstance(value, str) else value


def _caption(value: RichText | dict[str, Any] | None) -> dict[str, Any] | None:
    """RichBlockCaption from RichText; a RichBlockCaption ({"text", "credit"?}, no "type") is kept."""
    if value is None or (isinstance(value, dict) and "type" not in value):
        return value
    return {"text": value}


# ---- InputRichBlock* -----------------------------------------------------------

def paragraph_block(text: RichText) -> Block:
    return _obj("paragraph", text=text)


def heading_block(text: RichText, size: int) -> Block:
    """size 1-6, 1 is the largest (<h1>-<h6>)."""
    return _obj("heading", text=text, size=size)


def pre_block(text: RichText, language: str | None = None) -> Block:
    return _obj("pre", text=text, language=language)


def footer_block(text: RichText) -> Block:
    return _obj("footer", text=text)


def divider_block() -> Block:
    return _obj("divider")


def mathematical_expression_block(expression: str) -> Block:
    """LaTeX source (<tg-math-block>)."""
    return _obj("mathematical_expression", expression=expression)


def anchor_block(name: str) -> Block:
    return _obj("anchor", name=name)


def list_block(items: list[dict[str, Any]]) -> Block:
    """items: list_item(...) objects."""
    return _obj("list", items=items)


def blockquote_block(blocks: list[Block], credit: RichText | None = None) -> Block:
    return _obj("blockquote", blocks=blocks, credit=credit)


def expandable_blockquote_block(blocks: list[Block], credit: RichText | None = None) -> Block:
    return _obj("expandable_blockquote", blocks=blocks, credit=credit)


def pullquote_block(text: RichText, credit: RichText | None = None) -> Block:
    return _obj("pullquote", text=text, credit=credit)


def collage_block(blocks: list[Block], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("collage", blocks=blocks, caption=_caption(caption))


def slideshow_block(blocks: list[Block], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("slideshow", blocks=blocks, caption=_caption(caption))


def table_block(cells: list[list[dict[str, Any]]], *, is_bordered: bool | None = None,
                is_striped: bool | None = None, is_compact: bool | None = None,
                caption: RichText | None = None) -> Block:
    """cells: rows of table_cell(...). The caption is RichText here, not a RichBlockCaption."""
    return _obj("table", cells=cells, is_bordered=is_bordered, is_striped=is_striped, is_compact=is_compact,
                caption=caption)


def details_block(summary: RichText, blocks: list[Block], *, is_open: bool | None = None) -> Block:
    return _obj("details", summary=summary, blocks=blocks, is_open=is_open)


def map_block(location: dict[str, float], *, zoom: int | None = None, width: int | None = None,
              height: int | None = None, caption: RichText | dict[str, Any] | None = None) -> Block:
    """location: {"latitude", "longitude"}."""
    return _obj("map", location=location, zoom=zoom, width=width, height=height, caption=_caption(caption))


def buttons_block(buttons: list[dict[str, Any]], align: str | None = None) -> Block:
    """buttons: 1-8 message_button(...) shown in one row."""
    return _obj("buttons", buttons=buttons, align=align)


def animation_block(animation: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("animation", animation=_media("animation", animation), caption=_caption(caption))


def audio_block(audio: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("audio", audio=_media("audio", audio), caption=_caption(caption))


@_renamed(file_ref="document")  # the pre-catalog name, kept for existing callers
def document_block(document: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    """document: a file_id (preferred), an HTTP URL, or attach://<name>.
    Not allowed in sendRichMessageDraft for new uploads or explicit URLs."""
    return _obj("document", document=_media("document", document), caption=_caption(caption))


def photo_block(photo: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("photo", photo=_media("photo", photo), caption=_caption(caption))


def video_block(video: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("video", video=_media("video", video), caption=_caption(caption))


def voice_note_block(voice_note: str | dict[str, Any], caption: RichText | dict[str, Any] | None = None) -> Block:
    return _obj("voice_note", voice_note=_media("voice_note", voice_note), caption=_caption(caption))


def thinking_block(text: RichText) -> Block:
    """sendRichMessageDraft only: a stage label such as "Reading the report", never model reasoning."""
    return _obj("thinking", text=text)


# ---- objects the blocks hold -----------------------------------------------------

def list_item(blocks: list[Block], *, has_checkbox: bool | None = None, is_checked: bool | None = None,
              value: int | None = None, type: str | None = None) -> dict[str, Any]:  # noqa: A002 - the field name
    """InputRichBlockListItem. `type` is the ordered-list label: a, A, i, I or 1."""
    return _obj(None, blocks=blocks, has_checkbox=has_checkbox, is_checked=is_checked, value=value, type=type)


def table_cell(text: RichText | None = None, *, align: str, valign: str, is_header: bool | None = None,
               colspan: int | None = None, rowspan: int | None = None) -> dict[str, Any]:
    """RichBlockTableCell. No text: an invisible cell."""
    return _obj(None, text=text, align=align, valign=valign, is_header=is_header, colspan=colspan, rowspan=rowspan)


def block_caption(text: RichText, credit: RichText | None = None) -> dict[str, Any]:
    """RichBlockCaption of a media, map, collage or slideshow block; credit is the <cite>."""
    return _obj(None, text=text, credit=credit)


def message_button(text: RichText, *, style: str | None = None, url: str | None = None,
                   callback_data: str | None = None, web_app: dict[str, Any] | None = None,
                   login_url: dict[str, Any] | None = None, switch_inline_query: str | None = None,
                   switch_inline_query_current_chat: str | None = None,
                   switch_inline_query_chosen_chat: dict[str, Any] | None = None,
                   copy_text: str | dict[str, Any] | None = None,
                   disabled: bool | dict[str, Any] | None = None) -> dict[str, Any]:
    """RichMessageButton with exactly one action. copy_text may be the text to copy; disabled=True
    writes the empty DisabledButton. An empty switch_inline_query* string is a valid action."""
    if isinstance(copy_text, str):
        copy_text = {"text": copy_text}
    if isinstance(disabled, bool):
        disabled = {} if disabled else None
    actions = {"url": url, "callback_data": callback_data, "web_app": web_app, "login_url": login_url,
               "switch_inline_query": switch_inline_query,
               "switch_inline_query_current_chat": switch_inline_query_current_chat,
               "switch_inline_query_chosen_chat": switch_inline_query_chosen_chat, "copy_text": copy_text,
               "disabled": disabled}
    chosen = {k: v for k, v in actions.items() if v is not None}
    if len(chosen) != 1:
        raise ValueError(f"a RichMessageButton needs exactly one action, got {sorted(chosen) or 'none'}")
    if style == "link" and callback_data is None:
        raise ValueError('style "link" is allowed only for callback buttons')
    out: dict[str, Any] = {"text": text, **chosen}
    if style:
        out["style"] = style
    return out


# ---- RichText* -------------------------------------------------------------------

def bold(text: RichText) -> dict[str, Any]:
    return _obj("bold", text=text)


def italic(text: RichText) -> dict[str, Any]:
    return _obj("italic", text=text)


def underline(text: RichText) -> dict[str, Any]:
    return _obj("underline", text=text)


def strikethrough(text: RichText) -> dict[str, Any]:
    return _obj("strikethrough", text=text)


def spoiler(text: RichText) -> dict[str, Any]:
    return _obj("spoiler", text=text)


def date_time(text: RichText, unix_time: int, date_time_format: str) -> dict[str, Any]:
    """date_time_format: see "date-time entity formatting" on the Bot API page."""
    return _obj("date_time", text=text, unix_time=unix_time, date_time_format=date_time_format)


def text_mention(text: RichText, user: dict[str, Any]) -> dict[str, Any]:
    """user: a User object ({"id", "is_bot", "first_name"} at least)."""
    return _obj("text_mention", text=text, user=user)


def subscript(text: RichText) -> dict[str, Any]:
    return _obj("subscript", text=text)


def superscript(text: RichText) -> dict[str, Any]:
    return _obj("superscript", text=text)


def marked(text: RichText) -> dict[str, Any]:
    return _obj("marked", text=text)


def code(text: RichText) -> dict[str, Any]:
    return _obj("code", text=text)


def custom_emoji(custom_emoji_id: str, alternative_text: str) -> dict[str, Any]:
    return _obj("custom_emoji", custom_emoji_id=custom_emoji_id, alternative_text=alternative_text)


def mathematical_expression(expression: str) -> dict[str, Any]:
    """Inline LaTeX (<tg-math>)."""
    return _obj("mathematical_expression", expression=expression)


def url(text: RichText, url: str) -> dict[str, Any]:
    return _obj("url", text=text, url=url)


def email_address(text: RichText, email_address: str) -> dict[str, Any]:
    return _obj("email_address", text=text, email_address=email_address)


def phone_number(text: RichText, phone_number: str) -> dict[str, Any]:
    return _obj("phone_number", text=text, phone_number=phone_number)


def bank_card_number(text: RichText, bank_card_number: str) -> dict[str, Any]:
    return _obj("bank_card_number", text=text, bank_card_number=bank_card_number)


def ton_address(text: RichText, address: str) -> dict[str, Any]:
    return _obj("ton_address", text=text, address=address)


def mention(text: RichText, username: str) -> dict[str, Any]:
    return _obj("mention", text=text, username=username)


def hashtag(text: RichText, hashtag: str) -> dict[str, Any]:
    return _obj("hashtag", text=text, hashtag=hashtag)


def cashtag(text: RichText, cashtag: str) -> dict[str, Any]:
    return _obj("cashtag", text=text, cashtag=cashtag)


def bot_command(text: RichText, bot_command: str) -> dict[str, Any]:
    return _obj("bot_command", text=text, bot_command=bot_command)


def button(button: dict[str, Any]) -> dict[str, Any]:
    """RichTextButton: a message_button(...) inside a text."""
    return _obj("button", button=button)


def anchor(name: str) -> dict[str, Any]:
    return _obj("anchor", name=name)


def anchor_link(text: RichText, anchor_name: str) -> dict[str, Any]:
    """An empty anchor_name links back to the top of the message."""
    return _obj("anchor_link", text=text, anchor_name=anchor_name)


def reference(text: RichText, name: str) -> dict[str, Any]:
    return _obj("reference", text=text, name=name)


def reference_link(text: RichText, reference_name: str) -> dict[str, Any]:
    return _obj("reference_link", text=text, reference_name=reference_name)


# Catalog type -> builder (tests/test_rich_blocks.py: every member has one, with the catalog's fields).
BLOCKS = {
    "InputRichBlockParagraph": paragraph_block, "InputRichBlockSectionHeading": heading_block,
    "InputRichBlockPreformatted": pre_block, "InputRichBlockFooter": footer_block,
    "InputRichBlockDivider": divider_block, "InputRichBlockMathematicalExpression": mathematical_expression_block,
    "InputRichBlockAnchor": anchor_block, "InputRichBlockList": list_block,
    "InputRichBlockBlockQuotation": blockquote_block,
    "InputRichBlockExpandableBlockQuotation": expandable_blockquote_block,
    "InputRichBlockPullQuotation": pullquote_block, "InputRichBlockCollage": collage_block,
    "InputRichBlockSlideshow": slideshow_block, "InputRichBlockTable": table_block,
    "InputRichBlockDetails": details_block, "InputRichBlockMap": map_block, "InputRichBlockButtons": buttons_block,
    "InputRichBlockAnimation": animation_block, "InputRichBlockAudio": audio_block,
    "InputRichBlockDocument": document_block, "InputRichBlockPhoto": photo_block, "InputRichBlockVideo": video_block,
    "InputRichBlockVoiceNote": voice_note_block, "InputRichBlockThinking": thinking_block,
}
PARTS = {"InputRichBlockListItem": list_item, "RichBlockTableCell": table_cell, "RichBlockCaption": block_caption,
         "RichMessageButton": message_button}
TEXTS = {
    "RichTextBold": bold, "RichTextItalic": italic, "RichTextUnderline": underline,
    "RichTextStrikethrough": strikethrough, "RichTextSpoiler": spoiler, "RichTextDateTime": date_time,
    "RichTextTextMention": text_mention, "RichTextSubscript": subscript, "RichTextSuperscript": superscript,
    "RichTextMarked": marked, "RichTextCode": code, "RichTextCustomEmoji": custom_emoji,
    "RichTextMathematicalExpression": mathematical_expression, "RichTextUrl": url,
    "RichTextEmailAddress": email_address, "RichTextPhoneNumber": phone_number,
    "RichTextBankCardNumber": bank_card_number, "RichTextTonAddress": ton_address, "RichTextMention": mention,
    "RichTextHashtag": hashtag, "RichTextCashtag": cashtag, "RichTextBotCommand": bot_command,
    "RichTextButton": button, "RichTextAnchor": anchor, "RichTextAnchorLink": anchor_link,
    "RichTextReference": reference, "RichTextReferenceLink": reference_link,
}


# ---- conveniences ----------------------------------------------------------------

def cell(text: RichText, *, header: bool = False, align: str = "left", valign: str = "middle") -> dict[str, Any]:
    return table_cell(text, align=align, valign=valign, is_header=header)


def table(header: list[str], rows: list[list[RichText]], *, compact: bool = False,
          numeric_cols: frozenset[int] = frozenset(), caption: RichText | None = None) -> dict[str, Any]:
    """A bordered table with a header row; numeric columns align right. compact (10.3): smaller
    cell indents for dense data on phones."""
    cells = [[cell(h, header=True, align="right" if i in numeric_cols else "left") for i, h in enumerate(header)]]
    for r in rows:
        cells.append([cell(v, align="right" if i in numeric_cols else "left") for i, v in enumerate(r)])
    return table_block(cells, is_bordered=True, is_compact=compact, caption=caption)


def expandable_quote(text: RichText | None = None, credit: RichText | None = None, *,
                     blocks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Collapsed quote. Since Bot API 10.5 it holds `blocks` (paragraphs, lists,
    tables, code...) instead of `text`; a plain `text` becomes one paragraph."""
    if (text is None) == (blocks is None):
        raise ValueError("pass either text or blocks")
    return expandable_blockquote_block(blocks if blocks is not None else [paragraph_block(text)], credit)


def rich_button(text: RichText, *, callback_data: str | None = None, url: str | None = None,
                copy_text: str | None = None, disabled: bool = False, style: str | None = None) -> dict[str, Any]:
    return message_button(text, callback_data=callback_data, url=url, copy_text=copy_text,
                          disabled=True if disabled else None, style=style)


def button_row(buttons: list[dict[str, Any]], align: str = "left") -> dict[str, Any]:
    if not 1 <= len(buttons) <= BUTTON_ROW_MAX:
        raise ValueError("InputRichBlockButtons takes 1-8 buttons")
    return buttons_block(buttons, align)


def inline_button_text(rich_text: RichText, button: dict[str, Any]) -> list[RichText]:
    """RichTextButton: a button inside a paragraph."""
    return [rich_text, {"type": "button", "button": button}]


# ---- reading ---------------------------------------------------------------

def plain(rt: RichText) -> str:
    if rt is None:
        return ""
    if isinstance(rt, str):
        return rt
    if isinstance(rt, list):
        return "".join(plain(x) for x in rt)
    if rt.get("type") == "button":
        return ""                     # buttons are not quotable text
    return plain(rt.get("text"))


def find_ton_addresses(rt: RichText) -> list[str]:
    """RichTextTonAddress (10.4) nodes -> addresses (shown text may be shortened)."""
    if isinstance(rt, list):
        return [a for x in rt for a in find_ton_addresses(x)]
    if isinstance(rt, dict):
        if rt.get("type") == "ton_address":
            return [rt["address"]]
        return find_ton_addresses(rt.get("text"))
    return []


def quote_text(quote: dict[str, Any]) -> str:
    """TextQuote -> plain text. Since 10.4 `text` may be EMPTY for a quote from a
    rich message; the content is in `rich_texts`. Code that reads only
    quote["text"] silently loses it."""
    if quote.get("text"):
        return quote["text"]
    return "\n".join(plain(rt) for rt in quote.get("rich_texts") or [])


def slice_rich(rt: RichText, start: int, end: int) -> RichText:
    """Characters [start, end) of a RichText, keeping nested formatting."""
    out, _ = _slice(rt, start, end, 0)
    return out


def _slice(rt: RichText, start: int, end: int, pos: int):
    if isinstance(rt, str):
        s, e = max(start - pos, 0), min(end - pos, len(rt))
        return (rt[s:e] if s < e else None), pos + len(rt)
    if isinstance(rt, list):
        items = []
        for x in rt:
            part, pos = _slice(x, start, end, pos)
            if part not in (None, "", []):
                items.append(part)
        return (items[0] if len(items) == 1 else items or None), pos
    inner, newpos = _slice(rt.get("text"), start, end, pos)
    return ({**rt, "text": inner} if inner not in (None, "", []) else None), newpos


def quote_from_paragraph(paragraph_text: RichText, start: int, end: int) -> list[RichText]:
    """quote_rich_texts for a quote inside ONE quotable text (a paragraph):
    a single element, possibly partial. Spanning several quotable texts needs
    one element per text, whole except the first and last."""
    part = slice_rich(paragraph_text, start, end)
    if not plain(part) or len(plain(part)) > QUOTE_MAX_CHARS:
        raise ValueError("quote must be 1-1024 characters")
    return [part]
