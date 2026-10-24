# Adapters

An adapter turns one harness's history into [call records](SCHEMA.md). The built-in ones in `scripts/adapters/` cover Claude Code, Codex, T3 Code, Cursor, Antigravity and the hook log; they are also the worked examples for writing a new one. `antigravity.py` shows how to read a store with no published schema (protobuf blobs in SQLite) and record what the fields were found to mean. Put a new adapter in the audit's work directory and load it with `extract.py --adapter <file>`, so the skill folder stays unchanged.

## Interface

```python
from common import each_source, guess_kind, iso_ms, query_ro, read_jsonl, record   # extract.py puts scripts/ on sys.path

NAME = "my-harness"            # what --only and --list show

def detect(ctx):               # paths holding this harness's history; [] when absent
    return glob.glob(ctx.path(".my-harness", "sessions", "*.jsonl"))

def records(ctx):              # yield record(...) per call with ts >= ctx.since
    return each_source(NAME, detect(ctx), lambda path: _session(ctx, path))
                               # in _session: skip calls where ctx.excluded(cwd); pass _cwd=cwd for claims

def claims(ctx):               # optional, for a frontend that drives other agents
    yield dict(frontend="My Frontend", session="<backend session id>")   # or id=..., or cwd="<substring>"
                               # add agents=("Claude Code",) to limit a cwd claim to the agents it drives
```

`record()` masks secrets, clips text, and raises on a missing field or unknown kind. Map the harness's tool names to kinds explicitly; `guess_kind()` is the fallback for names you have not seen. `iso_ms()` returns `None` for a missing or malformed timestamp: skip that call. `each_source()` skips a file that fails to parse and says so, and `query_ro()` opens SQLite read-only and falls back to a temporary copy when the owning app holds a lock. If an adapter raises anyway, `extract.py` reports it, writes the other adapters' calls, and exits 2.

An adapter is code that runs with the user's permissions. Show a newly written one to the user before its first `--adapter` run.

## Finding the history

1. **Prefer a documented export.** Some harnesses have a CLI or API that exports sessions; it survives format changes better than internal files.
2. **Otherwise make the harness point at its own files.** Ask the user to run one call with a distinctive marker in that harness (you cannot drive it from here), for example the shell command `echo latency-marker-7319`. Then list what changed in the last few minutes and search it for the marker:

   ```sh
   find ~ -newermt '-5 minutes' -type f \( -name '*.json*' -o -name '*.db' -o -name '*.sqlite*' -o -name '*.log' \) \
     -not -path '*/node_modules/*' 2>/dev/null | xargs grep -l 'latency-marker-7319' 2>/dev/null
   ```

   SQLite files need a query, not grep: open them read-only (`sqlite3 'file:<path>?mode=ro'`) and search the text columns. Usual roots: `~/.<name>`, `~/.config/<name>`, `~/.local/share/<name>`, `~/Library/Application Support/<Name>` on macOS, `%APPDATA%` on Windows.
3. **Read the marker's neighbourhood.** Find where the call starts and where its result lands, what timestamps each carries, and how a call id links them. That decides the record's `timing`.

Harness history is the user's chat history. Open it read-only (`query_ro()` copies a locked database to a temporary file first), and never write, move or delete anything under a harness's directories.

## Timing rules

These come from bugs found in real logs; each one silently skews the totals.

- **Parallel calls.** When one assistant message issues several calls, most start only after the whole message has streamed. Time such calls from the message's last block; a call whose result arrives before the message ends started early, so keep its own start.
- **Copied history.** Resumed and forked sessions copy earlier calls into a new file. Keep the harness's call id in `id`; `extract.py` keeps one record per (`agent`, `id`), preferring the copy with the best `timing`.
- **Frontends.** A frontend that drives another agent leaves the same call in the agent's own log. Emit it once, from the agent's adapter, and let the frontend's `claims()` relabel it.
- **The audit's own runs.** Benchmark sessions land in the same history. Run them under a unique path and pass it to `--exclude-cwd`.
- **Background calls** return at once while the work runs elsewhere; set `background`.
- **Approvals.** When the user answered a prompt, set `human_wait`; that time is the user's, not the tool's. An automatic reviewer that runs as its own session becomes one `review` call per reviewer turn.
- **Clocks.** Check the unit (seconds or milliseconds) and the zone: a timestamp without an offset is local time.

## Done when

- `validate_calls.py calls.jsonl --harness "<harness>"` exits 0, and each WARN it prints is fixed or explained in the report.
- Three spot checks it prints match the raw log: open each `src`, find the issuing line, and confirm the duration to within a second.
- The call count of one session the user can see in the harness's UI matches the adapter's count for that session.

## Capturing with hooks

When a harness's history has no per-call timestamps, start recording its calls live instead. Most harnesses can run a command before and after each tool call; wire both to `scripts/hook_capture.py`, which writes `~/.cache/agent-tool-call-latency/hooks.jsonl` (or `$AGENT_LATENCY_HOOK_LOG`), and the `hooklog` adapter pairs the lines. For Claude Code the wiring in `settings.json` is:

```json
{"hooks": {
  "PreToolUse":  [{"matcher": "*", "hooks": [{"type": "command", "command": "python3 <skill>/scripts/hook_capture.py pre --agent 'Claude Code' --harness 'Claude Code CLI'"}]}],
  "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "python3 <skill>/scripts/hook_capture.py post --agent 'Claude Code' --harness 'Claude Code CLI'"}]}]
}}
```

For other harnesses, read their hook documentation for the event names and the payload; the script accepts the common spellings of the call id, tool name, session id and input. Three things to settle with the user before wiring it:

- It is a config change: back up the file first, record it in `changes.md` with the date the capture window ends, and remove the hooks then. A harness that also has an adapter records each call twice; the hook copy shares its call id, so `extract.py` keeps one, with the hook's exact timing. Pass `--harness` with the label the adapter uses, so both copies land in the same row.
- Each hook adds its own start-up time (tens of milliseconds for Python) to every call, so fast-operation comparisons from a hook capture overstate overhead by that much.
- Where the harness fires the hooks relative to its approval step decides whether approval time is inside the window. Check it with one call that needs approval.

A harness that exports OpenTelemetry spans for tool calls offers the same data without hooks; an adapter can read the exported spans.
