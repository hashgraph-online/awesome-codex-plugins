# AsItIs for Claude Code

A read-only linter for the files that steer coding agents: CLAUDE.md, AGENTS.md, SKILL.md, Cursor rules, Copilot instructions and memory files. It shows what each agent loads when a session starts in a folder, roughly what that costs in tokens, and where hidden comments or invisible characters sit. It doesn't write to your files and makes no network calls.

It runs in Claude Code (and in Cowork sessions on your own computer), because the linter is a local MCP server started with `node`. In claude.ai chat that server doesn't run, so the commands have nothing to call there.

| Part | What it does |
|---|---|
| MCP server `asitis` | Seven read-only tools: `read_markdown`, `outline`, `lint_steering`, `context_budget`, `load_plan`, `find_steering_files`, `suggest_fixes`. See [`@asitis/mcp`](https://github.com/Katta041/asitis-agent-tools/blob/main/packages/mcp/README.md). |
| Skill `steering-check` | Picks the right tool when you ask in plain words: why an agent ignores a file, what loads in a folder, what the files cost, or whether anything hides text. |
| Skill `markdown-byte-clean` | Teaches Claude to edit minimal ranges, never rewrite whole markdown files, and keep frontmatter, line endings, BOM and trailing spaces exactly as they are. |
| `/asitis:md-lint [path] [skills] [config]` | Lints steering files: frontmatter on line 1, YAML, required fields, limits, broken links and `@imports`, invisible characters, hidden instructions, and drift between AGENTS.md, CLAUDE.md and the other agents' files. Add `skills` to also scan the scripts in skill folders, and `config` to audit `.claude/settings.json` and the MCP config files. |
| `/asitis:md-budget [path]` | Shows approximately how many tokens load every session, per tool, and what to cut. |
| `/asitis:md-loads [folder] [tool]` | Shows what each agent loads when it starts in a folder, what loads later, what gets cut and what is never read. |
| `/asitis:md-fix [path]` | Shows mechanical fixes (invisible characters, frontmatter, skill names, trailing spaces, final newline) as a diff, asks, and applies only the ones you accept. |
| Guard hook (optional) | Warns before a Write, Edit or MultiEdit that would change line endings, strip trailing spaces that make a line break, drop a BOM or break frontmatter in an existing markdown file. |
| `asitis` CLI | The same linter for scripts and CI, bundled at `server/asitis.mjs`: `node server/asitis.mjs lint`. See [CLI and CI](https://github.com/Katta041/asitis-agent-tools#cli-and-ci). |

## Install

Requires Claude Code and Node 22.13 or later on your `PATH` (the server and hook run with `node`).

If you're reading this in Claude's plugin directory, add it from there. It goes on your claude.ai account and Claude Code loads it as `asitis@synced` the next time you start it (signed in with that account). If you already installed `asitis@asitis` from GitHub, Claude Code keeps using that copy and skips the synced one.

To install from GitHub instead:

```bash
claude plugin marketplace add Katta041/asitis-agent-tools
claude plugin install asitis@asitis
```

Inside a session, `/plugin marketplace add Katta041/asitis-agent-tools` and `/plugin install asitis@asitis` do the same. Then start a new session and run `/asitis:md-lint` to lint the project's steering files, or `/asitis:md-budget` to see what they cost in tokens.

To update a GitHub install, run `claude plugin marketplace update asitis`, then `claude plugin update asitis@asitis`, and restart Claude Code. To remove it, run `claude plugin uninstall asitis@asitis`. A directory install updates by itself; to turn it off in Claude Code, run `claude plugin disable asitis@synced`.

From a local clone of [the repository](https://github.com/Katta041/asitis-agent-tools), pass the clone's folder instead: `claude plugin marketplace add ./asitis-agent-tools`. To try it for one session without installing, run `claude --plugin-dir ./asitis-agent-tools/plugins/asitis`.

The same folder installs as a Codex plugin: `codex plugin marketplace add Katta041/asitis-agent-tools`, then `codex plugin add asitis@asitis`. Codex gets the MCP server (from npm, see the [repository README](https://github.com/Katta041/asitis-agent-tools#codex-plugin) for why) and both skills, but not the commands or the guard hook. Gemini CLI has its own extension in the repository root, and Claude Desktop, Cursor and VS Code use the MCP server on its own; config snippets are in the [repository README](https://github.com/Katta041/asitis-agent-tools#other-mcp-clients-claude-desktop-cursor-codex-gemini-cli).

### Troubleshooting

| You see | What to do |
|---|---|
| `asitis-mcp: AsItIs needs Node 22.13 or later; you have 20.18.0. ...` | Install a current Node from [nodejs.org](https://nodejs.org) and restart Claude Code. (Run without the plugin's launcher, older Node prints only `node: bad option: --permission`.) |
| `asitis-mcp: Refusing your home folder ...` | Start Claude Code in a project folder, not in your home folder. |
| `Linted 0 files` or `No steering files found` | The project is the folder Claude Code was started in. Start it at the repository root, or the CLAUDE.md and AGENTS.md files above that folder won't be found. |
| `asitis-mcp: Node's permission model will not let the server read the root folder ...` | Only when you run the server by hand: list the project folder in `--allow-fs-read` and drop any folder inside it. The plugin does this for you. |

## Privacy

- No network. The server and the hook make no connections, collect nothing and send nothing.
- No writes. The server has no write tool and no write code; the hook only reads the file it is asked about. `/asitis:md-fix` edits a file only after you accept the fix, through Claude's own Edit tool.
- Markdown only, unless you ask. `/asitis:md-lint` reads steering files and `.asitisrc.json`. With `skills` it also reads the scripts in skill folders; with `config` it reads `.claude/settings.json`, `.mcp.json`, `.cursor/mcp.json`, `.cursor/cli.json`, `.vscode/mcp.json` and `.gemini/settings.json`, files named `.gitignore`, the first 4 KB of `<uuid>.jsonl` files (to spot committed transcripts), and `package.json` and Makefile files for the script and target names `dead-command` checks. `.claude/settings.local.json` needs `config-local`, and `~/.claude.json` is never read. A repo's `.asitisrc.json` cannot turn these scans on for you.
- The server runs under Node's permission model: `node --permission` with read access to this plugin and your project folder only, and no write or child-process rights. Node enforces that, not just our code. Node blocks network access too from version 25; on Node 22.13 to 24 the no-network guarantee rests on the code, which contains no network calls. A small launcher (`server/launch.mjs`, about 150 lines, no dependencies) checks the Node version, takes the project folder from `CLAUDE_PROJECT_DIR` (which Claude Code sets), and starts the server with those flags; it reads no files and makes no connections.
- Tool results go into Claude's context and so reach Anthropic like the rest of your session. That is Claude Code's traffic, not ours.

## Pinned server

The server is not fetched from npm at runtime. `server/asitis-mcp.mjs` is the exact `@asitis/mcp` build for this plugin version (one file, zero dependencies), `server/asitis.mjs` is the CLI from the same build, and `server/VERSION` records the version and both SHA-256 values. A test fails if the file differs from a fresh build or if the versions disagree. Both files are minified esbuild bundles; the readable TypeScript source is in [`packages/mcp/src`](https://github.com/Katta041/asitis-agent-tools/tree/main/packages/mcp/src), and `npm run sync-plugin` rebuilds them byte for byte. [`server/THIRD_PARTY_NOTICES.md`](https://github.com/Katta041/asitis-agent-tools/blob/main/plugins/asitis/server/THIRD_PARTY_NOTICES.md) lists the bundled open-source licences.

## Guard hook

**The guard is an accident guard, not a security boundary.** It exists to catch the common accident: an agent rewrites a whole file with `Write`, or an `Edit` whose `new_string` quietly drops trailing spaces or CRLF line endings. It checks `Write`, `Edit` and `MultiEdit` on existing `.md`, `.mdc`, `.markdown`, `.mdx`, `.cursorrules`, `.windsurfrules` and `.clinerules` files and warns when the change would:

- convert CRLF to LF (or the reverse), flatten mixed line endings or remove lone CRs;
- strip trailing whitespace that can be a hard line break (two or more spaces with more paragraph text on the next line), any trailing whitespace in fenced code or frontmatter, including on a line whose words also change;
- remove the BOM with an `Edit`, add a BOM, or drop the final newline (Claude Code's `Write` keeps an existing BOM, so a `Write` without one is fine);
- move the frontmatter off line 1, remove its closing `---`, drop keys or indent it with tabs;
- rewrite much of an existing file: with `Write`, more than 30% of its lines (at least 3 lines); with `Edit` or `MultiEdit`, more than half (at least 5 lines). Lines count as kept only if they stay in the same order, so a reordered file counts as rewritten;
- touch a file with invalid UTF-8 bytes, which a text tool will replace.

It does not ask about whitespace that cannot change how the file renders: a single trailing space, trailing tabs, spaces on an otherwise blank line or at the end of a paragraph, and adding a missing final newline. Those are the safe fixes `/asitis:md-fix` applies, so accepting them takes one answer, not two.

It checks an `Edit` or `MultiEdit` the way Claude Code writes it: Claude Code turns CRLF into LF, applies the edit, and writes every line break back in one style picked from the first 4,096 characters of the file. So a one-word `Edit` to a file with mixed line endings rewrites all of them, and so does any `Edit` to a CRLF file whose first 4,096 characters have no line break. The guard warns about that and tells Claude to ask you, because no `Edit` can avoid it.

What it does not do: it does not see `Bash` (`sed -i`, redirects, scripts), `NotebookEdit`, other tools or other programs, and anything running as you can bypass it. It never changes the tool call.

Modes, set with the environment variable `ASITIS_GUARD_MODE` (see Options below):

| Mode | Behaviour |
|---|---|
| `ask` (default) | Shows the warning and asks you to allow or reject the change. |
| `deny` | Blocks the change and tells Claude to retry with a minimal edit. |
| `off` | Disabled. |

Any other value is treated as `deny`, the safest mode, and the guard says so in its message.

It fails closed:

- If the hook input is not valid JSON or lacks the fields it needs, the change is blocked with a one-line message saying why (`AsItIs guard: the hook input is not valid JSON. The change was blocked to be safe; ...`).
- Claude Code gives the hook 10 seconds and lets the change through if a hook times out. The guard therefore stops itself after 6 seconds (counted from when the hook process starts), and on files over 16 MB, and asks you (blocks in `deny` mode) instead of letting an unchecked change through.

One case it cannot cover: Claude Code starts the guard with `node`. If `node` is not on your `PATH`, or is older than Node 12, the guard cannot run and Claude Code lets the change through. The plugin's server needs Node 22.13 or later anyway, so with a working plugin the guard runs too.

In a headless run (`claude -p`) Claude Code treats an "ask" as a denial and may label it "hook error". The guard's message starts with "AsItIs guard flagged this change on purpose (a guard decision, not a failure)" so the reason is clear.

Set `ASITIS_GUARD_MODE` to `off` if that ever gets in your way.

## Options

The plugin works with no setup, so installing it asks nothing. To change a default, set an environment variable in the `env` block of your Claude Code settings (`~/.claude/settings.json`, or `.claude/settings.local.json` for one project), then start a new session:

```json
{
  "env": {
    "ASITIS_GUARD_MODE": "deny"
  }
}
```

| Variable | Default | Effect |
|---|---|---|
| `ASITIS_GUARD_MODE` | `ask` | `ask`, `deny` or `off` for the guard hook. |
| `ASITIS_MCP_FOOTER` | off | Set to `1` to end the first tool result of each session with one line linking to asitis.app. |

## Develop

From the repository root:

```bash
npm ci
npm test               # includes the hook, plugin and protocol tests
npm run sync-plugin    # rebuild the server and copy it into server/
claude plugin validate . --strict
claude plugin validate ./plugins/asitis --strict
```

## License

[MIT](https://github.com/Katta041/asitis-agent-tools/blob/main/plugins/asitis/LICENSE). Changes are listed in the [changelog](https://github.com/Katta041/asitis-agent-tools/blob/main/plugins/asitis/CHANGELOG.md).
