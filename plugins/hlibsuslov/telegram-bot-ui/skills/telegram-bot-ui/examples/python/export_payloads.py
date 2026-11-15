"""Write examples/payloads/*.json from the recipes' real request sequences.

The payload files are the SDK-independent layer: exactly the JSON each recipe
puts on the wire (captured after a JSON round trip by FakeTransport). A second
adapter (TypeScript, another SDK, raw HTTP) can replay them. The test suite
regenerates them and fails if a file drifted from the code.

Run:  py -3 examples/python/export_payloads.py [--check]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "recipes"))
OUT = os.path.join(os.path.dirname(HERE), "payloads")

import mini_recipes  # noqa: E402
import r01_ai_assistant  # noqa: E402
import r02_interactive_document  # noqa: E402
import r03_multi_step_form  # noqa: E402
import r04_shared_card_personal_panel  # noqa: E402
import r05_private_widget  # noqa: E402
import r06_shared_widget  # noqa: E402
import r07_wallet  # noqa: E402
import r08_multi_topic_bot  # noqa: E402
import r09_tracker_bot  # noqa: E402

SCENARIOS = {
    "r01-ai-stop-keep-marked": (lambda: r01_ai_assistant.run("keep_marked", "stop")[0], "production", "private"),
    "r01-ai-stop-discard": (lambda: r01_ai_assistant.run("discard", "stop")[0], "production", "private"),
    "r01-ai-complete": (lambda: r01_ai_assistant.run("keep_marked", "complete")[0], "production", "private"),
    "r02-interactive-document": (lambda: r02_interactive_document.run()[0], "production", "private"),
    "r03-multi-step-form": (lambda: r03_multi_step_form.run()[0], "production", "private"),
    "r04-shared-card-personal-panel": (lambda: r04_shared_card_personal_panel.run()[0], "production", "supergroup"),
    "r05-private-widget": (lambda: r05_private_widget.run()[0], "production", "private"),
    "r06-shared-widget": (lambda: r06_shared_widget.run()[0], "production + test-server parts", "private; forwards/inline on test server"),
    "r07-wallet": (lambda: r07_wallet.run()[0], "production", "private"),
    "r08-multi-topic-bot": (lambda: r08_multi_topic_bot.run()[0], "production", "private chat with topics"),
    "r09-tracker-bot": (lambda: r09_tracker_bot.run()[0], "production (widgets in private chats)", "private"),
    "mini-recipes": (lambda: mini_recipes.run_all(), "production (destructive calls dry-run)", "mixed"),
}


def build(name: str) -> dict:
    fn, status, context = SCENARIOS[name]
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        transport = fn()
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
        "bot_api": "10.4 (verified 2026-11-12)",
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
            with open(path, encoding="utf-8") as fh:
                if fh.read() != text:
                    drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(SCENARIOS)} payload files in {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
