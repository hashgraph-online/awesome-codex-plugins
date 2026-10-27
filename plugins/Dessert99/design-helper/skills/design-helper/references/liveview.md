# Live view

Every ready revision is brought back to the user's browser, even if they switched
away or closed it. **Never end a turn with "새로고침하세요."** Editing, reloading,
verifying, and foregrounding the comparison are mine.

`file://` can't do this — a page there can't check whether its own file changed. So the
sheet is served, not opened as a file.

## The workspace

Everything this skill makes lives in **one directory outside the project**, created once
per session and deleted at the end:

    WS=$(mktemp -d "${TMPDIR:-/tmp}/design-helper.XXXXXX")   # or a new folder in the session's scratch dir

`$WS` is the whole workspace, with nothing above it to clean up. Teardown deletes
`$WS` itself and nothing else.

The sheet, the server, the built CSS, the memo, screenshots, any entry file a build
tool needs, and the pid files below — all in `$WS`. **Nothing is ever written inside
the project** except the selected changes applied after each choice. If a tool seems
to need a file in the project, it doesn't — `references/stylesystems.md` has the flag or
entry file that keeps it out.

Every background process gets a pid file so teardown can find it:

    ... >/dev/null 2>&1 & echo $! > "$WS/<name>.pid"

## The kit

The fixed parts are files in `assets/`, next to `worker.md`. Copy them into `$WS` once
per workspace, right after creating it, and never retype them:

    A=<directory of worker.md>/assets
    cp "$A/serve.py" "$A/sheet.html" "$A/check.cjs" "$WS/"

- `serve.py`: the server below
- `sheet.html`: the empty sheet, with the sheet style, the table of contents and the
  reloader already in it (`references/sheet.md`)
- `check.cjs`: verification steps 2 and 3 of `worker.md` in one run

## Serve it

`$WS/serve.py` is a static file server for `$WS` that sends `Cache-Control: no-store`
and reaps itself (below). Once per session, in the background:

    python3 "$WS/serve.py" 8765 >"$WS/server.log" 2>&1 &
    echo $! > "$WS/server.pid"

Port busy → walk up (8766, 8767...). Never kill whatever is already there. When the
first sheet is ready (`After every edit` below), open the URL, not the path:

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
- Workspace deleted by timeout: the user closed the page, so they no longer need what
  was on it. Create a fresh workspace and draw **only what the new request asks for** —
  never rebuild the old ladders. If the request points back at an old specimen
  (`B랑 새 거 비교`), draw just that specimen beside the new ones. Rewrite `memo.md` from
  the settled values in the conversation so the new ladder still sits on top of them.
  Letters and turn numbers continue from the chat (`D`, `요청 3`), so a letter the user
  already said never means two things. Say it in one line, e.g.
  `이전 시안 페이지는 닫혀서 정리됐습니다. 이번 요청만 새 페이지에 그립니다.` — never
  offer to restore it, and never claim its history was recovered.

Don't add a keepalive that defeats this cleanup. A wrapper that swallows SIGTERM can
leave a watcher running, so manage processes directly and check for survivors at
teardown. A hard crash cannot run cleanup.

## The reloader

The last script in `assets/sheet.html`, at the end of `<body>`, so the DOM is parsed when
it runs. Keep it as copied. Every second it compares the sheet's `Last-Modified` and
length with the copy the page was loaded from, reloads when they differ, and lands
where the user needs to be: on the newest ladder if one was appended, otherwise
exactly where they were reading. The browser's own scroll restoration is turned off so
it can't override that landing.

One ladder per `<section>`, appended at the end — the count compares them and the last
one is where an append lands. Break either and the page reloads to the top
mid-comparison. Turn dividers and the table of contents (`references/sheet.md`) are a
`<div>` and a `<nav>`, so they never change the count.

## After every edit

Show first, then verify. The user's tab reloads by itself on every write, so a fix made
during verification reaches them without another step, and they are not left waiting on
an empty screen while it runs.

1. Check names (verification step 1 in `worker.md`). It takes a second and catches the
   failure that shows nothing at all, so it runs before anyone sees the sheet
2. Present it as described below: the first sheet opens, a revision comes forward.
   Do this before step 3, with every caption and the recommendation already written
3. Verify: computed style and screenshot with `check.cjs`, per `worker.md`. Fix what it
   finds in the sheet; the open tab picks the fix up within a second and keeps its
   scroll position. Fixes are not presented again
4. Then report, saying what to look at: `맨 아래 그림자 사다리입니다`. The report comes
   after verification, so it describes the checked sheet

The screenshot comes from Playwright's own page at the same URL, so it and the user's
browser are looking at the same bytes.

Two cases verify before presenting instead: a sheet with controls
(`references/controls.md`), and a sheet on `file://` (below), which can't reload itself.

An optional interactive sheet keeps its state across these reloads as described in
`references/controls.md`.

## Present every revision

Bring the user to the first sheet and to every ready revision after feedback, including
an edit inside an existing section. A revision is ready once its content is written and
its names are checked (`After every edit`). Do not steal focus for intermediate writes,
fixes made during verification or a turn that produces nothing new to compare.

1. Check that the session's server (and CSS watcher, if any) is up and the sheet URL
   answers. Workspace gone → a fresh sheet as above; server stopped → restart it.
   Port taken → pick a free one; never kill what is already there.
2. With the browser or desktop controls you have, find the user's comparison tab by
   its URL, select it and bring its window forward. **Never open a second tab for the
   same sheet**: open the URL only after confirming no such tab exists, and if the
   port changed, navigate the existing tab instead. Use those controls, not a
   page-level `window.focus()`, and never a URL opener as a focus fallback.
3. Make sure the latest content is loaded (reload if polling was suspended) and scroll
   to the section being presented.
4. Verify, then report. A screenshot from your own headless page or a successful HEAD request
   does not show that the user's tab came forward. If you can't find or activate the
   tab, say so in one line and give the URL; don't claim it came forward.

## No python3

Open the sheet on `file://` and say once that automatic reload and the two-minute
cleanup are unavailable. Without reload, verify each revision before presenting it. For each ready revision, reload through browser controls or
reopen the file URL; if neither is available, ask for a manual refresh. Avoid background
watchers, and clean up on explicit completion. Do not build a replacement server.

## At the end

One command, when the user says it's done. It stops everything this skill started and
deletes everything it made:

    for f in "$WS"/*.pid; do kill "$(cat "$f")" 2>/dev/null; done; rm -rf "$WS"

Then check `git status` in the project for stray comparison files. Remove only those
temporary artifacts, preserving the applied changes and all existing user work.
