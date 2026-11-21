"""Addressing: which fields a reply needs depends on the context, not on habit.

Contexts that look alike and are addressed differently:
* forum supergroup topic     -> message_thread_id
* private chat with topics   -> message_thread_id (Message.is_topic_message)
                                 (bots with forum topic mode, Bot API 9.3/9.4)
* channel direct-messages    -> direct_messages_topic_id (from
  chat (chat.is_direct_messages)  Message.direct_messages_topic.topic_id);
                                 never message_thread_id; no ephemeral replies
                                 to callback queries there (10.4)
* business chat              -> business_connection_id
* drafts (sendMessageDraft / sendRichMessageDraft) take only chat_id (private)
  + message_thread_id; MessageGenerationStopped reports the same pair.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Address:
    chat_id: int
    chat_type: str
    message_thread_id: int | None = None
    direct_messages_topic_id: int | None = None
    business_connection_id: str | None = None

    @classmethod
    def of(cls, message: dict[str, Any]) -> "Address":
        chat = message["chat"]
        dm_topic = (message.get("direct_messages_topic") or {}).get("topic_id")
        thread = message.get("message_thread_id") if message.get("is_topic_message") else None
        if chat.get("is_direct_messages"):
            thread = None                    # DM topics use their own field
        return cls(chat_id=chat["id"], chat_type=chat["type"], message_thread_id=thread,
                   direct_messages_topic_id=dm_topic if chat.get("is_direct_messages") else None,
                   business_connection_id=message.get("business_connection_id"))

    def send_params(self) -> dict[str, Any]:
        p: dict[str, Any] = {"chat_id": self.chat_id}
        if self.message_thread_id:
            p["message_thread_id"] = self.message_thread_id
        if self.direct_messages_topic_id:
            p["direct_messages_topic_id"] = self.direct_messages_topic_id
        if self.business_connection_id:
            p["business_connection_id"] = self.business_connection_id
        return p

    def draft_params(self) -> dict[str, Any]:
        if self.chat_type != "private":
            raise ValueError("drafts stream to private chats only")
        p: dict[str, Any] = {"chat_id": self.chat_id}
        if self.message_thread_id:
            p["message_thread_id"] = self.message_thread_id
        return p

    @property
    def conversation_key(self) -> tuple[int, int, int]:
        """Isolation key for per-topic state (operations, forms, drafts)."""
        return (self.chat_id, self.message_thread_id or 0, self.direct_messages_topic_id or 0)


def private_topic_link(bot_username: str, message_thread_id: int) -> str:
    """Bot API 10.4: opens that topic only for the user whose private chat has it.
    Anyone else following the link gets nothing useful - don't share it publicly."""
    if not message_thread_id:
        raise ValueError("message_thread_id required")
    return f"https://t.me/{bot_username}/{message_thread_id}"
