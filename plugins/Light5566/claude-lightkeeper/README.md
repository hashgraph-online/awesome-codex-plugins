# Lightkeeper

[![Listed on ClaudePluginHub](https://www.claudepluginhub.com/badge/light5566-lightkeeper)](https://www.claudepluginhub.com/plugins/light5566-lightkeeper?ref=badge)

**A knowledge map of your codebase that your coding agent reads before it edits and updates before it stops.** For Claude Code, Hermes Agent and Codex.

[English](README.md) · [中文](README.zh.md) · [Live gallery](https://light5566.github.io/claude-lightkeeper/) (interactive maps of Excalidraw, Mastodon, Gitea, Paperless-ngx and BookStack) · [Changelog](CHANGELOG.md)

![Claude Code beside Obsidian: Claude checks the map before changing code, then updates the note that owns the file it edited](https://light5566.github.io/claude-lightkeeper/assets/demo-v3.gif)

A coding agent rediscovers your codebase every session, and a long session loses what it read when its context is compacted. Lightkeeper writes down what the agent should know, and hooks put the right note in front of it at the moment it opens the file.

```
/plugin marketplace add Light5566/claude-lightkeeper
/plugin install lightkeeper@claude-lightkeeper
/lightkeeper:init
```

Three lines in Claude Code, the third from inside your project. It makes a map for the repo you are in, then offers to write the first notes from your code. Nothing is written into your repo: the map lives in `~/vaults/<name>`. Using [Hermes Agent or Codex](docs/agents.md)? Their install lines are there.

Lightkeeper is a Claude Code plugin, and runs as a Hermes Agent and a Codex plugin too. It keeps an Obsidian-compatible markdown map of how your system works (modules, flows, integrations, platform traps, decisions, releases, the words it uses in its own way) *outside* the code repo, and wires five behaviours into the agent so the map stays true:

- a **session primer** that tells the agent the map exists and how to query it,
- **prompt hints** that surface the notes relevant to what you just asked,
- a **file pointer** at the note that owns a file, the first time the agent reads or edits it,
- a **Stop reminder** that names the exact notes the session's changed files belong to when the map didn't move,
- **maintenance signals** that say which notes have grown too long, gone stale while their code moved, or claim files that no longer exist.

It is the [LLM-wiki pattern](https://www.noze.it/en/insights/llm-wiki/) applied to a codebase, kept honest by hooks. Ten months of daily use across three production codebases: 464 notes, 4,500 reasoned links.

[![The interactive map of BookStack from the gallery](https://light5566.github.io/claude-lightkeeper/assets/map.png)](https://light5566.github.io/claude-lightkeeper/maps/bookstack.html)

```
$ vault find payment timeout
Payment  (module/shipped/full, updated 2026-10-02)
  Takes the money for an order.
  → 2 Modules/Payment.md
  connects:
    → Order — a paid order moves to fulfilment
    ← Refund — a refund reverses the gateway charge through Payment::reverse()
```

When the agent then opens `app/Services/PaymentService.php`, the file pointer says:

> `app/Services/PaymentService.php` is documented by vault note "Payment" (updated 2026-10-02) — read its Gotchas before going further.
> If you change this file and the change alters behavior, updating the note afterwards is part of the definition of done.

And when it tries to stop without touching the map:

> Knowledge vault not updated. 3 file(s) under app, routes changed in the last 6h, but no note in the vault moved. Affected notes: Payment, Order. Update the note(s): amend 'How it works' / 'Gotchas', bump 'updated:'.

## How this is different

| | What it keeps | How it stays current |
|---|---|---|
| **claude-mem** and other memory tools | what happened in past sessions | automatic capture of transcripts |
| **Understand-Anything** and code-graph tools | every file, function and class | regenerated from the AST |
| **Lightkeeper** | how the system works and *why*: curated notes with reasons on every link, Gotchas no AST contains, decisions and client rulings | hooks make the agent read the map before editing and update it before stopping; signals say when a note is lying |

Use a memory tool *and* this. They answer different questions.

## Why the map lives outside the repo

1. **Worktrees.** A busy repo has many checkouts at once. An in-repo map would exist in every one of them, your editor opens one, and a stale copy looks exactly like the current one.
2. **Branches.** Notes written on a branch would be invisible until merged, so the map would lag the work by the life of every branch.
3. **Several repos.** A backend and a web app are one system. A map inside one repo makes the other second-class.

The cost: a map update is a separate commit in a separate repo, so git cannot couple them. That is exactly what the hooks and the `vault check` ritual are for.

## Install, from zero

**You need:** [Claude Code](https://code.claude.com), git, and Python 3.9 or newer on your PATH (macOS and most Linux distributions ship it). Obsidian is optional: get it at [obsidian.md/download](https://obsidian.md/download) or `brew install --cask obsidian`.

1. **Install the plugin** inside Claude Code:

   ```
   /plugin marketplace add Light5566/claude-lightkeeper
   /plugin install lightkeeper@claude-lightkeeper
   ```

   or from a shell: `claude plugin marketplace add Light5566/claude-lightkeeper && claude plugin install lightkeeper@claude-lightkeeper`.

2. **Create the map**, from a session inside your project:

   ```
   /lightkeeper:init
   ```

   With no arguments it covers the repo you are in, names the vault after its folder, puts it in `~/vaults/<name>` and installs the `vault` command into `~/.local/bin`. It shows you those choices and asks once before doing anything. To choose yourself: `/lightkeeper:init ~/vaults/myapp --name "My App" --repo ~/code/myapp --repo ~/code/myapp-web --git-hook`.

3. **Seed the first notes** from the code:

   ```
   /lightkeeper:seed
   ```

   Claude proposes domains and up to 60 module stubs with real file paths, asks, then writes them. From that moment the file pointer fires, in this session too. The session primer shows from your next session.

That's it. Three things worth knowing:

- **See the map:** open the vault folder in Obsidian (*Open folder as vault*), or run `vault export --html map.html` for a single page you can open in a browser.
- **Check it works:** `vault doctor` checks the setup on one screen and prints a fix beside each problem. If you install the plugin and never create a map, the first session in a repo tells you once.
- **Turn it off:** `vault init --forget` stops using the vault in this project and removes the git hooks it installed. The vault folder stays where it is.

Working on a project that already has a vault? Clone and register it in one step:

```
/lightkeeper:init --clone git@github.com:your-team/myapp-vault.git --repo ~/code/myapp --git-hook
```

Have an existing Obsidian vault you want to grow into this? `vault init --adopt ~/my-vault --name "My App" --repo ~/code/myapp` writes the config and registers it without touching your notes; only notes that carry a `type:` are linted, so you can adopt gradually.

## The hooks

All advisory. None can block an edit, and all of them are silent no-ops in a repo no vault covers and on a machine without the vault.

![The pre-edit pointer and the Stop reminder firing in a Claude Code session](https://light5566.github.io/claude-lightkeeper/assets/hooks.png)

| Event | What it says | When it stays quiet |
|---|---|---|
| SessionStart | where the vault is, how to query it, that updating it is part of done; once a day, what needs attention | on resume |
| SessionStart (after compaction) | re-query the vault instead of re-exploring code you already read; names the notes that were in play, whose text the compaction dropped, and lets the hints and the pointer name them again | |
| UserPromptSubmit | up to three notes whose names, aliases or flags appear in your prompt, with their one-liners and nearest neighbours; a glossary term in your prompt comes back with its meaning; once per session, a nudge when the prompt sounds like a decision or a ruling | nothing new matches |
| PreToolUse (Read/Write/Edit) | the note that owns the file about to be read or changed, with its neighbours; on a Read it arrives while the agent is still planning; for a stub, "nothing recorded yet, write what you learn" | the file is unowned, or you were already pointed at that note |
| Stop | watched files changed in the last 6 hours but no note moved; names the owning notes and counts files that match no note | the vault is dirty or was committed within the window |

## Writing notes

Every note is plain markdown with flat one-line frontmatter. The engine reads three things from your writing:

- **The one rule: every `[[link]]` carries a reason.** `- [[Invoice]] — a paid order raises an invoice through InvoiceService::create()`. Reasons become the "blast radius" shown beside every search hit; a bare link makes the graph a hairball.
- **The *Where it lives* table** of a module note is machine-read: real files, first path in a cell fully qualified, never a container directory. It is the file→note index the pre-edit hook runs on.
- **Glossary terms.** A word this codebase uses in its own way gets a short note in `9 Glossary` (`type: term`): what it means here, and where it shows up. Whenever the word appears in a prompt, the hint gives its meaning, so the agent doesn't guess. When one word means different things in different modules, write each meaning on that module's line under *Where it shows up*: the hint lists the meaning per module, the modules already in play this session first, and adds the first line of *Not to be confused with*.
- **The honesty fields.** `status: shipped` means the code is on the production branch; `depth: stub` means the note is thin; `updated:` is bumped every time you touch a note. A note can be wrong; when the code disagrees, the code wins and fixing the note is part of the change.

The scaffold's `_meta/Conventions.md` and `_meta/How to update.md` hold the full conventions, the trigger table (which note to touch for which kind of change) and the sixty-second version. The `knowledge-vault` skill teaches them to Claude.

## The command line

```
vault find <terms>              topic search, tiered: names → aliases/flags → tags → full text
vault find --paths <files>      which notes own these files
vault check [--write]           lint; --write also rebuilds the index and regenerates
                                Coverage.md, Vault Changelog.md, Attention.md and World.canvas
vault status                    coverage, stale notes, attention, sync drift on one screen
vault status --session          what the hooks did in the latest session: runs, notes surfaced, notes updated
vault sync [target] [--advance] what landed on the repos since the vault last caught up
vault log <note>                that note's git history
vault export --html <file>      a self-contained interactive map
vault export --agents-md        a block for AGENTS.md: where the map is, how to search it, which note owns which code
vault doctor                    is it set up and working here? a fix beside each problem
vault init                      inside a git checkout: a vault for this repo, all defaults
vault init <path> --repo ...    scaffold, clone (--clone) or adopt (--adopt) a vault, your choices
vault init --forget             stop using a vault here; the folder stays
```

Every command takes `--vault <path>`; without it, the vault covering the current directory is used.

`vault export --agents-md` is for agents that don't run Lightkeeper's hooks. It prints the block and never writes it anywhere: paste it into `AGENTS.md`, `CLAUDE.md` or `GEMINI.md`, or ask your agent to, so you see the diff. To refresh it, run the command again and replace what sits between the two markers. When one vault covers several repos, run it from the checkout, or pass `--repo KEY`.

`vault check` catches unresolved links, duplicate note names, bare links, container-directory claims, off-schema frontmatter, orphans, stale notes, and anything that looks like a secret or personal data (email addresses, long digit runs, API-key shapes, private keys). Run it with `--write` before every vault commit.

## Compatibility

| | |
|---|---|
| Claude Code (CLI, desktop, IDE extensions) | hooks, skills, commands and the CLI |
| Hermes Agent | hooks, skills, procedures and the CLI, through the adapter at the repo root; see [docs/agents.md](docs/agents.md) |
| Codex | hooks, skills and the CLI, through the adapter in `codex/`; see [docs/agents.md](docs/agents.md) |
| Other agents (Cursor, Gemini CLI, …) | the `vault` CLI, the SKILL.md files, and a block for their AGENTS.md from `vault export --agents-md` |
| macOS, Linux | tested |
| Windows | untested; hooks call Python directly, so WSL or Git Bash should work |
| Obsidian | optional: the graph colours, Bases views and canvas are extras; the notes are plain markdown with wikilinks that Foam, Logseq or any editor can read |
| Python | 3.9 or newer, standard library only, nothing to pip install |
| Languages and frameworks | any; `vault init` detects the layout, and `vault.json` covers the rest |

## Going further

- **[Configuration, teams and keeping the map honest](docs/guide.md):** `vault.json`, sharing a vault with teammates, the PR comment bot, branch notes, and the checks that say which notes have gone stale.
- **[Hermes Agent and Codex](docs/agents.md):** install lines and exactly what is wired in each.

## Not included, on purpose

- **An MCP server.** The map is a discipline the hooks enforce and a CLI any agent can run, not a database an agent queries when it remembers to.
- **Transcript mining.** The Stop hook asks the agent to write what it learned; it does not try to guess it from the transcript.
- **Auto-commit.** A human, or the agent on your instruction, reviews the vault diff and commits it.

## Development

```
bash check.sh      # scaffolds a throwaway vault and runs every hook and command against it
```

MIT. Issues and pull requests welcome.
