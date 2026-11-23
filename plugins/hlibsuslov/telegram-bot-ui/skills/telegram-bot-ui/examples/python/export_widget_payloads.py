"""Write examples/payloads/r5N-*.json from the widget recipes' real request sequences.

Same format as export_payloads.py (which covers recipes 01-09); kept separate so the widget
recipes can be added without touching that file. The test suite runs --check.

Run:  py -3 examples/python/export_widget_payloads.py [--check]
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "recipes"))
OUT = os.path.join(os.path.dirname(HERE), "payloads")

# payload name -> (recipe module, status, context)
SCENARIOS = {
    "r50-monitoring-dashboard": ("r50_monitoring_dashboard", "production", "private"),
    "r51-booking": ("r51_booking", "production", "private"),
    "r52-shop-to-checkout": ("r52_shop_to_checkout", "production", "private"),
    "r53-shared-quiz-leaderboard": ("r53_shared_quiz_leaderboard", "production (shared widget re-sent to private chats)", "private"),
    "r54-job-progress": ("r54_job_progress", "production", "private"),
    "r55-design-a-widget": ("r55_design_a_widget", "production", "private"),
    "r56-api-data-browser": ("r56_api_data_browser", "production", "private"),
}


def build(name: str) -> dict:
    module, status, context = SCENARIOS[name]
    mod = importlib.import_module(module)
    with contextlib.redirect_stdout(io.StringIO()):
        transport = mod.run()[0]
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
        "bot_api": "10.5 (verified 2026-11-22)",
        "steps": [{"method": m, "params": p} for m, p in transport.calls],
    }


def available() -> list[str]:
    return [n for n, (mod, _, _) in SCENARIOS.items()
            if os.path.exists(os.path.join(HERE, "recipes", mod + ".py"))]


def main() -> int:
    check = "--check" in sys.argv
    drift = []
    for name in available():
        text = json.dumps(build(name), ensure_ascii=False, indent=2) + "\n"
        path = os.path.join(OUT, f"{name}.json")
        if check:
            current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if current != text:
                drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(available())} widget payload files in {os.path.relpath(OUT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
