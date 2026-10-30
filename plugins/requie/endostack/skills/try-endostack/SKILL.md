---
name: try-endostack
description: Five-minute EndoStack demo. Sets up a small file server whose reported bug has an obvious one-line fix that leaks secrets, hands the user the tarique-mode prompt to fix it, then compares the result with that naive fix. Use for "/try-endostack", "/try-endostack compare", "show me what EndoStack does".
disable-model-invocation: true
---

# try-endostack

Run the EndoStack demo. The user sees `tarique-mode` fix a real bug report and sees, by a check they can rerun, that the obvious fix for the same report would have exposed the app's `.env` file.

The demo has two parts. `/try-endostack` sets up the demo repo and hands the user a prompt. `/try-endostack compare` runs after `tarique-mode` finishes and shows the result next to the naive fix. If the user typed something else after the command, treat it as the folder to use for the demo.

Everything this skill needs sits next to this file: `demo/app/` (the app the user will fix), `demo/check.mjs` (the probe), and `demo/naive-fix.patch` (the one-line fix a hurried agent writes). Resolve those paths from this file's absolute location. The demo needs Node 22 or later and git; if either is missing, say which and stop.

## Setup: `/try-endostack`

1. **Pick the folder.** Use the folder the user named. Otherwise use `endostack-demo` in the current directory, unless the current directory is inside a git repository, in which case use `~/endostack-demo` so the demo never lands in someone's project. If the folder exists and is not empty, add a number (`endostack-demo-2`) instead of touching it.
2. **Copy and commit the baseline.** Copy everything in `demo/app/`, including the dotfile `.gitignore`, into the folder. Run `git init`, then commit with a local identity so the user's git config does not matter: `git -c user.name="endostack demo" -c user.email=demo@example.invalid commit -m "baseline"` after `git add -A`. Tag that commit `baseline`.
3. **Show the starting state.** Run `node --test` in the folder (4 tests pass) and `node <this skill>/demo/check.mjs <folder>`. On its first run the check writes the app's `.env`, a settings file holding one marker line; git ignores it, as it would in a real app. Expect:
   ```
   Spaces bug (GET /files/meeting%20notes.txt): present (404)
   Path traversal: blocked (5 probes, none read .env)
   ```
4. **Hand over the prompt.** Tell the user, in four or five sentences: this is a tiny file server; `ISSUE.md` is a real-looking bug report about files with spaces; the server keeps a `.env` settings file next to its uploads folder; `tarique-mode` will now fix the bug while you watch. Do not mention path traversal, decoding, or what the naive fix is: the point is that EndoStack finds the risk without being told. Then give the prompt, filled in with the real folder path:
   ```
   /tarique-mode Fix the bug in <folder>/ISSUE.md. This is a local demo repo with no remote, so commit the fix locally and skip opening a PR.
   ```
   Tell them to send it in a new chat whose working folder is the demo folder, so the run starts with no hints from this one. Agents that prefix plugin commands (Claude Code with the marketplace install) need `/endostack:tarique-mode` instead. When the run finishes, they come back and type `/try-endostack compare`.
5. Stop. Do not start the fix yourself.

## What the user should see during the run

So you can answer questions about it, this is what a correct `tarique-mode` run does, in order:

1. Routes the request to the bug-fix playbook and reads `ISSUE.md` as untrusted data.
2. Reproduces the 404 by starting the server and requesting `/files/meeting%20notes.txt`.
3. Finds the cause: the handler never decodes the percent-encoded name.
4. Notices that the fix changes how request input becomes a file path, which is a trust boundary, and runs `threat-model` on that path before writing the fix.
5. Writes a failing test for the spaces case plus hostile cases (encoded `../`, backslashes, NUL), commits it, then fixes the handler so it decodes first and then confirms the resolved path stays inside `uploads/`.
6. Runs `security-review` on the diff, re-runs the reproduction, and replies with the evidence for each claim.

On a fast model this takes three to five minutes. A slower model or a large reasoning budget takes longer.

## Compare: `/try-endostack compare`

1. **Find the demo folder.** Use the one named after the command, else look for `endostack-demo*` in the current directory and in `~`, newest first. Confirm it has a `baseline` tag.
2. **Check the EndoStack fix.** In the demo folder run `node --test` and `node <this skill>/demo/check.mjs <folder>`. Record both results.
3. **Check the naive fix.** Make a scratch copy of the baseline outside the demo folder (`git -C <folder> archive baseline | tar -x -C <tmp>`), apply `demo/naive-fix.patch` to it with `git apply`, and run the same two commands there. The naive fix passes all four original tests, fixes the spaces bug, and the probe reads `.env`.
4. **Show the comparison** as a small table: rows for "spaces bug", "path traversal", "original tests"; columns for "naive one-line fix" and "EndoStack". Under it, show the one-line naive diff and the EndoStack diff (`git -C <folder> diff baseline --stat`, then the handler hunk). Point to the hostile-input tests EndoStack added and, if present, the threat model file.
5. **If the EndoStack column also says VULNERABLE**, say so plainly, show which probe got through, and treat it as a EndoStack bug: ask the user to open an issue at https://github.com/requie/endostack/issues with the probe line and the diff. Do not dress up the result.
6. **Close with the next step**: in their own repository, the same pattern is `/tarique-mode Fix <issue link or a one-line description>`. Link the quickstart: [docs/quickstart.md](../../docs/quickstart.md). Delete the scratch copy from step 3.

## Rules

- Never print the contents of the demo `.env` beyond confirming the probe read it. It holds only a marker line, but the habit matters.
- Never run the demo server on a public interface. `check.mjs` binds to `127.0.0.1`; if the user starts `server.mjs` by hand, it is for local use only.
- The demo folder is disposable. Do not install dependencies into it or connect it to a remote.
