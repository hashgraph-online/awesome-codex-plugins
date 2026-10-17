#!/usr/bin/env python3
"""Visual companion HTTP server with SSE auto-reload and click event capture.

Usage: python3 server.py --dir <path> [--owner-pid <pid>]

Serves HTML files from --dir. Fragments (no <!DOCTYPE or <html>) are wrapped
with a full document template including frame CSS and client JS. File changes
trigger SSE reload in connected browsers. Click events on [data-choice]
elements are captured to events.jsonl.
"""

import argparse
import atexit
import json
import mimetypes
import os
import signal
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRAME_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, -apple-system, sans-serif; padding: 2rem; background: #fafafa; color: #1a1a1a; }
h1 { font-size: 1.5rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #444; }
.options { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.option { background: #fff; border: 2px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.option.recommended { border-color: #2563eb; }
.option h3 { margin-bottom: 0.75rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.card { background: #fff; border: 1px solid #e5e5e5; border-radius: 6px; padding: 1rem; }
.mockup { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; max-width: 800px; margin: 0 auto; }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.pros-cons { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.pros-cons .pros { color: #16a34a; }
.pros-cons .cons { color: #dc2626; }
.mock-nav { background: #f3f4f6; padding: 0.75rem 1rem; border-bottom: 1px solid #e5e5e5; display: flex; gap: 1rem; align-items: center; }
.mock-sidebar { background: #f9fafb; padding: 1rem; border-right: 1px solid #e5e5e5; min-width: 200px; }
.mock-content { padding: 1.5rem; flex: 1; }
.mock-button { display: inline-block; background: #2563eb; color: #fff; padding: 0.5rem 1rem; border-radius: 4px; font-size: 0.875rem; }
.mock-input { display: block; width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; background: #fff; margin-bottom: 0.5rem; }
.selected { border-color: #2563eb; background: #f0f7ff; }"""

CLIENT_JS = """\
<script>
(function() {
  // Click delegation for [data-choice] elements
  document.body.addEventListener('click', function(e) {
    var el = e.target.closest('[data-choice]');
    if (!el) return;
    // Toggle selection: remove .selected from siblings, add to clicked
    var parent = el.parentElement;
    if (parent) {
      var siblings = parent.querySelectorAll('[data-choice]');
      for (var i = 0; i < siblings.length; i++) {
        siblings[i].classList.remove('selected');
      }
    }
    el.classList.add('selected');
    // Post event to server
    fetch('/event', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        type: 'choice',
        choice: el.dataset.choice,
        text: el.textContent.trim(),
        timestamp: new Date().toISOString()
      })
    });
  });
  // SSE auto-reload
  var es = new EventSource('/sse');
  es.onmessage = function() { location.reload(); };
})();
</script>"""

IDLE_TIMEOUT = 1800  # 30 minutes
POLL_INTERVAL = 0.5  # seconds
SSE_STREAM_LIMIT = 3600  # seconds per SSE connection; the browser reconnects on its own

# ---------------------------------------------------------------------------
# Server state (module-level, shared across threads)
# ---------------------------------------------------------------------------

last_request_time = time.time()
sse_clients = []  # list of threading.Event objects, one per SSE connection
sse_lock = threading.Lock()
_events_lock = threading.Lock()
serve_dir = ""
verbose = False
_cleanup_fn = None  # set by main(), called before exit


MAX_SSE_CLIENTS = 20
MAX_EVENTS_SIZE = 1_000_000  # 1MB


def _find_latest_html(directory):
    try:
        candidates = []
        for name in os.listdir(directory):
            if not (name.endswith('.html') or name.endswith('.htm')):
                continue
            full = os.path.join(directory, name)
            if not os.path.isfile(full):
                continue
            try:
                candidates.append((os.path.getmtime(full), full))
            except OSError:
                pass
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]
    except OSError:
        return None


def register_sse_client():
    with sse_lock:
        if len(sse_clients) >= MAX_SSE_CLIENTS:
            return None
        ev = threading.Event()
        sse_clients.append(ev)
    return ev


def unregister_sse_client(ev):
    with sse_lock:
        try:
            sse_clients.remove(ev)
        except ValueError:
            pass


def notify_sse_clients():
    with sse_lock:
        for ev in sse_clients:
            ev.set()


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        if verbose:
            super().log_message(format, *args)

    def log_request(self, code='-', size='-'):
        global last_request_time
        # SSE traffic must NOT reset the idle timer. EventSource auto-reconnects
        # on every network blip (WiFi switch, VPN, sleep/wake), so counting SSE
        # requests as activity makes the idle timeout effectively unreachable
        # while a browser tab is open -- a server was found alive 29 days after
        # start because of this. Real user/agent activity (HTML GET, POST
        # /event, DELETE /events) still resets the timer below.
        if self.path != '/sse':
            last_request_time = time.time()

    def do_GET(self):
        path = self.path.lstrip('/')
        if path == 'sse':
            return self._handle_sse()
        is_root_request = not path or path == 'index.html'
        if not path:
            path = 'index.html'
        # Block access to .vc-meta directory
        if path.startswith('.vc-meta/') or path == '.vc-meta':
            self.send_error(404)
            return
        filepath = os.path.realpath(os.path.join(serve_dir, path))
        real_serve = os.path.realpath(serve_dir)
        if not (filepath == real_serve or filepath.startswith(real_serve + os.sep)):
            self.send_error(403)
            return
        if not os.path.isfile(filepath):
            # Root request with no explicit index.html: serve the most recently
            # modified HTML file in the dir, or a waiting page if none exists.
            # This keeps a single browser tab on `/` continuously useful as the
            # agent writes new versioned files (layout-v1.html, layout-v2.html);
            # SSE reload pulls the newest file each time without manual
            # navigation. Specific paths still 404 so broken links stay visible.
            if is_root_request:
                latest = _find_latest_html(serve_dir)
                if latest is None:
                    return self._serve_waiting_page()
                filepath = latest
            else:
                self.send_error(404)
                return
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            self.send_error(413, "File too large")
            return
        with open(filepath, 'rb') as f:
            content = f.read()
        # Serve HTML with potential wrapping
        if path.endswith('.html') or path.endswith('.htm'):
            content = self._process_html(content)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            ctype, _ = mimetypes.guess_type(filepath)
            self.send_response(200)
            self.send_header('Content-Type', ctype or 'application/octet-stream')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    def do_POST(self):
        MAX_EVENT_SIZE = 65536  # 64 KB
        path = self.path.lstrip('/')
        if path != 'event':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
        except (ValueError, TypeError):
            self.send_error(400)
            return
        if length < 0:
            self.send_error(400)
            return
        if length > MAX_EVENT_SIZE:
            self.send_error(413, "Event too large")
            return
        body = self.rfile.read(length) if length else b''
        body_text = body.decode('utf-8', errors='replace').strip()
        if not body_text:
            self.send_response(204)
            self.end_headers()
            return
        try:
            parsed = json.loads(body_text)
        except (json.JSONDecodeError, ValueError):
            self.send_error(400, 'Invalid JSON')
            return
        meta_dir = os.path.join(serve_dir, '.vc-meta')
        os.makedirs(meta_dir, exist_ok=True)
        events_path = os.path.join(meta_dir, 'events.jsonl')
        with _events_lock:
            if os.path.exists(events_path) and os.path.getsize(events_path) > MAX_EVENTS_SIZE:
                with open(events_path, 'r') as f:
                    lines = f.readlines()
                with open(events_path, 'w') as f:
                    f.writelines(lines[-100:])
            with open(events_path, 'a') as f:
                f.write(json.dumps(parsed, separators=(',', ':')) + '\n')
        self.send_response(204)
        self.end_headers()

    def do_DELETE(self):
        path = self.path.lstrip('/')
        if path != 'events':
            self.send_error(404)
            return
        events_path = os.path.join(serve_dir, '.vc-meta', 'events.jsonl')
        with _events_lock:
            try:
                with open(events_path, 'w') as f:
                    pass  # truncate
            except FileNotFoundError:
                pass  # nothing to truncate
        self.send_response(204)
        self.end_headers()

    def _serve_waiting_page(self):
        body = (
            '<div style="display:flex;align-items:center;justify-content:center;'
            'height:100vh;font-family:system-ui;color:#666;text-align:center">'
            '<div><h1 style="font-size:1.25rem;margin-bottom:0.5rem">'
            'Visual companion ready</h1>'
            '<p>Waiting for the first visual to arrive. This page will refresh '
            'automatically.</p></div></div>'
        )
        wrapped = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<style>\n' + FRAME_CSS + '\n</style>\n'
            '</head>\n<body>\n' + body + '\n' + CLIENT_JS + '\n</body>\n</html>'
        ).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(wrapped)))
        self.end_headers()
        self.wfile.write(wrapped)

    def _process_html(self, raw):
        text = raw.decode('utf-8', errors='replace')
        prefix = text[:256].strip().lower()
        is_full = prefix.startswith('<!doctype') or prefix.startswith('<html')
        if is_full:
            # Inject client JS before </body> if not already present
            if 'new EventSource' not in text:
                text = text.replace('</body>', CLIENT_JS + '\n</body>')
            return text.encode('utf-8')
        # Fragment: wrap with full document
        wrapped = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<style>\n' + FRAME_CSS + '\n</style>\n'
            '</head>\n<body>\n' + text + '\n' + CLIENT_JS + '\n</body>\n</html>'
        )
        return wrapped.encode('utf-8')

    def _handle_sse(self):
        ev = register_sse_client()
        if ev is None:
            self.send_error(503, "Too many SSE clients (max 20)")
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        stream_deadline = time.time() + SSE_STREAM_LIMIT
        try:
            while time.time() < stream_deadline:
                ev.wait(timeout=30)
                if ev.is_set():
                    self.wfile.write(b'data: reload\n\n')
                    self.wfile.flush()
                    ev.clear()
                else:
                    # Keepalive comment
                    self.wfile.write(b': keepalive\n\n')
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            unregister_sse_client(ev)


# ---------------------------------------------------------------------------
# Threading server
# ---------------------------------------------------------------------------

class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


# ---------------------------------------------------------------------------
# Directory polling thread
# ---------------------------------------------------------------------------

def poll_directory(directory, owner_pid, server, max_lifetime):
    snapshot = {}
    for name in os.listdir(directory):
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            try:
                snapshot[name] = os.path.getmtime(full)
            except OSError:
                pass

    start_time = time.time()
    while True:
        time.sleep(POLL_INTERVAL)

        # Hard lifetime ceiling -- final safety net regardless of idle/owner state.
        if max_lifetime > 0 and time.time() - start_time > max_lifetime:
            sys.stderr.write("visual-companion: shutting down (max lifetime {}s reached)\n".format(int(max_lifetime)))
            if _cleanup_fn:
                _cleanup_fn()
            threading.Thread(target=server.shutdown, daemon=True).start()
            return

        # Idle timeout
        if time.time() - last_request_time > IDLE_TIMEOUT:
            sys.stderr.write("visual-companion: shutting down (idle timeout)\n")
            if _cleanup_fn:
                _cleanup_fn()
            threading.Thread(target=server.shutdown, daemon=True).start()
            return

        # Owner PID check
        if owner_pid is not None:
            try:
                os.kill(owner_pid, 0)
            except OSError:
                sys.stderr.write("visual-companion: shutting down (owner process exited)\n")
                if _cleanup_fn:
                    _cleanup_fn()
                threading.Thread(target=server.shutdown, daemon=True).start()
                return

        # Check for changes in HTML files
        try:
            current = {}
            for name in os.listdir(directory):
                full = os.path.join(directory, name)
                if os.path.isfile(full):
                    try:
                        current[name] = os.path.getmtime(full)
                    except OSError:
                        pass
        except OSError:
            sys.stderr.write("visual-companion: shutting down (serve directory gone)\n")
            if _cleanup_fn:
                _cleanup_fn()
            threading.Thread(target=server.shutdown, daemon=True).start()
            return

        changed = False
        for name, mtime in current.items():
            if name.endswith(('.html', '.htm')):
                if name not in snapshot or snapshot[name] != mtime:
                    changed = True
                    break

        snapshot = current
        if changed:
            notify_sse_clients()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global serve_dir

    parser = argparse.ArgumentParser(description='Visual companion server')
    parser.add_argument('--dir', required=True, help='Directory to serve HTML from')
    parser.add_argument('--owner-pid', type=int, default=None, help='Parent process PID for lifecycle tracking')
    parser.add_argument('--verbose', action='store_true', help='Enable HTTP request logging to stderr')
    parser.add_argument('--max-lifetime', type=float, default=28800,
                        help='Hard ceiling on server lifetime in seconds (default: 28800 = 8h). '
                             'Server exits no matter what once exceeded. Set to 0 to disable.')
    args = parser.parse_args()

    global verbose
    verbose = args.verbose
    serve_dir = os.path.abspath(args.dir)
    if not os.path.isdir(serve_dir):
        os.makedirs(serve_dir, exist_ok=True)

    # Bind directly to port 0 to avoid TOCTOU race
    server = ThreadingServer(('127.0.0.1', 0), Handler)
    port = server.server_address[1]

    # Write server-info.json to .vc-meta (not directly served)
    meta_dir = os.path.join(serve_dir, '.vc-meta')
    os.makedirs(meta_dir, exist_ok=True)
    info = {'port': port, 'pid': os.getpid(), 'url': 'http://localhost:{}'.format(port)}
    info_path = os.path.join(meta_dir, 'server-info.json')
    with open(info_path, 'w') as f:
        json.dump(info, f)

    def cleanup():
        try:
            os.remove(info_path)
        except OSError:
            pass

    global _cleanup_fn
    _cleanup_fn = cleanup
    atexit.register(cleanup)

    def sigterm_handler(signum, frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start polling thread
    t = threading.Thread(target=poll_directory, args=(serve_dir, args.owner_pid, server, args.max_lifetime), daemon=True)
    t.start()

    url = info['url']
    print('visual-companion: {}'.format(url))

    server.serve_forever()
    cleanup()


if __name__ == '__main__':
    main()
