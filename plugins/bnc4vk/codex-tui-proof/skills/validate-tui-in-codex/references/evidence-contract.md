# Codex TUI Proof evidence contract

Use this reference when automating the harness or reporting validation evidence.

## Ready signal

The runner prints one machine-readable line:

```text
TUI_PROOF_READY {"url":"http://127.0.0.1:<port>","host":"127.0.0.1","port":<port>,"command":"...","cwd":"...","cols":100,"rows":30,"autostart":true}
```

Use the returned URL verbatim.

## HTTP endpoints

- `GET /api/health`: readiness, harness version, and current status.
- `GET /api/evidence`: concise validation state without the terminal transcript.
- `GET /api/state`: complete live state plus the retained ANSI transcript.

`/api/evidence` includes:

- `contractVersion`
- `harnessVersion`
- `status`, `sessionId`, and `pid`
- `command` and `cwd`
- `cols` and `rows`
- start/stop/exit metadata
- `recordingPath`
- input/output byte counters
- current error, if any

## Stable browser selectors

- `command`: configured command input
- `cwd`: working-directory input
- `cols`, `rows`: geometry inputs
- `restart`, `stop`: lifecycle buttons
- `status`: session status
- `session-label`: active command/session identifier
- `dimensions`: authoritative PTY size
- `terminal`: xterm container
- `metrics`: live input/output byte counts
- `recording`: JSONL recording label

The xterm accessibility layer exposes the active keyboard target as `textbox "Terminal input"`.

## WebSocket messages

The WebSocket accepts only an exact same-origin connection from the allocated `127.0.0.1` page.

Client to server:

- `{ "type": "input", "data": "..." }`
- `{ "type": "resize", "cols": 100, "rows": 30 }`
- `{ "type": "start" | "restart", "command": "...", "cwd": "...", "cols": 100, "rows": 30 }`
- `{ "type": "stop" }`

Server to client:

- `state`, `output`, `metrics`, `reset`, and `error`

## Recording

Each session writes JSONL under `runtime/recordings/`. Records contain an ISO timestamp, `direction` (`meta`, `input`, or `output`), data, and lifecycle/resize fields where applicable.

Input records contain typed characters. Never enter secrets during a proof session.

## Minimum acceptance criteria

1. Browser status is `running` for the target command and cwd.
2. Browser dimensions equal the requested PTY geometry.
3. At least one requested keyboard or lifecycle interaction is observed in resulting TUI state.
4. `/api/evidence` agrees with the browser state.
5. A screenshot comes from the controlled in-app-browser tab.
6. No Computer Use or desktop terminal was invoked.
