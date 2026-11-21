"""Command line: py -3 -m agent_bridge <command> [options]   (from examples/python)
or            py -3 path/to/examples/python/agent_bridge <command> [options]

Dry-run by default: requests are printed (redacted) to stderr and nothing is
sent. Incoming updates come from --fixture. Live mode needs BOTH `--live` and
the env vars named by --token-env / --operator-env; the token is never printed.

stdout carries exactly one JSON object (JSON lines for `listen`).
Exit codes: 0 ok / approved / answered, 3 rejected, 4 timeout or expired,
1 refused or failed, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from .approvals import IdFactory
from .bridge import AgentBridge, BridgeConfig, VirtualClock
from .intake import ALLOWED_UPDATES, FixtureSource, PollingSource
from .redact import Redactor
from .security import Allowlist
from .store import JsonStore
from .transport import DryRunTransport, live_from_env
from . import hooks
from tgkit.errors import OutcomeUnknown, TelegramError

DEMO_OPERATOR = 111111111          # offline demo id (fixtures use it); never a real account
EXIT = {"approved": 0, "answered": 0, "rejected": 3, "expired": 4, "timeout": 4}


def _common(suppress: bool) -> argparse.ArgumentParser:
    """Global options, accepted before or after the command name."""
    c = argparse.ArgumentParser(add_help=False)
    d = (lambda v: argparse.SUPPRESS) if suppress else (lambda v: v)
    c.add_argument("--live", action="store_true", default=d(False),
                   help="really call Telegram (needs the env vars below)")
    c.add_argument("--token-env", default=d("AGENT_BRIDGE_TOKEN"), help="NAME of the env var holding the bot token")
    c.add_argument("--operator-env", default=d("AGENT_BRIDGE_OPERATOR_ID"),
                   help="NAME of the env var with operator numeric ids (comma-separated)")
    c.add_argument("--members-env", default=d("AGENT_BRIDGE_MEMBER_IDS"), help="NAME of env var: team member ids")
    c.add_argument("--groups-env", default=d("AGENT_BRIDGE_GROUP_IDS"), help="NAME of env var: allowed group chat ids")
    c.add_argument("--state", default=d(os.environ.get("AGENT_BRIDGE_STATE")),
                   help="state file (offset, pending requests, status cards); needed to resume")
    c.add_argument("--fixture", default=d(None),
                   help="offline: JSON file with incoming updates (list or {updates: [...]})")
    c.add_argument("--seed", default=d(None), help="offline: deterministic request ids (default 'offline')")
    c.add_argument("--bot-username", default=d(os.environ.get("AGENT_BRIDGE_BOT_USERNAME")))
    c.add_argument("--quiet", action="store_true", default=d(False), help="dry-run: don't print requests to stderr")
    return c


def _parser() -> argparse.ArgumentParser:
    sub_common = _common(True)
    p = argparse.ArgumentParser(prog="agent_bridge", parents=[_common(False)],
                                description="An agent's Telegram bridge to its operator.")
    sub = p.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda *a, **k: _add(*a, parents=[sub_common], **k)  # type: ignore[method-assign]

    s = sub.add_parser("notify", help="one-way message")
    s.add_argument("text")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--thread", type=int)

    s = sub.add_parser("progress", help="create/update/finish one status card")
    s.add_argument("--key", required=True)
    s.add_argument("--title")
    s.add_argument("--stages", help="comma-separated stage names")
    s.add_argument("--stage")
    s.add_argument("--note")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--done", action="store_true")
    g.add_argument("--failed", action="store_true")
    s.add_argument("--thread", type=int)

    s = sub.add_parser("ask", help="ask and wait for an answer")
    s.add_argument("question")
    s.add_argument("--choice", action="append", dest="choices")
    s.add_argument("--timeout", type=float, default=600)
    s.add_argument("--remind-after", type=float)
    s.add_argument("--default")
    s.add_argument("--placeholder")
    s.add_argument("--thread", type=int)

    s = sub.add_parser("approve", help="request approval and wait for the decision")
    s.add_argument("summary")
    s.add_argument("--details")
    s.add_argument("--ttl", type=float, default=900)
    s.add_argument("--destructive", action="store_true", help="red Approve button")
    s.add_argument("--thread", type=int)

    s = sub.add_parser("wait", help="resume waiting for a pending request (after a restart)")
    s.add_argument("request_id")
    sub.add_parser("pending", help="list open requests in the state file")

    s = sub.add_parser("send-file", help="send a file as a document to the operator")
    s.add_argument("path")
    s.add_argument("--caption")
    s.add_argument("--no-scan", action="store_true", help="skip the secret scan (binary or reviewed files)")

    s = sub.add_parser("report", help="send a Rich Message report")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--json", dest="json_path", help="report JSON (title, summary, table, items, log_tail)")
    g.add_argument("--markdown", dest="md_path", help="Rich Markdown file")

    s = sub.add_parser("listen", help="emit allowlisted commands/messages as JSON lines")
    s.add_argument("--max-events", type=int)

    s = sub.add_parser("hook", help="adapter for coding-agent hooks (reads hook JSON on stdin)")
    s.add_argument("kind", choices=["claude-notification", "claude-stop", "claude-permission",
                                    "codex-stop", "codex-permission", "codex-notify"])
    s.add_argument("--ttl", type=float, default=240, help="approval TTL; keep below the hook timeout")
    s.add_argument("--on-timeout", choices=["none", "deny"], default="none",
                   help="none = fall back to the local prompt; deny = refuse")
    s.add_argument("payload", nargs="?", help="codex-notify: JSON passed as an argument")

    s = sub.add_parser("export-payloads", help="regenerate examples/payloads/r4N-*.json")
    s.add_argument("--check", action="store_true")
    return p


def build(args: argparse.Namespace, environ: dict[str, str] | None = None,
          transport: Any = None) -> tuple[AgentBridge, Any]:
    env = os.environ if environ is None else environ
    redactor = Redactor()
    operators = env.get(args.operator_env)
    if args.live:
        transport = transport or live_from_env(args.token_env, environ=env)
        redactor.add(env.get(args.token_env))
        if not operators:
            raise SystemExit(f"--live needs operator ids in the environment variable {args.operator_env}.")
        clock, sleep, ids = None, None, IdFactory()
    else:
        transport = transport or DryRunTransport()
        redactor.add(env.get(args.token_env))      # even offline, never echo it
        operators = operators or str(DEMO_OPERATOR)
        vc = VirtualClock(1_762_900_000.0)
        clock, sleep, ids = vc, vc.sleep, IdFactory(args.seed or "offline")
    allow = Allowlist.parse(operators, env.get(args.members_env), env.get(args.groups_env))
    cfg = BridgeConfig(chat_id=sorted(allow.operators)[0], allow=allow, bot_username=args.bot_username)
    store = JsonStore(args.state)
    log = _stderr_log if not args.quiet else (lambda e: None)
    kwargs: dict[str, Any] = {"store": store, "redactor": redactor, "ids": ids, "log": log}
    if clock is not None:
        kwargs.update(clock=clock, sleep=sleep)
    bridge = AgentBridge(transport, cfg, **kwargs)
    if args.live:
        bridge.source = PollingSource(bridge.call, store, allowed_updates=list(ALLOWED_UPDATES))
    else:
        bridge.source = FixtureSource(_load_fixture(args.fixture), clock=bridge.clock)
    bridge.intake.source = bridge.source
    return bridge, transport


def _load_fixture(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("updates", [data])
    return data


def _stderr_log(event: dict[str, Any]) -> None:
    print(json.dumps({"log": event}, ensure_ascii=False), file=sys.stderr)


_OUTPUT_REDACTOR: Redactor | None = None    # set once the bridge exists; every result passes it


def _out(obj: Any) -> None:
    if _OUTPUT_REDACTOR is not None:
        obj = _OUTPUT_REDACTOR.obj(obj)
    print(json.dumps(obj, ensure_ascii=False))


def _read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {}
    return data if isinstance(data, dict) else {}


def run(argv: list[str] | None = None, *, environ: dict[str, str] | None = None, transport: Any = None) -> int:
    args = _parser().parse_args(argv)
    if args.cmd == "export-payloads":
        from .payloads import main as export_main
        return export_main(check=args.check)
    bridge, tr = build(args, environ, transport)
    global _OUTPUT_REDACTOR
    _OUTPUT_REDACTOR = bridge.redactor
    try:
        code = _dispatch(args, bridge)
    except (PermissionError, ValueError, KeyError, FileNotFoundError) as err:
        _out({"ok": False, "error": bridge.redactor.text(str(err))})
        code = 1
    except TelegramError as err:
        _out({"ok": False, "error": bridge.redactor.text(str(err)), "class": err.category})
        code = 1
    except OutcomeUnknown as err:      # a send may have been delivered: report, don't repeat
        _out({"ok": False, "error": str(err), "class": "outcome_unknown"})
        code = 1
    finally:
        if not args.live and not args.quiet:
            for method, params in getattr(tr, "calls", []):
                print("DRY-RUN " + method + " " + json.dumps(bridge.redactor.obj(params), ensure_ascii=False),
                      file=sys.stderr)
    return code


def _dispatch(args: argparse.Namespace, b: AgentBridge) -> int:
    if args.cmd == "notify":
        _out(b.notify(args.text, silent=args.silent, thread_id=args.thread))
        return 0
    if args.cmd == "progress":
        state = "done" if args.done else "failed" if args.failed else "running"
        stages = [s.strip() for s in args.stages.split(",")] if args.stages else None
        _out(b.progress(args.key, title=args.title, stages=stages, stage=args.stage, note=args.note,
                        state=state, thread_id=args.thread))
        return 0
    if args.cmd == "ask":
        res = b.ask(args.question, choices=args.choices, timeout=args.timeout, remind_after=args.remind_after,
                    default=args.default, placeholder=args.placeholder, thread_id=args.thread)
        _out(res)
        return EXIT[res["status"]]
    if args.cmd == "approve":
        res = b.approve(args.summary, details=args.details, ttl=args.ttl, destructive=args.destructive,
                        thread_id=args.thread)
        _out(res)
        return EXIT[res["decision"]]
    if args.cmd == "wait":
        res = b.wait(args.request_id)
        _out(res)
        return EXIT[res.get("decision") or res["status"]]
    if args.cmd == "pending":
        _out({"open": [{k: r[k] for k in ("rid", "kind", "summary", "expires", "message_id")}
                       for r in b.store.open_requests().values()]})
        return 0
    if args.cmd == "send-file":
        _out(b.send_file(args.path, caption=args.caption, scan=not args.no_scan))
        return 0
    if args.cmd == "report":
        if args.json_path:
            with open(args.json_path, encoding="utf-8") as fh:
                _out(b.report(data=json.load(fh)))
        else:
            with open(args.md_path, encoding="utf-8") as fh:
                _out(b.report(markdown=fh.read()))
        return 0
    if args.cmd == "listen":
        for ev in b.listen(max_events=args.max_events):
            _out(ev)
            sys.stdout.flush()
        return 0
    if args.cmd == "hook":
        return _hook(args, b)
    raise SystemExit(2)


def _hook(args: argparse.Namespace, b: AgentBridge) -> int:
    kind = args.kind
    if kind == "codex-notify":
        try:
            payload = json.loads(args.payload or "{}")
        except ValueError:
            payload = {}
        b.notify(hooks.codex_notify_text(payload if isinstance(payload, dict) else {}))
        return 0
    payload = _read_stdin_json()
    if kind == "claude-notification":
        b.notify(hooks.notification_text(payload))
        return 0
    if kind in ("claude-stop", "codex-stop"):
        text = hooks.stop_text(payload)
        if text:
            b.notify(text, silent=True)
        if kind == "codex-stop":
            _out({})                       # Codex Stop expects JSON on stdout when it exits 0
        return 0
    summary, details = hooks.permission_summary(payload)
    if not hooks.permission_reviewable(payload):
        b.notify(summary + "\nToo long to review here: answer it at the computer.")
        _out(hooks.permission_output(None))   # no decision -> the host's local prompt
        return 0
    res = b.approve(summary, details=details, ttl=args.ttl)
    decision = {"approved": "allow", "rejected": "deny"}.get(res["decision"])
    if decision is None and args.on_timeout == "deny":
        decision = "deny"
    _out(hooks.permission_output(decision, "Rejected by the operator over Telegram." if decision == "deny" else None))
    return 0                               # the decision travels in JSON; exit 2 isn't honoured here


def main() -> None:
    sys.exit(run())


__all__ = ["run", "build", "main"]
