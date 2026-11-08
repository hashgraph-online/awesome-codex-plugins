# Hooks

Everything in this repository that runs on its own. `hooks/hooks.json` is the declaration; the three scripts
below are the whole of it. Nothing here sends mail, installs a service, or writes outside the paths named in
this file.

**They only run once this is installed as a plugin.** Copying `skills/centricmem-agent/` into a skills
directory installs the Skill and nothing else - no hook, no manifest, no code path in this file. That is why
`install.json` names the folder rather than the repository.

| Event | Script | Hosts that fire it | Reads | Writes | Network |
| --- | --- | --- | --- | --- | --- |
| `SessionStart` | `hooks/ambient.mjs` | Claude Code, and any host that runs a Claude Code `hooks.json` through a bridge | the librarian, over HTTPS | on goose: the Top Of Mind file; everywhere else: stdout only | one request to `CENTRICMEM_URL` |
| `SessionStart` | `goose/wire-recipes.mjs` | goose only | `goose/*.yaml` in this tree | goose's own recipe library | none |
| `SessionEnd` | `hooks/close.mjs` | Claude Code, Codex | a credential, if one exists | nothing directly - it spawns the local `centricmem` CLI | the CLI's request to the librarian |

## `hooks/ambient.mjs`

Fetches the ambient text and puts it where the host can see it.

- **No credential, no work.** `fetchAmbient()` returns without a credential, nothing is written, nothing is
  printed, exit code 0.
- **On goose** (`PLUGIN_ROOT` set and `CLAUDE_PLUGIN_ROOT` not - that is the whole test) it writes the file
  named by `GOOSE_MOIM_MESSAGE_FILE`, default `~/.goose/centricmem-ambient.md`, which goose's Top Of Mind
  extension injects into every turn. stdout stays empty: on goose, hook stdout is the decision channel and a
  stray line there reads as a decision.
- **Everywhere else** it writes one `hookSpecificOutput.additionalContext` envelope to stdout.
- Any failure is swallowed and exits 0. A hook that cannot reach the librarian must not break somebody's
  session.

## `goose/wire-recipes.mjs`

goose plugins carry skills and hooks and nothing else, so the two recipes in `goose/` would otherwise be
inert. This copies `centricmem-preflight.yaml` and `centricmem-close.yaml` into goose's recipe library and
exits. It never replaces a file it did not write: line 1 of a file must read `# managed by centricmem-skill`
before it is touched. No network. On any host that is not goose it exits immediately.

## `hooks/close.mjs`

Files the session that just ended, which is the point of the product - so it does not ask permission first. It
does honour the switches below.

- Spawns the **locally installed** `centricmem` CLI as `centricmem log-session --auto`, detached and unref'd,
  with a 20 second timer, so the session never waits on it.
- On Windows the CLI is a `.cmd` shim and spawning it with `shell: false` throws `EINVAL`; that is why the
  Windows branch uses `shell: true` with a fixed argument list.
- Runs only when a credential exists. Looking for one would be guessing, which the other hooks also refuse to
  do.

## Switches

| Variable | Effect |
| --- | --- |
| `CENTRICMEM_HOOK_DISABLE=1` | Every hook in this directory exits 0 immediately. |
| `CENTRICMEM_DONT_LOG=1` | `close.mjs` does not file the session; the ambient hooks still refresh. |
| `CENTRICMEM_HOOK_DRY_RUN=1` | `close.mjs` prints what it would do to stderr instead of doing it. |

The same three are honoured by the other clients' hooks in this repository (see `mimocode/README.md`), so a
host does not give a different answer than the one before it.

## What this code does not do

- **No mail.** Every mention of an email address in this repository is an instruction to the human, to contact
  support. `skills/centricmem-agent/REFERENCE.md` says it in as many words: *do not email on their behalf*.
- **No service or scheduled task.** Nothing here registers itself with the operating system. Whether to run
  the refresher on a timer is the operator's decision, taken outside this repository - see `goose/README.md`
  and `mimocode/README.md` for the constraints that apply.
- **No third-party host.** `grep` for `http` across `*.mjs` / `*.js` / `*.ts` in this repository returns one
  host: `mem.centricmem.com`.
- **No writes outside the paths above.** No system directories, no shell profile, no PATH change.

## Checking this without running it

`tools/ambient.mjs` is the shared implementation - the two ambient hooks and the three client-specific
refreshers all import it, so there is one copy of the logic, not six. Read `moimText()` and `fetchAmbient()`
there and you have read what all of them do.
