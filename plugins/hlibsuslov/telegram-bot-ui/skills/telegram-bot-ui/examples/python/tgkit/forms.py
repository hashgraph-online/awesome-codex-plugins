"""Multi-step forms with force_reply on keyboards and disabled buttons (Bot API 10.3).

Three different things, kept apart:
* `ForceReply` object (old): reply_markup = {"force_reply": true, ...}. Shows the
  reply UI, but then the message has NO keyboard.
* `InlineKeyboardMarkup.force_reply` (10.3): an inline keyboard AND the reply UI.
  "The value of the field can't be changed when the inline keyboard is edited" -
  decide it when the message is sent.
* `ReplyKeyboardMarkup.force_reply` (10.3): a reply keyboard AND the reply UI.

`DisabledButton` (10.3): InlineKeyboardButton.disabled = {} is the button's ONLY
action field ("does nothing"). It shows state; it never replaces the server-side
check - a stale message or a crafted callback can still arrive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import TelegramError


def button(text: str, data: str | None = None, *, disabled: bool = False,
           style: str | None = None) -> dict[str, Any]:
    b: dict[str, Any] = {"text": text}
    if disabled:
        b["disabled"] = {}            # an object, and the only action field
    else:
        b["callback_data"] = data
    if style:
        b["style"] = style
    return b


def retired(label: str) -> dict[str, Any]:
    """Markup for an edited step message. The message was sent with
    force_reply: true and the field "can't be changed when the inline keyboard
    is edited" - so every edit repeats it (whether omitting it counts as a
    change is not documented; repeating it is safe either way)."""
    return {"inline_keyboard": [[button(label, disabled=True)]], "force_reply": True}


@dataclass
class Step:
    key: str
    prompt: str
    validate: Callable[[str], str | None]   # -> error text or None
    options: list[str] = field(default_factory=list)


@dataclass
class FormSession:
    form_id: str
    user_id: int
    chat_id: int
    steps: list[Step]
    index: int = 0
    answers: dict[str, str] = field(default_factory=dict)
    prompt_message_id: int | None = None
    submitted: bool = False
    submission_id: str | None = None

    @property
    def step(self) -> Step:
        return self.steps[self.index]


class FormRunner:
    """One message per step, force_reply on the inline keyboard so the user can
    type an answer or tap an option. Back / Cancel keep what was typed."""

    def __init__(self, transport: Any, submit: Callable[[FormSession], str]):
        self.transport = transport
        self.submit_fn = submit
        self.sessions: dict[tuple[int, int], FormSession] = {}
        self.submissions: dict[str, str] = {}   # idempotency: form_id -> result id

    def keyboard(self, s: FormSession) -> dict[str, Any]:
        rows = [[button(o, f"f:{s.form_id}:{s.index}:o:{i}")] for i, o in enumerate(s.step.options)]
        nav = []
        if s.index > 0:
            nav.append(button("← Back", f"f:{s.form_id}:{s.index}:back"))
        nav.append(button("Cancel", f"f:{s.form_id}:{s.index}:cancel"))
        rows.append(nav)
        last = s.index == len(s.steps) - 1
        complete = all(st.key in s.answers for st in s.steps)
        if last:
            # Visible but inert until every answer is valid.
            rows.append([button("Submit", f"f:{s.form_id}:submit", disabled=not complete,
                                style="success" if complete else None)])
        return {"inline_keyboard": rows, "force_reply": True}

    def _text(self, s: FormSession, error: str | None = None) -> str:
        current = s.answers.get(s.step.key)
        lines = [f"Step {s.index + 1} of {len(s.steps)}", s.step.prompt]
        if current:
            lines.append(f"Current answer: {current}")
        if error:
            lines.append(f"⚠ {error}")
        return "\n".join(lines)

    def start(self, s: FormSession) -> None:
        self.sessions[(s.chat_id, s.user_id)] = s
        self._render_new(s)

    def _render_new(self, s: FormSession, error: str | None = None) -> None:
        # force_reply can't be toggled by an edit, and the reply UI targets the
        # newest prompt - so each step is a new message.
        msg = self.transport.call("sendMessage", {"chat_id": s.chat_id, "text": self._text(s, error),
                                                  "reply_markup": self.keyboard(s)})
        old = s.prompt_message_id
        s.prompt_message_id = msg["message_id"]
        if old:
            # Retire the previous step's buttons: keep the text, disable actions.
            try:
                self.transport.call("editMessageReplyMarkup", {
                    "chat_id": s.chat_id, "message_id": old,
                    "reply_markup": retired("Answered")})
            except TelegramError:
                pass                    # too old / deleted: the server check still protects us

    def on_text(self, chat_id: int, user_id: int, text: str, reply_to: int | None) -> str:
        s = self.sessions.get((chat_id, user_id))
        if s is None or s.submitted:
            return "no_form"
        if reply_to is not None and reply_to != s.prompt_message_id:
            return "stale_reply"        # replied to an old step's message
        return self._accept(s, text)

    def _accept(self, s: FormSession, value: str) -> str:
        error = s.step.validate(value)
        if error:
            self._render_new(s, error)  # keep the step; tell what's wrong
            return "invalid"
        s.answers[s.step.key] = value
        if s.index < len(s.steps) - 1:
            s.index += 1
        self._render_new(s)
        return "accepted"

    def on_callback(self, cq: dict[str, Any]) -> str:
        user_id = cq["from"]["id"]
        chat_id = cq["message"]["chat"]["id"]
        s = self.sessions.get((chat_id, user_id))
        parts = cq.get("data", "").split(":")
        ack = {"callback_query_id": cq["id"]}
        if s is None or len(parts) < 3 or parts[1] != s.form_id:
            self.transport.call("answerCallbackQuery", {**ack, "text": "This form is closed."})
            return "stale"
        if parts[2] == "submit":
            return self._submit(s, ack)
        if int(parts[2]) != s.index or cq["message"]["message_id"] != s.prompt_message_id:
            self.transport.call("answerCallbackQuery", {**ack, "text": "That step is already answered."})
            return "stale"
        verb = parts[3]
        self.transport.call("answerCallbackQuery", ack)
        if verb == "back":
            s.index -= 1
            self._render_new(s)
            return "back"
        if verb == "cancel":
            del self.sessions[(chat_id, user_id)]
            self.transport.call("editMessageText", {"chat_id": chat_id, "message_id": s.prompt_message_id,
                                                    "text": "Form cancelled. Nothing was sent.",
                                                    "reply_markup": retired("Cancelled")})
            return "cancelled"
        return self._accept(s, s.step.options[int(parts[4])])

    def _submit(self, s: FormSession, ack: dict[str, Any]) -> str:
        if s.form_id in self.submissions:          # double tap / retried update
            self.transport.call("answerCallbackQuery", {**ack, "text": "Already sent."})
            return "duplicate"
        if not all(st.key in s.answers for st in s.steps):  # disabled button bypassed
            self.transport.call("answerCallbackQuery", {**ack, "text": "Some answers are missing."})
            return "incomplete"
        result = self.submit_fn(s)                 # must itself be idempotent by form_id
        self.submissions[s.form_id] = result
        s.submitted = True
        self.transport.call("answerCallbackQuery", ack)
        self.transport.call("editMessageText", {"chat_id": s.chat_id, "message_id": s.prompt_message_id,
                                                "text": f"Sent. Reference: {result}",
                                                "reply_markup": retired("Sent")})
        return "submitted"
