"""Dialogue engine: one event in, effects and a trace entry out.

The simulator replays scenario fixtures through it; the adapters feed it real updates
mapped to the same events and turn its effects into Bot API requests. The Studio runs a
TypeScript port that is checked against the same fixtures (tests/test_bot_ui_parity.py).

Session (JSON-serialisable): screen, locale, context, state, data, input, history,
messages [{instance, screen, state, kind, accessible}], active (instance with the inline
keyboard of the active screen), reply (screen whose reply keyboard is shown), awaiting
(screen waiting for text), next (next message instance number).

Events: {"command": "start"} · {"text": "..."} · {"press": actionId, "message"?: instance}
· {"event": eventKey, "data"?: {...}} · {"context": {...}} · {"inaccessible": instance}
· {"expect": {"screen"?: id, "contains"?: text}} (scenario assertion).

Effects: send · edit · answer (callback acknowledgement, optional toast text) · fallback
(the intended presentation is unavailable; a send follows) · link (shown, never opened)
· noop (nothing to do, with a reason).

Policies (also in studio/docs/contract.md): a press on a message that no longer shows the
action is stale: it is acknowledged with the project's stale text and nothing else changes.
An edit of an inaccessible message falls back to a new message. A widget outside a private
chat (or with widgets disabled) is replaced by its screen's regular message.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from . import render
from .project import Snapshot

HISTORY_MAX = 20
HandlerFn = Callable[[str, dict], str]
DEFAULT_TEXTS = {"stale": {"en": "This button is out of date.", "ru": "Эта кнопка устарела.", "uk": "Ця кнопка застаріла."},
                 "disabled": {"en": "Not available right now.", "ru": "Сейчас недоступно.", "uk": "Зараз недоступно."}}


def new_session(project: dict, *, locale: str | None = None, context: dict | None = None,
                data: dict | None = None) -> dict:
    return {"screen": None, "locale": locale or project.get("defaultLocale", "en"),
            "context": dict(context or {}), "state": {}, "data": dict(data or {}), "input": {},
            "history": [], "messages": [], "active": None, "reply": None, "awaiting": None, "next": 1}


class Engine:
    def __init__(self, snap: Snapshot, handler: HandlerFn | None = None) -> None:
        self.snap = snap
        self.project = snap.project or {}
        self.handler = handler

    # ------------------------------------------------------------ helpers
    def _text(self, key: str, locale: str) -> str:
        custom = (self.project.get("messages") or {}).get(key)
        return render.localized(custom or DEFAULT_TEXTS[key], locale, "en") or ""

    def _values(self, s: dict) -> dict:
        out: dict[str, Any] = {}
        for part in ("data", "context", "state", "input"):
            out.update(s[part])
        return out

    def _render(self, s: dict, sid: str, state: str | None = None) -> dict:
        return render.render_screen(self.project, self.snap.screens[sid], locale=s["locale"], state=state,
                                    values=self._values(s))

    def _view(self, logical: dict) -> dict:
        """The parity projection of a rendered message."""
        kb = logical["keyboard"]
        media = logical.get("media")
        return {"screenId": logical["screenId"], "state": logical["state"], "text": logical["text"],
                "media": media["type"] if media else None,
                "keyboard": {"type": kb["type"],
                             "rows": [[{"actionId": b["actionId"], "text": b["text"]} for b in row] for row in kb["rows"]]},
                "richButtons": [{"actionId": b["actionId"], "text": b["text"]} for b in logical.get("richButtons") or []]}

    def _widgets_ok(self, s: dict) -> bool:
        caps = self.project.get("capabilities") or {}
        return caps.get("widgets", False) and s["context"].get("chat", "private") == "private"

    def _field_value(self, s: dict, name: str) -> Any:
        fd = (self.project.get("fields") or {}).get(name) or {}
        src = fd.get("source")
        return s["state"].get(name) if src == "state" else s["context"].get(name)

    # ------------------------------------------------------------ transitions
    def _show(self, s: dict, sid: str, *, origin: str, presentation: str | None, instance: int | None,
              effects: list[dict], state: str | None = None) -> None:
        screen = self.snap.screens[sid]
        logical = self._render(s, sid, state)
        is_widget = bool(screen.get("widget"))
        want_edit = origin == "callback" and (presentation or "edit") == "edit" and instance is not None
        msg = next((m for m in s["messages"] if m["instance"] == instance), None)
        if is_widget and not self._widgets_ok(s):
            effects.append({"type": "fallback", "reason": "widget_unsupported", "screenId": sid})
            is_widget = False
        ktype = (screen.get("keyboard") or {}).get("type", "none")
        target_media = (logical.get("media") or {}).get("type")
        if want_edit and msg is not None and (not msg["accessible"] or msg["kind"] != "message" or is_widget
                                              or not _edit_ok(msg.get("media"), target_media)
                                              or ktype not in ("inline", "none")):
            reason = ("edit_unavailable" if not msg["accessible"] else
                      "edit_kind" if msg["kind"] != "message" or is_widget or not _edit_ok(msg.get("media"), target_media)
                      else "edit_keyboard")
            effects.append({"type": "fallback", "reason": reason, "instance": instance})
            want_edit = False
        # The callback buttons inside this rendering of a rich document (this locale, this state):
        # a press is checked against what the user was actually shown.
        rich_ids = [b["actionId"] for b in logical.get("richButtons") or [] if b.get("actionId") and b.get("callbackData")]
        if want_edit and msg is not None:
            msg["screen"], msg["state"], msg["media"], msg["rich"] = sid, state, target_media, rich_ids
            effects.append({"type": "edit", "instance": instance, "render": logical, "view": self._view(logical)})
            target_instance = instance
        else:
            target_instance = s["next"]
            s["next"] += 1
            kind = "widget" if is_widget else "message"
            s["messages"].append({"instance": target_instance, "screen": sid, "state": state, "kind": kind,
                                  "media": None if is_widget else target_media, "accessible": True,
                                  "rich": [] if is_widget else rich_ids})
            eff = {"type": "send", "instance": target_instance, "kind": kind, "render": logical,
                   "view": self._view(logical)}
            if is_widget:
                eff["widget"] = screen["widget"]["ref"]
            effects.append(eff)
        if state is None:
            s["screen"] = sid
            kt = (screen.get("keyboard") or {}).get("type", "none")
            if kt == "inline" or rich_ids:
                s["active"] = target_instance
            if kt == "reply":
                s["reply"] = sid
            elif kt == "remove":
                s["reply"] = None
            s["awaiting"] = sid if isinstance(screen.get("input"), dict) else None

    def _navigate(self, s: dict, target: str, via: str, *, origin: str, presentation: str | None,
                  instance: int | None, effects: list[dict], push: bool = True) -> dict:
        frm = s["screen"]
        if push and frm and frm != target:
            s["history"] = (s["history"] + [frm])[-HISTORY_MAX:]
        self._show(s, target, origin=origin, presentation=presentation, instance=instance, effects=effects)
        return {"from": frm, "to": target, "via": via}

    # ------------------------------------------------------------ events
    def feed(self, s: dict, event: dict) -> dict:
        """Apply one event to session `s` (mutated). Returns the trace entry."""
        effects: list[dict] = []
        entry: dict[str, Any] = {"update": _summary(event), "action": None, "transition": None,
                                 "effects": effects, "diagnostics": []}
        if "command" in event:
            self._command(s, str(event["command"]).lstrip("/").split("@")[0], entry)
        elif "text" in event:
            text = str(event["text"])
            if text.startswith("/"):
                self._command(s, text[1:].split()[0].split("@")[0], entry)
            else:
                self._text_in(s, text, entry)
        elif "press" in event:
            self._press(s, str(event["press"]), event.get("message"), entry, origin="callback")
        elif "event" in event:
            self._event(s, event, entry)
        elif "context" in event:
            s["context"].update(event["context"])
        elif "locale" in event:
            s["locale"] = event["locale"]
        elif "inaccessible" in event:
            for m in s["messages"]:
                if m["instance"] == event["inaccessible"]:
                    m["accessible"] = False
        elif "expect" in event:
            self._expect(s, event["expect"], entry)
        else:
            entry["diagnostics"].append({"code": "EVENT_UNKNOWN", "severity": "error", "message": f"unknown event {event}"})
        return entry

    def _command(self, s: dict, cmd: str, entry: dict) -> None:
        ep = next((e for e in self.project.get("entryPoints") or [] if e.get("type") == "command" and e.get("command") == cmd), None)
        if not ep:
            entry["effects"].append({"type": "noop", "reason": f"/{cmd} is not an entry point"})
            return
        s["history"] = []
        entry["transition"] = self._navigate(s, ep["screen"], f"entry:{ep.get('id', cmd)}", origin="text",
                                             presentation="send", instance=None, effects=entry["effects"], push=False)

    def _text_in(self, s: dict, text: str, entry: dict) -> None:
        if s["reply"]:
            screen = self.snap.screens.get(s["reply"]) or {}
            logical = self._render(s, s["reply"])
            for row in logical["keyboard"]["rows"]:
                for b in row:
                    if b["text"] == text:
                        self._press(s, b["actionId"], None, entry, origin="reply", screen_id=screen.get("id"))
                        return
        if s["awaiting"]:
            screen = self.snap.screens[s["awaiting"]]
            inp = screen["input"]
            fd = (self.project.get("fields") or {}).get(inp["field"]) or {}
            limit = fd.get("maxLength")
            if limit and len(text) > limit:
                entry["diagnostics"].append({"code": "INPUT_TOO_LONG", "severity": "warning",
                                             "message": f"{len(text)} > {limit} characters; the screen is shown again"})
                self._show(s, screen["id"], origin="text", presentation="send", instance=None, effects=entry["effects"])
                return
            s["input"][inp["field"]] = text
            entry["action"] = {"screenId": screen["id"], "actionId": None, "type": "input", "field": inp["field"]}
            entry["transition"] = self._navigate(s, inp["to"], "input", origin="text", presentation="send",
                                                 instance=None, effects=entry["effects"])
            return
        entry["effects"].append({"type": "noop", "reason": "text is not expected here"})

    def _press(self, s: dict, aid: str, instance: Any, entry: dict, *, origin: str, screen_id: str | None = None) -> None:
        if origin == "callback":
            instance = instance if instance is not None else s["active"]
            msg = next((m for m in s["messages"] if m["instance"] == instance), None)
            screen_id = msg["screen"] if msg else None
            current = msg is not None and instance == s["active"] and msg["state"] is None
            screen = self.snap.screens.get(screen_id or "")
            act = (screen or {}).get("actions", {}).get(aid)
            on_kb = screen is not None and (any(aid in row for row in render.keyboard_rows(screen))
                                            or aid in (msg or {}).get("rich", []))
            if not (current and act and on_kb):
                entry["action"] = {"screenId": screen_id, "actionId": aid, "type": "stale"}
                entry["effects"].append({"type": "answer", "text": self._text("stale", s["locale"])})
                return
        else:
            screen = self.snap.screens[screen_id]  # type: ignore[index]
            act = screen["actions"][aid]
        t = act["type"]
        entry["action"] = {"screenId": screen_id, "actionId": aid, "type": t}
        for name, value in (act.get("set") or {}).items():
            s["state"][name] = value
        eff = entry["effects"]
        ack = origin == "callback"
        pres = act.get("presentation")
        if t == "url":
            eff.append({"type": "link", "url": act.get("url")})
            return
        if t == "answer":
            eff.append({"type": "answer", "text": render.localized(act.get("text"), s["locale"], self.project.get("defaultLocale", "en"))})
            return
        if t == "disabled":
            eff.append({"type": "answer", "text": self._text("disabled", s["locale"])})
            return
        if t == "navigate":
            if ack:
                eff.append({"type": "answer", "text": None})
            if isinstance(act.get("rule"), dict):
                r = act["rule"]
                matched = self._field_value(s, r["when"]["field"]) == r["when"].get("eq")
                branch = "match" if matched else "otherwise"
                tr = self._navigate(s, r[branch], f"rule:{branch}", origin=origin, presentation=pres,
                                    instance=instance, effects=eff)
                tr["rule"] = {"field": r["when"]["field"], "matched": matched, "branch": branch}
                entry["transition"] = tr
            else:
                entry["transition"] = self._navigate(s, act["to"], "to", origin=origin, presentation=pres,
                                                     instance=instance, effects=eff)
            return
        if t == "back":
            if ack:
                eff.append({"type": "answer", "text": None})
            if s["history"]:
                target, via = s["history"].pop(), "back"
            else:
                target, via = act.get("fallback"), "back-fallback"
            if not target:
                eff.append({"type": "noop", "reason": "no history and no fallback"})
                return
            entry["transition"] = self._navigate(s, target, via, origin=origin, presentation=pres,
                                                 instance=instance, effects=eff, push=False)
            return
        if t == "handler":
            hid = act["handlerId"]
            eff.append({"type": "answer", "text": render.localized(act.get("pending"), s["locale"],
                                                                   self.project.get("defaultLocale", "en"))} if ack else
                       {"type": "noop", "reason": "handler started"})
            msg_states = (screen.get("message") or {}).get("states") or {}
            if "loading" in msg_states and origin == "callback":
                self._show(s, screen_id, origin="callback", presentation="edit", instance=instance,  # type: ignore[arg-type]
                           effects=eff, state="loading")
            outcome = self.handler(hid, {"screenId": screen_id, "actionId": aid, "session": s}) if self.handler else None
            target = (act.get("outcomes") or {}).get(outcome) if outcome else None
            if not target:
                entry["diagnostics"].append({"code": "HANDLER_RESULT_UNKNOWN", "severity": "error",
                                             "message": f"{hid} returned {outcome!r}, which has no target"})
                return
            entry["transition"] = self._navigate(s, target, f"outcome:{outcome}", origin=origin, presentation=pres,
                                                 instance=instance, effects=eff)

    def _event(self, s: dict, event: dict, entry: dict) -> None:
        ep = next((e for e in self.project.get("entryPoints") or []
                   if e.get("type") == "event" and e.get("eventKey") == event["event"]), None)
        if not ep:
            entry["effects"].append({"type": "noop", "reason": f"no entry point for event {event['event']}"})
            return
        s["data"].update(event.get("data") or {})
        entry["transition"] = self._navigate(s, ep["screen"], f"event:{event['event']}", origin="event",
                                             presentation="send", instance=None, effects=entry["effects"])

    def _expect(self, s: dict, exp: dict, entry: dict) -> None:
        if "screen" in exp and s["screen"] != exp["screen"]:
            entry["diagnostics"].append({"code": "EXPECT_SCREEN", "severity": "error",
                                         "message": f"expected screen {exp['screen']}, got {s['screen']}"})
        if "contains" in exp:
            last = next((m for m in reversed(s["messages"]) if m["screen"] == s["screen"]), None)
            text = self._render(s, last["screen"], last["state"])["text"] if last else ""
            if exp["contains"] not in text:
                entry["diagnostics"].append({"code": "EXPECT_TEXT", "severity": "error",
                                             "message": f"text of {s['screen']} does not contain {exp['contains']!r}"})


def _edit_ok(current: str | None, target: str | None) -> bool:
    """What Telegram can edit in place: text -> text (editMessageText); text or an editable media
    kind -> an editable media kind (editMessageMedia). Never media -> text, never voice, video
    notes or stickers."""
    if target is None:
        return current is None
    return target in render.EDITABLE_MEDIA and (current is None or current in render.EDITABLE_MEDIA)


def _summary(event: dict) -> dict:
    if "command" in event:
        return {"type": "message", "text": "/" + str(event["command"]).lstrip("/")}
    if "text" in event:
        return {"type": "message", "text": event["text"]}
    if "press" in event:
        out = {"type": "callback_query", "actionId": event["press"]}
        if "message" in event:
            out["message"] = event["message"]
        return out
    if "event" in event:
        return {"type": "event", "eventKey": event["event"]}
    return {"type": "local", **{k: v for k, v in event.items()}}


def run_scenario(snap: Snapshot, scenario: dict, *, overrides: dict | None = None) -> dict:
    """Replay a scenario fixture. Handler results come from scenario.handlers queues."""
    sc = copy.deepcopy(scenario)
    if overrides:
        for k in ("locale",):
            if k in overrides:
                sc[k] = overrides[k]
        sc.setdefault("context", {}).update(overrides.get("context") or {})
    queues = {k: list(v) for k, v in (sc.get("handlers") or {}).items()}

    def handler(hid: str, _ctx: dict) -> str:
        q = queues.get(hid) or []
        return q.pop(0) if q else ""

    eng = Engine(snap, handler)
    s = new_session(snap.project or {}, locale=sc.get("locale"), context=sc.get("context"), data=sc.get("data"))
    trace = []
    for i, ev in enumerate(sc.get("steps") or [], 1):
        entry = eng.feed(s, ev)
        entry["step"] = i
        trace.append(entry)
    ok = not any(d["severity"] == "error" for e in trace for d in e["diagnostics"])
    return {"ok": ok, "scenarioId": sc.get("scenarioId"), "revision": snap.revision, "locale": s["locale"],
            "trace": trace, "final": {"screen": s["screen"], "history": s["history"]}}


def parity_view(result: dict) -> dict:
    """What the Python and TypeScript engines must agree on, byte for byte."""
    steps = []
    for e in result["trace"]:
        steps.append({"step": e["step"], "update": e["update"], "action": e["action"], "transition": e["transition"],
                      "effects": [{k: v for k, v in eff.items() if k != "render"} for eff in e["effects"]],
                      "diagnostics": [d["code"] for d in e["diagnostics"]]})
    return {"ok": result["ok"], "scenarioId": result["scenarioId"], "final": result["final"], "steps": steps}
