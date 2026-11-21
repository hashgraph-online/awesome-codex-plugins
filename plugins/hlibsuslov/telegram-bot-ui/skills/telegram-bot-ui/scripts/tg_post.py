#!/usr/bin/env python3
"""Validate, preview and publish a Telegram channel post described in JSON or Markdown.

  py -3 scripts/tg_post.py validate post.md [--context channel]
  py -3 scripts/tg_post.py preview  post.json [--chat @your_channel]
  py -3 scripts/tg_post.py publish  post.md --chat-env TG_CHANNEL_ID --token-env TG_BOT_TOKEN [--live]

* validate - limits, button rules for the context, media refs, entity offsets.
* preview  - prints the exact request payloads (one JSON object per line).
* publish  - dry run unless --live is given. Live mode reads the bot token and
  the chat id from the NAMED environment variables (never from arguments),
  never prints the token, and keeps an idempotency ledger (--ledger) so a
  re-run with the same --key never posts twice; a timeout is reported as
  "unknown" and must be reconciled by hand. Use a test bot and a test channel.

Post JSON = tgkit.publish.Post fields (see references/publishing-pipeline.md).
Markdown subset (one block per paragraph):
  # Title / ## Heading       - [ ] task / - [x] done / - item
  > quote  >> expandable quote (a last line "> — Name" is the credit)
  | a | b | table rows (first row = header)       ```lang code```     ---
  ![photo](file_id-or-https-url)   ![video](...)   [button: Label](https://...)
  Inline: **bold**, _italic_, `code`, ||spoiler||, [text](https://...)
  Optional front matter between "---" lines: kind, silent, protect, preview
  (a URL or "off"), caption_above, stars, rich_source (blocks | markdown | html:
  how a rich post is sent; the content is the same).
Exit codes: 0 ok, 1 invalid post or failed send, 2 usage / environment error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "examples", "python"))

from tgkit.publish import Ledger, Post, Publisher, plan, validate  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

INLINE_RE = re.compile(r"\*\*(.+?)\*\*|\|\|(.+?)\|\||`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|(?<!\w)_(.+?)_(?!\w)")
MEDIA_RE = re.compile(r"^!\[(photo|video|document)\]\(([^)\s]+)\)$")
BUTTON_RE = re.compile(r"\[button:\s*([^\]]+)\]\(([^)\s]+)\)")


def parse_inline(s: str):
    out, pos = [], 0
    for m in INLINE_RE.finditer(s):
        if m.start() > pos:
            out.append(s[pos:m.start()])
        bold, spoiler, code, ltext, url, italic = m.groups()
        if bold is not None:
            out.append({"bold": parse_inline(bold)})
        elif spoiler is not None:
            out.append({"spoiler": parse_inline(spoiler)})
        elif code is not None:
            out.append({"code": code})
        elif ltext is not None:
            out.append({"link": url, "text": parse_inline(ltext)})
        else:
            out.append({"italic": parse_inline(italic)})
        pos = m.end()
    if pos < len(s):
        out.append(s[pos:])
    return out[0] if len(out) == 1 else out


def parse_markdown(src: str) -> Post:
    d: dict = {"blocks": [], "media": [], "buttons": []}
    lines = src.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---" and "---" in [x.strip() for x in lines[1:]]:
        end = [x.strip() for x in lines[1:]].index("---") + 1
        for ln in lines[1:end]:
            if ":" in ln:
                k, v = (x.strip() for x in ln.split(":", 1))
                if k in ("silent", "protect", "caption_above"):
                    d[k] = v.lower() in ("1", "true", "yes")
                elif k in ("kind", "rich_source"):
                    d[k] = v
                elif k == "stars":
                    d["stars"] = int(v)
                elif k == "preview":
                    d["link_preview"] = {"disabled": True} if v == "off" else {"url": v, "large": True}
        lines = lines[end + 1:]
    paras, cur, in_code = [], [], False
    for ln in lines:
        if ln.startswith("```"):
            cur.append(ln)
            in_code = not in_code
            if not in_code:
                paras.append(cur)
                cur = []
            continue
        if not in_code and not ln.strip():
            if cur:
                paras.append(cur)
            cur = []
        else:
            cur.append(ln)
    if cur:
        paras.append(cur)
    for p in paras:
        first = p[0]
        if first.startswith("```"):
            d["blocks"].append({"type": "code", "text": "\n".join(p[1:-1]), **({"language": first[3:].strip()}
                                                                              if first[3:].strip() else {})})
        elif re.match(r"^#{1,6} ", first) and len(p) == 1:
            level = len(first) - len(first.lstrip("#"))
            d["blocks"].append({"type": "heading", "text": parse_inline(first[level + 1:]), **({"size": level} if level > 1 else {})})
        elif first.strip() == "---" and len(p) == 1:
            d["blocks"].append({"type": "divider"})
        elif all(MEDIA_RE.match(x.strip()) for x in p):
            d["media"] += [{"type": m.group(1), "ref": m.group(2)} for m in (MEDIA_RE.match(x.strip()) for x in p)]
        elif all(BUTTON_RE.search(x) for x in p):
            d["buttons"] += [[{"text": t.strip(), "url": u} for t, u in BUTTON_RE.findall(x)] for x in p]
        elif all(x.startswith(("- ", "* ")) for x in p):
            items = []
            for x in p:
                body = x[2:]
                m = re.match(r"^\[( |x|X)\] (.*)$", body)
                items.append({"text": parse_inline(m.group(2)), "done": m.group(1) != " "} if m else parse_inline(body))
            d["blocks"].append({"type": "list", "items": items})
        elif all(x.startswith(">") for x in p):
            expandable = first.startswith(">>")
            body = [x.lstrip(">").strip() for x in p]
            credit = body.pop()[2:].strip() if len(body) > 1 and body[-1].startswith("— ") else None
            blk = {"type": "quote", "text": parse_inline("\n".join(body)), "expandable": expandable}
            if credit:
                blk["credit"] = credit
            d["blocks"].append(blk)
        elif all(x.strip().startswith("|") for x in p):
            rows = [[cell.strip() for cell in x.strip().strip("|").split("|")] for x in p
                    if not re.match(r"^\|?\s*:?-{2,}", x.strip())]
            d["blocks"].append({"type": "table", "header": rows[0], "rows": rows[1:]})
        else:
            d["blocks"].append({"type": "paragraph", "text": parse_inline("\n".join(p))})
    return Post.from_dict(d)


def load_post(path: str) -> Post:
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if path.lower().endswith(".json"):
        return Post.from_dict(json.loads(src))
    return parse_markdown(src)


def _print_issues(issues) -> bool:
    ok = True
    for i in issues:
        ok &= i.level != "error"
        print(f"{i.level.upper():5} {i.code}: {i.message}")
    return ok


def _chat(value: str):
    return int(value) if re.fullmatch(r"-?\d+", value) else value


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "preview", "publish"):
        s = sub.add_parser(name)
        s.add_argument("file")
        s.add_argument("--context", default="channel", choices=["channel", "channel_dm", "group", "private"])
        s.add_argument("--custom-emoji-ok", action="store_true",
                       help="the bot has Fragment usernames (custom emoji allowed in channels)")
        if name == "preview":
            s.add_argument("--chat", default="@your_channel", help="chat id or @username used in the payloads")
        if name == "publish":
            s.add_argument("--chat-env", required=True, help="NAME of the env var holding the target chat id")
            s.add_argument("--token-env", required=True, help="NAME of the env var holding the bot token")
            s.add_argument("--live", action="store_true", help="really send (default: dry run)")
            s.add_argument("--test-server", action="store_true", help="use Telegram's test environment")
            s.add_argument("--key", help="idempotency key (default: hash of the post and chat)")
            s.add_argument("--ledger", default=".tg_post_ledger.json", help="ledger file for idempotency")
    a = ap.parse_args(argv)
    try:
        post = load_post(a.file)
    except (OSError, ValueError, KeyError) as exc:
        print(f"cannot read post: {exc}", file=sys.stderr)
        return 2
    issues = validate(post, context=a.context, custom_emoji_ok=a.custom_emoji_ok,
                      live=getattr(a, "live", False))
    ok = _print_issues(issues)
    if a.cmd == "validate":
        print("OK" if ok else "INVALID")
        return 0 if ok else 1
    if not ok:
        print("INVALID: nothing sent")
        return 1
    if a.cmd == "preview":
        for method, params in plan(post, _chat(a.chat)):
            print(json.dumps({"method": method, "params": params}, ensure_ascii=False))
        return 0

    chat_raw = os.environ.get(a.chat_env)
    if not chat_raw:
        print(f"environment variable {a.chat_env} is not set", file=sys.stderr)
        return 2
    chat = _chat(chat_raw.strip())
    key = a.key or "cli:" + hashlib.sha256(json.dumps([post.to_dict(), chat], sort_keys=True,
                                                      ensure_ascii=False).encode()).hexdigest()[:16]
    if not a.live:
        for method, params in plan(post, chat):
            print(json.dumps({"method": method, "params": params}, ensure_ascii=False))
        print(f"dry run: nothing sent (key {key}); add --live to publish")
        return 0
    token = os.environ.get(a.token_env)
    if not token:
        print(f"environment variable {a.token_env} is not set", file=sys.stderr)
        return 2
    from tgkit.transport import HttpTransport
    transport = HttpTransport(token, test_environment=a.test_server)
    del token
    result = Publisher(transport, Ledger(a.ledger), context=a.context,
                       custom_emoji_ok=a.custom_emoji_ok).publish(post, chat, key)
    print(json.dumps({"status": result.status, "key": result.key, "message_ids": result.message_ids,
                      "detail": result.detail}, ensure_ascii=False))
    return 0 if result.status in ("sent", "already_sent") else 1


if __name__ == "__main__":
    sys.exit(main())
