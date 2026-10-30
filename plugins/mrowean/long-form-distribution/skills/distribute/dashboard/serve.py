#!/usr/bin/env python3
"""serve.py: the local server behind the distribution dashboard.

Standard library only. Binds to 127.0.0.1, so nothing leaves your machine.

    python3 serve.py              # your data, at http://127.0.0.1:8799
    python3 serve.py --demo       # the bundled sample issue, nothing written to disk
    python3 serve.py --port 9000

Your data lives in ~/distribution-tracker (set LFD_HOME to move it):

    issues/<slug>.json   one file per issue, written by the /distribute skill
    covers/<file>        optional cover images, referenced as "cover": "covers/<file>"
    log.jsonl            one row per tick, skip or posted link; append-only

The page reads /api/state and writes through three routes:
    POST /api/check  {issue, item, on}        tick or untick a post
    POST /api/skip   {issue, item, on}        "not posting this one"
    POST /api/log    {issue, item, url}       the permalink, once it's live
    GET  /api/export.csv                      every posted link, as a spreadsheet
"""
import argparse
import csv
import errno
import io
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
SAMPLE = HERE.parent / "sample"
HOME = Path(os.environ.get("LFD_HOME", Path.home() / "distribution-tracker"))

# A permalink must come from the platform the post was written for.
# Substack is open-ended because publications can run on their own domain.
HOSTS = {
    "linkedin": ("linkedin.com",),
    "x": ("x.com", "twitter.com"),
    "threads": ("threads.net", "threads.com"),
    "bluesky": ("bsky.app",),
    "substack": None,
}
NAMES = {"linkedin": "LinkedIn", "x": "X", "threads": "Threads", "bluesky": "Bluesky", "substack": "Substack"}
LOOPBACK = ("127.0.0.1", "localhost", "[::1]")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    def __init__(self, root, demo=False):
        self.root = Path(root)
        self.demo = demo
        self.mem = []  # demo mode keeps the log in memory only
        if not demo:
            (self.root / "issues").mkdir(parents=True, exist_ok=True)

    def issues(self):
        out = []
        for p in sorted((self.root / "issues").glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                print(f"skipping {p.name}: {e}", file=sys.stderr)
                continue
            d.setdefault("slug", p.stem)
            out.append(d)
        # newest first; an issue with no published date yet is the one being worked on
        out.sort(key=lambda d: d.get("published") or "9999", reverse=True)
        return out

    def log(self):
        if self.demo:
            return list(self.mem)
        p = self.root / "log.jsonl"
        if not p.exists():
            return []
        rows = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
        return rows

    def append(self, row):
        row = dict(row, at=now())
        if self.demo:
            self.mem.append(row)
            return row
        with open(self.root / "log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def find(self, slug, item_id):
        for d in self.issues():
            if d.get("slug") == slug:
                for it in d.get("items", []):
                    if it.get("id") == item_id:
                        return d, it
                return d, None
        return None, None


def host_ok(platform, url):
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.netloc:
        return False, "That isn't a link. Paste the post's full URL."
    allowed = HOSTS.get(platform)
    if allowed is None:
        return True, ""
    host = u.netloc.lower().split(":")[0]
    if any(host == h or host.endswith("." + h) for h in allowed):
        return True, ""
    return False, f"That link is from {host}, but this post is for {NAMES.get(platform, platform)}."


def export_csv(store):
    issues = {d["slug"]: d for d in store.issues()}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["issue", "section", "platform", "format", "date posted", "link"])
    for r in store.log():
        if r.get("kind") != "log":
            continue
        d = issues.get(r.get("issue"), {})
        it = next((i for i in d.get("items", []) if i.get("id") == r.get("item")), {})
        sec = next((s.get("title") for s in d.get("sections", []) if s.get("id") == it.get("section")), "")
        w.writerow([d.get("title", r.get("issue")), sec, it.get("platform", ""),
                    it.get("format", ""), (r.get("at") or "")[:10], r.get("url", "")])
    return buf.getvalue()


def make_handler(store):
    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):  # quiet; errors still print
            pass

        def send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype if ctype.startswith("image/") else ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def js(self, code, obj):
            self.send(code, json.dumps(obj, ensure_ascii=False))

        def local(self):
            # A page on some other site can point its own domain at 127.0.0.1
            # ("DNS rebinding"); its requests then carry that domain as Host.
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if host in LOOPBACK:
                return True
            self.js(403, {"ok": False, "error": "this server only answers to 127.0.0.1"})
            return False

        def do_GET(self):
            if not self.local():
                return
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                return self.send(200, (HERE / "index.html").read_bytes(), "text/html")
            if path in ("/app.js", "/sample-data.js"):
                return self.send(200, (HERE / path[1:]).read_bytes(), "text/javascript")
            if path == "/api/state":
                return self.js(200, {"ok": True, "demo": store.demo, "home": str(store.root),
                                     "issues": store.issues(), "log": store.log()})
            if path.startswith("/covers/"):
                name = path[len("/covers/"):]
                kind = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                        "webp": "image/webp", "gif": "image/gif"}.get(name.rsplit(".", 1)[-1].lower())
                f = store.root / "covers" / name
                if kind and "/" not in name and not name.startswith(".") and f.is_file():
                    return self.send(200, f.read_bytes(), kind)
                return self.js(404, {"ok": False, "error": "not found"})
            if path == "/api/export.csv":
                body = export_csv(store)
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="posted.csv"')
                self.end_headers()
                return self.wfile.write(body.encode("utf-8"))
            self.js(404, {"ok": False, "error": "not found"})

        def do_POST(self):
            if not self.local():
                return
            path = urlparse(self.path).path
            # Same-origin only: the page is served from here, so anything else is a stranger.
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                return self.js(403, {"ok": False, "error": "cross-origin request refused"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(min(n, 65536)) or b"{}")
            except ValueError:
                return self.js(400, {"ok": False, "error": "bad JSON"})
            slug, item_id = str(body.get("issue", "")), str(body.get("item", ""))
            d, it = store.find(slug, item_id)
            if not it:
                return self.js(404, {"ok": False, "error": "no such post in that issue"})
            if path in ("/api/check", "/api/skip"):
                kind = path.rsplit("/", 1)[1]
                row = store.append({"kind": kind, "issue": slug, "item": item_id, "on": bool(body.get("on", True))})
                return self.js(200, {"ok": True, "row": row})
            if path == "/api/log":
                url = str(body.get("url", "")).strip()
                ok, why = host_ok(it.get("platform", ""), url)
                if not ok:
                    return self.js(400, {"ok": False, "error": why})
                row = store.append({"kind": "log", "issue": slug, "item": item_id,
                                    "platform": it.get("platform"), "url": url})
                return self.js(200, {"ok": True, "row": row})
            self.js(404, {"ok": False, "error": "not found"})

    return H


def main():
    ap = argparse.ArgumentParser(description="Serve the distribution dashboard on this machine only.")
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--demo", action="store_true", help="show the bundled sample issue; write nothing")
    a = ap.parse_args()
    store = Store(SAMPLE if a.demo else HOME, demo=a.demo)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(store))
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            print(f"Port {a.port} is already in use. If the dashboard is already running, open http://127.0.0.1:{a.port}")
            print("Otherwise start it on another port with --port.")
            sys.exit(3)
        # Anything else is usually an agent sandbox that blocks local servers.
        print(f"Couldn't open port {a.port}: {e.strerror or e}.")
        print("If an agent ran this, its sandbox may not allow local servers. Run this command in your own terminal:")
        print(f'    python3 "{Path(__file__).resolve()}"' + (f" --port {a.port}" if a.port != 8799 else ""))
        sys.exit(4)
    print(f"Distribution dashboard: http://127.0.0.1:{a.port}")
    print(f"Data: {'bundled sample (demo, nothing saved)' if a.demo else store.root}")
    print("Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
