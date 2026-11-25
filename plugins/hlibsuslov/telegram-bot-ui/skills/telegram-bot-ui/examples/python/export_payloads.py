"""Write examples/payloads/*.json from the recipes' real request sequences.

The payload files are the SDK-independent layer: exactly the JSON each recipe
puts on the wire (captured after a JSON round trip by FakeTransport). A second
adapter (TypeScript, another SDK, raw HTTP) can replay them. The test suite
regenerates them and fails if a file drifted from the code.

Per-method API examples live in recipes/api_<domain>.py and are found by name, so a new
domain never edits this file. Such a module defines:
  STATUS = "production"                      # the payload's "status"
  CONTEXT = "private; supergroup admin"      # the payload's "context"
  STEP_CONTEXT = {"<methodName>": "supergroup; bot admin with <right>"}  # optional
  def run_all() -> FakeTransport             # every request of the domain, offline
and is written to payloads/api-<domain>.json (underscores become dashes). A step whose method
is in STEP_CONTEXT carries "_context": the chat type and rights the call needs.

Run:  py -3 examples/python/export_payloads.py [--check] [--only NAME ...]
"""
from __future__ import annotations

import glob
import importlib
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
import r10_bot_settings  # noqa: E402

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
    "r10-bot-settings": (lambda: r10_bot_settings.run()[0], "production", "private"),
    "mini-recipes": (lambda: mini_recipes.run_all(), "production (destructive calls dry-run)", "mixed"),
}
for _path in sorted(glob.glob(os.path.join(HERE, "recipes", "api_*.py"))):
    _mod = importlib.import_module(os.path.basename(_path)[:-3])
    SCENARIOS["api-" + _mod.__name__[4:].replace("_", "-")] = (
        _mod.run_all, _mod.STATUS, _mod.CONTEXT, getattr(_mod, "STEP_CONTEXT", {}))


def build(name: str) -> dict:
    fn, status, context, *rest = SCENARIOS[name]
    step_context = rest[0] if rest else {}
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        transport = fn()
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
        "bot_api": "10.5 (verified 2026-11-22)",
        "steps": [{"method": m, **({"_context": step_context[m]} if m in step_context else {}), "params": p}
                  for m, p in transport.calls],
    }


def orphans(out_dir: str, names) -> list[str]:
    """api-*.json payloads whose recipes/api_*.py module is gone: they would still count as examples."""
    return sorted(f for f in os.listdir(out_dir) if f.startswith("api-") and f.endswith(".json")
                  and f[:-5] not in names)


def parse_args(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail when a payload file differs from its recipe")
    ap.add_argument("--only", nargs="+", action="extend", metavar="NAME", help="these scenarios only")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    check, only = args.check, args.only or []
    unknown = [n for n in only if n not in SCENARIOS]
    if unknown:
        print("unknown scenario:", ", ".join(unknown), "- known:", ", ".join(SCENARIOS))
        return 2
    os.makedirs(OUT, exist_ok=True)
    drift = []
    if check and not only:
        drift += [f"{f} (no recipes/api_*.py module makes it)" for f in orphans(OUT, SCENARIOS)]
    names = only or list(SCENARIOS)
    for name in names:
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
    print(f"{'checked' if check else 'wrote'} {len(names)} payload files in {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
