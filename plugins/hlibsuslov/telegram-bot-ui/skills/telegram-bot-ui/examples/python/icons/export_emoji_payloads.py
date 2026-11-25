"""Write examples/payloads/r7N-*.json from recipes 70-76 (same format as export_payloads.py).

Kept separate so the premium-emoji recipes can be exported and drift-checked on their own;
the SCENARIOS below can be merged into examples/python/export_payloads.py later.

Run:  py -3 examples/python/icons/export_emoji_payloads.py [--check]
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

PY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PY)
sys.path.insert(0, os.path.join(PY, "recipes"))
OUT = os.path.join(os.path.dirname(PY), "payloads")

import r70_restyle_to_premium  # noqa: E402
import r71_icons_from_zero  # noqa: E402
import r72_channel_post_series  # noqa: E402
import r73_mixed_eligibility  # noqa: E402
import r74_premium_lapse  # noqa: E402
import r75_migrate_pack  # noqa: E402
import r76_own_emoji_pack  # noqa: E402

SCENARIOS = {
    "r70-restyle-to-premium": (lambda: r70_restyle_to_premium.run()[0], "production (fixture ids)", "private"),
    "r71-icons-from-zero": (lambda: r71_icons_from_zero.run()[0], "production (fixture ids)", "private"),
    "r72-channel-post-series": (lambda: r72_channel_post_series.run(fragment=True)[0], "production (fixture ids; Fragment route)", "channel"),
    "r73-mixed-eligibility": (lambda: r73_mixed_eligibility.run()[0], "production (fixture ids)", "private, group, supergroup, channel, business, inline"),
    "r74-premium-lapse": (lambda: r74_premium_lapse.run()[0], "production (fixture ids; illustrative error text)", "private"),
    "r75-migrate-pack": (lambda: r75_migrate_pack.run()[0], "production (fixture ids)", "private"),
    "r76-own-emoji-pack": (lambda: r76_own_emoji_pack.run()[0], "production (fixture ids)", "private"),
}


def build(name: str) -> dict:
    fn, status, context = SCENARIOS[name]
    with contextlib.redirect_stdout(io.StringIO()):
        transport = fn()
    return {
        "scenario": name,
        "status": status,
        "context": context,
        "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram; "
                    "ids are synthetic fixture ids (leading 0), never real custom_emoji_id values",
        "bot_api": "10.5 (verified 2026-11-22)",
        "steps": [{"method": m, "params": p} for m, p in transport.calls],
    }


def main() -> int:
    check = "--check" in sys.argv
    drift = []
    for name in SCENARIOS:
        text = json.dumps(build(name), ensure_ascii=False, indent=2) + "\n"
        path = os.path.join(OUT, f"{name}.json")
        if check:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
                drift.append(name)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    if drift:
        print("payloads out of date:", ", ".join(drift))
        return 1
    print(f"{'checked' if check else 'wrote'} {len(SCENARIOS)} payload files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
