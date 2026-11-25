"""Local Studio server: the built web client plus a small typed JSON API over one project.

Security model (local tool, one user):
* binds 127.0.0.1 only; the project root is fixed at start, nothing else is served;
* every request must carry Host 127.0.0.1:<port> or localhost:<port> (DNS-rebinding guard);
* every /api POST needs Origin http://127.0.0.1:<port> or http://localhost:<port>, a JSON
  Content-Type and the per-run token from the page (X-Bot-UI-Token) - another web page can
  neither read nor write; the sandboxed widget preview has an opaque origin and is refused;
* writes go through store.write_patch (revision check, lock, validation, atomic replace);
* no request leaves this machine, with one exception the user starts by hand: importing a premium
  emoji pack by link sends the pack name to the telegram-bot-ui resolver (emoji.py), or, when
  the resolver is off and a token is in the environment, calls the read-only
  getStickerSet/getFile on api.telegram.org; the page never sends or receives a token;
* widget builds run the skill's offline builder.
"""
from __future__ import annotations

import json
import mimetypes
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import SCHEMA_VERSION, TOOL_VERSION, builder, emoji, widgets
from .engine import parity_view, run_scenario
from .project import Snapshot, open_snapshot, parse_files
from .render import bot_request, render_screen
from .store import StoreError, screen_patch, write_patch
from .validate import summary, validate

from .skill import trusted_web_dir

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BODY = 2 * 1024 * 1024


def project_document(snap: Snapshot, *, include_widget_sources: bool = True) -> dict:
    """What a client needs to draw the map, edit and simulate. No absolute paths."""
    diags = validate(snap)
    widgets_doc = {}
    for wid, w in snap.widgets.items():
        files = {rel.split("/", 2)[2]: snap.files[rel].decode("utf-8") for rel in snap.files
                 if rel.startswith(f"widgets/{wid}/")} if include_widget_sources else {}
        widgets_doc[wid] = {"meta": w, "files": files}
    return {"schemaVersion": SCHEMA_VERSION, "tool": TOOL_VERSION, "revision": snap.revision,
            "readOnly": snap.read_only, "project": snap.project, "screens": snap.screens,
            "screenFiles": snap.screen_files, "scenarios": snap.scenarios, "widgets": widgets_doc,
            "diagnostics": [d.to_json() for d in diags], "summary": summary(diags)}


def _overlay(snap: Snapshot, screens: dict | None) -> Snapshot:
    """A draft snapshot: the saved files with some screens replaced in memory (never written)."""
    if not screens:
        return snap
    from .project import canonical_json
    files = dict(snap.files)
    for sid, doc in screens.items():
        files[snap.screen_path(sid) if sid in snap.screens else f"screens/{sid}.json"] = canonical_json(doc, "screen")
    return parse_files(snap.root, files)


def _examples(snap: Snapshot) -> dict:
    """Caption values for previews and exports: the declared example of each field (synthetic)."""
    return {k: f["example"] for k, f in ((snap.project or {}).get("fields") or {}).items()
            if isinstance(f, dict) and "example" in f}


def git_status(root: str, snap: Snapshot) -> dict:
    """What is saved in the project folder but not committed (read-only Git calls only)."""
    import subprocess

    def git(*args: str) -> str | None:
        try:
            p = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=root, capture_output=True,
                               timeout=10, encoding="utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout if p.returncode == 0 else None

    top = git("rev-parse", "--show-toplevel")
    if top is None:
        return {"git": False, "files": [], "diff": ""}
    rel = os.path.relpath(os.path.realpath(root), os.path.realpath(top.strip())).replace(os.sep, "/")
    by_path = {f"{rel}/{p}" if rel != "." else p: sid for sid, p in snap.screen_files.items()}
    files = []
    for line in (git("status", "--porcelain=v1", "--untracked-files=all", "--", ".") or "").splitlines():
        status, path = line[:2].strip() or "M", line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if "/.bot-ui/" in f"/{path}":
            continue
        item = {"path": path, "status": status}
        if path in by_path:
            item["screenId"] = by_path[path]
        m = path.split("/widgets/", 1)
        if len(m) == 2 and "/" in m[1] and not m[1].startswith("_kit/"):
            item["widgetId"] = m[1].split("/", 1)[0]
        files.append(item)
    return {"git": True, "branch": (git("rev-parse", "--abbrev-ref", "HEAD") or "").strip(),
            "head": (git("rev-parse", "--short", "HEAD") or "").strip(), "projectPath": rel,
            "files": files, "diff": git("diff", "HEAD", "--", ".") or ""}


class Studio:
    def __init__(self, root: str, port: int, emoji_library_file: str | None = None) -> None:
        self.root = root
        self.library_file = emoji_library_file  # the emoji library's offline export, instead of the network
        self.port = port
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.dist = trusted_web_dir(root, "dist")  # None: the client lies inside the repository being opened

    # ------------------------------------------------------------ API
    def api(self, path: str, body: dict) -> tuple[int, dict]:
        snap = open_snapshot(self.root)
        if path == "/api/project":
            import hashlib
            root_key = hashlib.sha256(os.path.normcase(os.path.realpath(self.root)).encode()).hexdigest()[:16]
            return 200, {**project_document(snap), "rootKey": root_key, "rootLabel": os.path.basename(self.root),
                         "cliProject": self.root}
        if path in ("/api/requests/save", "/api/requests/list", "/api/requests/cancel"):
            from .context import ContextError, add_request, list_requests, set_request_status
            if path == "/api/requests/list":
                return 200, {"requests": list_requests(os.path.join(self.root, "context"))}
            if snap.read_only:
                return 403, {"error": "READ_ONLY", "message": "this project is read-only"}
            try:  # api() already runs under self.lock; the request file has its own lock for agents
                if path == "/api/requests/cancel":
                    doc = set_request_status(self.root, "context", str(body.get("id") or ""), "cancel",
                                             "removed in the Studio")
                else:
                    doc = add_request(self.root, "context", body.get("sid") or None, str(body.get("text") or ""),
                                      snap.revision)
            except ContextError as err:
                status = {1: 404, 4: 409}.get(err.exit_code, 400)
                return status, {"error": "BAD_REQUEST" if status == 400 else "CONFLICT" if status == 409 else
                                "NOT_FOUND", "message": str(err)}
            return 200, {"request": doc, "path": f"context/requests/{doc['id']}.json"}
        if path == "/api/git-status":
            return 200, git_status(self.root, snap)
        if path == "/api/revision":
            return 200, {"revision": snap.revision}
        if path == "/api/validate":
            draft = _overlay(snap, body.get("screens"))
            diags = validate(draft)
            return 200, {"revision": snap.revision, "diagnostics": [d.to_json() for d in diags], "summary": summary(diags)}
        if path in ("/api/save", "/api/preview-patch"):
            patch = body.get("patch")
            if patch is None and "screen" in body:
                patch = screen_patch(snap, body["screen"]["id"], body["screen"])
                patch["baseRevision"] = body.get("expectedRevision", snap.revision)
            try:
                res = write_patch(self.root, patch, dry_run=path == "/api/preview-patch")
            except StoreError as err:
                status = 409 if err.code == "REVISION_CONFLICT" else 422
                return status, {"ok": False, "error": err.to_json(), "patch": patch}
            return 200, {**res.to_json(), "patch": patch}
        if path == "/api/simulate":
            draft = _overlay(snap, body.get("screens"))
            sc = body.get("scenario")
            if isinstance(sc, str):
                sc = draft.scenarios.get(sc)
            if not isinstance(sc, dict):
                return 404, {"ok": False, "error": {"code": "SCENARIO_NOT_FOUND", "message": "no such scenario"}}
            return 200, parity_view(run_scenario(draft, sc))
        if path == "/api/render":
            draft = _overlay(snap, body.get("screens"))
            sid = body.get("screenId")
            if sid not in draft.screens:
                return 404, {"ok": False, "error": {"code": "SCREEN_NOT_FOUND", "message": str(sid)}}
            logical = render_screen(draft.project or {}, draft.screens[sid], locale=body.get("locale"),
                                    state=body.get("state"), values=body.get("values"))
            return 200, {"render": logical, "request": bot_request(logical, 111111111)}
        if path == "/api/widget/build":
            wid = body.get("widget")
            draft = snap
            if body.get("files"):
                files = dict(snap.files)
                for name, text in body["files"].items():
                    if "/" in name or "\\" in name or name.startswith("."):
                        return 422, {"ok": False, "error": {"code": "PATH_REFUSED", "message": name}}
                    files[f"widgets/{wid}/{name}"] = str(text).encode("utf-8")
                draft = parse_files(self.root, files)
            if wid not in draft.widgets:
                return 404, {"ok": False, "error": {"code": "WIDGET_NOT_FOUND", "message": str(wid)}}
            built = widgets.build(draft, wid, lang=body.get("lang"), values=body.get("values") or _examples(draft),
                                  state=body.get("state"))
            if built["ok"]:
                built["payload"] = widgets.payload(draft, wid, built, state=body.get("state", "default"))
                built["payload"]["params"]["html"] = f"<{built['rawBytes']} bytes>"
            built["draft"] = bool(body.get("files"))
            return 200, built
        if path == "/api/widget/export":
            wid = body.get("widget")
            built = widgets.build(snap, wid, lang=body.get("lang"), values=body.get("values") or _examples(snap))
            try:
                return 200, widgets.export(snap, wid, built, body.get("sourceHash", ""))
            except widgets.WidgetError as err:
                return 409, {"ok": False, "error": {"code": err.code, "message": err.message,
                                                    "currentHash": built["sourceHash"]}}
        if path == "/api/widget/templates":
            return 200, {"templates": widgets.templates()}
        if path == "/api/widget/template-preview":
            try:
                return 200, widgets.template_preview(snap, str(body.get("template", "blank")), body.get("lang"))
            except widgets.WidgetError as err:
                return 422, {"ok": False, "error": {"code": err.code, "message": err.message}}
        if path == "/api/widget/create":
            try:
                patch = widgets.creation_patch(snap, str(body.get("widgetId", "")), str(body.get("template", "blank")),
                                               body.get("title"))
                if body.get("expectedRevision"):
                    patch["baseRevision"] = body["expectedRevision"]
                res = write_patch(self.root, patch)
            except widgets.WidgetError as err:
                return 422, {"ok": False, "error": {"code": err.code, "message": err.message}}
            except StoreError as err:
                return (409 if err.code == "REVISION_CONFLICT" else 422), {"ok": False, "error": err.to_json()}
            return 200, res.to_json()
        if path == "/api/widget/builder-schema":
            return 200, builder.schema((snap.project or {}).get("locales"))
        if path == "/api/widget/builder-validate":
            wid = body.get("widget")
            assets = builder.assets_of(snap, wid) if isinstance(wid, str) and wid in snap.widgets else None
            issues = builder.validate_config(body.get("config"), assets)
            return 200, {"ok": not issues, "issues": issues}
        if path == "/api/widget/eject":
            try:
                patch = builder.eject_patch(snap, str(body.get("widget", "")))
                if body.get("expectedRevision"):
                    patch["baseRevision"] = body["expectedRevision"]
                res = write_patch(self.root, patch)
            except widgets.WidgetError as err:
                return (404 if err.code == "WIDGET_NOT_FOUND" else 422), {"ok": False, "error": {"code": err.code, "message": err.message}}
            except StoreError as err:
                return (409 if err.code == "REVISION_CONFLICT" else 422), {"ok": False, "error": err.to_json()}
            return 200, res.to_json()
        if path.startswith("/api/emoji"):
            return self.emoji_api(path, body, snap)
        if path == "/api/widget/runtime":
            wid = body.get("widget")
            return 200, {**widgets.preview_runtime(), "answers": widgets.mock_answers(snap, wid) if wid in snap.widgets else {}}
        return 404, {"ok": False, "error": {"code": "NOT_FOUND", "message": path}}

    def emoji_api(self, path: str, body: dict, snap: Snapshot) -> tuple[int, dict]:
        from . import emoji_catalog
        try:
            if path == "/api/emoji":
                return 200, emoji.client_document(self.root, snap, self.library_file)
            if snap.read_only and path in ("/api/emoji/import", "/api/emoji/import-used", "/api/emoji/icon",
                                                     "/api/emoji/remove-pack"):
                return 409, {"ok": False, "error": {"code": "READ_ONLY", "message": "this project opens read-only"}}
            if path == "/api/emoji/import":
                res = emoji.import_pack(self.root, link=body.get("link"), sticker_set=body.get("stickerSet"))
                return 200, {**res, **emoji.client_document(self.root, open_snapshot(self.root), self.library_file)}
            if path == "/api/emoji/import-used":
                res = emoji.import_used(self.root, snap)
                return 200, {**res, **emoji.client_document(self.root, open_snapshot(self.root), self.library_file)}
            if path == "/api/emoji/icon":
                emoji.set_icon(self.root, str(body.get("slot", "")), body.get("id"), note=body.get("note"),
                               fallback=body.get("fallback"))
                return 200, {"ok": True, **emoji.client_document(self.root, snap, self.library_file)}
            if path == "/api/emoji/remove-pack":
                res = emoji.remove_pack(self.root, str(body.get("pack", "")))
                return 200, {**res, **emoji.client_document(self.root, snap, self.library_file)}
            if path == "/api/emoji/library":  # the user's action: network (or the export), cache only
                emoji_catalog.fetch_catalog(self.root, library_file=self.library_file)
                return 200, {"ok": True, **emoji.client_document(self.root, snap, self.library_file)}
            if path == "/api/emoji/pick":
                emoji_catalog.pick(self.root, snap, library_file=self.library_file)
                return 200, {"ok": True, **emoji.client_document(self.root, snap, self.library_file)}
            if path == "/api/emoji/brief":
                b = emoji.brief(_overlay(snap, body.get("screens")))
                return 200, {**b, "markdown": emoji.brief_markdown(b)}
        except emoji.EmojiError as err:
            status = 502 if err.code.startswith("TELEGRAM_") else 404 if err.code.endswith("NOT_FOUND") else 422
            return status, {"ok": False, "error": err.to_json()}
        return 404, {"ok": False, "error": {"code": "NOT_FOUND", "message": path}}

    # ------------------------------------------------------------ HTTP
    def handler(self):
        studio = self

        class H(BaseHTTPRequestHandler):
            server_version = "bot-ui-studio"

            def log_message(self, *args):
                pass

            def _host_ok(self) -> bool:
                return self.headers.get("Host") in (f"127.0.0.1:{studio.port}", f"localhost:{studio.port}")

            def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Cross-Origin-Resource-Policy", "same-origin")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)

            def _json(self, status: int, doc: Any) -> None:
                self._send(status, json.dumps(doc, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

            def do_GET(self):
                if not self._host_ok():
                    return self._json(421, {"ok": False, "error": {"code": "HOST_REFUSED", "message": "unexpected Host"}})
                path = self.path.split("?", 1)[0]
                if path.startswith("/api/"):
                    return self._json(405, {"ok": False, "error": {"code": "POST_ONLY", "message": "API calls are POST"}})
                return self._static(path)

            def do_POST(self):
                if not self._host_ok():
                    return self._json(421, {"ok": False, "error": {"code": "HOST_REFUSED", "message": "unexpected Host"}})
                origin = self.headers.get("Origin")
                if origin not in (f"http://127.0.0.1:{studio.port}", f"http://localhost:{studio.port}"):
                    return self._json(403, {"ok": False, "error": {"code": "ORIGIN_REFUSED", "message": f"origin {origin!r}"}})
                if self.headers.get("X-Bot-UI-Token") != studio.token:
                    return self._json(403, {"ok": False, "error": {"code": "TOKEN_REFUSED", "message": "missing or wrong token"}})
                if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                    return self._json(415, {"ok": False, "error": {"code": "JSON_ONLY", "message": "Content-Type: application/json"}})
                n = int(self.headers.get("Content-Length") or 0)
                if n > MAX_BODY:
                    return self._json(413, {"ok": False, "error": {"code": "TOO_LARGE", "message": f"> {MAX_BODY} bytes"}})
                try:
                    body = json.loads(self.rfile.read(n) or b"{}")
                except json.JSONDecodeError:
                    return self._json(400, {"ok": False, "error": {"code": "JSON_INVALID", "message": "body is not JSON"}})
                api_path = self.path.split("?", 1)[0]
                try:
                    if api_path in ("/api/emoji/import", "/api/emoji/import-used", "/api/emoji/library", "/api/emoji/pick"):
                        # they wait on Telegram or the library; imports take the write lock themselves, the others
                        # write the local cache only
                        status, doc = studio.api(api_path, body if isinstance(body, dict) else {})
                    else:
                        with studio.lock:
                            status, doc = studio.api(api_path, body if isinstance(body, dict) else {})
                except Exception as err:  # report, never crash the server
                    status, doc = 500, {"ok": False, "error": {"code": "INTERNAL", "message": f"{type(err).__name__}: {err}"}}
                return self._json(status, doc)

            def _static(self, path: str) -> None:
                if path.startswith("/emoji-preview/"):
                    full = emoji.preview_file(studio.root, path.rsplit("/", 1)[-1])
                    if not full:
                        return self._json(404, {"ok": False, "error": {"code": "NOT_FOUND", "message": path}})
                    with open(full, "rb") as fh:
                        data = fh.read()
                    ext = full.rsplit(".", 1)[-1]
                    return self._send(200, data, {"webm": "video/webm", "jpg": "image/jpeg"}.get(ext, f"image/{ext}"))
                if path == "/preview-frame.html":
                    return self._send(200, PREVIEW_FRAME.encode("utf-8"), "text/html; charset=utf-8",
                                      {"Content-Security-Policy": PREVIEW_CSP})
                if path in ("/", "/index.html") or not os.path.splitext(path)[1]:
                    if studio.dist is None:
                        return self._send(503, REFUSED.encode("utf-8"), "text/html; charset=utf-8")
                    index = os.path.join(studio.dist, "index.html")
                    if not os.path.isfile(index):
                        return self._send(503, NOT_BUILT.encode("utf-8"), "text/html; charset=utf-8")
                    with open(index, encoding="utf-8") as fh:
                        html = fh.read().replace("__BOT_UI_TOKEN__", studio.token).replace("__BOT_UI_MODE__", "studio")
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8", {
                        "Content-Security-Policy": CSP})
                rel = path.lstrip("/")
                dist = os.path.realpath(studio.dist) if studio.dist else None
                full = os.path.realpath(os.path.join(dist, *rel.split("/"))) if dist else None
                if not full or os.path.commonpath([full, dist]) != dist or not os.path.isfile(full):
                    return self._json(404, {"ok": False, "error": {"code": "NOT_FOUND", "message": path}})
                with open(full, "rb") as fh:
                    data = fh.read()
                ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
                if full.endswith(".js"):
                    ctype = "text/javascript; charset=utf-8"
                return self._send(200, data, ctype)

        return H


# The page may call only itself; the widget preview frame (srcdoc, sandbox without
# allow-same-origin) carries its own stricter CSP with connect-src 'none'.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; "
       "font-src 'self' data:; connect-src 'self'; frame-src 'self' about: data:; child-src 'self' about: data:; "
       "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

# The widget preview frame. Loaded with <iframe sandbox="allow-scripts"> (opaque origin: no
# cookies, storage or same-origin access to the Studio, its API refuses Origin: null), and
# its own CSP: no network at all, inline code only. The parent sends the document to show;
# the frame accepts it once, from its parent only.
# `sandbox allow-scripts` in the response header gives the same opaque-origin isolation as the
# iframe attribute, so the frame stays isolated even where an embedding browser (e.g. an app's
# built-in pane) refuses frames that carry the sandbox attribute.
PREVIEW_CSP = ("sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
               "img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'")
PREVIEW_FRAME = """<!doctype html><html><head><meta charset="utf-8"></head><body><script>
addEventListener("message", function once(e) {
  if (e.source !== parent || !e.data || e.data.k !== "load" || typeof e.data.doc !== "string") return;
  removeEventListener("message", once);
  document.open(); document.write(e.data.doc); document.close();
});
parent.postMessage({k: "frame-ready"}, "*");
</script></body></html>"""

REFUSED = """<!doctype html><meta charset="utf-8"><title>bot-ui Studio</title>
<body style="font:16px system-ui;max-width:40rem;margin:4rem auto">
<h1>The Studio client was not served</h1>
<p>The client folder found by default lies inside the repository you opened, and a repository could
ship its own page there. Start the Studio again with <code>BOT_UI_STUDIO_DIR</code> set to the
<code>studio</code> folder of a telegram-bot-ui checkout you trust.</p>"""

NOT_BUILT = """<!doctype html><meta charset="utf-8"><title>bot-ui Studio</title>
<body style="font:16px system-ui;max-width:40rem;margin:4rem auto">
<h1>The Studio client is not built</h1>
<p>Run once, then restart <code>bot-ui studio</code>:</p>
<pre>cd studio/web
npm ci
npm run build</pre>
<p>The CLI works without it: <code>bot-ui list</code>, <code>show</code>, <code>validate</code>, <code>simulate</code>.</p>"""


def serve(root: str, *, host: str = "127.0.0.1", port: int = 0, open_screen: str | None = None,
          open_browser: bool = False, ready: threading.Event | None = None, holder: dict | None = None,
          quiet: bool = False, emoji_library_file: str | None = None) -> int:
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("the Studio binds to loopback only")
    srv = ThreadingHTTPServer((host, port), BaseHTTPRequestHandler)
    studio = Studio(root, srv.server_address[1], emoji_library_file)
    srv.RequestHandlerClass = studio.handler()
    url = f"http://127.0.0.1:{studio.port}/" + (f"#/screen/{open_screen}" if open_screen else "")
    banner = f"bot-ui Studio {TOOL_VERSION} for {root}\n  {url}\n  Ctrl+C stops it (local only; nothing is sent to Telegram)\n"
    try:
        sys.stdout.write("" if quiet else banner)
    except UnicodeEncodeError:  # a non-UTF-8 console and a Unicode project path
        sys.stdout.write(banner.encode("ascii", "backslashreplace").decode("ascii"))
    sys.stdout.flush()
    if holder is not None:
        holder.update(server=srv, studio=studio, url=url)
    if ready is not None:
        ready.set()
    if open_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0
