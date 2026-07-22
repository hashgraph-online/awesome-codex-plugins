#!/usr/bin/env python3
"""Download and stage verified Codex skin packs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


RELEASE_BASE = "https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0"

PACKS = {
    "caishen-lite": "Soft fortune skin with readable working areas.",
    "caishen-readable": "Lower-strain fortune skin.",
    "caishen-max": "Brighter fortune skin for short immersive sessions.",
    "global-founder-bright": "Bright international growth/workspace skin.",
    "export-night": "Dark export-ops skin.",
    "mythic-guardian-noir": "Dark mythic focus skin.",
}


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def safe_extract(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination != target and destination not in target.parents:
                fail(f"unsafe zip path: {member.filename}")
        archive.extractall(destination)


def locate_pack_root(destination: Path) -> Path:
    candidates = []
    for path in [destination, *destination.iterdir()]:
        if path.is_dir() and (path / "theme.json").is_file() and (path / "background.png").is_file():
            candidates.append(path)
    if not candidates:
        fail("staged pack must contain theme.json and background.png")
    return candidates[0]


def validate_theme(pack_root: Path) -> None:
    theme_path = pack_root / "theme.json"
    try:
        json.loads(theme_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"theme.json is invalid JSON: {exc}")


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "codex-skin-pack-installer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status >= 400:
            fail(f"download failed with HTTP {response.status}")
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def stage_pack(slug: str, output_dir: Path) -> Path:
    if slug not in PACKS:
        fail(f"unknown pack '{slug}'. Run with --list to see available packs.")

    url = f"{RELEASE_BASE}/{slug}.zip"
    destination = output_dir.expanduser() / slug

    with tempfile.TemporaryDirectory(prefix="codex-skin-pack-") as temp_dir:
        temp_root = Path(temp_dir)
        zip_path = temp_root / f"{slug}.zip"
        staging = temp_root / "staged"
        staging.mkdir()
        download(url, zip_path)
        safe_extract(zip_path, staging)

        pack_root = locate_pack_root(staging)
        validate_theme(pack_root)

        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)

        if pack_root == staging:
            final_pack_root = destination
            for child in pack_root.iterdir():
                shutil.move(str(child), final_pack_root / child.name)
        else:
            final_pack_root = destination / pack_root.name
            shutil.move(str(pack_root), final_pack_root)

    manifest = {
        "slug": slug,
        "source": url,
        "stagedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "packRoot": str(final_pack_root),
    }
    (destination / "source.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return final_pack_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and stage verified Codex skin packs.")
    parser.add_argument("slug", nargs="?", help="Pack slug to stage")
    parser.add_argument(
        "--out",
        default=os.path.expanduser("~/.codexthemes/packs"),
        help="Output directory, default: ~/.codexthemes/packs",
    )
    parser.add_argument("--list", action="store_true", help="List available packs")
    args = parser.parse_args()

    if args.list:
        for slug, description in PACKS.items():
            print(f"{slug}\t{description}")
        return

    if not args.slug:
        fail("missing pack slug. Run with --list to see available packs.")

    pack_root = stage_pack(args.slug, Path(args.out))
    print(f"staged: {pack_root}")
    print("next: apply with your active Codex theme manager, then verify readability and restore path.")


if __name__ == "__main__":
    main()
