---
name: bulkhead
description: How to work on a machine where other coding agent sessions (Claude Code, Copilot CLI, Codex and others) and their subagents run at the same time. Use before starting a dev server, stopping or killing a process, freeing a port, running a build, test suite, browser run or other heavy command, switching branches, stashing, staging or committing, deleting a folder or worktree, measuring disk usage, or waiting on a long job.
---

# Working on a shared machine

Other agent sessions (Claude Code, Copilot CLI, Codex and others), their subagents and the user run on this machine too. Their dev servers, test runs and git trees look like yours from a shell. The bulkhead hooks block the most damaging mistakes; this is how to avoid hitting them at all.

## Running the bulkhead commands

The commands below (`bulkhead`, `bulkhead-slot`) are on `PATH` with the Claude Code plugin or after `npm install -g claude-bulkhead`. A Copilot CLI plugin install does not put them on `PATH`. If `bulkhead` is not found, run the same command with `node` from the plugin folder, which is two levels above this skill's folder (`<plugin>/skills/bulkhead/`):

```
node "<plugin>/bin/bulkhead" status
node "<plugin>/bin/bulkhead-slot" run --gb=4 -- npm test
```

Copilot CLI keeps plugins under `~/.copilot/installed-plugins/<marketplace>/bulkhead` (`$COPILOT_HOME` instead of `~/.copilot` when it is set). Do not install anything to get the command; the hooks work without it.

## Look before you act

Run `bulkhead status` before you start a server, stop a process or start heavy work. It lists every agent session with its project, memory, listening ports, the heavy jobs queued in bulkhead-slot, and free RAM.

## Dev servers and ports

- A port listed under another session belongs to that session. Do not stop its server and do not start yours on the same port.
- Get a free port with `bulkhead port --near 3000` and pass it explicitly, for example `npm run dev -- --port $(bulkhead port --near 3000)`.
- Next.js and Vite move to the next port on their own when theirs is taken. Read the port the server prints instead of assuming the default.
- Start long-running servers in the background (`run_in_background: true` in Claude Code, an async or detached shell in Copilot CLI), and stop them when you are done.

## Stopping processes

- Stop only processes you started, by PID. Never by program name: `taskkill /IM node.exe`, `pkill node`, `killall python` and `Stop-Process -Name node` stop every session's processes, and can end your own session.
- Find the PID by port (`netstat -ano | findstr :<port>` on Windows, `lsof -ti :<port>` elsewhere) or by your project path (`pgrep -af '<project dir>'`, or `Get-CimInstance Win32_Process` filtered on `CommandLine`). Check that it is yours before stopping it.
- Then `taskkill /PID <pid> /T /F` on Windows, `kill <pid>` elsewhere.
- Kills by port (`npx kill-port`, `fuser -k`, `lsof -ti :N | xargs kill`) are blocked when another session owns that port.

## When the session ends

In Claude Code, servers, test runners and their workers, watchers, builds and headless browsers you start from the Bash tool are stopped by orphan-reaper a few seconds after the session exits. `bulkhead reap --dry-run` lists what sessions that already exited left running.

In Copilot CLI and the other agents nothing is stopped for you when the session ends. Before you finish, stop every server, watcher and browser you started, by PID, unless the user asked to keep it running; tell them which ones are still running and on which port.

In either case, do not promise the user that a server will keep running after the session; if they want that, they should start it in their own terminal.

## Heavy commands

Builds, full test suites, type checks of large projects, browser automation, emulators and Docker builds can use several GB each. Queue them so sessions take turns instead of freezing the machine:

```
bulkhead-slot run --gb=4 -- npx playwright test
```

`--gb` is the job's honest peak size: about 4 for browser suites, `next build` or an emulator, 3 for a dev server or a 4-worker test run, 2 for one type check. The command waits until there is room, runs, and frees the slot when it exits; its exit code passes through. `bulkhead-slot status` shows who holds slots. Never edit, touch or delete slot files by hand. Limit workers (`--maxWorkers=2`, one browser) when memory is tight.

### On another machine

If `bulkhead remote list` shows a remote, a heavy job can run there instead and use none of this machine's RAM. It sends this project's code to another machine, so it never runs on your own decision, even when free RAM is low or memory-guard blocked the command. Suggest it, and run it only after the user says yes to that run:

1. Run `git log -1 --oneline` and `git status --short`, then tell the user in a few lines: the remote it goes to, that the current commit (only commits the remote lacks) and every uncommitted change listed, deletions included, are sent over SSH, any ignored file you would add with `--files`, and the command it runs there.
2. Ask whether to go ahead and end your turn. If they say no, send nothing and run the job here through bulkhead-slot. A yes covers that one run, not later ones, and not files or commands you did not name.
3. Once they agree:

```
bulkhead remote run --tail=60 --gb=4 -- npx playwright test
```

- Run it with `run_in_background: true` and end your turn. Its exit code is the command's, and `--tail=60` keeps the output to the last 60 lines plus the path of the full log.
- It sends the current commit and the uncommitted changes. An ignored file goes only with `--files=<path>`, and only one the user named or agreed to in step 1. Never add an env or secrets file on your own.
- A server the command starts must listen on `$BULKHEAD_PORT`, not a fixed port: other runs use the same remote. Everything the command started is stopped when it ends.
- Reports and screenshots stay on the remote. Bring them back with `--fetch=playwright-report` on the run, or `bulkhead remote fetch playwright-report` afterwards.
- Exit 3 means no free copy or RAM there in time, 4 a transfer or setup problem, 5 an unreachable remote. Then tell the user and run it here through bulkhead-slot instead.

## Waiting

Do not sit in a foreground loop waiting for a long job: the session cannot do anything else meanwhile, and long foreground sleeps are blocked. In Claude Code, run the wait with `run_in_background: true` and end your turn; you are notified when it exits. In other agents, start the job in the background and check its output or exit status later. A command ending in `&` also returns at once.

## Git trees

When another session works in the same checkout, `git checkout`, `switch`, `stash`, `reset --hard`, `clean -f`, `rebase` and `merge` change its files under it. Work in your own worktree: `git worktree add ../<repo>-<task> -b <branch>`.

- Commit only the files you changed, by name: `git add src/a.ts src/b.ts` or `git commit -m "..." -- src/a.ts`. In a shared checkout `git add -A`, `git add .` and `git commit -a` also take the other session's half-finished edits.
- Never delete a folder or worktree another session works in. `bulkhead status` lists each session's project folder. When cleaning up worktrees, remove only the ones you created and that no live session uses.
- Commit as the user's git identity. Do not set `user.name` or `user.email`, and do not pass `--author`; a `Co-Authored-By` line in the message is the place for the agent.

## Disk

The disk is shared too. Measure one folder at a time in the foreground (`du -sh node_modules`), starting from the folders you suspect. Never size or `find` the whole drive or home folder, and never run several scans at once (`xargs -P`, `parallel`, `&` in a loop): the disk sits at 100% and every session stalls. Use `find <folder> -maxdepth 3`, `git ls-files`, `mdfind` or `locate` to find a file.

## When a guard blocks you

Read the message: it names the other session and what to do instead. Do not work around it by splitting, encoding or hiding the command. If the block is wrong for this project, tell the user which setting would allow it (`bulkhead config` lists them, for example `killGuard.allowNames` or `portGuard.ignorePorts`). Settings that loosen a guard are read from the user's global config file only; a project's `.claude/bulkhead.json` can only make the guards stricter. `bulkhead log` shows what was blocked.
