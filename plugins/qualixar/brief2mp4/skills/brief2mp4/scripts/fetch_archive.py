#!/usr/bin/env python3
"""fetch_archive.py: find and download archive photos, maps and documents you can put in a video, with the credit written for you.

Searches Wikimedia Commons (https://commons.wikimedia.org) and Openverse (https://openverse.org) and keeps only public
domain, CC0 and CC BY. ShareAlike, NonCommercial, NoDerivatives and anything unknown or "no restrictions" are rejected,
both in the request and again on every answer, so a server that ignores the filter changes nothing.

  python3 fetch_archive.py search "submarine cable ship" [--source commons|openverse|both] [--kind photo|map|document]
  python3 fetch_archive.py download "submarine cable ship" --pick 1 --out-dir assets/archive --assets ASSETS.json

A download is checked to be a real PNG, JPEG or WebP and stops at 25 MB. Commons is asked for a 1920 px copy of wide files;
anything still over 1920 px on its longest side (an Openverse original, a tall scan) is scaled down with ffmpeg when it is
installed (otherwise kept as it came, and the record says so). It is recorded in ASSETS.json: file, source URL, author,
licence, attribution text, size, SHA-256 of the saved file and the date. Running it again for the same
picture changes nothing. Server errors (5xx), rate limits (429) and dropped connections are retried with a growing wait,
and requests are spaced --delay seconds apart. Public domain is as the host tags it, which differs by country: check
the source page before a commercial release. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_music import FetchError, http_get  # noqa: E402  (retry, 429 and 5xx handling are shared with the music fetcher)

AGENT = "brief2mp4-fetch-archive/1.0 (+https://github.com/qualixar/brief2mp4)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
ALLOWED_QUERY = "cc0,pdm,by"
MAX_WIDTH = 1920
KIND_WORDS = {"photo": "", "map": " map", "document": " document"}
IMAGE_MIMES = ("image/jpeg", "image/png", "image/webp")
_last_call = [0.0]


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(markup: str | None) -> str:
    """Commons returns names and captions as HTML: reduce to the words."""
    parser = _Text()
    parser.feed(html.unescape(markup or "") if "<" not in (markup or "") else markup or "")
    return re.sub(r"\s+", " ", html.unescape("".join(parser.parts))).strip()


def licence_code(raw) -> str | None:
    """cc0, pdm (public domain) or by (CC BY, any version); None for everything else, so the caller must drop it."""
    s = re.sub(r"[\s_]+", "-", str(raw or "").strip().lower())
    if re.fullmatch(r"cc0(-\d\.\d)?|cc-zero", s):
        return "cc0"
    if s in ("pd", "pdm", "public-domain") or re.fullmatch(r"pd-[a-z0-9.\-]+", s):
        return "pdm"
    if re.fullmatch(r"(?:cc-)?by(?:-\d(?:\.\d)?)?", s):
        return "by"
    return None


def licence_name(code: str, version: str | None) -> str:
    return {"cc0": "CC0 1.0 (public domain dedication)", "pdm": "Public domain"}.get(code) or f"CC BY {version or ''}".strip()


def attribution(title: str, creator: str, code: str, version: str | None, url: str, page: str, source: str) -> str:
    via = {"wikimedia-commons": "Wikimedia Commons"}.get(source, f"Openverse ({source})")
    if code == "by":
        return f'"{title}" by {creator or "unknown"}, licensed {licence_name(code, version)} ({url}), via {via}: {page}'
    return f'"{title}", {licence_name(code, version)}{" by " + creator if creator else ""}, via {via}: {page}'


def _version(*raws) -> str | None:
    for raw in raws:
        m = re.search(r"(\d\.\d)", str(raw or ""))
        if m:
            return m.group(1)
    return None


def _candidate(source, title, creator, raw_licence, version, licence_url, page, url, width, height):
    code = licence_code(raw_licence)
    if not code or not url or not str(url).startswith("https://"):
        return None
    return {"source": source, "title": title, "creator": creator, "licence_code": code, "licence": licence_name(code, version),
            "licence_url": licence_url or "", "page_url": page, "url": url, "width": width or 0, "height": height or 0,
            "attribution": attribution(title, creator, code, version, licence_url or "", page, source)}


def parse_commons(data: dict, min_width: int = 0) -> list[dict]:
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    found = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        val = lambda k: (meta.get(k) or {}).get("value")
        if info.get("mime") not in IMAGE_MIMES or (info.get("width") or 0) < min_width:
            continue
        raw = val("License") or val("LicenseShortName")
        url = info.get("thumburl") if (info.get("width") or 0) > MAX_WIDTH and info.get("thumburl") else info.get("url")
        title = plain(val("ObjectName")) or re.sub(r"^File:|\.[A-Za-z]+$", "", page.get("title", ""))
        c = _candidate("wikimedia-commons", title, plain(val("Artist")) or plain(val("Credit")), raw,
                       _version(raw, val("LicenseShortName")), val("LicenseUrl"), info.get("descriptionurl"), url,
                       min(info.get("width") or 0, MAX_WIDTH), info.get("height"))
        if c:
            found.append(c)
    return found


def parse_openverse(data: dict, min_width: int = 0) -> list[dict]:
    found = []
    for r in data.get("results", []):
        if r.get("mature") or (r.get("width") or 0) < min_width:
            continue
        c = _candidate(r.get("source") or r.get("provider") or "openverse", plain(r.get("title")), plain(r.get("creator")),
                       r.get("license"), r.get("license_version"), r.get("license_url"), r.get("foreign_landing_url"),
                       r.get("url"), r.get("width"), r.get("height"))
        if c:
            found.append(c)
    return found


def _pace(delay: float) -> None:
    wait = delay - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def _api(url: str, delay: float, retries: int, backoff: float) -> dict:
    _pace(delay)
    body, _ = http_get(url, retries, backoff, agent=AGENT)
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        raise FetchError("the server sent something that is not JSON")


def search(query: str, source: str = "both", limit: int = 8, min_width: int = 1000, delay: float = 1.0,
           retries: int = 3, backoff: float = 1.0, kind: str = "photo", warnings: list | None = None) -> list[dict]:
    query = query + KIND_WORDS.get(kind, "")
    jobs = []
    if source in ("commons", "both"):
        params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6,
                  "gsrlimit": min(max(limit * 3, 10), 30), "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": MAX_WIDTH,
                  "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|Artist|Credit|ObjectName"}
        jobs.append(("commons", COMMONS_API + "?" + urllib.parse.urlencode(params), parse_commons))
    if source in ("openverse", "both"):
        params = {"q": query, "license": ALLOWED_QUERY, "page_size": min(max(limit * 2, 10), 20), "mature": "false"}
        jobs.append(("openverse", OPENVERSE_API + "?" + urllib.parse.urlencode(params), parse_openverse))
    found, seen = [], set()
    for name, url, parse in jobs:
        try:
            batch = parse(_api(url, delay, retries, backoff), min_width)
        except FetchError as err:
            if warnings is not None:
                warnings.append(f"{name}: {err}")
            continue
        for c in batch:
            key = re.sub(r"\W+", "", c["title"].lower())
            if key not in seen:
                seen.add(key)
                found.append(c)
    return found[:limit]


def image_ext(body: bytes) -> str | None:
    if body[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if body[:3] == b"\xff\xd8\xff":
        return "jpg"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "webp"
    return None


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "image").lower()).strip("-")[:40] or "image"


def load_assets(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "assets": []}


def record(assets_path: Path, entry: dict) -> None:
    data = load_assets(assets_path)
    data["assets"] = [a for a in data["assets"] if a.get("file") != entry["file"]] + [entry]
    assets_path.parent.mkdir(parents=True, exist_ok=True)
    assets_path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def download(candidate: dict, out_dir: Path, assets_path: Path, delay: float = 1.0, retries: int = 3, backoff: float = 1.0) -> dict:
    code = candidate.get("licence_code")
    if licence_code(code) != code or code not in ("cc0", "pdm", "by"):
        raise FetchError(f"the licence '{code}' is not allowed: only public domain, CC0 and CC BY go in a video")
    _pace(delay)
    body, _ = http_get(candidate["url"], retries, backoff, timeout=120, agent=AGENT)
    ext = image_ext(body)
    if not ext or len(body) < 64:
        raise FetchError("the download is not an image (the host sent a web page or an error): nothing was kept")
    sha = hashlib.sha256(body).hexdigest()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{slug(candidate['title'])}-{sha[:8]}.{ext}"      # named by the download, so a rerun finds the same file
    dest.write_bytes(body)
    size = fit(dest)
    width, height = size or (candidate["width"], candidate["height"])
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()                 # the record holds the saved file's checksum
    assets_path = Path(assets_path)
    rel = Path(dest).resolve().relative_to(assets_path.resolve().parent).as_posix() if assets_path.resolve().parent in dest.resolve().parents else dest.as_posix()
    entry = {"file": rel, "kind": "archive", "source": candidate["source"], "source_url": candidate["page_url"], "download_url": candidate["url"],
             "title": candidate["title"], "author": candidate["creator"] or "unknown", "licence": candidate["licence"],
             "licence_code": code, "licence_url": candidate["licence_url"], "attribution": candidate["attribution"],
             "width": width, "height": height, "resized": bool(size), "sha256": sha,
             "credit_required": code == "by", "retrieved": datetime.date.today().isoformat()}
    record(assets_path, entry)
    return entry


def fit(path: Path, longest: int = MAX_WIDTH) -> tuple[int, int] | None:
    """Scale a picture down so its longest side is at most `longest` px (aspect kept). Returns the new (w, h), or None when
    ffmpeg is missing or the picture is already small enough."""
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        return None
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True)
    try:
        w, h = (int(v) for v in probe.stdout.strip().split(",")[:2])
    except ValueError:
        return None
    if max(w, h) <= longest:
        return None
    k = longest / max(w, h)
    nw, nh = max(2, round(w * k / 2) * 2), max(2, round(h * k / 2) * 2)
    tmp = path.with_name(path.stem + ".fit" + path.suffix)
    done = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", f"scale={nw}:{nh}:flags=lanczos", "-frames:v", "1",
                           *(["-q:v", "2"] if path.suffix == ".jpg" else []), str(tmp)], capture_output=True, text=True)
    if done.returncode != 0 or not tmp.is_file():
        tmp.unlink(missing_ok=True)
        return None
    tmp.replace(path)
    return nw, nh


def describe(i: int, c: dict) -> str:
    return f"{i}. {c['title'][:70]} | {c['creator'] or 'unknown'} | {c['licence']} | {c['width']} px | {c['source']}\n   {c['page_url']}"


def _find(args) -> list[dict]:
    warnings: list[str] = []
    found = search(args.query, args.source, args.limit, args.min_width, args.delay, args.retries, args.backoff, args.kind, warnings)
    for w in warnings:
        print(f"WARN  fetch_archive: {w}")
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("search", "download"):
        p = sub.add_parser(name)
        p.add_argument("query")
        p.add_argument("--source", choices=["commons", "openverse", "both"], default="both")
        p.add_argument("--kind", choices=sorted(KIND_WORDS), default="photo", help="photo (default), map or document: adds that word to the search")
        p.add_argument("--limit", type=int, default=8)
        p.add_argument("--min-width", type=int, default=1000, help="skip pictures narrower than this many pixels (default 1000)")
        p.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1)")
        p.add_argument("--retries", type=int, default=3)
        p.add_argument("--backoff", type=float, default=1.0)
    d = sub.choices["download"]
    d.add_argument("--pick", type=int, default=1, help="which search result to download (default 1)")
    d.add_argument("--out-dir", default="assets/archive")
    d.add_argument("--assets", default="ASSETS.json", help="the licence record to update (default ASSETS.json)")
    args = ap.parse_args(argv)
    try:
        found = _find(args)
        if not found:
            print("FAIL  fetch_archive: no usable public domain, CC0 or CC BY picture for that search. Try fewer or different words.")
            return 1
        if args.cmd == "search":
            print("\n".join(describe(i, c) for i, c in enumerate(found, 1)))
            return 0
        if args.pick < 1 or args.pick > len(found):
            raise FetchError(f"no result number {args.pick} for that search ({len(found)} found)")
        entry = download(found[args.pick - 1], Path(args.out_dir), Path(args.assets), args.delay, args.retries, args.backoff)
    except FetchError as err:
        print(f"FAIL  fetch_archive: {err}")
        return 1
    print(f"PASS  downloaded {entry['file']} ({entry['licence']})")
    print(f"INFO  recorded in {args.assets}" + ("; CC BY needs this credit in the film: " + entry["attribution"] if entry["credit_required"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
