"""Replay the send* steps of a payload file against a TEST bot (explicit opt-in).

  TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=... TELEGRAM_TEST_CHAT_ID=<your private chat id> \
    py -3 examples/python/live_send.py examples/payloads/r05-private-widget.json --yes
  Add TELEGRAM_TEST_ENV=1 for Telegram's test server (groups / inline / forwards).

Only send* methods are replayed (chat_id replaced by TELEGRAM_TEST_CHAT_ID).
Steps that need incoming context (answer*, edit* with ids from another run,
updates from users) are listed as manual - they can't be faked against a live
server. Destructive methods are never replayed. Never use a production token.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tgkit.errors import OutcomeUnknown, TelegramError  # noqa: E402
from tgkit.transport import live_transport_from_env  # noqa: E402

NEVER = {"deleteBusinessAccountGift", "promoteChatMember", "verifyChat", "verifyUser", "deleteEphemeralMessage"}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    transport = live_transport_from_env()
    chat = os.environ.get("TELEGRAM_TEST_CHAT_ID")
    if transport is None or not chat or "--yes" not in sys.argv:
        print("Live mode is off: set TELEGRAM_LIVE=1, TELEGRAM_TEST_BOT_TOKEN, TELEGRAM_TEST_CHAT_ID and pass --yes.")
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        doc = json.load(fh)
    for i, step in enumerate(doc["steps"], 1):
        method, params = step["method"], dict(step["params"])
        if method in NEVER or not method.startswith("send") or "ephemeral_message_parameters" in params:
            print(f"{i:2}. MANUAL  {method} (needs live context or is destructive)")
            continue
        params["chat_id"] = int(chat)
        params.pop("message_thread_id", None)
        params.pop("business_connection_id", None)
        try:
            result = transport.call(method, params)
            print(f"{i:2}. OK      {method} -> message_id={result.get('message_id') if isinstance(result, dict) else result}")
        except TelegramError as err:
            print(f"{i:2}. FAIL    {method}: {err.error_code} [{err.category}] {err.description}")
        except OutcomeUnknown:
            print(f"{i:2}. UNKNOWN {method}: timeout - check the chat before re-running")
    return 0


if __name__ == "__main__":
    sys.exit(main())
