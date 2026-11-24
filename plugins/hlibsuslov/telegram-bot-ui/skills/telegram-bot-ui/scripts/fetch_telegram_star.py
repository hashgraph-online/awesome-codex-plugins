#!/usr/bin/env python3
"""Download Telegram's original Stars glyph into YOUR app (not into this skill).

  py -3 scripts/fetch_telegram_star.py --out <app>/assets --accept-gpl
  py -3 scripts/fetch_telegram_star.py --info            # what is fetched, from where, under which licence

The kit draws its own gold star (`_kit/icons.svg#i-stars-gold`, MIT with the skill). Telegram's own artwork
lives in Telegram Web A (github.com/Ajaxy/telegram-tt), licensed GPL-3.0: shipping it in an app makes that
file GPL-3.0 inside the app, so the choice is the app owner's. This script pins the commit, checks the
SHA-256 of each file and writes a LICENSE-telegram-star.txt next to them. Without --accept-gpl it downloads
nothing. Reference: references/mini-apps/telegram-elements.md T1.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request

REPO = "Ajaxy/telegram-tt"
COMMIT = "4566a14adb6287867f21ed6c51449292581c8653"  # checked 2026-11-24
FILES = {
    "src/assets/icons/star/GoldStar.svg": "1bb6ccef1cca96f26e6f3e72e314c91a53c4ca8558fee0ec0ca00b41582e9917",
    "src/assets/icons/star/GoldStarFill.svg": "d0c7411d670b846c8e3764620625743e90bea5ddac6b95d35537530d8a9e6f16",
}
NOTICE = f"""Telegram Stars glyph (GoldStar.svg, GoldStarFill.svg)
Source: https://github.com/{REPO}/tree/{COMMIT}/src/assets/icons/star
Licence: GNU General Public License v3.0 (https://www.gnu.org/licenses/gpl-3.0.html), as the source repository.
Fetched by telegram-bot-ui's scripts/fetch_telegram_star.py; unmodified, SHA-256 checked.
"""


def raw_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{path}"


def fetch(out: str) -> list[str]:
    os.makedirs(out, exist_ok=True)
    written = []
    for path, sha in FILES.items():
        with urllib.request.urlopen(raw_url(path), timeout=30) as r:
            body = r.read()
        got = hashlib.sha256(body).hexdigest()
        if got != sha:
            raise SystemExit(f"hash mismatch for {path}: expected {sha}, got {got}; nothing written for it")
        target = os.path.join(out, os.path.basename(path))
        with open(target, "wb") as fh:
            fh.write(body)
        written.append(target)
    notice = os.path.join(out, "LICENSE-telegram-star.txt")
    with open(notice, "w", encoding="utf-8") as fh:
        fh.write(NOTICE)
    return written + [notice]


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Fetch Telegram's original Stars glyph (GPL-3.0) into an app")
    ap.add_argument("--out", help="folder in your app, e.g. my-app/assets")
    ap.add_argument("--accept-gpl", action="store_true", help="the app owner accepts GPL-3.0 for these files")
    ap.add_argument("--info", action="store_true")
    args = ap.parse_args(argv)
    if args.info or not args.out:
        print(NOTICE)
        for path, sha in FILES.items():
            print(f"{raw_url(path)}\n  sha256 {sha}")
        print("\nUse: --out <app>/assets --accept-gpl. Without it the kit's own i-stars-gold glyph stays in use.")
        return 0 if args.info else 2
    if not args.accept_gpl:
        print("refused: these files are GPL-3.0; pass --accept-gpl if the app owner agrees (see --info)")
        return 2
    for p in fetch(args.out):
        print(f"wrote {p}")
    print('Use it in place of the kit glyph: <img class="tma-star" src="assets/GoldStar.svg" alt="">')
    return 0


if __name__ == "__main__":
    sys.exit(main())
