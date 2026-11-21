# AgentAvow Trust

Automatically checks your MCP servers and packages before Claude uses them.

**What you'll see.** Install the plugin and start a session. Claude's first reply opens with
one line, for example: "AgentAvow pre-check: checked 8 MCP servers — 5 Safe, 2 Review, 1
Don't connect (needs attention: 'example-server' Do not connect — one critical finding: eval of
input). Dependencies: checked 12 of 38 — 11 Safe, 1 Review (needs attention: 'left-pad'
Review before you connect — the maintainer has deprecated this package)." Every line leads
with one of three answers — **Safe to connect**, **Review before you connect** or **Do not
connect** — and the one reason behind it, then the 0–100 score; a Certified tool reads
"Safe to connect · Certified". Ask for the pre-check and you get one such line per server
and per dependency, with its report link. From then on, a server you add with `claude mcp
add` is checked before it is added. On Do not connect, Claude Code asks before you install
it, and stops calls to a server that's already connected, unless you allow that server.
"Review before you connect" just tells you. Dependencies are read from the session's folder (the `cwd` Claude Code hands the hook). In Claude Desktop's Code tab, which starts in a scratch workspace, move into the project and type `/clear`: the hook runs again for that folder.

The servers your other plugins bring are checked too. In a folder with nothing of its own
(no project, or your home folder), the hook says once a day what your own servers read,
for example "AgentAvow: your 3 tools are fine — all Safe to connect."

Check whether a tool is safe before your agent connects to it. AgentAvow scans an MCP
server, a package, or a GitHub repo and returns one of three answers with its reason,
then two scores underneath: a 0–100 trust score with the findings behind it, and an adoption score
built from real usage (downloads, stars, installs). Every result is signed (Ed25519) and
can be verified offline, so you do not have to take AgentAvow's word for it.

Scanning is free and needs no account.

**Cost to Claude:** zero tokens per check (the hooks run as scripts on your machine, and Safe says nothing), and under 1,000 tokens a session for the connector's tool names and instructions, the command and the skill. Run `/context` with the plugin on and off to see it.

## What the plugin adds

| Component | What it does | Where it runs |
| --- | --- | --- |
| MCP connector | The AgentAvow tools: `scan_mcp_server`, `scan_package`, `scan_repo`, and identity lookups. All read-only, no sign-in. | Chat, Cowork, Claude Code |
| Scan command | Ask in plain words ("scan npm chalk", "is this MCP server safe?"), or use the command: `/agentavow-trust:scan npm chalk`, `/agentavow-trust:scan owner/repo`, `/agentavow-trust:scan https://mcp.example.com/mcp`. Claude Code puts the plugin's name in front of plugin commands, so a plain `/scan` is not found. | Chat, Cowork, Claude Code |
| `scan-before-connect` skill | When you ask Claude to add an MCP server or install a package you name, Claude scans it first and tells you the answer before it goes ahead. | Chat, Cowork, Claude Code |
| Install-time hook | When a server is about to be added (`claude mcp add …`, or a write to `.mcp.json`), grades it first. "Do not connect": Claude Code asks you, with the answer as the reason. Anything else (Safe to connect; Review before you connect; not scannable): a one-line answer and the add proceeds. Never denies. | Claude Code, Cowork |
| Package installs | When Claude runs `npm`/`pnpm`/`yarn`/`bun` add or install, `pip`/`python -m pip` install, `uv add`, `uv pip install`, `pipx install` or `poetry add` with named packages (up to 5 per command; with more, it asks first and names the ones it did not check), each is checked against its stored grade. Safe to connect: silent, unless part of the package could not be read (a file past the read cap or past the unpack budget), which gets one quiet note. Deprecated by its maintainer: a one-line note that it is deprecated (not a security finding). Review before you connect: a one-line note and the install proceeds. Do not connect: Claude Code asks you first. Lockfile installs (`npm install`, `npm ci`, `uv sync`), requirements files, local paths and repository or URL installs are left alone; a package AgentAvow could not grade (not found, not scannable, or the service is busy) gets a one-line "not checked" note; an offline or slow check stays silent. The next session start mentions once how many installs were checked. Turn it off with `AGENTAVOW_INSTALL_CHECKS=off`. | Claude Code, Cowork |
| SessionStart hook | At the start of a session, grades each MCP server this session can use (user scope, this project, and the servers your installed plugins bring) that it has not seen before, and the project's direct dependencies: package.json `dependencies` (or `devDependencies` when there are none), requirements.txt, pyproject `[project].dependencies`, and Cargo.toml `[dependencies]` (Rust crates). In a workspace root with no manifest of its own, it reads the manifests one folder down (up to 5 sub-projects; never in your home folder). Up to 8 dependencies per start, re-graded only when the declared version changes; `AGENTAVOW_PRECHECK_DEPS=off` turns the dependency pass off. A server whose check has no answer within the start's time limit (a first scan can take a minute or more) is named as still being checked and asked about again at the next start until its answer shows (at most 5 starts or 24 hours; then it is reported once as "not checked: check timed out" and checked again in a week). Servers for other projects are counted and graded when you open them. Claude opens its first reply with a one-line summary (how many Safe / Review / Don't connect, the one needing attention), and keeps one line per server and dependency for when you ask. Dependencies are already installed: their answer is advice, never a stop. | Claude Code, Cowork |
| PreToolUse gate | Before each MCP tool call, checks the answer on file for that server. Stops a call to a server whose answer is "Do not connect" (and, as before, one in the blocked tier), unless you allowed that one server; asks before a tool whose definition changed since it was scanned. "Review before you connect" never prompts. | Claude Code, Cowork |

When a server, package or dependency is pinned to an exact version (`npx -y name@1.2.3`,
`npm install name@1.2.3`, `pip install name==1.2.3`, `uvx name@1.2.3`, `uvx --from
name==1.2.3 …`, or an exact version in package.json or requirements.txt), the hooks grade
that version, not the latest one. A range or a tag (`^1.2`, `>=1`, `latest`, `next`) is
graded at the latest version.

The session-start hook and the skill warn; a low score adds context and you decide.
The gate is the one part that can stop a call, and by default only for a server whose
answer is "Do not connect" (a critical finding, a planted credential leaving the sandbox,
a known-malicious package) or that is graded in the blocked tier (0 to 10 out of 100). A
changed definition asks; it never denies.

The hooks start through a small `sh` launcher (`scripts/run_hook.sh`) that uses the first
working Python 3 it finds: `python3`, then `python`, then `py -3` (Windows). If none works,
the hook does nothing and the session carries on.

## Per-call gate

`scripts/agentavow_pretool_gate.py` runs before each MCP tool call (tool names look
like `mcp__<server>__<tool>`). It reads the grade the session-start hook stored for
that server and:

- **denies** the call when the server's answer is "Do not connect", or its grade is in
  the `blocked` tier, unless you allowed that server (below). The reason leads with the
  answer, gives the score and the report link, and says how to allow that one server.
- **asks** before a tool on a remote server whose definition no longer matches the one
  AgentAvow graded, or that the grade never saw. The gate fetches `tools/list` from the
  server itself, at most once per server per 15 minutes, and recomputes the per-tool
  digest the signed attestation carries. That is done offline, with no call to
  AgentAvow. A server whose definitions changed is re-graded at your next session
  start.
- **allows** everything else: a server with no grade on file, a stdio server (there is
  no served definition to re-fetch, so only its grade applies), any network error or
  timeout, any definition the gate cannot canonicalize.

It fails open. It stops within 8 seconds, and if anything goes wrong it allows the
call and says nothing.

### Allow a server you have reviewed

If you have looked at a server that reads "Do not connect" and want to use it anyway,
add one line for it to `~/.cache/agentavow/allowed-servers.txt` (create the file if it
is not there). When the gate stops the server, it shows you (not Claude) the exact line:
the server's name, the URL or package its grade is for, and a confirmation code. For
example:

```
example-server https://mcp.example.com/mcp K7Q2M-9XA3B
```

- The code is what makes the line yours. It is shown only to you, in the gate's notice;
  Claude's copy of the refusal never carries it, so a line Claude writes, by whatever
  route, allows nothing. Don't paste the code into the chat. It comes from a random key
  the gate keeps in `~/.cache/agentavow/allow.key` (readable only by you); deleting that
  file turns every allow line off, and the next refusal shows new codes.
- It allows that one server only. There are no patterns and no "allow everything": a
  line that is not exactly `<name> <graded URL or package> <code>` allows nothing. A
  line written for 0.1.37 (without a code) no longer counts; the next refusal shows the
  new line.
- It is tied to what was graded. If the server's config later points at a different URL
  or package, the old line no longer matches and the gate stops calls again.
- A changed tool definition still asks, allowed or not.
- Each session shows one note when an allowed server's tools run.
- Lines starting with `#` are comments. Delete a line to stop allowing that server.
- If you can't see the gate's notice (the VS Code extension may not show it), print the
  line yourself in your own terminal. The refusal gives the exact command for your
  install; it looks like this:

  ```
  python3 ~/.claude/plugins/.../scripts/agentavow_pretool_gate.py --allow-line example-server
  ```

  It prints the line only when it runs in a real terminal (its input and its output
  both a terminal). Run from Claude's Bash tool, a pipe or a file, it refuses and
  prints no code, so Claude can't fetch the code this way either. A name with no grade
  on file is an error; use the name from the refusal.
- As a second check, if Claude tries to run a command that names AgentAvow's folder
  `~/.cache/agentavow` (or a file in it), or to write into that folder, the
  install-time hook asks you first, and so does the gate for an MCP tool call that
  names it. A Claude command that runs `--allow-line` asks too. A different folder that
  happens to be named AgentAvow, such as a checkout of this repo or the plugin's own
  install folder, does not count, and neither does a word that only contains "allow"
  (such as "shallow") in a command about another cache folder.

Settings, all optional, read from the environment and never sent anywhere:

- `AGENTAVOW_GATE_DENY_BELOW` (default: deny on "Do not connect" and the `blocked`
  tier). A number such as `51` also denies any server graded below it. A tier name
  (`restricted`, `minimal`, `standard`, `trusted`, `verified`) also denies anything
  below that tier's floor. `off` never denies, not even on "Do not connect"; a changed
  definition still asks.
- `AGENTAVOW_GATE_RECHECK_SECONDS` (default `900`). How often a remote server's
  `tools/list` is re-fetched to check for a changed definition.
- `AGENTAVOW_GATE=off` turns the gate off. Uninstalling the plugin removes it.

## Try it

Ask Claude to "scan npm chalk", or run:

```
/agentavow-trust:scan npm chalk
```

Then add an MCP server and start a new session. The hook reports a line such as:

```
⚠️ MCP 'example' (https://mcp.example.com/mcp): Review before you connect — one high finding: shell command built from user input · AgentAvow 66/100.
```

## Works in Codex too

The same plugin runs in OpenAI's Codex (CLI and desktop app):

```
codex plugin marketplace add AgentAvow/AgentAvow
codex plugin add agentavow-trust@agentavow
```

Codex asks you to review the plugin's hooks before they run: at the next start it
shows "Hooks need review"; pick "Trust all and continue" (or use `/hooks`). It asks
again after each plugin update. Until you trust them, only the connector and the
skill work, and `codex exec` skips untrusted hooks without a word.

In Codex the session-start check reads the servers in `~/.codex/config.toml` (and a
trusted project's `.codex/config.toml`), and the install check watches
`codex mcp add <name> --url <url>`, `codex mcp add <name> -- <command>` and the package
installs listed above. Codex hooks cannot ask, so where Claude Code asks, Codex stops
the step and says why, with the report and how to go ahead anyway (run it yourself in
your own terminal outside Codex, or switch AgentAvow's hooks off in `/hooks`). Review
before you connect is still a one-line note.

## The sandbox result in the line

AgentAvow runs every npm and PyPI package it grades in an isolated gVisor sandbox on its own
servers (automatically, on the first scan; results are kept for a day). The hook's line
includes that result in one clause when it exists:

- `sandbox: called 9 tools, network only api.example.com`: the server started, its tools
  were called with synthetic inputs, and these are the hosts it reached (package
  registries left out).
- `sandbox: CAUGHT a read-only tool writing files (high)`: the run observed a behavior
  worth reviewing; a planted credential leaving the sandbox is always listed first.
- `sandbox: not started (needs a database URL)`: the server needs a credential or a
  startup argument the sandbox does not have, so its tools were not called. This is not
  a finding.
- `sandbox: running now, results in about a minute`: the first run is still in progress.
  The answer is provisional until it lands ("…; sandbox still running") and may move to
  "Review before you connect".

The hook makes no extra request for it and nothing from your machine is run in the
sandbox. The `/agentavow-trust:scan` command and the scan-before-connect skill report the full sandbox
observation (tools called, network, file writes, credentials) as its own section.

## What the hook reads and what leaves your machine

What leaves your machine: the server URL or package name being checked, and a random
install ID, a code made up once on your machine that isn't tied to you, your account or
your files. Once a day the session-start hook also sends that install ID with the plugin
version and the app type (desktop, CLI, SDK or cloud), and nothing about your tools or
code, so we can count how many machines the plugin protects. To turn both off, set
`AGENTAVOW_ANON_ID=off`.

The hooks are three Python scripts, `scripts/agentavow_precheck.py` (session start),
`scripts/agentavow_pre_install.py` (install time) and `scripts/agentavow_pretool_gate.py`
(per call), started by the `scripts/run_hook.sh` launcher. They use only the standard
library and you can read all of them.

**The session-start hook reads**, looking only for `mcpServers` entries:
`~/.claude.json`, `.mcp.json` in the current folder, `.claude/settings.json` and
`.claude/settings.local.json` in the current folder, and the plugins Claude Code has
installed for you: `~/.claude/plugins/installed_plugins.json`, the `enabledPlugins` list
in `~/.claude/settings.json` (a plugin you switched off is skipped), and each installed or
account-synced plugin's `.claude-plugin/plugin.json` and `.mcp.json`. From each server
entry it takes the server URL, or the launcher command and package name. It does not use
headers, environment values, tokens, or any other part of those files. For dependencies
it reads `package.json`, `requirements.txt`, `pyproject.toml` and `Cargo.toml` in the
current folder, or one folder down in a workspace root with none of its own.

**It sends** one HTTPS request per new server or dependency to
`https://agentavow.com/api/v1/public/scan`, containing either:

- the server URL reduced to scheme, host, and path (any `user:password@` part, query
  string, and fragment are removed first), or
- a package name and its registry (npm, PyPI or crates.io).

Each of those requests also carries the install ID, as the `X-AgentAvow-Install`
header: a random UUID made once, with Python's `uuid.uuid4()`, and kept in
`~/.cache/agentavow/install_id` (readable only by you). Nothing about you, your
machine or your files goes into it. AgentAvow keeps only a one-way hash of it, for each
day it was seen, for 40 days, and never with your IP address. With
`AGENTAVOW_ANON_ID=off` the file is not made and the header is not sent. The
install-time hook sends the same header on its requests; the gate sends nothing to
AgentAvow, so it never sends it.

**Once a day** (the first session start of each UTC day, even when there is nothing new
to check) the session-start hook sends one more small request, a POST to
`https://agentavow.com/api/v1/public/plugin/active` with the same install ID header and
a body of `{"version": "0.1.45", "app": "desktop"}`: the plugin version and the app
type, one of `desktop`, `cli`, `sdk`, `cloud` or `other`, read from Claude Code's
`CLAUDE_CODE_ENTRYPOINT`. No tool, server, path or repo name goes in it. It lets
AgentAvow count the machines the plugin protects, including the many days the hook
answers from its cache and sends nothing else. The day it was sent is kept in the
hook's cache file so it never goes twice in a day; it waits at most 2 seconds, runs
beside the check, prints nothing, and a failure is simply skipped. `AGENTAVOW_ANON_ID=off`
turns it off too.

**It does not send:**

- servers on localhost, a private network, or a `.local` / `.internal` name;
- any URL whose path looks like it contains a secret (a UUID or a long token). These
  are reported as "not scanned";
- any URL that still holds a `${...}` placeholder (the hook never reads the environment
  to fill it in);
- servers that run a local script (`node server.js`, `python server.py`), which have
  no published package to grade;
- AgentAvow's own connector;
- anything else from your machine. No file contents, environment values, or credentials.

**It writes** `~/.cache/agentavow/install_id` once (see above) and `~/.cache/agentavow/scanned.json`, so each server is scanned
once: per server, the score, tier and grade, the signed per-tool digests, the report
link, and when it was scanned. A server AgentAvow cannot read (one that needs sign-in,
for example) is reported once and retried after a week. A server still being checked
is kept as its id, when it was first asked about and how many times, never as a grade.
Delete the file to scan
everything again.

**The gate reads** the same config files, for the URL and any `Authorization` header
of the one server being called, your allow list `~/.cache/agentavow/allowed-servers.txt` and its key
if they exist, plus its own `AGENTAVOW_GATE*` settings from the
environment. **It sends** one short `initialize` + `tools/list` exchange to that
server, over the URL in your config (`user:password@` and `#fragment` removed), with
the configured `Authorization` header if there is one, as Claude Code itself does when
it connects. A header that still holds a `${...}` placeholder is not expanded and not
sent. Nothing goes to AgentAvow, and the header is never written to the cache or
printed. The gate writes the digests it last saw to the same cache file; the graded
digests are never overwritten by it. It never writes the allow list. The first time it
stops a server it creates `~/.cache/agentavow/allow.key`, a random key readable only by
you that the confirmation codes come from; the key never leaves your machine. Run by
you with `--allow-line <name>`, it reads the cache file and that key (creating the key
if needed), prints one line to your terminal, and sends nothing.

The first time the hook finds nothing to scan (no MCP servers it can grade and no
manifest), it shows one line saying so and how to scan a tool on demand. That line is
shown once per machine, is recorded in the same file, and makes no request. The "your N
tools are fine" line is built from the same file, at most once a day, and makes no
request either.

If the network is down or anything unexpected happens, every hook prints nothing and
exits cleanly. The session-start hook cannot stop a session from starting. The gate
refuses a call only when the server's answer on file is Do not connect (or its score is
below `AGENTAVOW_GATE_DENY_BELOW`, the Blocked tier by default) and you have not allowed
that server, and asks before a tool whose definition changed since it was checked.

The MCP connector sends AgentAvow only the target you ask it to scan. Its URL carries
`?via=plugin`, which tells AgentAvow the connection came through this plugin (so we can
count plugin installs apart from connectors added by hand); it carries nothing about you
or your machine. Scan results for public tools are public.

## Privacy and support

- Privacy policy: https://agentavow.com/legal/privacy
- How scoring works: https://agentavow.com/docs/how-grading-works
- Verify a result yourself: https://agentavow.com/docs/verify-attestations
- Questions or problems: support@agentavow.com
- Security issues: security@agentavow.com, see `SECURITY.md`

## License

MIT. See `LICENSE`.
