# orch

`orch` keeps the shared state of a multi-agent program as plain files in one directory: work units, a verification ledger keyed by PR and head SHA, an inbox of agent reports, decision gates waiting on the human, the PR stack frontier, and standing orders. Every agent in the program reads and writes the same directory, and a human can open any file to see where things stand. Writers take a pid lock, so two agents writing at once cannot interleave and corrupt a file.

It needs Node.js 22 or newer, `git`, and an authenticated `gh` CLI for `frontier set`. It has no package dependencies.

## Usage

```
orch [--store <dir>] [--json] [--force] <command> ...
```

| global option | meaning |
|---|---|
| `--store <dir>` | store directory; falls back to `ORCH_STORE`. Required; blank counts as missing. |
| `--json` | print complete rows as JSON (2-space indent) |
| `--force` | take the store lock even when a live process holds it |
| `-h`, `--help` | print help; after a command, print that command's help |

| command | effect | plain output |
|---|---|---|
| `init` | create the directory and every missing file; safe to rerun, never touches existing files | `initialized DIR` |
| `unit add <name> --track <t> [--brief <path>]` | add a unit at stage `pending`; a repeated name fails | the row, tab-separated |
| `unit set <name> --stage <s> [--branch <b>] [--pr <n>] [--head <sha>]` | move the unit to a new stage and set any field given | the row |
| `unit get <name>` | one unit | the row |
| `unit list [--stage <s>] [--track <t>]` | filter by exact stage and track | up to 4 rows, then `N more; use --json`; `no units` when empty |
| `unit counts` | units by stage | `merged=1, pending=5` or `none` |
| `ledger record <pr> <head> <verdict> --evidence <path> [--verifier <name>]` | insert or replace the row for (PR, head SHA), stamped with the current time | `pr head verdict` |
| `ledger check <pr> <head>` | the verdict for that head | the verdict, or `NO-VERDICT` with exit 2 |
| `ledger summary` | rows by verdict | `verdict=n, ...` or `none` |
| `inbox push <from> <unit> <outcome> [--report <path>]` | add one pointer file to the inbox | `unit outcome filename` |
| `inbox drain [--peek]` | take every pointer (with `--peek`, read without taking or locking) | one pointer per line, or `(empty)` |
| `inbox count` | pointers waiting | the number (`{"count": n}` with `--json`) |
| `gate park <id> --question <q> --options <o> --default <d>` | open or replace a gate | `parked ID` |
| `gate list` | open gates | up to 4 rows, then `N more; use --json` |
| `gate resolve <id> --answer <a>` | mark resolved, keep question, options, and default | `resolved ID: ANSWER` |
| `frontier set [--repo <dir>] [--prs <n,...>]` | resolve the PR stack for the repo's checked-out branch and store it | `generation=N prs=branch#pr@sha:STATE,... lowest-unmerged=N\|none` |
| `frontier show` | the stored frontier | same line |
| `status` | write `status.md` and print a summary | three lines (below) |
| `standing show` | standing orders | `1. text` lines, up to 4 |
| `standing add <line>` | append the next numbered order | `N. text` |

A verdict must be one of five values. From strongest to weakest: `live-proven` (seen working in the running product), `tests-proven` (passing tests cover it), `types-only` (it type-checks and nothing more was run), `check-blocked` (the checker could not run it), `check-failed` (the checker saw it fail). PR numbers must match `^[1-9][0-9]*$` and be safe integers. `--prs` is a comma list with no empty entries and no duplicates. `--repo` falls back to `ORCH_REPO`.

`status` prints:

```
units=6 (merged=1, pending=5) ledger=tests-proven=1
changed: units pending 4->5; open gates 0->1
open gates=1: g1
```

The `changed:` line compares with the summary saved in the previous `status.md`. It reads `first render` when there is no readable previous summary and `no derived changes` when nothing moved. At most four open gate ids are listed, then `+N more`.

## Exit codes

| code | meaning |
|---|---|
| 0 | success, including `--help` |
| 1 | usage error (message plus help on stderr) or user error (`error: ...` on stderr): missing store, bad value, lock held, malformed store file, forge or git failure |
| 2 | not found: `unit get`, `unit set`, or `gate resolve` naming something absent (message on stderr), or `ledger check` with no row (`NO-VERDICT` on stdout, nothing on stderr; with `--json`, `{"pr": N, "head": "...", "verdict": "NO-VERDICT"}`) |

The distinct exit 2 for `ledger check` lets a merge gate script treat "never verified" as its own outcome without parsing stderr.

## Store layout

| file | contents |
|---|---|
| `work-units.tsv` | header `name track stage pr branch head brief`, one row per unit |
| `ledger.tsv` | header `pr head verdict evidence verifier recorded` |
| `inbox/` | one `<timestamp>-<pid>-<uuid>.tsv` per pointer, a single line with the fields `at from unit outcome report` |
| `gates.md` | empty, or `# Gates` then one `## id` per gate with `- Status:`, `- Question:`, `- Options:`, `- Default:`, and (resolved only) `- Answer:` |
| `standing-orders.md` | standing orders as `1. text`, `2. text`, numbered from 1 with no gaps |
| `frontier.json` | `{}` at first, then `{ generation, prs: [{ pr, branch, sha, state }], lowestUnmerged }` |
| `status.md` | generated report: units, ledger, frontier, open gates, each with a count line and a Markdown table, plus the summary as an HTML comment |
| `.writer.pid` | pid of the current writer |

Agents write values that came from other agents, issue text, and tool output, so every TSV cell is cleaned before it is stored: tabs and line breaks become spaces, and a cell starting with `=`, `+`, `-`, or `@` gets a leading `'` so a spreadsheet shows it as text instead of running it as a formula. Gate and standing-order text has line breaks replaced with spaces, which keeps one value from forging a new Markdown field. Markdown table cells in `status.md` escape `\` and `|`.

Every file is read strictly. A wrong TSV header, a row with the wrong column count, an unknown ledger verdict, a frontier with the wrong shape, a malformed inbox pointer, a malformed gate block, or a numbering gap in standing orders each fail with a message naming the file.

## Locking and atomic writes

Read-only commands (`get`, `list`, `counts`, `check`, `summary`, `drain --peek`, `count`, `gate list`, `frontier show`, `standing show`) never take the lock. Every other command, including `status` (it writes `status.md`) and `init`, creates `.writer.pid` with an exclusive create and writes its pid. If the lock exists:

- held by a well-formed pid whose process is gone: reported on stderr as stale and taken over;
- otherwise, with `--force`: reported on stderr with the holder's pid and taken over;
- otherwise: `error: another writer (pid N) holds the store lock`, exit 1.

On exit the lock is removed only if it still holds this process's pid. Each file write goes to a hidden temp file in the same directory and is renamed over the target, so a reader sees either the old or the new file. `inbox drain` reads the pointers, renames the inbox directory aside, creates a fresh empty one (restoring the old one if that fails), returns every pointer from the renamed directory, and deletes it.

## Frontier resolution

`frontier set` runs `git` and `gh` in the repository given by `--repo` or `ORCH_REPO`:

1. Trunk is the branch `origin/HEAD` points to, or `main`. If the checked-out branch is trunk, the frontier is empty.
2. Walking down from the checked-out branch, it lists PRs whose head is that branch (all states), prefers open ones (drafts count as open), and follows the base until trunk. A branch with no PR fails and names the branch. A branch with more than one candidate fails and lists them.
3. Walking up from the tip, it follows the single open PR whose base is the tip. Two or more is a fork, reported as `stack forks at '<branch>'`. A repeated branch is a loop error, and a PR number appearing twice is an error.
4. Each branch's SHA comes from the local branch, then `origin/<branch>`, then the head SHA `gh` reports; it must be 40 to 64 hex characters.
5. With `--prs`, the resolved order must match. A mismatch reports PRs missing from the chain, extras, or (when the sets match) both orders.

`gh` output must be a JSON array whose rows each carry a number above zero, a state of `OPEN`, `MERGED`, or `CLOSED`, and non-empty head and base names; anything else fails with the command line in the message. The written frontier has the generation incremented and `lowestUnmerged` set to the first open PR.

## Layout

| file | role |
|---|---|
| `orch` | POSIX launcher; follows symlinks, runs `orch.mjs` with Node |
| `lib/cli.mjs` | argument parsing, command table, help, output, exit codes |
| `lib/store.mjs` | the `Store` class: every command's logic and `status.md` rendering |
| `lib/files.mjs` | atomic writes, cell cleaning, TSV read and write |
| `lib/lock.mjs` | the pid lock |
| `lib/gates.mjs` | `gates.md` and `standing-orders.md` formats |
| `lib/frontier.mjs` | stack resolution through `git` and `gh` |

## Tests

`node --test skills/tarique-mode/scripts/` runs the whole suite. The store tests use temp directories. The frontier tests build real git repositories with a bare `origin` and put a fake `gh` script first on `PATH`, so they run with no network.
