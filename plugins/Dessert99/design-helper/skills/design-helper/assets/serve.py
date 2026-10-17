import http.server, os, shutil, signal, sys, time
D = os.path.dirname(os.path.abspath(__file__))
IDLE = 120
seen = time.monotonic()

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=D, **k)
    def setup(self):
        super().setup()
        self.connection.settimeout(5)
    def parse_request(self):
        global seen
        ok = super().parse_request()
        if ok: seen = time.monotonic()
        return ok
    def end_headers(self):
        # Never answer a reload from cache: If-Modified-Since has 1s resolution and would
        # serve a stale sheet after two edits within the same second.
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a): pass

def cleanup():
    if not os.path.isdir(D): return
    for f in os.listdir(D):
        if f.endswith('.pid') and f != 'server.pid':
            try:
                with open(os.path.join(D, f)) as pidfile:
                    pid = int(pidfile.read())
                if pid > 1 and pid != os.getpid(): os.kill(pid, signal.SIGTERM)
            except (OSError, ValueError): pass
    # Delete only this session workspace, never its parent or the project.
    shutil.rmtree(D)

# Bind successfully before taking ownership of cleanup. A busy port must not erase D.
server = http.server.HTTPServer(('127.0.0.1', int(sys.argv[1])), H)
server.timeout = 1
try:
    while time.monotonic() - seen < IDLE:
        server.handle_request()
finally:
    server.server_close()
    cleanup()
