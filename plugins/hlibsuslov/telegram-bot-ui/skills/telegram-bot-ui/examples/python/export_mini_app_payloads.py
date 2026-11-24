"""Write examples/payloads/r90..r99-*.json from the Mini App recipes' real request sequences.

Same contract as export_payloads.py: captured from the recipe code through FakeTransport, never hand-written;
the tests regenerate them and fail on drift.

Run:  py -3 examples/python/export_mini_app_payloads.py [--check]
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "recipes"))
OUT = os.path.join(os.path.dirname(HERE), "payloads")

import r90_99_mini_apps as r  # noqa: E402

SCENARIOS = {
    "r90-decide-and-hybrid": ("r90", "production", "private chat; the alert link works in any chat"),
    "r91-minimal-mini-app": ("r91", "production", "private chat (menu and inline web_app buttons)"),
    "r92-init-data-session": ("r92", "production", "server verifies initData, then answers the query"),
    "r93-mini-app-shop": ("r93", "production", "Mini App opens the invoice; the bot gets successful_payment"),
    "r94-form-booking": ("r94", "production", "reply-keyboard launch (sendData -> web_app_data)"),
    "r95-dashboard-portfolio": ("r95", "production", "alert with a startapp link"),
    "r96-profile-settings": ("r96", "production", "write access from the Mini App, then a bot message"),
    "r97-game-fullscreen": ("r97", "production", "fullscreen link and a prepared share message"),
    "r98-share-result": ("r98", "production", "prepared message, query answer, prepared chat picker"),
    "r99-editor": ("r99", "production", "revisioned drafts, publish confirmation"),
}


def build(name: str) -> dict:
    key, status, context = SCENARIOS[name]
    with contextlib.redirect_stdout(io.StringIO()):
        transport = r.SCENARIOS[key]()[0]
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
        "bot_api": "10.5 (verified 2026-11-23)",
        "steps": [{"method": m, "params": p} for m, p in transport.calls],
    }


def main() -> int:
    check = "--check" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    drift = []
    for name in SCENARIOS:
        text = json.dumps(build(name), ensure_ascii=False, indent=2) + "\n"
        path = os.path.join(OUT, f"{name}.json")
        if check:
            if not os.path.isfile(path):
                drift.append(name)
                continue
            with open(path, encoding="utf-8") as fh:
                if fh.read() != text:
                    drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(SCENARIOS)} Mini App payload files in {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
