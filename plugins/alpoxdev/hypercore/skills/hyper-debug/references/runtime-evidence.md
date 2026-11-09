# Runtime Evidence

## Contents

1. [How to use](#1-how-to-use)
2. [Node.js](#2-nodejs)
3. [Python](#3-python)
4. [Rust](#4-rust)
5. [Go](#5-go)
6. [Native binaries](#6-native-binaries)
7. [Silent-failure table](#7-silent-failure-table)
8. [Sources](#sources)

## 1. How To Use

A probe answers one hypothesis. Pick the probe that would read differently under two competing hypotheses; a probe that reads the same either way is not evidence.

- Name the capability first, then the command. A runtime's flag set changes between versions; check `--help` when the version is not the one you assumed.
- Prefer a probe that needs no source edit. Edit the source only when no external probe can reach the value.
- Record the command and the output verbatim. A probe whose output is not quoted cannot be re-checked by the next engineer.
- These probes observe values, they do not fix anything. Nothing in this file opens a debugger, attaches to a running process, or instruments a binary.

## 2. Node.js

| Question | Probe |
|---|---|
| Which runtime and version actually runs? | `node -v`, `which -a node`, `npm ls --depth=0`, and for TypeScript `npx tsx --version` |
| Does the module I read match the module that loads? | `node -e "console.log(require.resolve('<module>'))"`; for ESM, `node --input-type=module -e "console.log(import.meta.resolve('<module>'))"` |
| Is the environment variable set at the point of use? | `node -e "console.log(JSON.stringify({KEY: process.env.KEY}))"` with the same launcher |
| Is a rejection escaping unhandled? | Add `process.on('unhandledRejection', e => { console.error(e); process.exitCode = 1 })` in a scratch entry, or run with `--trace-uncaught` |
| Which async operation is still pending? | `node --report-on-signal` plus a `SIGUSR2` signal, then read the report's `libuv` handles; or check `process._getActiveHandles()` in a scratch entry |
| Does the stack point at source or at transpiled output? | Run with `--enable-source-maps` and compare the two traces |
| Does the exit code match the failure? | `node script.js; echo "exit=$?"` — an uncaught rejection historically exited 0 on older versions |
| Is the server listening where the client calls? | `lsof -nP -iTCP -sTCP:LISTEN` and compare with the configured port |

`--trace-warnings` shows a warning's origin. `--trace-sync-io` finds synchronous I/O in a timing hypothesis.

## 3. Python

| Question | Probe |
|---|---|
| Which interpreter runs? | `which -a python3`, `python3 -VV`, `python3 -c "import sys; print(sys.executable, sys.prefix)"` |
| Which module file was imported? | `python3 -c "import m; print(m.__file__)"`; for a package with a `.pth` or a shadowing local file, print `sys.path` too |
| Is the installed version the one declared? | `python3 -m pip show <pkg>`, or `importlib.metadata.version('<pkg>')` |
| Is an exception swallowed? | Run with `-X dev`; read `sys.excepthook`; search for bare `except`, `except Exception: pass`, and `contextlib.suppress` |
| Did an asyncio task fail silently? | Add `loop.set_exception_handler` in a scratch entry, or check `asyncio.all_tasks()` for pending tasks at exit |
| Is a warning the cause? | `python3 -W error::DeprecationWarning` turns the class into a failure to make it visible |
| Is the value at the call the one expected? | Call the function directly with the same inputs from a scratch script in a temp directory and print the value; a direct call is narrower than starting the whole server |
| Which files does the process open? | `python3 -X importtime` for import order; `strace -f -e trace=openat` on Linux, `dtruss` on macOS when permitted |

Prefer `python3 -X dev` as the default run for a reproduction: it surfaces resource warnings and unraisable exceptions that a normal run hides.

## 4. Rust

| Question | Probe |
|---|---|
| Which build runs? | `cargo build --message-format=json`, then pick the `compiler-artifact` record's `executable` field, and compare with `cargo metadata` targets |
| Was the binary built in debug or release? | `cargo run -- --version` where available; check `target/debug` versus `target/release`; `file <binary>` for `with debug_info` |
| Where exactly did it panic? | `RUST_BACKTRACE=1 cargo run`; `RUST_BACKTRACE=full` when the short trace is inlined |
| Is an error being discarded? | Search for `.unwrap_or_default()`, `let _ = `, `.ok()`, `if let Ok(_)`, and `Err(_) => {}` |
| Is the panic being caught and hidden? | Search for `catch_unwind` and `panic::set_hook`; a hook that logs to a sink the run never reads is a silent failure |
| Which feature flags are active? | `cargo tree -e features -i <crate>` and `cargo metadata --format-version 1` |
| Is it a lock or a deadlock? | `RUST_BACKTRACE=1` plus a hang reproduction; `Mutex::try_lock` in a scratch copy converts the stall into an error |
| Is the async runtime dropping the future? | Check `tokio::spawn` handles that are never awaited, and `select!` branches that cancel work |

`RUST_LOG` only helps when the crate uses a logging facade; confirm the subscriber is initialized before trusting an empty log.

## 5. Go

| Question | Probe |
|---|---|
| Which binary and module version runs? | `go version -m <binary>`; `go list -m all` |
| Where did the panic start? | The panic prints a goroutine dump; read the first `created by` line and the goroutine that holds the lock |
| Is an error ignored? | `go vet ./...` plus a search for `_ = `, `if err != nil { }`, and `recover()` without a re-panic |
| Is a goroutine leaking? | `go tool pprof` against a `net/http/pprof` endpoint, or `runtime.NumGoroutine()` in a scratch test |
| Is a channel blocking silently? | Reproduce under `-race` and a bounded timeout; a full send or an unread receive shows as a stuck goroutine |
| Is the race real? | `go test -race -count=10 ./...` — the count makes the race more likely without changing the test |
| Is the build the one running? | `go build -o /tmp/<name> .` and run that path explicitly; a `go run` cache or a stale install is a classic mismatch |
| Which context deadline fired? | Log `ctx.Err()` at the call site; `context.Canceled` and `context.DeadlineExceeded` mean different causes |

## 6. Native Binaries

| Question | Probe |
|---|---|
| What is the binary? | `file <path>`, `uname -m`, `otool -L` (macOS) or `ldd` (Linux) for the loaded libraries |
| Which build is deployed? | Compare a build-id or hash: `shasum -a 256 <binary>` against the artifact store |
| How did it end? | `echo "exit=$?"`; `128 + signal` means a signal, not a normal exit; `dmesg` for an OOM kill on Linux |
| Was a syscall refused? | `strace -f -e trace=%file,%network -o /tmp/trace <cmd>` on Linux; `dtruss -f <cmd>` on macOS when permitted |
| Is a return code ignored? | Search the call sites for a discarded `int` return; check `-Wunused-result` and `warn_unused_result` |
| Is it a library version mismatch? | `otool -L` / `ldd` against the version the build expected; `DYLD_PRINT_LIBRARIES=1` (macOS) or `LD_DEBUG=libs` (Linux) |
| Does it fail only under load? | Run with a bounded fan-out and watch `ulimit -n`, thread count, and RSS over the reproduction window |

A core dump or a signal number is an observation, not a cause. Feed it back into the hypothesis set.

## 7. Silent-Failure Table

The symptom is a success response with no effect. Check every row that matches the shape of the code under test.

| Pattern | What to read | Why it looks like success |
|---|---|---|
| HTTP 2xx with an empty or default body | The body, its length, and the content type at the boundary | The status line is what a client checks first |
| `ok: true` with a failing sub-field | The whole payload, not the top-level flag | Aggregated statuses hide per-item errors |
| A promise not awaited | The call site, and whether the caller returns the promise | The work is scheduled, so nothing throws at the call |
| `try { } catch { }` or `except: pass` | The catch block and what it swallows | The failure never reaches a caller |
| `let _ = result` / `.ok()` / `.unwrap_or_default()` | The error path, and the default it substitutes | A value is returned, so the code proceeds |
| A recovered panic or a `recover()` that logs nowhere | The recovery handler and its sink | The process keeps running |
| `if err != nil { return }` with no error propagated | The caller's error handling | The caller sees a zero value, not an error |
| Write reported as applied, but a read returns the old value | A read after the write, in the same session | The write call returned without error |
| A job marked complete before its side effect | The completion signal and the side-effect check | The state machine moved forward |
| A cache hit returning a stale entry | The cache key, its TTL, and the invalidation path | A value came back quickly |
| Exit code 0 with a traceback on stderr | Both streams and the exit code together | Harnesses often read only the exit code |
| A test that passes because its assertion never ran | The assertion count, and a deliberate failure to check it can fail | A green run looks like proof |
| A timeout raised until the failure stops appearing | The configured timeout and the actual duration | The run passes more slowly |
| A retry that hides a first-attempt error | The attempt count and the first error | The final result is green |

A silent failure found outside the reported symptom is a journal follow-up, not a fix in this run. Record `path:line`, the pattern, a one-line fix sketch, and the risk of leaving it.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| Silent-failure catalog (2xx with empty body, un-awaited promise, swallowed exception, recovered panic, ignored return value, stale read after write, premature completion, stale cache, exit 0 with stderr) | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/08-qa.md` (mechanism reference, re-authored) |
| Node and Python probe shapes, and the `--enable-source-maps` and `-X dev` signals | `dbc-hbin/omp-ulw@74df40f debugging/references/runtimes/node.md`, `debugging/references/runtimes/python.md` (mechanism reference, re-authored) |
| `RUST_BACKTRACE`, `go test -race`, `go vet`, `strace`, `otool -L`, `ldd` as observation tools | runtime documentation and command help as installed, checked 2026-11-09 |

### Evidence grade

`LOCAL` for the table structure and probe selection; `PRIMARY` for the commands, which are the runtimes' own documented interfaces. Flags that change between versions are described by their purpose, so a reader confirms the exact spelling with `--help` on the installed version. The silent-failure rows are re-authored mechanism references from a repository with no license; no text or code is copied.
