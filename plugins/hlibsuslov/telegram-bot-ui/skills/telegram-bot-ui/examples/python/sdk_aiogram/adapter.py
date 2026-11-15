"""aiogram 3.31.0 (Bot API 10.3) adapter for Bot API 10.4 widgets.

Verified locally on 2026-11-12 against aiogram 3.31.0 from PyPI:
* `Update` keeps unknown keys (pydantic extra="allow"), so `widget_query` is in
  `update.model_extra` - but `update.event_type` raises UpdateTypeLookupError and
  `Dispatcher.feed_update` only warns "Detected unknown update type" and drops it.
* `Dispatcher.resolve_used_update_types()` (used by start_polling when
  allowed_updates is not passed) can't include widget_query: there is no
  observer for it. The widget then times out on the user's screen.
* There are no SendWidget / AnswerWidgetQuery method classes.

This adapter (1) routes widget_query / shared_widget_query before aiogram's own
routing, (2) adds both to allowed_updates, (3) defines the 10.4 methods as
aiogram TelegramMethod subclasses so they go through the bot's session.

REMOVE WHEN: the lockfile has an aiogram release that implements Bot API 10.4
(check `aiogram.__api_version__ >= "10.4"`); then use its native handlers.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import Dispatcher
from aiogram.methods.base import TelegramMethod
from aiogram.types import Message, Update

WIDGET_UPDATES = ("widget_query", "shared_widget_query")
RawHandler = Callable[[str, dict[str, Any]], Awaitable[Any]]


class WidgetAwareDispatcher(Dispatcher):
    def __init__(self, *args: Any, widget_handler: RawHandler, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._widget_handler = widget_handler

    async def _listen_update(self, update: Update, **kwargs: Any) -> Any:
        # Called by feed_update AFTER the update-level outer/inner middlewares
        # (allowlists, rate limits, logging), so widget queries pass the same gates
        # as every other update. Overriding feed_update instead would bypass them.
        extra = update.model_extra or {}
        for kind in WIDGET_UPDATES:
            if kind in extra:
                return await self._widget_handler(kind, extra[kind])   # raw dict, as on the wire
        return await super()._listen_update(update, **kwargs)

    def resolve_used_update_types(self, skip_events=None) -> list[str]:
        return sorted(set(super().resolve_used_update_types(skip_events)) | set(WIDGET_UPDATES))


class SendWidget(TelegramMethod[Message]):
    __returning__ = Message
    __api_method__ = "sendWidget"

    chat_id: int | str
    html: str
    message_thread_id: int | None = None
    width: int | None = None
    height: int | None = None
    public_data: str | None = None
    chat_data: str | None = None
    caption: str | None = None
    parse_mode: str | None = None
    allow_queries: bool | None = None
    is_shared: bool | None = None
    reply_markup: Any = None


class AnswerWidgetQuery(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "answerWidgetQuery"

    widget_query_id: str
    data: str | None = None


class EditMessageWidgetData(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "editMessageWidgetData"

    chat_id: int | str | None = None
    message_id: int | None = None
    inline_message_id: str | None = None
    public_data: str | None = None
    chat_data: str | None = None
