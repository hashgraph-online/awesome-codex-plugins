# Live view

Every ready revision is brought back to the user's browser, even if they switched
away or closed it. **Never end a turn with "새로고침하세요."** Editing, reloading,
verifying, and foregrounding the comparison are mine.

`file://` can't do this — a page there can't check whether its own file changed. So the
sheet is served, not opened as a file.

## The workspace

Everything this skill makes lives in **one directory outside the project**, created once
per session and deleted at the end:

    WS=$(mktemp -d)/design-helper    # or under the session's own scratch dir, if there is one
    mkdir -p "$WS"

The sheet, the server, the built CSS, the memo, screenshots, any entry file a build
tool needs, and the pid files below — all in `$WS`. **Nothing is ever written inside
the project** except the selected changes applied after each choice. If a tool seems
to need a file in the project, it doesn't — `references/stylesystems.md` has the flag or
entry file that keeps it out.

Every background process gets a pid file so teardown can find it:

    ... >/dev/null 2>&1 & echo $! > "$WS/<name>.pid"

## Serve it

```python
# $WS/serve.py
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

```

Once per session, in the background:

    python3 "$WS/serve.py" 8765 >"$WS/server.log" 2>&1 &
    echo $! > "$WS/server.pid"

Port busy → walk up (8766, 8767...). Never kill whatever is already there. Then open the
URL, not the path:

    open http://localhost:8765/sheet.html

It binds `127.0.0.1`, not `0.0.0.0` — the sheet is on the user's machine and has no
business on the network.

## It reaps itself

After **120 seconds without a valid HTTP request**, the server sends SIGTERM to
registered helpers, deletes this session's entire `$WS`, and exits. It never removes
the project or the workspace's parent. Cleanup errors stay visible in the server log.

The reloader's HEAD requests keep the session alive while an open tab polls. Closing
every comparison tab — or a browser suspending the tab — starts the two-minute clock.

Before editing or presenting, check both the workspace and server:

- Workspace present, server alive: reuse the session; requests reset the idle timer.
- Workspace present, server unexpectedly stopped: restart from that workspace.
- Workspace deleted by timeout: create a fresh workspace and regenerate the comparison
  from project code and available conversation context. Explain that the old temporary
  sheet expired. Do not claim its exact history or optional browser state was recovered.

Don't add a keepalive that defeats this cleanup. A wrapper that swallows SIGTERM can
leave a watcher running, so manage processes directly and check for survivors at
teardown. A hard crash cannot run cleanup.

## The reloader

At the end of `<body>`, so the DOM is parsed when it runs. It polls the sheet's
`Last-Modified`, reloads when it moves, and lands where the user needs to be — on the
newest ladder if one was appended, otherwise exactly where they were reading.

```html
<script>
(() => {
  const S = sessionStorage;
  const n = document.querySelectorAll('section').length;
  const prev = +S.getItem('n') || 0, y = +S.getItem('y') || 0;
  S.setItem('n', n);

  let touched = false;
  const place = () => {
    if (touched) return;
    if (n > prev) document.querySelectorAll('section')[n - 1]?.scrollIntoView();
    else scrollTo(0, y);
  };
  addEventListener('load', place);
  document.fonts?.ready.then(place);
  addEventListener('scroll', () => { touched = true; S.setItem('y', scrollY); }, { passive: true });

  let seen = null;
  setInterval(async () => {
    const r = await fetch(location.href, { method: 'HEAD', cache: 'no-store' });
    const t = r.headers.get('last-modified');
    if (seen && t !== seen) location.reload();
    seen = t;
  }, 1000);
})();
</script>
```

One ladder per `<section>`, appended at the end — the count compares them and the last
one is where an append lands. Break either and the page reloads to the top
mid-comparison. Turn dividers and the table of contents (`references/sheet.md`) are a
`<div>` and a `<nav>`, so they never change the count.

## After every edit

1. Wait past one poll (~1.5s) so the browser has picked it up
2. Verify — computed style and screenshot, per SKILL.md
3. When the revision is ready to present, foreground or reopen the user's comparison
   as described below and show the changed section
4. Then report, saying what to look at: `맨 아래 그림자 사다리입니다`

The screenshot comes from Playwright's own page at the same URL, so it and the user's
browser are looking at the same bytes.

**For optional interactive sheets, a reload wipes unsaved client state.** Scrub windows and context toggles
live in `sessionStorage` under `ctl:<section id>` and `ctx`, restored on
load by the engine in `references/controls.md`. Anything interactive added later goes
through the same two helpers or it dies on my next edit — which is the worst possible
moment, because the user was mid-comparison.

## Present every revision

This applies to the first sheet and each ready revision after user feedback, including
changes within an existing section. Do not steal focus during intermediate writes,
verification, background polling, or a conversation that produces no new comparison.

1. Ensure the same session's server and required CSS build are healthy, and the current
   sheet URL responds. If the workspace expired, regenerate it as described above;
   if only the server stopped, restart it and recover a watcher if needed. If the port is occupied,
   choose a free port and use the updated URL without killing unrelated processes.
2. With the available browser/desktop controls, locate the user's comparison tab by
   session URL or saved tab identity. Select it and activate its containing window/app.
   Open the sheet only after confirming that its tab is absent. If its tab exists,
   reuse it, including when its window is minimized or another tab is selected.
   A changed server port does not justify a duplicate: navigate the existing session
   tab to the updated URL. Track its tab/window identity for later revisions.
3. Ensure the latest content has loaded; explicitly reload if background polling was
   suspended. Scroll to the section being presented, whether it is new or edited in
   place. Keep optional interactive state when reusing the tab; a reopened tab may
   reset sessionStorage, so inspect what is actually displayed.
4. Verify the visible result when the available tools support it, then report. A
   screenshot from a separate verification tab or successful HEAD request does not
   establish that the user's browser was activated.

Use browser activation controls, not a page-level `window.focus()`. **Never invoke a URL
opener as a focus fallback** — it may create a duplicate tab. If existing-tab detection
or activation is unavailable, briefly explain the limitation and give the current URL;
do not claim focus changed without evidence.

## No python3

Open the sheet on `file://` and say once that automatic reload and the two-minute
cleanup are unavailable. For each ready revision, reload through browser controls or
reopen the file URL; if neither is available, ask for a manual refresh. Avoid background
watchers, and clean up on explicit completion. Do not build a replacement server.

## At the end

One command, when the user says it's done. It stops everything this skill started and
deletes everything it made:

    for f in "$WS"/*.pid; do kill "$(cat "$f")" 2>/dev/null; done; rm -rf "$WS"

Then check `git status` in the project for stray comparison files. Remove only those
temporary artifacts, preserving the applied changes and all existing user work.
