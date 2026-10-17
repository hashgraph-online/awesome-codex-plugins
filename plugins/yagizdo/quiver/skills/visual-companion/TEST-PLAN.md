# Test Plan -- visual-companion

**Trigger:** Used by `/brainstorm` Step 1.5 when the user opts into the visual companion. Not directly slash-invoked.

**Setup:**
- Python 3 available on PATH.
- A brainstorm session in progress where the user has accepted the "Open visual companion" prompt.

**Expected behavior:**
1. `/brainstorm` reads this skill, starts the companion server (`server.py`) in a temp directory, and points the user to the local URL.
2. For each visual question, the orchestrator writes HTML to the companion temp dir; for non-visual questions, it stays in the terminal.
3. On session end (or manual cleanup), the server process is stopped using the PID recorded in `<temp-dir>/.vc-meta/server-info.json`.
4. Any mockups the user wants to keep are copied alongside the spec in `docs/brainstorms/`.

**Verification checklist:**
- [ ] `/brainstorm` only offers the companion when the topic is visual (UI/UX, layout, architecture diagrams).
- [ ] Companion server boots from `server.py`, prints a local URL, and serves written HTML files.
- [ ] PID is captured in `<temp-dir>/.vc-meta/server-info.json` and used for clean shutdown.
- [ ] Refusal path (user says "No, continue with text") leaves the companion stopped and falls back to terminal-only flow.

**Known gotchas:**
- This is the only Quiver skill that ships a runtime executable (`server.py`); never assume skill dirs are prompt-only.
- Stopping the server depends on the PID file; if the temp dir is deleted before the kill, manual `pkill -f server.py` is needed.
- Root request (`/` or `/index.html`) routes to the most recently modified HTML file in the serve dir; if none exists, it returns a built-in "waiting" landing page that subscribes to SSE. Both responses inject the SSE client, so the browser auto-reloads when the agent writes or updates any HTML. Specific paths (e.g. `/foo.html`) still 404 when missing -- do not rely on root routing to mask broken links.
- The 8h hard ceiling and SSE-immune idle timer exist because a server was once found alive 29 days after start. Browser SSE auto-reconnects (WiFi switch / sleep / VPN) used to reset the idle timer indefinitely. Do not "simplify" `log_request` back to unconditional reset; do not remove `--max-lifetime`.
