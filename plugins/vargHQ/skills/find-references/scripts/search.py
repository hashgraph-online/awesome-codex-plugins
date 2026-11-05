#!/usr/bin/env python3
"""Search open reference sources with one command, and write links for the sites only a person may open.

Python 3 standard library only. No keys. Identifies itself honestly and waits between calls, per host and across
processes: 1.1 s, or 3 s on Commons. Retries a server error or a broken connection once. 401, 402, 403, 451 and a bot
wall are final: status "blocked", stop and write the link. A 429 waits what Retry-After says, or 60 s, and tries once
more. If it persists, status "rate_limited": stop using that source for this run.

  python3 search.py sources
  python3 search.py met "candlelight" --medium Paintings
  python3 search.py met "Georges de La Tour" --artist --public-domain
  python3 search.py commons '"low key" portrait'
  python3 search.py commons "gas stations 1970s" --categories
  python3 search.py commons "filetype:video split-flap"        adds filetype:bitmap unless you pass filetype:
  python3 search.py commons-cat "Category:SBB Historic - Plakate" --width 1920   a sized copy in "image"
  python3 search.py commons-cat "Category:Diners in New Jersey"
  python3 search.py loc "mechanic" --collection fsa-owi-black-and-white-negatives
  python3 search.py loc "window light portrait" --dates 1900/1970
  python3 search.py rijksmuseum "kaarslicht" --type painting   record links only: open each for title and maker
  python3 search.py polyhaven "night,artificial,outdoor" --asset hdris
  python3 search.py archive 'collection:prelinger AND (diner OR "lunch counter")'
  python3 search.py flickr "cinestill800t"
  python3 search.py arena "practical light"
  python3 search.py arena-walk 12977078
  python3 search.py refs '{"query": "coffee", "aspect": "9:16", "ai_made": false}'
  python3 search.py aic "Edward Hopper Nighthawks"
  python3 search.py wellcome "poster" --color d7372c
  python3 search.py ambientcg "paper"
  python3 search.py openverse "kodachrome"
  python3 search.py openverse-audio "room tone"
  python3 search.py lantern '"low key" lighting'
  python3 search.py sakugabooru "smears"
  python3 search.py aesthetics "liminal"
  python3 search.py musicbrainz 'tag:"library music" AND firstreleasedate:[1970 TO 1979]'
  python3 search.py listenbrainz "library music"
  python3 search.py discogs "" --style Berlin-School --year 1976

Every source prints JSON: {"source", "query", "status", "total", "results": [{"rank", "title", "maker", "date", "url",
"image", "licence", ...}]}, with "original", "width", "height" and "bytes" where the source gives them. Rijksmuseum rows
hold only a record link. LoC's licence can be null: read rights_advisory on the item. Status is ok, blocked, rate_limited
or error, and anything but ok exits 1. Add --log log.jsonl to append every outcome to a search log, which the method asks
you to keep.

  python3 search.py fuse a.json b.json --limit 20   reciprocal rank fusion (k = 60); merges duplicates and rank
  python3 search.py fuse a.json b.json --per-maker 1   also keep one item per maker, once you have opened them
  python3 search.py links "sodium street" --job light   that job's person-only links for links.md; nothing is fetched

A hit is a candidate, not a reference. Open it and say what you can see: keyword search lies.
"""
import argparse
import collections
import email.utils
import html
import http.client
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import fcntl
except ImportError:  # Windows: pacing then holds between calls, without a lock
    fcntl = None

USER_AGENT = "find-references/2.0 (varg skills; +https://github.com/vargHQ/skills/tree/main/find-references)"
TIMEOUT = 60
PAUSE = 1.1  # MusicBrainz asks for 1 request a second; the rest get the same courtesy.
SLOW_HOSTS = {"commons.wikimedia.org": 3.0, "upload.wikimedia.org": 3.0}
BLOCKED = (401, 402, 403, 451)
WAIT_429, LONGEST_WAIT = 60, 120  # seconds. A longer Retry-After is reported, not slept through.
ADVICE = {"blocked": "Final: stop and write the link in links.md.",
          "rate_limited": "Stop using this source for this run."}


def pace(host, hold=None):
    """Wait for this host's next free slot. The slot lives in a small file in the system temp dir, so that one process
    per query still paces. `hold` pushes the next slot out by that many seconds, after a 429. Returns the seconds left
    if the host is on a hold too long to sleep through, else 0."""
    now = start = time.time()
    uid = os.getuid() if hasattr(os, "getuid") else "user"
    folder = os.path.join(tempfile.gettempdir(), f"find-references-pace-{uid}")
    try:
        os.makedirs(folder, mode=0o700, exist_ok=True)
        with open(os.path.join(folder, re.sub(r"[^\w.-]", "_", host)), "a+", encoding="ascii") as state:
            if fcntl:
                fcntl.flock(state, fcntl.LOCK_EX)
            state.seek(0)
            try:
                slot = float(state.read() or 0)
            except ValueError:
                slot = 0.0
            if hold is None and slot - now > LONGEST_WAIT:
                return round(slot - now)
            start = max(now, slot)
            state.seek(0)
            state.truncate()
            state.write(str(now + hold if hold is not None else start + SLOW_HOSTS.get(host, PAUSE)))
    except OSError:
        pass  # no state file: the call still runs, unpaced across processes
    if hold is None and start > now:
        time.sleep(start - now)
    return 0


def retry_after(header):
    """Seconds from a Retry-After header, a number or an HTTP date. Default 60."""
    try:
        return max(0, int(header))
    except (TypeError, ValueError):
        pass
    try:
        return max(0, int(email.utils.parsedate_to_datetime(header).timestamp() - time.time()))
    except (TypeError, ValueError):
        return WAIT_429


def polite(host, call):
    """Run call() under the rules, and return (status, its value or the reason)."""
    for attempt in (1, 2):
        left = pace(host)
        if left:
            return "rate_limited", f"on hold for {left} s more after an earlier 429"
        try:
            return "ok", call()
        except urllib.error.HTTPError as error:
            if error.code in BLOCKED or error.headers.get("cf-mitigated"):
                return "blocked", f"HTTP {error.code}"
            if error.code == 429:
                wait = retry_after(error.headers.get("Retry-After"))
                pace(host, hold=wait)
                if attempt == 2 or wait > LONGEST_WAIT:
                    return "rate_limited", f"HTTP 429, Retry-After {wait} s"
                print(f"search.py: 429 from {host}. Waiting {wait} s, then one more try.", file=sys.stderr)
                continue
            if error.code >= 500 and attempt == 1:
                time.sleep(3)
                continue
            return "error", f"HTTP {error.code}"
        except (OSError, http.client.HTTPException) as error:  # includes URLError, timeouts and IncompleteRead
            if attempt == 1:
                time.sleep(3)
                continue
            return "error", f"{type(error).__name__}: {error}"
    return "error", "no response"


def fetch(url):
    """Return (status, body). A block is reported, never worked around."""
    def call():
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8", "replace")
    return polite(urllib.parse.urlsplit(url).netloc, call)


def get_json(url):
    status, body = fetch(url)
    if status != "ok":
        return status, body
    try:
        return "ok", json.loads(body)
    except json.JSONDecodeError:
        return "error", "response was not JSON. It may be a bot wall: do not retry."


def qs(**params):
    return urllib.parse.urlencode({k: v for k, v in params.items() if v is not None and v != "" and v is not False})


def plain(text):
    """Commons credits arrive as HTML."""
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(text or "")).split()) or None


def out(source, query, url, status, total=None, results=None, note=None, **extra):
    results = results or []
    for rank, item in enumerate(results, 1):
        item["rank"] = rank
    record = {"source": source, "query": query, "url": url, "status": status, "total": total, **extra,
              "results": results}
    if note:
        record["note"] = note
    return record


def failed(source, query, url, status, detail):
    return out(source, query, url, status, note=f"{detail}. {ADVICE[status]}" if status in ADVICE else detail)


# --- Art and photo archives ---


def met(a):
    base = "https://collectionapi.metmuseum.org/public/collection/v1.1/search?"
    url = base + qs(q=a.query, hasImages="true", medium=a.medium, artistOrCulture="true" if a.artist else None,
                    isPublicDomain="true" if a.public_domain else None, limit=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("met", a.query, url, status, data)
    ids = data.get("objectIDs") or data.get("objects") or []
    results, outcome = [], "ok"
    note = "The public-domain search filter leaks: trust the licence field on each object, read here per object."
    for object_id in ids[: a.limit]:
        object_id = object_id.get("objectID", object_id) if isinstance(object_id, dict) else object_id
        s, o = get_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        if s in ADVICE:
            outcome, note = s, f"Stopped after {len(results)} objects: {o}. {ADVICE[s]}"
            break
        if s != "ok":
            continue
        results.append({"title": o.get("title"), "maker": o.get("artistDisplayName"), "date": o.get("objectDate"),
                        "medium": o.get("medium"), "url": o.get("objectURL"), "image": o.get("primaryImageSmall"),
                        "original": o.get("primaryImage"),
                        "licence": "public domain" if o.get("isPublicDomain") else "not public domain"})
    return out("met", a.query, url, outcome, data.get("total"), results, note)


COMMONS = "https://commons.wikimedia.org/w/api.php?"
COMMONS_FILE = dict(prop="imageinfo", iiprop="url|size|user|timestamp|extmetadata", iiurlwidth=800, format="json")


def commons_file(page):
    """One Commons file: image is a sized copy, original the full file, and width, height and bytes are the original's."""
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    value = lambda key: (meta.get(key) or {}).get("value")
    return {"title": page.get("title"), "maker": plain(value("Artist")) or info.get("user"),
            "date": plain(value("DateTimeOriginal")), "uploaded": info.get("timestamp"),
            "url": info.get("descriptionurl"), "image": info.get("thumburl"), "original": info.get("url"),
            "width": info.get("width"), "height": info.get("height"), "bytes": info.get("size"),
            "licence": value("LicenseShortName")}


def commons(a):
    if a.categories:
        url = COMMONS + qs(action="query", list="search", srsearch=a.query, srnamespace=14, srlimit=a.limit,
                           format="json")
        status, data = get_json(url)
        if status != "ok":
            return failed("commons", a.query, url, status, data)
        hits = data["query"]["search"]
        results = [{"title": h["title"], "url": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(
            h["title"].replace(" ", "_"))} for h in hits]
        return out("commons", a.query, url, "ok", data["query"].get("searchinfo", {}).get("totalhits"), results,
                   "Walk one with: search.py commons-cat \"<title>\"")
    query = a.query
    if not a.allow_ai and "AI-generated images" not in query:
        query += ' -deepcat:"AI-generated images"'
    if "filetype:" not in query:
        query += " filetype:bitmap"
    url = COMMONS + qs(action="query", generator="search", gsrsearch=query, gsrnamespace=6, gsrlimit=a.limit,
                       gsrinfo="totalhits", **dict(COMMONS_FILE, iiurlwidth=a.width or COMMONS_FILE["iiurlwidth"]))
    status, data = get_json(url)
    if status != "ok":
        return failed("commons", query, url, status, data)
    found = data.get("query") or {}
    pages = sorted(found.get("pages", {}).values(), key=lambda p: p.get("index", 0))
    return out("commons", query, url, "ok", (found.get("searchinfo") or {}).get("totalhits", 0),
               [commons_file(page) for page in pages])


def commons_cat(a):
    """One category: its files, its subcategories and its file count. Category walks were the best route in testing."""
    title = a.query if a.query.lower().startswith("category:") else "Category:" + a.query
    url = COMMONS + qs(action="query", titles=title, prop="categoryinfo", list="categorymembers", cmtitle=title,
                       cmtype="subcat", cmlimit=200, format="json")
    status, data = get_json(url)
    if status != "ok":
        return failed("commons-cat", title, url, status, data)
    found = data.get("query") or {}
    subcats = [m["title"] for m in found.get("categorymembers", [])]
    info = next(iter((found.get("pages") or {}).values()), {}).get("categoryinfo")
    files_url = COMMONS + qs(action="query", generator="categorymembers", gcmtitle=title, gcmtype="file",
                             gcmlimit=a.limit, **dict(COMMONS_FILE, iiurlwidth=a.width or COMMONS_FILE["iiurlwidth"]))
    status, data = get_json(files_url)
    if status != "ok":
        return failed("commons-cat", title, files_url, status, data)
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("title", ""))
    note = ("Read the author field of good hits: institutions upload whole collections." if info else
            "No such category, or it holds nothing. Find names with: search.py commons \"<words>\" --categories")
    return out("commons-cat", title, files_url, "ok", (info or {}).get("files", 0), [commons_file(p) for p in pages],
               note, subcats=subcats)


def loc(a):
    if a.collection:
        base = f"https://www.loc.gov/collections/{a.collection}/?"
    else:
        base = "https://www.loc.gov/photos/?"
    url = base + qs(q=a.query, dates=a.dates, fo="json", c=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("loc", a.query, url, status, data)
    results = []
    for r in data.get("results", [])[: a.limit]:
        images = r.get("image_url") or []
        results.append({"title": r.get("title"), "maker": ", ".join(r.get("contributor") or []) or None,
                        "date": r.get("date"), "url": r.get("url") or r.get("id"), "image": images[-1] if images else None,
                        "licence": "; ".join(r.get("rights_information") or []) if isinstance(
                            r.get("rights_information"), list) else r.get("rights_information")})
    return out("loc", a.query, url, "ok", (data.get("pagination") or {}).get("of"), results,
               "Any identifiable person here is a words reference: public domain does not clear likeness. licence can "
               "be null: read item.rights_advisory at <url>?fo=json. Check date there too: it can be coarse.")


def rijksmuseum(a):
    url = "https://data.rijksmuseum.nl/search/collection?" + qs(description=a.query, type=a.type)
    status, data = get_json(url)
    if status != "ok":
        return failed("rijksmuseum", a.query, url, status, data)
    items = data.get("orderedItems", [])[: a.limit]
    results = [{"title": None, "url": item.get("id")} for item in items]
    return out("rijksmuseum", a.query, url, "ok", (data.get("partOf") or {}).get("totalItems"), results,
               "Dutch works best for candlelight (kaarslicht). venster usually means a window in the description, "
               "often a niche behind a sitter. Results are record links: open each one.")


def aic(a):
    fields = "id,title,artist_title,date_display,image_id,is_public_domain,thumbnail"
    url = "https://api.artic.edu/api/v1/artworks/search?" + qs(q=a.query, fields=fields, limit=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("aic", a.query, url, status, data)
    iiif = (data.get("config") or {}).get("iiif_url", "https://www.artic.edu/iiif/2")
    results = [{"title": r.get("title"), "maker": r.get("artist_title"), "date": r.get("date_display"),
                "url": f"https://www.artic.edu/artworks/{r.get('id')}",
                "image": f"{iiif}/{r['image_id']}/full/843,/0/default.jpg" if r.get("image_id") else None,
                "width": (r.get("thumbnail") or {}).get("width"), "height": (r.get("thumbnail") or {}).get("height"),
                "licence": "public domain" if r.get("is_public_domain") else "not public domain"}
               for r in data.get("data", [])]
    return out("aic", a.query, url, "ok", (data.get("pagination") or {}).get("total"), results,
               "Best with an artist or title. Light words such as candlelight mostly return unrelated works.")


def wellcome(a):
    url = "https://api.wellcomecollection.org/catalogue/v2/images?" + qs(
        query=a.query, color=a.color, pageSize=a.limit, **{"locations.license": "cc0,pdm"})
    status, data = get_json(url)
    if status != "ok":
        return failed("wellcome", a.query, url, status, data)
    results = []
    for r in data.get("results", []):
        location = (r.get("locations") or [{}])[0]
        source = r.get("source") or {}
        results.append({"title": source.get("title"), "url": f"https://wellcomecollection.org/works/{source.get('id')}",
                        "image": location.get("url"), "licence": (location.get("license") or {}).get("id")})
    return out("wellcome", a.query, url, "ok", data.get("totalResults"), results)


def archive(a):
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        [("q", a.query), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "year"), ("fl[]", "creator"),
         ("fl[]", "licenseurl"), ("rows", a.limit), ("output", "json")])
    status, data = get_json(url)
    if status != "ok":
        return failed("archive", a.query, url, status, data)
    response = data.get("response", {})
    results = [{"title": d.get("title"), "maker": d.get("creator"), "date": d.get("year"),
                "url": f"https://archive.org/details/{d.get('identifier')}", "licence": d.get("licenseurl")}
               for d in response.get("docs", [])]
    return out("archive", a.query, url, "ok", response.get("numFound"), results, "Rights are per item: most list none.")


def flickr(a):
    url = "https://www.flickr.com/services/feeds/photos_public.gne?" + qs(
        tags=a.query, tagmode="all", format="json", nojsoncallback=1)
    status, data = get_json(url)
    if status != "ok":
        return failed("flickr", a.query, url, status, data)
    results = []
    for item in data.get("items", [])[: a.limit]:
        tags = item.get("tags", "")
        results.append({"title": item.get("title"), "maker": (re.findall(r'"(.+)"', item.get("author") or "") or [None])[0],
                        "date": item.get("date_taken"),
                        "url": item.get("link"), "image": (item.get("media") or {}).get("m"), "tags": tags,
                        "ai_tagged": any(t in tags.split() for t in ("aigenerated", "aiart", "generativeai", "midjourney"))})
    return out("flickr", a.query, url, "ok", None, results,
               "Tags are comma separated and all must match. Name the process (portra160), not the look. Newest first.")


def openverse(a):
    url = "https://api.openverse.org/v1/images/?" + qs(q=a.query, license="cc0,pdm", page_size=a.limit)
    return _openverse("openverse", a, url)


def openverse_audio(a):
    url = "https://api.openverse.org/v1/audio/?" + qs(q=a.query, license_type="commercial,modification", page_size=a.limit)
    return _openverse("openverse-audio", a, url)


def _openverse(source, a, url):
    status, data = get_json(url)
    if status != "ok":
        return failed(source, a.query, url, status, data + " (Openverse is unstable: keep a fallback.)")
    results = [{"title": r.get("title"), "maker": r.get("creator"), "url": r.get("foreign_landing_url"),
                "image": r.get("thumbnail") or r.get("url"), "original": r.get("url"), "width": r.get("width"),
                "height": r.get("height"), "licence": f"{r.get('license')} {r.get('license_version') or ''}".strip()}
               for r in data.get("results", [])]
    return out(source, a.query, url, "ok", data.get("result_count"), results,
               "Filter the licence field again: BY-ND cannot go under video, and result_count stops at 240.")


def lantern(a):
    url = "https://lantern.mediahist.org/catalog.json?" + qs(q=a.query, per_page=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("lantern", a.query, url, status, data)
    results = []
    for d in (data.get("response") or {}).get("docs") or data.get("data") or []:
        attributes = d.get("attributes") or d
        title = attributes.get("title") or attributes.get("title_tesim") or d.get("id")
        text = lambda name: plain(((attributes.get(name) or {}).get("attributes") or {}).get("value"))
        results.append({"title": title, "date": text("dateString"), "excerpt": text("body"),
                        "url": f"https://lantern.mediahist.org/catalog/{d.get('id')}"})
    meta = (data.get("response") or {}).get("pages") or (data.get("meta") or {}).get("pages") or {}
    return out("lantern", a.query, url, "ok", meta.get("total_count"), results,
               "Period trade press. Use it for vocabulary and for checking a reading.")


# --- Texture, light and materials ---


def polyhaven(a):
    url = "https://api.polyhaven.com/assets?" + qs(t=a.asset)
    status, data = get_json(url)
    if status != "ok":
        return failed("polyhaven", a.query, url, status, data)
    wanted = [w.strip().lower() for w in a.query.split(",") if w.strip()]
    results = []
    for slug, asset in data.items():
        words = set(str(x).lower() for x in list(asset.get("tags", [])) + list(asset.get("categories", [])))
        words |= set(str(v).lower() for v in (asset.get("attributes") or {}).values())
        if all(w in words for w in wanted):
            results.append({"title": asset.get("name"), "maker": ", ".join(asset.get("authors", {})),
                            "url": f"https://polyhaven.com/a/{slug}", "image": asset.get("thumbnail_url"),
                            "licence": "CC0", "attributes": asset.get("attributes"), "slug": slug})
    return out("polyhaven", a.query, url, "ok", len(results), results[: a.limit],
               "Comma-separated words, matched against tags, categories and attributes on your side.")


def ambientcg(a):
    url = "https://ambientcg.com/api/v2/full_json?" + qs(type="Material", q=a.query, limit=a.limit, include="tagData")
    status, data = get_json(url)
    if status != "ok":
        return failed("ambientcg", a.query, url, status, data)
    results = [{"title": x.get("displayName") or x.get("assetId"),
                "url": f"https://ambientcg.com/view?id={x.get('assetId')}", "licence": "CC0", "tags": x.get("tags")}
               for x in data.get("foundAssets", [])]
    return out("ambientcg", a.query, url, "ok", data.get("numberOfResults"), results)


# --- Boards and motion ---


def arena_channels(data):
    channels = sorted(data.get("channels", []), key=lambda c: c.get("follower_count", 0), reverse=True)
    return [{"title": c.get("title"), "url": f"https://www.are.na/{(c.get('user') or {}).get('slug')}/{c.get('slug')}",
             "blocks": c.get("length"), "followers": c.get("follower_count"), "id": c.get("id")} for c in channels]


def arena(a):
    url = "https://api.are.na/v2/search/channels?" + qs(q=a.query, per=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("arena", a.query, url, status, data + " (Are.na search is unstable: keep a fallback.)")
    pages, total = data.get("total_pages") or 1, data.get("length")
    if pages > 1:  # length counts one page here, so the last page gives the exact count
        s, last = get_json(f"{url}&page={pages}")
        total = (pages - 1) * data.get("per", a.limit) + last.get("length", 0) if s == "ok" else None
    return out("arena", a.query, url, "ok", total, arena_channels(data),
               "Taste, not provenance: most blocks carry no source. Targeted lookups only; the terms ban mass "
               "retrieval.", pages=pages)


def arena_walk(a):
    url = f"https://api.are.na/v2/blocks/{a.query}/channels?" + qs(per=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("arena-walk", a.query, url, status, data)
    return out("arena-walk", a.query, url, "ok", data.get("length"), arena_channels(data),
               "Everyone else who saved this block. Stop at two hops and below 30 reads a minute.",
               pages=data.get("total_pages"))


REFS = "https://refs.video/mcp"
REFS_NOTE = ("Cards give a summary and a thumbnail, with no clip, so nothing is measurable from Refs alone: find the "
             "film's own public page, and a person watches. ai_made true = made with AI or code (Claude, Remotion, "
             "three.js), so it mixes code with generated; false = human-made. For code-made films use made_with, such "
             "as hyperframes or remotion. Keyless reach is 48 unique cards: 8 per call, offset up to 40.")


def load_mcp_call():
    """Load the sibling file by path. It works under python3 -I, a planted mcp_call.py in the working folder never runs,
    and nothing is written into the skill folder."""
    sys.dont_write_bytecode = True
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_call.py")
    spec = importlib.util.spec_from_file_location("mcp_call", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refs(a):
    """search_videos on Refs. The query is the tool's JSON arguments, or plain words."""
    try:
        args = json.loads(a.query)
    except ValueError:
        args = {"query": a.query}
    if not isinstance(args, dict):
        args = {"query": a.query}
    notes = []
    args["limit"] = args.get("limit", a.limit or 8)
    if args["limit"] > 8:
        notes.append(f"Asked for limit {args['limit']}, sent 8: keyless cards stop at 8 per call.")
        args["limit"] = 8
    if args.get("offset", 0) > 40:
        notes.append(f"Asked for offset {args['offset']}, sent 40: a higher offset repeats that page.")
        args["offset"] = 40
    query = json.dumps(args, ensure_ascii=False)
    mcp_call = load_mcp_call()
    status, reply = polite("refs.video", lambda: mcp_call.call_tool(REFS, "search_videos", args))
    if status != "ok":
        return failed("refs", query, REFS, status, reply)
    if not reply or "error" in reply:
        return failed("refs", query, REFS, "error", str((reply or {}).get("error", "no answer from the server")))
    text = " ".join(b.get("text", "") for b in reply["result"].get("content", []))
    if reply["result"].get("isError"):
        return failed("refs", query, REFS, "error", text)
    data = json.loads(text)
    results = [{"title": r.get("title"), "maker": r.get("by"), "url": r.get("url"), "image": r.get("thumb"),
                "thumbnail": r.get("thumb"), "summary": r.get("summary"), "locked": r.get("locked"),
                "ref": r.get("ref"), "category": r.get("category"), "seconds": r.get("duration_s"),
                "aspect": r.get("aspect")}
               for r in data.get("items", [])]
    return out("refs", query, REFS, "ok", data.get("total"), results, " ".join(notes + [REFS_NOTE]),
               locked_note=data.get("locked_note"))


def sakugabooru(a):
    tags = a.query.replace(" ", "_") + " order:score"
    url = "https://www.sakugabooru.com/post.json?" + qs(tags=tags, limit=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("sakugabooru", a.query, url, status, data)
    results = [{"title": p.get("tags", "")[:120], "maker": p.get("author"), "url": f"https://www.sakugabooru.com/post/show/{p.get('id')}",
                "score": p.get("score"), "source": p.get("source")} for p in data]
    return out("sakugabooru", a.query, url, "ok", None, results,
               "Metadata only, for study. Tags are exact: smears has results, smear has none.")


def aesthetics(a):
    url = "https://aesthetics.fandom.com/api.php?" + qs(action="query", list="search", srsearch=a.query, srlimit=a.limit,
                                                        format="json")
    status, data = get_json(url)
    if status != "ok":
        return failed("aesthetics", a.query, url, status, data)
    results = [{"title": h["title"], "url": "https://aesthetics.fandom.com/wiki/" + urllib.parse.quote(
        h["title"].replace(" ", "_"))} for h in data["query"]["search"]]
    return out("aesthetics", a.query, url, "ok", data["query"].get("searchinfo", {}).get("totalhits"), results,
               "Community-written. Use it to name a style, not as evidence.")


# --- Music ---


def musicbrainz(a):
    url = "https://musicbrainz.org/ws/2/release-group?" + qs(query=a.query, fmt="json", limit=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("musicbrainz", a.query, url, status, data)
    results = [{"title": r.get("title"), "maker": ", ".join(x.get("name", "") for x in r.get("artist-credit", [])),
                "date": r.get("first-release-date"), "url": f"https://musicbrainz.org/release-group/{r.get('id')}"}
               for r in data.get("release-groups", [])]
    return out("musicbrainz", a.query, url, "ok", data.get("count"), results,
               "Use era and function tags. Instrument adjectives such as felt piano return nothing.")


def listenbrainz(a):
    url = "https://api.listenbrainz.org/1/lb-radio/tags?" + qs(tag=a.query, operator="and", pop_begin=0, pop_end=100,
                                                              count=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("listenbrainz", a.query, url, status, data)
    recordings = data if isinstance(data, list) else data.get("recordings") or data.get("payload") or []
    ids = [r.get("recording_mbid") if isinstance(r, dict) else r for r in recordings][: a.limit]
    results = []
    if ids:
        s, meta = get_json("https://api.listenbrainz.org/1/metadata/recording?" + qs(
            recording_mbids=",".join(i for i in ids if i), inc="artist"))
        if s == "ok":
            for mbid in ids:
                item = meta.get(mbid) or {}
                results.append({"title": (item.get("recording") or {}).get("name"),
                                "maker": (item.get("artist") or {}).get("name"),
                                "url": f"https://musicbrainz.org/recording/{mbid}"})
    return out("listenbrainz", a.query, url, "ok", len(ids), results, "An agent cannot hear: a person listens before anything is kept.")


def discogs(a):
    url = "https://api.discogs.com/database/search?" + qs(q=a.query, style=a.style, year=a.year, type="master", per_page=a.limit)
    status, data = get_json(url)
    if status != "ok":
        return failed("discogs", a.query, url, status, data)
    results = [{"title": r.get("title"), "date": r.get("year"), "url": "https://www.discogs.com" + (r.get("uri") or ""),
                "style": r.get("style")} for r in data.get("results", [])]
    return out("discogs", a.query or a.style, url, "ok", (data.get("pagination") or {}).get("items"), results,
               "A silent empty result means a wrong word: Library Music is not a style. Use year=, not decade=.")


SOURCES = {
    "met": (met, "paintings and photographs, by artist more than by light word"),
    "commons": (commons, "photos with date, author and camera; --categories finds categories; filetype:video finds clips"),
    "commons-cat": (commons_cat, "one category's files and subcategories: the best route for a real place or trade"),
    "loc": (loc, "real faces, work, places; search the cataloguer's job word"),
    "rijksmuseum": (rijksmuseum, "paintings; Dutch words, best for candlelight; record links only, open each one"),
    "aic": (aic, "known artists and titles"),
    "wellcome": (wellcome, "real images by hex colour"),
    "archive": (archive, "moving flaws, period film, manuals, type specimens"),
    "lantern": (lantern, "period trade press for vocabulary"),
    "flickr": (flickr, "film stocks and capture devices by tag"),
    "openverse": (openverse, "CC0 and public-domain images; unstable"),
    "polyhaven": (polyhaven, "CC0 HDRIs and textures"),
    "ambientcg": (ambientcg, "CC0 materials"),
    "arena": (arena, "human-curated channels by taste"),
    "arena-walk": (arena_walk, "channels that saved one block"),
    "refs": (refs, "dissected top-performing videos: summary and thumbnail, no clip"),
    "sakugabooru": (sakugabooru, "hand-animation timing, metadata only"),
    "aesthetics": (aesthetics, "name a style"),
    "musicbrainz": (musicbrainz, "music by era and function"),
    "listenbrainz": (listenbrainz, "recordings by tag"),
    "discogs": (discogs, "music by style and year"),
    "openverse-audio": (openverse_audio, "licensed room tone and effects; unstable"),
}

FILM_GRAB = ("Film-Grab: stills from whole films", "https://film-grab.com/?s={q}")
SHOTDECK = ("ShotDeck: filter by light, colour, angle (subscription)", "https://shotdeck.com")
FRAME_SET = ("Frame Set: how its filters work (subscription)",
             "https://intercom.help/frame-set/en/articles/5683324-filtered-search")
GOOGLE = ("Google Images, before generators, photos only",
          "https://www.google.com/search?udm=2&q={q}+before:2022-11-30&tbs=itp:photo")
PINTEREST = ("Pinterest: curated boards, tuner on", "https://www.pinterest.com/search/pins/?q={q}")
ADS_OF_THE_WORLD = ("Ads of the World: browse by category", "https://www.adsoftheworld.com/")
PERSON_LINKS = {
    "light": [FILM_GRAB, SHOTDECK, FRAME_SET, GOOGLE],
    "framing": [FILM_GRAB, ("Shot Cafe: browse its tags", "https://shot.cafe"), SHOTDECK, FRAME_SET],
    "people": [("Flickr group 100 Strangers: browse", "https://www.flickr.com/groups/100strangers/"),
               ("Magnum: search", "https://www.magnumphotos.com/?s={q}"),
               ("Portrait of Britain", "https://www.1854.photography/?p=77622"), SHOTDECK, PINTEREST],
    "location": [("Street View: a person pans, nobody saves", "https://www.google.com/maps"),
                 ("Atlas Obscura: search", "https://www.atlasobscura.com/search?q={q}"),
                 ("ArchDaily: search", "https://www.archdaily.com/search/projects/text/{p}"),
                 ("Shorpy: search", "https://www.shorpy.com/search/node/{p}"),
                 ("Dezeen", "https://www.dezeen.com/"), ("British Pathé", "https://www.britishpathe.com/"), GOOGLE],
    "texture": [("filmdev.org: ties a film stock to its developer", "https://filmdev.org"),
                ("Camera-wiki", "https://camera-wiki.org"), ("Lomography: films", "https://www.lomography.com/films")],
    "type": [("Fonts In Use: search", "https://fontsinuse.com/search?terms={q}"),
             ("D&AD awards archive", "https://www.dandad.org/en/d-ad-awards-archive"), ADS_OF_THE_WORLD],
    "motion": [("Meta Ad Library: search what a category really runs", "https://www.facebook.com/ads/library/"),
               ("TikTok Creative Center: top ads",
                "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"),
               ADS_OF_THE_WORLD, ("Instagram Reels", "https://www.instagram.com/reels/"),
               ("Vimeo Staff Picks", "https://vimeo.com/channels/staffpicks"),
               ("Eyecannndy: name a technique", "https://eyecannndy.com")],
    "style": [PINTEREST, ("Cosmos: curated images; set AI to Hide in its settings", "https://www.cosmos.so"),
              ("Same.energy: search by image", "https://same.energy"),
              ("Public Work: copyright-free images", "https://www.cosmos.so/public-work")],
    "music": [("Rate Your Music: genres and descriptors", "https://rateyourmusic.com/genres/"),
              ("Bandcamp: AI music banned since January 2026", "https://bandcamp.com"),
              ("Cosine.club: similar tracks", "https://cosine.club/")],
    "provenance": [("TinEye: upload the image, sort by oldest", "https://tineye.com"),
                   ("Google Lens: upload the image", "https://lens.google.com"),
                   ("Yandex Images: for a face or Eastern Europe", "https://yandex.com/images/search?text={q}"),
                   ("DuckDuckGo with AI images hidden", "https://noai.duckduckgo.com/?q={q}&iax=images&ia=images")],
}


def links(a):
    words = a.query.strip()
    values = {"q": urllib.parse.quote_plus(words), "p": urllib.parse.quote(words)}
    jobs = [a.job] if a.job else list(PERSON_LINKS)
    rows = [{"job": job, "title": title, "url": template.format(**values)}
            for job in jobs for title, template in PERSON_LINKS[job]]
    return out("links", words, None, "ok", len(rows), rows, "For a person to open. Do not fetch these.")


def fuse(a):
    """Reciprocal rank fusion: score = sum of 1 / (60 + rank). It merges duplicates and rank across queries, and cuts by
    maker only with --per-maker. One pick per maker belongs at the shortlist, after opening."""
    scores, items, empty = {}, {}, []
    for path in a.files:
        try:
            with open(path, encoding="utf-8") as handle:
                record = json.load(handle)
        except (OSError, ValueError):
            record = {}
        rows = (record.get("results") or record.get("items") or []) if isinstance(record, dict) else []
        if not rows:
            empty.append(path)
            print(f"search.py fuse: no results in {path}", file=sys.stderr)
        for position, item in enumerate(rows, 1):
            key = item.get("url") or item.get("title")
            if not key:
                continue
            rank = item.get("rank") or position
            scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank)
            found = items.setdefault(key, dict(item, maker=item.get("maker") or item.get("by"), found_by=[]))
            found["found_by"].append({"source": record.get("source") or os.path.basename(path),
                                      "query": record.get("query"), "rank": rank})
    per_maker, kept = collections.Counter(), []
    for key in sorted(scores, key=scores.get, reverse=True):
        maker = (items[key].get("maker") or "").strip().lower()
        if a.per_maker and maker and per_maker[maker] >= a.per_maker:
            continue
        per_maker[maker] += 1
        items[key]["fused_score"] = round(scores[key], 5)
        kept.append(items[key])
    note = "Across different sources few items overlap, so read the top of each query too."
    if empty:
        note += " No results in: " + ", ".join(empty) + "."
    return {"source": "fuse", "inputs": a.files, "status": "ok" if scores else "error", "total": len(scores),
            "found_by_several": sum(len(item["found_by"]) > 1 for item in items.values()), "results": kept[: a.limit],
            "note": note}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="a source name, or: sources, links, fuse")
    parser.add_argument("query", nargs="*", help="the query (for fuse: result files)")
    parser.add_argument("--limit", type=int, help="default 10; arena-walk 100, commons-cat 50, refs 8")
    parser.add_argument("--log", help="append every outcome to this JSONL file")
    parser.add_argument("--job", choices=list(PERSON_LINKS), help="links: only this job's sites")
    parser.add_argument("--per-maker", type=int, help="fuse: keep at most N per maker")
    parser.add_argument("--medium")
    parser.add_argument("--artist", action="store_true")
    parser.add_argument("--public-domain", action="store_true")
    parser.add_argument("--categories", action="store_true")
    parser.add_argument("--allow-ai", action="store_true", help="commons: keep AI-generated images, for the never board")
    parser.add_argument("--width", type=int, help="commons, commons-cat: width of the sized copy in image (default 800)")
    parser.add_argument("--collection")
    parser.add_argument("--dates")
    parser.add_argument("--type")
    parser.add_argument("--asset", default="hdris")
    parser.add_argument("--color")
    parser.add_argument("--style")
    parser.add_argument("--year")
    a = parser.parse_args()
    if a.source == "sources":
        for name, (_, purpose) in SOURCES.items():
            print(f"{name:16} {purpose}")
        return 0
    if a.limit is None and a.source != "refs":
        a.limit = {"arena-walk": 100, "commons-cat": 50}.get(a.source, 10)
    if a.source == "fuse":
        a.files = a.query
        handler = fuse
    else:
        a.query = " ".join(a.query)
        handler = links if a.source == "links" else (SOURCES.get(a.source) or (None,))[0]
        if handler is None:
            parser.error(f"unknown source {a.source}. Run: search.py sources")
    try:
        record = handler(a)
    except Exception as error:  # a record and a log row, never a traceback
        record = failed(a.source, a.query, None, "error", f"{type(error).__name__}: {error}")
    if a.log:
        try:
            with open(a.log, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({k: v for k, v in record.items() if k != "results"} | {"hits": [
                    {"rank": r.get("rank"), "url": r.get("url")} for r in record.get("results", [])]}) + "\n")
        except OSError as error:
            print(f"search.py: could not write the log: {error}", file=sys.stderr)
    print(json.dumps(record, indent=1, ensure_ascii=False))
    return 0 if record.get("status", "ok") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
