#!/usr/bin/env python3
"""Local server for the previz. Serves the PROJECT folder (the parent of this folder), so the storyboard, the track
and the stills referenced in config.json resolve, and saves edits.

  python3 previz/serve.py [port] [--no-open]   -> http://localhost:8765/previz/
  POST /api/save    body = edits JSON           -> previz/data/edits.json (+ timestamped copy in data/history/)
  POST /api/export  {name, text}                -> previz/<name> (.md only)
"""
import json
import sys
import webbrowser
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
PORT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8765)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _local(self):
        """Writes only from this app: Host must be localhost, and a browser Origin (if sent) must be this server.
        Stops any other website the user visits from POSTing to the local server."""
        ok = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in ok and (origin is None or origin.split("://", 1)[-1] in ok)

    def do_POST(self):
        if not self._local():
            return self._reply(403, {"error": "only same-origin requests from localhost"})
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            return self._reply(400, {"error": f"bad json: {e}"})
        if self.path == "/api/save":
            (DATA / "history").mkdir(parents=True, exist_ok=True)
            text = json.dumps(payload, ensure_ascii=False, indent=1)
            (DATA / "edits.json").write_text(text, encoding="utf-8")
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            (DATA / "history" / f"edits_{stamp}.json").write_text(text, encoding="utf-8")
            return self._reply(200, {"ok": True, "path": f"{HERE.name}/data/edits.json"})
        if self.path == "/api/export":
            name = Path(str(payload.get("name", ""))).name
            if not name.endswith(".md"):
                return self._reply(400, {"error": "only .md"})
            (HERE / name).write_text(str(payload.get("text", "")), encoding="utf-8")
            return self._reply(200, {"ok": True, "path": f"{HERE.name}/{name}"})
        return self._reply(404, {"error": "unknown endpoint"})

    def log_message(self, fmt, *args):
        if self.command == "POST":
            super().log_message(fmt, *args)


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/{HERE.name}/"
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(ROOT)))
    print(f"previz: {url}", flush=True)
    if "--no-open" not in sys.argv:
        webbrowser.open(url)
    srv.serve_forever()
