"""AgentBridge: the operations an agent performs through its Telegram bot.

Every outgoing call goes through `call()`: secrets redacted, per-chat pacing,
the shared retry policy (tgkit.errors.call_with_policy: honours retry_after,
never blindly repeats a send whose outcome is unknown). Every incoming update
goes through intake.Intake -> security.classify: strangers are dropped, text
is data, decisions only arrive through bound buttons (approvals.py).

Blocking operations (`ask`, `approve`) poll for updates until an answer, a
decision or the deadline. Offline, the clock is virtual (VirtualClock) and the
updates come from fixtures, so a 15-minute timeout takes microseconds.
"""
from __future__ import annotations

import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from tgkit.errors import OutcomeUnknown, TelegramError, call_with_policy
from tgkit.generation import Generation, GenerationConfig, execute
from tgkit.rich import LIMITS, table
from tgkit.text import escape_html, split_text

from .approvals import ApprovalBook, IdFactory, Resolution
from .intake import FixtureSource, Intake
from .redact import Redactor
from .security import Allowlist, injection_signals
from .store import JsonStore
from .transport import UPLOAD_LIMIT, file_meta, read_file

# Files that hold credentials by convention; refused even when the content scan is skipped.
SECRET_FILE_NAMES = re.compile(
    r"(?i)^(\.env(\..*)?|.*\.pem|.*\.key|.*\.p12|.*\.pfx|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?|"
    r"\.netrc|\.npmrc|\.pypirc|credentials(\.json)?|auth\.json)$")

TEXTS = {
    "approval_title": "Approval needed",
    "approve": "Approve", "reject": "Reject", "details": "Details",
    "expires_in": "Expires in {minutes} min. No answer = not approved.",
    "approved_by": "Approved by {name}", "rejected_by": "Rejected by {name}",
    "expired": "Expired — not approved. Nothing was run.", "expired_label": "Expired",
    "cb_approved": "Approved", "cb_rejected": "Rejected", "cb_duplicate": "Already recorded",
    "cb_decided": "Already decided", "cb_expired": "This request has expired",
    "cb_not_allowed": "You can't decide this request", "cb_unknown": "This button is no longer valid",
    "cb_answered": "Got it",
    "ask_default": "No answer in {minutes} min → I'll continue with: {default}",
    "ask_reminder": "Reminder: I'm still waiting for your answer.",
    "ask_answered": "Answer received: {answer}",
    "ask_timeout": "No answer — continued with: {default}",
    "ask_timeout_nodefault": "No answer — I stopped here.",
    "placeholder": "Type your answer",
    "unknown_chat": "I was added to chat {chat} ({kind}) by user {by}. It's not on my allowlist, so I left.",
    "long_output": "Full output: {lines} lines (too long for messages).",
    "final_notice": "{title}: {state} in {elapsed}.",
    "state_done": "finished", "state_failed": "failed", "state_running": "running",
}


class VirtualClock:
    """Offline time: sleep() advances now() instantly."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += max(0.0, seconds)


@dataclass
class BridgeConfig:
    chat_id: int                                   # the operator's private chat (= operator user id)
    allow: Allowlist
    bot_username: str | None = None
    approvers: set[int] = field(default_factory=set)   # default: allow.operators
    progress_min_interval: float = 3.0             # design heuristic: a stage change waits >= 3 s
    note_min_interval: float = 15.0                # a note-only change (same stage) waits >= 15 s
    send_min_interval: float = 1.0                 # per chat; official FAQ: avoid > ~1 msg/s per chat
    ask_timeout: float = 600.0
    approval_ttl: float = 900.0
    poll_timeout: float = 25.0
    idle_step: float = 5.0                         # offline: virtual seconds per empty poll
    max_text_parts: int = 3                        # more parts -> send as a document
    texts: dict[str, str] = field(default_factory=lambda: dict(TEXTS))

    def __post_init__(self) -> None:
        if not self.approvers:
            self.approvers = set(self.allow.operators)


class AgentBridge:
    def __init__(self, transport: Any, config: BridgeConfig, *, store: JsonStore | None = None,
                 source: Any = None, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep, redactor: Redactor | None = None,
                 ids: IdFactory | None = None, log: Callable[[dict[str, Any]], None] | None = None):
        self.transport, self.cfg = transport, config
        self.store = store or JsonStore()
        self.clock, self.sleep = clock, sleep
        self.redactor = redactor or Redactor()
        self.log = log or (lambda e: None)
        self.book = ApprovalBook(self.store, clock=clock, ids=ids)
        self.source = source if source is not None else FixtureSource([])
        self.intake = Intake(self.source, self.store, config.allow, bot_username=config.bot_username,
                             clock=clock, log=self._log)
        self.inbox: list[dict[str, Any]] = []
        self._last_send: dict[Any, float] = {}

    # ------------------------------------------------------------------ calls
    def call(self, method: str, params: dict[str, Any]) -> Any:
        params = self.redactor.obj(params)
        if method.startswith("send") and "Draft" not in method:
            self._pace(params.get("chat_id"))
        return call_with_policy(self.transport, method, params, sleep=self.sleep, log=self._log)

    def _pace(self, chat: Any) -> None:
        last = self._last_send.get(chat)
        now = self.clock()
        if last is not None and now - last < self.cfg.send_min_interval:
            self.sleep(self.cfg.send_min_interval - (now - last))
        self._last_send[chat] = self.clock()

    def _log(self, event: dict[str, Any]) -> None:
        self.log(self.redactor.obj(event))

    def _t(self, key: str, **kw: Any) -> str:
        return self.cfg.texts[key].format(**kw)

    def _addr(self, chat_id: int | None, thread_id: int | None) -> dict[str, Any]:
        a: dict[str, Any] = {"chat_id": chat_id if chat_id is not None else self.cfg.chat_id}
        if thread_id:
            a["message_thread_id"] = thread_id
        return a

    # ----------------------------------------------------------- one-way
    def notify(self, text: str, *, silent: bool = False, chat_id: int | None = None,
               thread_id: int | None = None) -> dict[str, Any]:
        sent = self.send_text(text, chat_id=chat_id, thread_id=thread_id, silent=silent)
        return {"ok": True, "message_ids": sent}

    def send_text(self, text: str, *, chat_id: int | None = None, thread_id: int | None = None,
                  silent: bool = False, html: bool = False) -> list[int]:
        """Plain text by default: agent output is never parsed as markup."""
        text = self.redactor.text(text)
        parts = split_text(text, None, 4096)
        if len(parts) > self.cfg.max_text_parts:
            return [self._send_as_document(text, chat_id, thread_id)]
        ids = []
        for chunk, _ in parts:
            params = {**self._addr(chat_id, thread_id), "text": chunk}
            if html:
                params["parse_mode"] = "HTML"
            if silent:
                params["disable_notification"] = True
            ids.append(self.call("sendMessage", params)["message_id"])
        return ids

    def _send_as_document(self, text: str, chat_id: int | None, thread_id: int | None) -> int:
        fd, path = tempfile.mkstemp(prefix="agent-output-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:
            caption = self._t("long_output", lines=text.count("\n") + 1)
            return self.send_file(path, caption=caption, chat_id=chat_id, thread_id=thread_id,
                                  scan=False)["message_id"]
        finally:
            os.unlink(path)

    # ------------------------------------------------------ status card
    def progress(self, key: str, *, title: str | None = None, stages: list[str] | None = None,
                 stage: str | None = None, note: str | None = None, state: str = "running",
                 chat_id: int | None = None, thread_id: int | None = None,
                 announce_final: bool = True) -> dict[str, Any]:
        """One status message per job, edited in place.

        Named real stages (never a fake percentage); edits throttled to
        `progress_min_interval`; identical text is never re-sent; the final
        state always goes out, and (by default) a short new message announces
        it - edits do not notify the operator.
        """
        now = self.clock()
        card = self.store.card(key)
        if card is None:
            card = {"chat": chat_id or self.cfg.chat_id, "thread": thread_id, "title": title or key,
                    "stages": list(stages or []), "done": [], "current": None, "note": None,
                    "state": "running", "started": now, "message_id": None, "last_text": None,
                    "last_edit": None}
        if stages:
            card["stages"] = list(stages)
        if stage:
            if stage not in card["stages"]:
                card["stages"].append(stage)
            idx = card["stages"].index(stage)
            card["done"] = card["stages"][:idx]
            card["current"] = stage
        if note is not None:
            card["note"] = self.redactor.text(note)[:500]
        if state in ("done", "failed"):
            card["state"] = state
            if state == "done":
                card["done"] = list(card["stages"])
        text = self._render_card(card, now)
        signature = self._render_card(card, None)      # content without the clock: the no-op test
        core = self._render_card({**card, "note": None}, None)
        final = card["state"] != "running"
        if card["message_id"] is None:
            msg = self.call("sendMessage", {**self._addr(card["chat"], card["thread"]), "text": text,
                                            "parse_mode": "HTML"})
            card.update(message_id=msg["message_id"], last_text=signature, last_core=core, last_edit=now)
            self.store.put_card(key, card)
            return {"action": "sent", "message_id": card["message_id"]}
        if signature == card["last_text"]:
            self.store.put_card(key, card)
            return {"action": "skipped_same", "message_id": card["message_id"]}
        interval = self.cfg.note_min_interval if core == card.get("last_core") else self.cfg.progress_min_interval
        if not final and card["last_edit"] is not None and now - card["last_edit"] < interval:
            self.store.put_card(key, card)        # newest state kept; the next call sends it
            return {"action": "skipped_throttled", "message_id": card["message_id"]}
        try:
            self.call("editMessageText", {"chat_id": card["chat"], "message_id": card["message_id"],
                                          "text": text, "parse_mode": "HTML"})
            action = "edited"
        except TelegramError as err:
            if "message to edit not found" not in err.description.lower():
                raise
            msg = self.call("sendMessage", {**self._addr(card["chat"], card["thread"]), "text": text,
                                            "parse_mode": "HTML"})
            card["message_id"], action = msg["message_id"], "resent"
        card.update(last_text=signature, last_core=core, last_edit=now)
        self.store.put_card(key, card)
        if final and announce_final:
            self.call("sendMessage", {**self._addr(card["chat"], card["thread"]),
                                      "text": self._t("final_notice", title=card["title"],
                                                      state=self._t(f"state_{card['state']}"),
                                                      elapsed=_elapsed(now - card["started"])),
                                      "reply_parameters": {"message_id": card["message_id"]}})
        return {"action": action, "message_id": card["message_id"]}

    def _render_card(self, card: dict[str, Any], now: float | None) -> str:
        head = f"<b>{escape_html(card['title'])}</b> — {self._t('state_' + card['state'])}"
        if now is not None:
            head += f" · {_elapsed(now - card['started'])}"
        lines = [head]
        for s in card["stages"]:
            if s in card["done"]:
                mark = "✅"
            elif s == card["current"]:
                mark = "❌" if card["state"] == "failed" else "⏳"
            else:
                mark = "▫️"
            lines.append(f"{mark} {escape_html(s)}")
        if card["note"]:
            lines.append(f"\n{escape_html(card['note'])}")
        return "\n".join(lines)

    # ----------------------------------------------------------- approvals
    def approve(self, summary: str, *, details: str | None = None, ttl: float | None = None,
                approvers: set[int] | None = None, destructive: bool = False,
                chat_id: int | None = None, thread_id: int | None = None) -> dict[str, Any]:
        rec = self.request_approval(summary, details=details, ttl=ttl, approvers=approvers,
                                    destructive=destructive, chat_id=chat_id, thread_id=thread_id)
        return self.wait(rec["rid"])

    def request_approval(self, summary: str, *, details: str | None = None, ttl: float | None = None,
                         approvers: set[int] | None = None, destructive: bool = False,
                         chat_id: int | None = None, thread_id: int | None = None) -> dict[str, Any]:
        ttl = ttl or self.cfg.approval_ttl
        chat = chat_id or self.cfg.chat_id
        rec = self.book.create("approval", chat_id=chat, approvers=approvers or self.cfg.approvers,
                               ttl=ttl, summary=self.redactor.text(summary))
        text = (f"<b>{escape_html(self._t('approval_title'))}</b>\n{escape_html(rec['summary'])}\n\n"
                f"{escape_html(self._t('expires_in', minutes=max(1, round(ttl / 60))))}")
        approve_btn = {"text": self._t("approve"), "callback_data": self.book.callback_data(rec, "a"),
                       "style": "danger" if destructive else "success"}
        row2 = [{"text": self._t("details"), "callback_data": self.book.callback_data(rec, "d")}] if details else []
        markup = {"inline_keyboard": [[approve_btn, {"text": self._t("reject"),
                                                     "callback_data": self.book.callback_data(rec, "r")}]]
                  + ([row2] if row2 else [])}
        msg = self.call("sendMessage", {**self._addr(chat, thread_id), "text": text, "parse_mode": "HTML",
                                        "reply_markup": markup})
        rec = self.store.get_pending(rec["rid"])
        rec.update(text=text, details=self.redactor.text(details) if details else None, thread=thread_id)
        self.store.put_pending(rec["rid"], rec)
        self.book.attach(rec["rid"], msg["message_id"])
        return self.store.get_pending(rec["rid"])

    # ---------------------------------------------------------------- asks
    def ask(self, question: str, *, choices: list[str] | None = None, timeout: float | None = None,
            remind_after: float | None = None, default: str | None = None,
            placeholder: str | None = None, chat_id: int | None = None,
            thread_id: int | None = None) -> dict[str, Any]:
        rec = self.request_answer(question, choices=choices, timeout=timeout, default=default,
                                  placeholder=placeholder, chat_id=chat_id, thread_id=thread_id)
        return self.wait(rec["rid"], remind_after=remind_after)

    def request_answer(self, question: str, *, choices: list[str] | None = None, timeout: float | None = None,
                       default: str | None = None, placeholder: str | None = None,
                       chat_id: int | None = None, thread_id: int | None = None,
                       approvers: set[int] | None = None, allow_text: bool = True) -> dict[str, Any]:
        timeout = timeout or self.cfg.ask_timeout
        chat = chat_id or self.cfg.chat_id
        rec = self.book.create("ask", chat_id=chat, approvers=approvers or self.cfg.approvers, ttl=timeout,
                               summary=self.redactor.text(question), choices=list(choices or []), default=default)
        text = escape_html(rec["summary"])
        if default is not None:
            text += "\n\n" + escape_html(self._t("ask_default", minutes=max(1, round(timeout / 60)), default=default))
        if choices:
            rows = [[{"text": c[:64], "callback_data": self.book.callback_data(rec, str(i))}]
                    for i, c in enumerate(choices)]
            markup: dict[str, Any] = {"inline_keyboard": rows}
            if allow_text:
                markup["force_reply"] = True              # 10.3: buttons + a reply field
        else:
            markup = {"force_reply": True, "input_field_placeholder": (placeholder or self._t("placeholder"))[:64]}
        msg = self.call("sendMessage", {**self._addr(chat, thread_id), "text": text, "parse_mode": "HTML",
                                        "reply_markup": markup})
        rec = self.store.get_pending(rec["rid"])
        rec.update(text=text, thread=thread_id, allow_text=bool(allow_text and choices))
        self.store.put_pending(rec["rid"], rec)
        self.book.attach(rec["rid"], msg["message_id"])
        return self.store.get_pending(rec["rid"])

    # ------------------------------------------------------------- waiting
    def wait(self, rid: str, *, remind_after: float | None = None) -> dict[str, Any]:
        """Block until request `rid` is decided/answered or expires. Works for
        a request created by an earlier process (state in JsonStore)."""
        rec = self.store.get_pending(rid)
        if rec is None:
            raise KeyError(f"unknown request {rid}")
        remind_at = rec["created"] + remind_after if remind_after else None
        while True:
            rec = self.store.get_pending(rid)
            if rec["status"] != "open":
                return self._result(rec)
            now = self.clock()
            if now >= rec["expires"]:
                self.book.expire_due()
                rec = self.store.get_pending(rid)
                self._close_card(rec)
                return self._result(rec)
            if remind_at and not rec["reminded"] and now >= remind_at:
                self.call("sendMessage", {**self._addr(rec["chat"], rec.get("thread")),
                                          "text": self._t("ask_reminder"),
                                          "reply_parameters": {"message_id": rec["message_id"]}})
                rec["reminded"] = True
                self.store.put_pending(rid, rec)
            got = self.pump(timeout=min(self.cfg.poll_timeout, max(0.0, rec["expires"] - now)))
            if not got and isinstance(self.source, FixtureSource):
                self.sleep(min(self.cfg.idle_step, max(0.01, rec["expires"] - self.clock())))

    def _result(self, rec: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {"request_id": rec["rid"], "kind": rec["kind"], "status": rec["status"],
                               "by": rec["by"], "decided_at": rec["decided_at"]}
        if rec["kind"] == "approval":
            out["decision"] = rec["decision"]
        else:
            answered = rec["status"] == "decided"
            out["status"] = "answered" if answered else "timeout"
            out["answer"] = rec["decision"] if answered else rec["default"]
            out["used_default"] = not answered
            out["via"] = rec.get("via")
            if answered and rec.get("via") == "text":
                out["content_is_untrusted_data"] = True
                out["injection_signals"] = injection_signals(rec["decision"])
        return out

    # ----------------------------------------------------- update handling
    def pump(self, timeout: float = 0.0) -> int:
        """Fetch and handle one batch of updates. Returns how many arrived."""
        n = 0
        for event in self.intake.events(timeout):
            n += 1
            self.handle(event)
        return n

    def handle(self, event: dict[str, Any]) -> None:
        kind = event["type"]
        if kind == "rejected":
            return                                     # strangers get silence, not a reply
        if kind == "callback":
            self._on_callback(event)
            return
        if kind == "reply" and not event.get("forwarded"):     # forwarded text never answers
            rec = self.book.find_by_message(event["chat"], event["reply_to_message_id"])
            if rec is not None:
                res = self.book.resolve_text(rec, event["from"], self.redactor.text(event["text"]))  # never persist a pasted secret
                if res.accepted:
                    self._close_card(res.record)
                    return
        if kind == "unknown_chat_added":
            self._leave_unknown(event)
            return
        self.inbox.append(event)

    def _on_callback(self, event: dict[str, Any]) -> None:
        data = event.get("data") or ""
        if not data.startswith(("ap:", "aq:")):
            self.inbox.append(event)                   # the app's own buttons (dashboards, menus)
            return
        res: Resolution = self.book.resolve_callback(event)
        texts = {"approved": "cb_approved", "rejected": "cb_rejected", "answered": "cb_answered",
                 "duplicate": "cb_duplicate", "already_decided": "cb_decided", "expired": "cb_expired",
                 "not_allowed": "cb_not_allowed", "forged": "cb_unknown", "wrong_message": "cb_unknown"}
        if res.outcome == "details":
            details = (res.record or {}).get("details") or ""
            if len(details) <= 200:
                self.call("answerCallbackQuery", {"callback_query_id": event["callback_query_id"],
                                                  "text": details, "show_alert": True})
            else:
                self.call("answerCallbackQuery", {"callback_query_id": event["callback_query_id"]})
                self.send_text(details, chat_id=res.record["chat"], thread_id=res.record.get("thread"))
            return
        self.call("answerCallbackQuery", {"callback_query_id": event["callback_query_id"],
                                          "text": self._t(texts[res.outcome]),
                                          "show_alert": res.outcome in ("not_allowed", "expired")})
        self._log({"event": "callback", "outcome": res.outcome, "from": event.get("from"),
                   "request": (res.record or {}).get("rid")})
        if res.accepted or res.outcome == "expired":
            res.record["by_name"] = event.get("from_name")
            self.store.put_pending(res.record["rid"], res.record)
            self._close_card(res.record)

    def _close_card(self, rec: dict[str, Any]) -> None:
        """Replace live buttons with one disabled button that states the result."""
        if rec.get("closed_card"):
            return
        name = rec.get("by_name") or (f"id {rec['by']}" if rec.get("by") else "")
        if rec["kind"] == "approval":
            label = {"approved": self._t("approved_by", name=name), "rejected": self._t("rejected_by", name=name)} \
                .get(rec["decision"], self._t("expired_label"))
            markup: dict[str, Any] = {"inline_keyboard": [[{"text": label[:64], "disabled": {}}]]}
            if rec["decision"] not in ("approved", "rejected"):
                label = self._t("expired")
        else:
            if rec["status"] == "decided":
                label = self._t("ask_answered", answer=str(rec["decision"])[:40])
            elif rec["default"] is not None:
                label = self._t("ask_timeout", default=rec["default"])
            else:
                label = self._t("ask_timeout_nodefault")
            markup = {"inline_keyboard": [[{"text": label[:64], "disabled": {}}]]}
            if rec.get("allow_text"):
                markup["force_reply"] = True           # can't change force_reply in an edit
        try:
            self.call("editMessageText", {"chat_id": rec["chat"], "message_id": rec["message_id"],
                                          "text": rec.get("text", "") + "\n\n" + escape_html(label),
                                          "parse_mode": "HTML", "reply_markup": markup})
        except (TelegramError, OutcomeUnknown) as err:
            self._log({"event": "close_card_failed", "request": rec["rid"], "detail": str(err)})
        rec["closed_card"] = True
        self.store.put_pending(rec["rid"], rec)

    def _leave_unknown(self, event: dict[str, Any]) -> None:
        self._log({"event": "unknown_chat", "chat": event["chat"], "by": event["by"]})
        try:
            self.call("leaveChat", {"chat_id": event["chat"]})
        except TelegramError as err:
            self._log({"event": "leave_failed", "chat": event["chat"], "class": err.category})
        self.send_text(self._t("unknown_chat", chat=event["chat"], kind=event.get("chat_type"), by=event["by"]))

    def listen(self, *, max_events: int | None = None, until: float | None = None) -> Iterable[dict[str, Any]]:
        """Yield allowlisted events (commands, data, stops, the app's own
        callbacks). Rejected updates are dropped and counted. Decisions and
        answers to pending requests are applied on the way through."""
        emitted = 0
        while max_events is None or emitted < max_events:
            if until is not None and self.clock() >= until:
                return
            got = self.pump(timeout=self.cfg.poll_timeout)
            self.book.expire_due()
            while self.inbox:
                yield self.inbox.pop(0)
                emitted += 1
                if max_events is not None and emitted >= max_events:
                    return
            if not got and isinstance(self.source, FixtureSource):
                if self.source.exhausted:
                    return
                self.sleep(self.cfg.idle_step)

    # ------------------------------------------------------------ artifacts
    def send_file(self, path: str, *, caption: str | None = None, chat_id: int | None = None,
                  thread_id: int | None = None, scan: bool = True, allow_group: bool = False) -> dict[str, Any]:
        chat = chat_id or self.cfg.chat_id
        if chat != self.cfg.chat_id and not allow_group:
            raise PermissionError("files go to the operator's private chat; pass allow_group for another chat")
        if os.path.getsize(path) > UPLOAD_LIMIT:
            raise ValueError("file exceeds the 50 MB bot upload limit; send a link or split it")
        source = read_file(path)          # read once: the scanned bytes are the uploaded bytes
        meta = file_meta(source)
        if meta["size"] > UPLOAD_LIMIT:
            raise ValueError("file exceeds the 50 MB bot upload limit; send a link or split it")
        if SECRET_FILE_NAMES.search(meta["name"]):   # applies even with scan=False
            raise PermissionError(f"refusing to upload {meta['name']}: secret-bearing file name")
        if scan:
            findings = self.redactor.findings(source[1].decode("utf-8", errors="ignore"))  # binary too
            if findings:
                raise PermissionError(f"refusing to upload {meta['name']}: possible secrets ({', '.join(findings)})")
        params: dict[str, Any] = {**self._addr(chat, thread_id), "document": "attach://document"}
        if caption:
            params["caption"] = self.redactor.text(caption)[:1024]
        params = self.redactor.obj(params)
        self._pace(chat)
        upload = getattr(self.transport, "upload", None)
        if upload is None:
            msg = call_with_policy(self.transport, "sendDocument", params, sleep=self.sleep, log=self._log)
        else:
            msg = upload("sendDocument", params, {"document": source})
        return {"ok": True, "message_id": msg["message_id"], **meta}

    def report(self, *, data: dict[str, Any] | None = None, markdown: str | None = None,
               chat_id: int | None = None, thread_id: int | None = None, silent: bool = False) -> dict[str, Any]:
        """A Rich Message report (10.x): JSON -> typed blocks, or Rich Markdown.
        Falls back to plain text when the server/SDK rejects rich messages."""
        if (data is None) == (markdown is None):
            raise ValueError("pass exactly one of data or markdown")
        rich = {"blocks": self.redactor.obj(report_blocks(data))} if data is not None \
            else {"markdown": self.redactor.text(markdown)}
        size = _rich_chars(rich)
        if size > LIMITS["chars"] or len(rich.get("blocks", [])) > LIMITS["blocks"]:
            return {"ok": True, "format": "document",
                    "message_id": self._send_as_document(_plain(rich), chat_id, thread_id)}
        try:
            params = {**self._addr(chat_id, thread_id), "rich_message": rich}
            if silent:
                params["disable_notification"] = True
            msg = self.call("sendRichMessage", params)
            return {"ok": True, "format": "rich", "message_id": msg["message_id"], "chars": size}
        except TelegramError as err:
            if err.category not in ("unsupported", "validation"):
                raise
            self._log({"event": "fallback", "from": "sendRichMessage", "class": err.category})
            ids = self.send_text(_plain(rich), chat_id=chat_id, thread_id=thread_id, silent=silent)
            return {"ok": True, "format": "plain", "message_id": ids[0], "fallback": err.category}

    # ----------------------------------------------------------- streaming
    def stream_answer(self, chunks: Iterable[Any], *, thread_id: int | None = None,
                      on_cancel: Callable[[], None] = lambda: None, rich: bool = True,
                      deadline: float = 300.0) -> dict[str, Any]:
        """Stream an answer as a draft with Stop (10.3). Items are text chunks
        or ("stage", name). On Stop: on_cancel() runs (cancel the agent's own
        work: model stream, tool calls, subprocesses) and the chunk generator
        is closed, so nothing keeps spending tokens after the user said stop."""
        draft_id = self.store.next_counter("draft") + 40000
        gen = Generation(op_id=f"stream-{draft_id}", chat_id=self.cfg.chat_id, draft_id=draft_id,
                         message_thread_id=thread_id,
                         config=GenerationConfig(rich=rich, stop_policy="keep_marked", deadline=deadline),
                         now=self.clock())
        cancelled = []

        def cancel() -> None:
            if not cancelled:
                cancelled.append(True)
                on_cancel()
                close = getattr(chunks, "close", None)
                if close:
                    close()

        def run(effects: list) -> None:
            execute(effects, self, gen, now=self.clock(), cancel_upstream=cancel, log=self._log, sleep=self.sleep)

        run(gen.start(self.clock()))
        for item in chunks:
            if self._stop_requested(gen):
                run(gen.on_stop(self.clock()))
                break
            if isinstance(item, tuple) and item[0] == "stage":
                run(gen.on_stage(item[1], self.clock()))
            else:
                run(gen.on_chunk(str(item), self.clock()))
            run(gen.on_tick(self.clock()))
            if gen.terminal:
                break
        else:
            if self._stop_requested(gen):
                run(gen.on_stop(self.clock()))
            else:
                run(gen.on_done(self.clock()))
        return {"outcome": gen.state.value, "draft_id": draft_id, "chars": len(gen.buffer),
                "upstream_cancelled": bool(cancelled), "finalizations": gen.finalizations}

    def _stop_requested(self, gen: Generation) -> bool:
        self.pump(timeout=0)
        for i, ev in enumerate(self.inbox):
            if ev["type"] == "stop_generation" and gen.matches_stop(
                    {"chat": {"id": ev["chat"]}, "message_thread_id": ev.get("message_thread_id"),
                     "draft_id": ev.get("draft_id")}):
                del self.inbox[i]
                return True
        return False


def report_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Report JSON -> InputRichBlock list. Keys: title, summary, table
    {header, rows, numeric_cols}, items [str | {text, done}], log_tail, log_language.
    RichText is passed as plain strings: agent output never becomes markup."""
    blocks: list[dict[str, Any]] = []
    if data.get("title"):
        blocks.append({"type": "heading", "size": 2, "text": str(data["title"])})
    for p in ([data["summary"]] if isinstance(data.get("summary"), str) else data.get("summary") or []):
        blocks.append({"type": "paragraph", "text": str(p)})
    tbl = data.get("table")
    if tbl:
        header = [str(h) for h in tbl["header"]][:LIMITS["table_columns"]]
        rows = [[str(v) for v in r][:len(header)] for r in tbl["rows"]]
        blocks.append(table(header, rows, compact=len(header) > 3,
                            numeric_cols=frozenset(tbl.get("numeric_cols", []))))
    items = data.get("items") or []
    if items:
        out = []
        for it in items:
            if isinstance(it, dict):
                li: dict[str, Any] = {"blocks": [{"type": "paragraph", "text": str(it.get("text", ""))}]}
                if "done" in it:
                    li["has_checkbox"] = True
                    if it["done"]:
                        li["is_checked"] = True
                out.append(li)
            else:
                out.append({"blocks": [{"type": "paragraph", "text": str(it)}]})
        blocks.append({"type": "list", "items": out})
    if data.get("log_tail"):
        pre: dict[str, Any] = {"type": "pre", "text": str(data["log_tail"])}
        if data.get("log_language"):
            pre["language"] = data["log_language"]
        blocks.append({"type": "details", "summary": "Log tail", "blocks": [pre]})
    return blocks


def _strings(v: Any) -> Iterable[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)
    elif isinstance(v, dict):
        for k, x in v.items():
            if k not in ("type", "align", "valign", "language"):
                yield from _strings(x)


def _rich_chars(rich: dict[str, Any]) -> int:
    return sum(len(s) for s in _strings(rich))


def _plain(rich: dict[str, Any]) -> str:
    if "markdown" in rich:
        return rich["markdown"]
    lines: list[str] = []
    for b in rich["blocks"]:
        if b["type"] == "table":
            lines += [" | ".join(str(c["text"]) for c in row) for row in b["cells"]]
        elif b["type"] == "list":
            lines += ["• " + " ".join(_strings(i["blocks"])) for i in b["items"]]
        elif b["type"] == "details":
            lines += [b["summary"]] + [x["text"] for x in b["blocks"]]
        else:
            lines.append(str(b.get("text", "")))
        lines.append("")
    return "\n".join(lines).strip()


def _elapsed(seconds: float) -> str:
    s = int(max(0, seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60:02d}s"
    return f"{s // 3600}h {(s % 3600) // 60:02d}m"


__all__ = ["AgentBridge", "BridgeConfig", "VirtualClock", "TEXTS", "report_blocks"]
