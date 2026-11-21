"""api-browser: a widget as the front end of a REST backend (list -> detail -> action).

The widget has no network (Widgets guide: every network API throws NetworkDisabledError). The bot
is the only bridge: widget query -> this handler -> backend call -> state edit + answer, all within
the 15-second answer window. Swap MockTicketsApi for RestTicketsApi (or your client) to go live.

Requests: "f:<open|mine|all>", "pg:<n>", "o:<id>", "b", "x:<id>:<assign|close>", "sync".
Contract:
* the user is identified by Telegram (`from.id`), mapped to the backend user on the server; the
  widget never holds an API key, token or session (its code and state are readable by the user);
* list pages are projected to <= 5 rows of [id, title, status, meta] (chat_data <= 1024 bytes);
* reads are cached per (user, filter, page) for CACHE_TTL seconds; a slow or failing upstream
  answers the cached page with "stale": 1 and a message instead of a timeout;
* actions are re-checked against the backend (the ticket may have changed), never trusted from
  the widget's view.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol

from .core import Action, BadRequest, Ctx, Spec, load_demo

PAGE = 5
CACHE_TTL = 30.0
UPSTREAM_TIMEOUT = 6.0      # leaves room for the edit and the answer inside 15 s
FILTERS = ("open", "mine", "all")
STATUS = {"open": "o", "pending": "p", "closed": "c"}


class UpstreamError(Exception):
    """The backend is slow, down or refused: answer from cache or say so, never time out."""


class TicketsApi(Protocol):
    def list(self, user: str, flt: str, page: int, size: int) -> dict[str, Any]: ...
    def get(self, user: str, ticket_id: int) -> dict[str, Any]: ...
    def act(self, user: str, ticket_id: int, action: str) -> dict[str, Any]: ...


class MockTicketsApi:
    """Offline stand-in shaped like a typical REST API:
    GET /tickets?filter=&page=&size= -> {"items":[...], "total": n}; GET /tickets/{id};
    POST /tickets/{id}/{assign|close}."""

    def __init__(self) -> None:
        names = ["Login loop on Android 15", "Refund not received", "Export stuck at 60%",
                 "Wrong VAT on invoice", "Webhook returns 502", "Cannot change e-mail",
                 "Duplicate charge", "Dark mode contrast", "2FA code never arrives", "Bulk import fails"]
        self.tickets = {4100 + i: {"id": 4100 + i, "title": t, "status": "closed" if i in (3, 7) else
                                   ("pending" if i % 4 == 2 else "open"), "assignee": "u7" if i % 3 == 0 else None,
                                   "requester": ["Olena P.", "Marco R.", "Aiko T."][i % 3],
                                   "priority": ["High", "Normal", "Low"][i % 3], "updated": 1794733200 + 300 * i,
                                   "body": f"Customer report #{4100 + i}: {t.lower()}. Steps and logs attached."}
                        for i, t in enumerate(names)}
        self.fail_next = 0       # tests: simulate a slow upstream

    def _check(self) -> None:
        if self.fail_next:
            self.fail_next -= 1
            raise UpstreamError("timeout")

    def list(self, user: str, flt: str, page: int, size: int) -> dict[str, Any]:
        self._check()
        rows = [t for t in self.tickets.values()
                if flt == "all" or (flt == "open" and t["status"] != "closed") or (flt == "mine" and t["assignee"] == user)]
        rows.sort(key=lambda t: -t["updated"])
        return {"items": rows[(page - 1) * size: page * size], "total": len(rows)}

    def get(self, user: str, ticket_id: int) -> dict[str, Any]:
        self._check()
        if ticket_id not in self.tickets:
            raise KeyError(ticket_id)
        return self.tickets[ticket_id]

    def act(self, user: str, ticket_id: int, action: str) -> dict[str, Any]:
        self._check()
        t = self.get(user, ticket_id)
        if t["status"] == "closed":
            raise ValueError("already closed")
        if action == "assign":
            t["assignee"] = user
        else:
            t["status"] = "closed"
        t["updated"] += 60
        return t


class RestTicketsApi:
    """A live client to copy: base URL and token come from the bot's environment by NAME
    (WIDGET_API_BASE, WIDGET_API_TOKEN), never from the widget. Not used by tests or recipes."""

    def __init__(self, base: str | None = None, token_env: str = "WIDGET_API_TOKEN"):
        self.base = (base or os.environ.get("WIDGET_API_BASE", "")).rstrip("/")
        self.token_env = token_env

    def _call(self, method: str, path: str, user: str) -> dict[str, Any]:
        req = urllib.request.Request(self.base + path, method=method, headers={
            "Authorization": "Bearer " + os.environ.get(self.token_env, ""),
            "X-On-Behalf-Of": user, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, ValueError) as err:
            raise UpstreamError(type(err).__name__) from None

    def list(self, user, flt, page, size):
        return self._call("GET", "/tickets?" + urllib.parse.urlencode({"filter": flt, "page": page, "size": size}), user)

    def get(self, user, ticket_id):
        return self._call("GET", f"/tickets/{ticket_id}", user)

    def act(self, user, ticket_id, action):
        return self._call("POST", f"/tickets/{ticket_id}/{action}", user)


API: TicketsApi = MockTicketsApi()


def use_api(api: TicketsApi) -> TicketsApi:
    """Swap the backend (a fresh mock in tests, RestTicketsApi() in production)."""
    global API
    API = api
    return api
APP_LINK = "t.me/example_bot?startapp=t_"     # the Mini App for what a widget cannot do


def backend_user(ctx: Ctx) -> str:
    """Telegram authenticates from.id; map it to your backend's account server-side."""
    return {111111111: "u7"}.get(ctx.user_id, f"tg{ctx.user_id}")


def _row(t: dict) -> list:
    return [t["id"], t["title"][:40], STATUS[t["status"]], f"{t['requester']} · {t['priority']}"]


def _list_state(state: dict, ctx: Ctx, flt: str, page: int) -> tuple[dict, dict]:
    cache = ctx.memo.setdefault("cache", {})
    key = (backend_user(ctx), flt, page)
    hit = cache.get(key)
    if hit and ctx.now - hit[0] < CACHE_TTL:
        data, stale, at = hit[1], 0, hit[0]
    else:
        try:
            data, stale, at = API.list(backend_user(ctx), flt, page, PAGE), 0, ctx.now
            cache[key] = (ctx.now, data)
        except UpstreamError:
            if not hit:
                return None, {"err": "upstream", "msg": "The service is not answering. Try again in a minute."}
            data, stale, at = hit[1], 1, hit[0]
    pages = max(1, -(-data["total"] // PAGE))
    if page > pages:
        raise BadRequest(f"pg:{page}")
    new = {**state, "v": "l", "f": flt, "pg": page, "np": pages, "n": data["total"],
           "it": [_row(t) for t in data["items"]], "d": None, "at": int(at), "stale": stale}
    answer = {"msg": "Showing cached data"} if stale else {}
    return new, answer


def _detail(t: dict) -> dict:
    return {"id": t["id"], "t": t["title"], "st": STATUS[t["status"]], "by": t["requester"], "pr": t["priority"],
            "up": t["updated"], "tx": t["body"][:200]}


def decide(state: dict, act: Action, ctx: Ctx):
    user = backend_user(ctx)
    if act.verb == "sync":
        if state.get("v") == "d":
            return None, {}
        return _list_state(state, ctx, state.get("f", "open"), state.get("pg", 1))
    if act.verb == "f":
        if act.arg not in FILTERS:
            raise BadRequest(act.raw)
        return _list_state(state, ctx, act.arg, 1)
    if act.verb == "pg":
        return _list_state(state, ctx, state.get("f", "open"), act.int_arg(1, 999))
    if act.verb == "b":
        return _list_state(state, ctx, state.get("f", "open"), state.get("pg", 1))
    if act.verb == "o":
        try:
            t = API.get(user, act.int_arg(1, 10 ** 9))
        except KeyError:
            raise BadRequest(act.raw) from None
        except UpstreamError:
            return None, {"err": "upstream", "msg": "The service is not answering. Try again in a minute."}
        return {**state, "v": "d", "d": _detail(t), "app": APP_LINK, "stale": 0}, {}
    if act.verb == "x":
        tid, _, action = act.arg.partition(":")
        if action not in ("assign", "close") or not tid.isdigit():
            raise BadRequest(act.raw)
        try:
            t = API.act(user, int(tid), action)
        except KeyError:
            raise BadRequest(act.raw) from None
        except ValueError:
            return None, {"err": "conflict", "msg": "This ticket is already closed."}
        except UpstreamError:
            return None, {"err": "upstream", "msg": "Not saved: the service is not answering."}
        ctx.memo.pop("cache", None)              # writes invalidate cached pages
        verb = "Assigned to you" if action == "assign" else "Ticket closed"
        return {**state, "d": _detail(t)}, {"msg": f"{verb}: #{t['id']}"}
    raise BadRequest(act.raw)


SPEC = Spec(name="api-browser", decide=decide, demo=load_demo("api-browser"))
