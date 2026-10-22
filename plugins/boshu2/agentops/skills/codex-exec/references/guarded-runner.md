# Guarded runner internals

Maintainer detail for `codex_exec_guarded` in `scripts/lib/codex-exec.sh`, the
one-shot runner that exists only in an AgentOps source checkout. The skill body
carries the rules, the fallback and the exit codes; this file carries the
mechanism.

## Inputs

- `CODEX_EXEC_TIMEOUT`: positive finite seconds. No default.
- `CODEX_EXEC_DEADLINE_EPOCH`: absolute Unix timestamp. Without a timeout it
  supplies the remaining time; with both, the earlier bound wins. The bound
  includes capability probes and prompt preparation. Pass the same absolute
  value to every call in its scope; a new invocation cannot renew it. Missing
  both bounds, or an empty, zero, negative or malformed value, prevents launch.
  An expired deadline times out before dispatch. There is no fixed ten-minute
  default.
- `CODEX_EXEC_MAX_OUTPUT_BYTES`: positive finite integer, default 10485760
  (10 MiB). It caps captured stdout and stderr combined.
- `CODEX_EXEC_OUT_FILE`, `CODEX_EXEC_STDERR_FILE`: capture sinks, which must be
  regular files or `/dev/null`. Without a separate stderr file, stderr merges
  into the output file. Reviewer workspace writes, including the file named by
  `-o`, are outside the capture cap.
- `CODEX_EXEC_SANDBOX` (default `read-only`), `CODEX_EXEC_DIR` (`-C`),
  `CODEX_EXEC_PROMPT_FILE` or `CODEX_EXEC_PROMPT_ARG` (otherwise stdin).
- `CODEX_EXEC_EXPECT_OUTPUT=0`: for a caller that keeps only the exit status. A
  clean exit with empty output is then success instead of a stall.

The library also serves other caller-selected reviewer adapters through
`REVIEWER` (`agy`, `local-mlx`; default `codex`). It never switches adapters on
its own. File-prompt copies and the non-Codex adapters' stdin preparation use
the same byte cap.

## Host requirements

The host needs `/usr/bin/perl` with its core POSIX, IO::Select, Fcntl and
Time::HiRes modules, a monotonic clock, process-group signalling, and a
resolved `timeout`/`gtimeout` that supports `--foreground`. A missing capability
fails closed with exit 2.

## Process supervision

The runner establishes one owned process group before launching the reviewer.
On expiry, cancellation, excess output or direct-parent exit it sends TERM, then
KILL after 200 ms. Pipe draining is bounded by a further short cleanup window
rather than waiting for descendants to close inherited pipes. This covers
ordinary descendants left by a successful parent and TERM-resistant children.
It does not promise cleanup of processes that deliberately escape the owned
group or session.

Group members remaining after direct-parent exit are reported as `rep-survivor`
(exit 122): the run stays degraded even when cleanup then succeeds. After the
cleanup window the runner checks whether the owned group still exists.
Remaining membership, including zombies it cannot reap, is reported as
`CLEANUP-UNVERIFIED` (exit 2), never as successful cleanup.

## External sandbox wrapper

`CODEX_EXEC_WRAP` is Codex-only. The sealed launch order is wrapper, then the
resolved timeout, then the reviewer. Codex's own sandbox is bypassed only when
the external wrapper supplies the sandbox. The capture and cleanup supervisor
runs outside that sealed launch. No process-wide file-size limit restricts
reviewer work products.

## Partial evidence

On timeout, cancellation or excess output, partial capture stays in the
caller-provided files; an adapter-owned output sink is streamed before removal.
Failed prompt preparation reports its preserved partial input path. The caller
decides whether to launch another invocation.
