# Security

## What bulkhead does on your machine

bulkhead makes no network requests. It does not send telemetry, check for updates or contact any server. The only sockets it opens are local:

- port-guard connects to `127.0.0.1` and `::1` on the port a command is about to use, to see whether something already answers there.
- `bulkhead port` binds and immediately closes a listening socket on `127.0.0.1`, `0.0.0.0`, `::1` and `::` to test whether a port is free.

### Files it reads

| What | Why |
|---|---|
| The hook payload on stdin | The command Claude is about to run, the session ID and the working directory |
| `~/.claude/sessions/*.json` (or `$CLAUDE_CONFIG_DIR/sessions`) | Each session's PID, ID, start time and project directory |
| `~/.claude/bulkhead/config.json` and `<project>/.claude/bulkhead.json` | Settings |
| `package.json` in the project | port-guard follows `npm run dev` to the script it runs |
| Linux: `/proc/<pid>/stat`, `cmdline`, `environ`, `fd`, `cwd`, `/proc/net/tcp`, `/proc/net/tcp6`, `/proc/meminfo`, `/proc/stat` | Processes, their listening ports and memory. From `environ` only `CLAUDE_PID` is used |
| Windows: `Win32_Process`, `Get-NetTCPConnection` and `Win32_OperatingSystem` through PowerShell | The same |
| macOS: `ps`, `lsof` and `vm_stat` output | The same. orphan-reaper also runs `ps -E`, which shows the environment of your own processes, and uses only `CLAUDE_PID` from it |
| `git status --porcelain` and `git rev-parse` | checkout-guard and basics, only for the git commands they check |

It does not read conversation transcripts, source files other than `package.json`, or credentials.

Command lines of other processes are read to tell Claude sessions, tool shells and dev servers apart. They are kept in memory and are not written anywhere, except the command line of a process orphan-reaper stops.

### Files it writes

All under the state directory, `~/.claude/bulkhead` unless `BULKHEAD_STATE_DIR` is set:

| File | Contents |
|---|---|
| `events.jsonl`, `events.jsonl.1` | One line per block: time, guard, rule, session ID, project directory and the blocked command, cut to 200 characters. At most about 2 MB. `BULKHEAD_NO_LOG=1` turns it off |
| `guards.log` | One text line per block and per reclaimed slot |
| `slots/slot-N.json`, `queue/<pid>.json` | bulkhead-slot jobs: label (the command, cut to 80 characters), size, PID, start time |
| `statusline.json` | The cached status line |

Blocked commands can contain secrets that were typed on the command line, such as a token in a `curl` header. They end up in `events.jsonl` and `guards.log` the same way they already are in Claude Code's own transcript. Set `BULKHEAD_NO_LOG=1` if that matters for you.

### Processes it stops

Only orphan-reaper stops processes, at session start, and only by PID: listening dev servers and headless browsers whose Claude session has exited, identified through `CLAUDE_PID` or a Claude tool shell in their parent chain. `node src/orphan-reaper.js --dry-run` shows what it would stop. The guards never stop, write or delete anything; they only allow or block the tool call.

## What it does not protect against

bulkhead is a guard rail against honest mistakes by agents, not a sandbox. It reads command text with regular expressions, so a command hidden in a script file, an alias, a variable or an encoded string is not seen. Do not rely on it to contain a hostile or prompt-injected agent; use Claude Code's permission settings and an OS-level sandbox for that.

## Reporting a vulnerability

If you find a way for bulkhead itself to cause harm, for example a crafted command or config file that makes orphan-reaper stop the wrong process, or that writes outside the state directory, please report it privately through GitHub's "Report a vulnerability" on the repository's Security tab rather than in a public issue. Include the platform, Node version and the exact input.
