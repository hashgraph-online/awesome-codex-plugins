#!/usr/bin/env python3
"""fetch_music.py: find and download free music or sound effects from Openverse, with an attribution file.

Openverse (https://openverse.org, a WordPress project) indexes openly licensed audio. Its API needs
no key for light use. This script only accepts licences you can put in a video: CC0 and public domain (no
credit needed) and CC BY (credit required: ATTRIBUTION.md is written for you, paste it into the video description).
It never takes NonCommercial, NoDerivatives or ShareAlike tracks.

  python3 fetch_music.py search "calm piano" [--category music|sound_effect] [--min-seconds 30] [--limit 10]
  python3 fetch_music.py download "calm piano" --pick 1 --out-dir audio/        # the 1st search result
  python3 fetch_music.py download --id 33d74b38-3baf-41b4-bfa8-27a292d26b0b --out-dir audio/

Each download is checked to be real audio when ffprobe is available, and recorded in <out-dir>/ATTRIBUTION.md:
title, creator, licence and its link, the source page, the Openverse text, and the date. Server errors (5xx),
rate limits (429) and dropped connections are retried with a growing wait. Other errors fail at once. Downloads
are streamed with a size cap (200 MB for audio, 25 MB for anything else) and only from https:// links.
Listen before you use a track, and check the licence on its source page: Openverse reports what the host says.
"""
import argparse
import datetime
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("OPENVERSE_API", "https://api.openverse.org/v1")
AGENT = "brief2mp4-fetch-music/1.0 (+https://github.com/qualixar/brief2mp4)"
ALLOWED = ("cc0", "pdm", "by")          # the only licences accepted, however the API is asked
PAGE_MAX = 20                            # the most results one anonymous request may ask for (more gets HTTP 401)
RETRY_STATUS = (429, 500, 502, 503, 504)
MAX_BYTES = 25 * 2 ** 20                 # the most any one request may download, unless the caller says otherwise
AUDIO_MAX_BYTES = 200 * 2 ** 20          # an audio file: about 20 minutes of WAV, hours of MP3
CHUNK = 1 << 16


class FetchError(Exception):
    pass


def read_capped(resp, max_bytes, url):
    """Read a response in chunks; stop at max_bytes. Raises ConnectionError when the body is shorter than announced."""
    length = resp.headers.get("Content-Length")
    host = urllib.parse.urlsplit(url).netloc
    if length and length.isdigit() and int(length) > max_bytes:
        raise FetchError(f"{host} offers {int(length) / 2 ** 20:.0f} MB, more than the {max_bytes / 2 ** 20:.0f} MB cap: nothing was kept")
    parts, total = [], 0
    while True:
        chunk = resp.read(CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FetchError(f"the download from {host} passed the {max_bytes / 2 ** 20:.0f} MB cap: nothing was kept")
        parts.append(chunk)
    if length and length.isdigit() and total < int(length):
        raise ConnectionError(f"the transfer stopped after {total} of {length} bytes")
    return b"".join(parts)


def http_get(url, retries, backoff, timeout=60, agent=None, max_bytes=MAX_BYTES):
    """GET a URL and return (body bytes, content type). Retries 429/5xx and network errors. `agent` overrides the User-Agent.

    The body is read in chunks and the request fails (without retrying) once it passes max_bytes."""
    last = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": agent or AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return read_capped(resp, max_bytes, url), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as err:
            last = f"HTTP {err.code} from {urllib.parse.urlsplit(url).netloc}"
            if err.code not in RETRY_STATUS:
                raise FetchError(last)
            wait = backoff * (2 ** attempt)
            retry_after = err.headers.get("Retry-After") if err.headers else None
            if retry_after and retry_after.isdigit():
                wait = max(wait, min(int(retry_after), 60))
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException, OSError) as err:
            last = f"network error: {getattr(err, 'reason', None) or err!r}"
            wait = backoff * (2 ** attempt)
        if attempt < retries:
            time.sleep(wait)
    raise FetchError(f"{last} (gave up after {retries + 1} tries)")


def safe_url(url):
    """Only https:// downloads (plain http only from this machine, for a local test server)."""
    parts = urllib.parse.urlsplit(url or "")
    local = parts.scheme == "http" and parts.hostname in ("127.0.0.1", "localhost", "::1")
    if parts.scheme != "https" and not local or not parts.hostname:
        raise FetchError(f"refusing to download from '{(url or '')[:80]}': only https:// links are used")
    return url


def api_json(path, params, retries, backoff):
    url = f"{API}{path}" + (("?" + urllib.parse.urlencode(params)) if params else "")
    body, _ = http_get(url, retries, backoff)
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        raise FetchError("Openverse sent something that is not JSON")


def usable(item, min_s, max_s):
    """Client-side guard: right licence, a download URL, and a length in range (when the length is known)."""
    if item.get("license") not in ALLOWED or not item.get("url"):
        return False
    seconds = (item.get("duration") or 0) / 1000.0
    return (not seconds or min_s <= seconds <= max_s) and not item.get("mature")


def search(query, args):
    params = {"q": query, "license": ",".join(ALLOWED), "page_size": min(max(args.limit * 2, 10), PAGE_MAX), "mature": "false"}
    if args.category:
        params["category"] = args.category
    data = api_json("/audio/", params, args.retries, args.backoff)
    return [r for r in data.get("results", []) if usable(r, args.min_seconds, args.max_seconds)][:args.limit]


def describe(i, r):
    secs = (r.get("duration") or 0) / 1000.0
    lic = r["license"].upper() if r["license"] in ("cc0", "pdm") else f"CC BY {r.get('license_version', '')}".strip()
    return (f"{i}. {r.get('title', '?')} | {r.get('creator') or 'unknown'} | {lic} | {secs:.0f}s | {r.get('source', '?')} | id {r['id']}\n"
            f"   {r.get('foreign_landing_url', '')}")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "track").lower()).strip("-")[:40] or "track"


def extension(item, ctype):
    guess = {"audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/ogg": "ogg", "audio/wav": "wav", "audio/x-wav": "wav", "audio/flac": "flac"}
    base = ctype.split(";")[0].strip().lower()
    if base in guess:
        return guess[base]
    ft = (item.get("filetype") or "").lower()
    return {"mp32": "mp3", "mpeg": "mp3"}.get(ft, ft if ft in ("mp3", "ogg", "wav", "flac", "m4a") else "mp3")


def is_audio(path):
    if shutil.which("ffprobe") is None:
        return True       # cannot check: trust the size test
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout
    return "audio" in out


def credit_block(item, filename):
    lic = item["license"]
    name = {"cc0": "CC0 1.0 (public domain dedication)", "pdm": "Public Domain Mark"}.get(lic, f"CC BY {item.get('license_version', '')}".strip())
    lines = [f"## {item.get('title', 'Untitled')}", "",
             f"- File: {filename}", f"- Creator: {item.get('creator') or 'unknown'}",
             f"- Licence: {name}" + (f" ({item['license_url']})" if item.get("license_url") else ""),
             f"- Source: {item.get('foreign_landing_url', '')}",
             f"- Credit required: {'yes, keep this entry in the video description' if lic == 'by' else 'no (credit is still polite)'}"]
    if item.get("attribution"):
        lines.append(f"- Openverse text: {item['attribution']}")
    lines.append(f"- Retrieved: {datetime.date.today().isoformat()} from Openverse")
    return "\n".join(lines) + "\n"


def record(out_dir, item, filename):
    path = os.path.join(out_dir, "ATTRIBUTION.md")
    existing = open(path, encoding="utf-8").read() if os.path.exists(path) else "# Attribution\n\nAudio used in this video.\n"
    if f"- File: {filename}\n" not in existing:
        open(path, "w", encoding="utf-8").write(existing.rstrip("\n") + "\n\n" + credit_block(item, filename))
    return path


def download(item, out_dir, args):
    body, ctype = http_get(safe_url(item["url"]), args.retries, args.backoff, timeout=120, max_bytes=AUDIO_MAX_BYTES)
    if len(body) < 1024:
        raise FetchError(f"the download is only {len(body)} bytes: not an audio file")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{slug(item.get('title'))}-{item['id'][:8]}.{extension(item, ctype)}"
    dest = os.path.join(out_dir, filename)
    with open(dest, "wb") as fh:
        fh.write(body)
    if not is_audio(dest):
        os.remove(dest)
        raise FetchError("the file is not audio (the host sent a web page or an error): nothing was kept")
    return dest, record(out_dir, item, filename)


def cmd_search(args):
    items = search(args.query, args)
    if not items:
        print("FAIL  fetch_music: no usable CC0, public domain or CC BY audio for that search. Try fewer or different words.")
        return 1
    print("\n".join(describe(i, r) for i, r in enumerate(items, 1)))
    return 0


def cmd_download(args):
    if args.id:
        item = api_json(f"/audio/{urllib.parse.quote(args.id)}/", None, args.retries, args.backoff)
        if not usable(item, 0, 10 ** 9):
            raise FetchError("that track is not CC0, public domain or CC BY (or has no download link)")
    else:
        if not args.query:
            raise FetchError("give a search query or --id")
        items = search(args.query, args)
        if args.pick < 1:
            raise FetchError(f"--pick counts from 1, got {args.pick}")
        if not items or args.pick > len(items):
            raise FetchError(f"no result number {args.pick} for that search")
        item = items[args.pick - 1]
    dest, attribution = download(item, args.out_dir, args)
    print(f"PASS  downloaded {dest} ({item['license'].upper()}, {(item.get('duration') or 0) / 1000:.0f}s)")
    print(f"INFO  attribution written to {attribution}" + (": CC BY needs the credit in the video description" if item["license"] == "by" else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("search", "download"):
        p = sub.add_parser(name)
        p.add_argument("query", nargs="?" if name == "download" else None)
        p.add_argument("--category", choices=["music", "sound_effect"], help="music or sound_effect (default: both)")
        p.add_argument("--min-seconds", type=float, default=0)
        p.add_argument("--max-seconds", type=float, default=3600)
        p.add_argument("--limit", type=int, default=10)
        p.add_argument("--retries", type=int, default=3, help="extra tries after a 5xx, 429 or network error (default 3)")
        p.add_argument("--backoff", type=float, default=1.0, help="first wait in seconds, doubled each try (default 1)")
    d = sub.choices["download"]
    d.add_argument("--pick", type=int, default=1, help="which search result to download (default 1)")
    d.add_argument("--id", help="download this Openverse id instead of searching")
    d.add_argument("--out-dir", default="audio")
    args = ap.parse_args()
    try:
        return cmd_search(args) if args.cmd == "search" else cmd_download(args)
    except FetchError as err:
        print(f"FAIL  fetch_music: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
