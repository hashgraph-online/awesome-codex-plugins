---
name: visual-companion
description: Browser-based visual brainstorming companion for showing mockups, diagrams, and visual options. Use when brainstorm topics involve UI/UX, layout, architecture diagrams, or any content better understood visually.
when-to-use: "user wants visual mockups, UI diagrams, or architecture sketches -- '/visual-companion', 'show me a diagram', 'sketch this UI', 'visualize this', 'open visual companion'"
---

# Visual Companion

A browser-based companion for displaying mockups, wireframes, architecture diagrams, and side-by-side visual comparisons during brainstorm sessions.

## 1. When to Use

Decide **per question** whether to show content in the browser or keep it in the terminal.

**Use the browser for:**
- UI mockups and wireframes
- Architecture diagrams and system maps
- Side-by-side visual comparisons (layout A vs. layout B)
- Spatial relationships (grid layouts, navigation flows, screen transitions)
- Color palettes, typography samples, component galleries

**Use the terminal for:**
- Requirements questions and conceptual choices
- Tradeoff lists and technical decisions
- Clarifying questions about scope or constraints
- API design, data models, algorithm selection

A question about a UI topic is not automatically a visual question. "Should we use tabs or accordion?" is a terminal question. "Here are two tab layouts -- which one?" is a browser question.

## 2. Starting a Session

1. Create a temporary directory for HTML files:
   ```
   mktemp -d /tmp/visual-companion-XXXXXX
   ```

2. Start the visual companion server in the background:
   ```
   python3 <skill-dir>/server.py --dir <temp-dir> &
   ```
   `<skill-dir>` is resolved by the invoking agent to the absolute path of `skills/visual-companion/`.
   Do NOT pass `--owner-pid` -- in the Bash tool context, `$$` resolves to the ephemeral shell PID that dies immediately, causing the server to self-terminate within seconds. The server already has idle timeout (30 min) and max lifetime (8h) for cleanup.

3. **Wait for the server to become ready before announcing its URL.** The `&` in step 2 returns immediately; the Python process still needs to import modules, bind the port, and write `server-info.json`. Announcing the URL before this finishes is the #1 cause of "localhost opened but link unreachable" failures. Probe until both `server-info.json` exists and the port accepts TCP connections:
   ```
   for i in $(seq 1 30); do
     [ -f <temp-dir>/.vc-meta/server-info.json ] && \
       python3 -c "import json,socket; info=json.load(open('<temp-dir>/.vc-meta/server-info.json')); s=socket.socket(); s.settimeout(0.5); s.connect(('127.0.0.1', info['port'])); s.close(); print(info['url'])" 2>/dev/null && break
     sleep 0.2
   done
   ```
   - If the loop prints a URL, the server is ready. Use that URL.
   - If the loop completes with no output, the server failed to launch. Do NOT announce a URL. Inspect `<temp-dir>/.vc-meta/` and the background-process output, fix the underlying issue, and retry step 2.

4. Tell the user (only after step 3 prints a URL):
   > Visual companion running at {url}. Open it in your browser.

5. **Push an initial HTML page immediately.** Do NOT enter the question flow while the browser shows the "waiting" page -- the user sees a broken-looking screen and loses confidence. Write a context-setting HTML fragment to `<temp-dir>` right now, before any `AskUserQuestion` call. The content depends on the session:
   - For brainstorm sessions: a brief "session overview" card showing the topic and what is coming next.
   - For other sessions: a simple title card with the session purpose.
   The server's SSE auto-reload will push this to the browser. Confirm the browser shows your content before proceeding.

## 3. The Loop

For each visual step in the brainstorm:

1. **Write an HTML fragment** to `<temp-dir>` with a semantic filename (e.g., `layout-options.html`). Write body content only -- the server wraps fragments automatically.
2. **Never reuse filenames.** Each screen gets a fresh file. For iterations, append a version suffix: `layout-options-v2.html`. Older files stay on disk so the agent can copy them out at the end of the session.
3. **Browser stays on `/` and auto-shows the newest file.** The server routes the root URL to the most recently modified `.html` file in the temp dir; SSE reload triggers whenever any HTML file changes. The user opens the URL once and never has to navigate manually -- each new file replaces the previous view automatically.

### Pick ONE input mode per step

A step is either **browser-answered** or **terminal-answered**. Do not do both in the same step. Mixing them produces the common failure: agent renders clickable cards, user clicks them, agent is actually blocked on `AskUserQuestion` -- clicks land in `events.jsonl` that the agent never reads, and the user sees their clicks "do nothing."

**Mode A -- Browser-answered (the cards ARE the question):**

Use when the whole point is "pick one of these visual options."

**Pre-write checklist (mandatory before every Mode A HTML write):**
- Every selectable visual element MUST have a `data-choice="<value>"` attribute. The client JS ignores elements without it -- styled cards that look clickable but lack `data-choice` are a silent bug (clicks vanish, user sees nothing happen).
- Do NOT use `AskUserQuestion` in Mode A. The browser click IS the answer.

1. Clear stale selections first so old clicks do not leak into the new question:
   ```
   python3 -c "import urllib.request; req=urllib.request.Request('http://localhost:{port}/events', method='DELETE'); urllib.request.urlopen(req)"
   ```
2. Write HTML with `[data-choice]` elements. The client JS highlights the clicked element and POSTs to `/event`, which appends a line to `.vc-meta/events.jsonl`.
3. Tell the user explicitly: `> Click one of the cards in the browser to select your choice.`
4. Poll `events.jsonl` until a new line arrives (up to ~60s):
   ```
   for i in $(seq 1 300); do
     line=$(tail -n 1 <temp-dir>/.vc-meta/events.jsonl 2>/dev/null)
     [ -n "$line" ] && echo "$line" && break
     sleep 0.2
   done
   ```
5. Parse the JSON line and use the `choice` field as the answer.
6. If the poll times out with no click, fall back to `AskUserQuestion` and treat the step as Mode B from this point on.

**Mode B -- Terminal-answered (browser is visual aid only):**

Use when the browser shows a diagram, mockup, or reference and the real answer is a conceptual choice or free text.

1. Write the HTML WITHOUT `[data-choice]` attributes. Clickable styling with no listener on the agent side is the bug that bit us before -- if you are not going to poll `events.jsonl`, do not ship clickable targets.
2. Ask the question with `AskUserQuestion`. The browser is decoration; the button click is the answer.

**Terminal-only steps (no browser):** No HTML update needed. Optionally push a placeholder page:
   ```html
   <div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:system-ui;color:#666">
     <p>Continuing in terminal...</p>
   </div>
   ```

## 4. HTML Content Guide

Write body content only. The server wraps fragments with DOCTYPE, CSS, and client JS automatically.

A file is treated as a fragment if its first 256 bytes (stripped, case-insensitive) do not start with `<!DOCTYPE` or `<html>`. Full HTML documents are served as-is, with client JS injected before `</body>`.

### Layout Patterns

- **Options grid:** Use `.options` + `.option` for comparing 2-3 approaches visually. Mark the recommended option with `.recommended`.
- **Cards:** Use `.cards` + `.card` for component galleries or feature inventories.
- **Mockup:** Use `.mockup` with `.mock-nav`, `.mock-sidebar`, `.mock-content` for wireframes.
- **Split view:** Use `.split` for before/after or A/B comparisons.
- **Pros/cons:** Use `.pros-cons` for tradeoff visualization.
- **Mock UI:** `.mock-button`, `.mock-input` for wireframe form elements.

### Clickable Options with `data-choice`

Add `data-choice` attributes to elements that users can click to make selections:

```html
<div class="options">
  <div class="option" data-choice="grid">
    <h3>Grid Layout</h3>
    <p>Content arranged in a responsive grid</p>
  </div>
  <div class="option" data-choice="list">
    <h3>List Layout</h3>
    <p>Content in a vertical list</p>
  </div>
</div>
```

When a user clicks a `[data-choice]` element:
- The `.selected` class is added (blue border + light blue background)
- Previous selections within the same parent are deselected
- A JSON event is appended to `.vc-meta/events.jsonl`:
  ```
  {"type":"choice","choice":"grid","text":"Grid Layout Content arranged in a responsive grid","timestamp":"2026-04-09T14:30:00.000Z"}
  ```

### events.jsonl Format

Each line is a JSON object appended by the server. The agent reads this file to see what the user clicked:
```
{"type":"choice","choice":"option-a","text":"Option A","timestamp":"..."}
{"type":"choice","choice":"option-b","text":"Option B","timestamp":"..."}
```

## 5. Cleaning Up

The server self-terminates in two cases:
- **Idle timeout:** No real HTTP activity (page loads, click events, agent updates) for 30 minutes. SSE keepalives and auto-reconnects do NOT reset this timer -- if they did, an open browser tab would keep the server alive forever through any network blip.
- **Max lifetime:** 8 hours since startup, regardless of activity. Override with `--max-lifetime <seconds>`; set to 0 to disable.

Note: `--owner-pid` exists in server.py but is NOT used in the startup template above. In the Bash tool context, `$$` resolves to an ephemeral shell PID that dies immediately, making the owner-PID mechanism unreliable. The idle timeout and max lifetime are sufficient.

To stop manually:
```
kill $(cat <temp-dir>/.vc-meta/server-info.json | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])") 2>/dev/null
```

HTML files remain in the temp directory for reference. Optionally copy key mockups to `docs/brainstorms/` alongside the spec:
```
cp <temp-dir>/final-layout.html docs/brainstorms/YYYY-MM-DD-<name>-mockups/
```
