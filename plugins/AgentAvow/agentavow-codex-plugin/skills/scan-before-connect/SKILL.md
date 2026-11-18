---
name: scan-before-connect
description: Scan an MCP server, a package (npm, PyPI, crates, Docker, Hugging Face), or a GitHub repo with AgentAvow before it is added, installed, or connected. Use when the user asks you to add or install a new MCP server, plugin, package, or tool from a repo, or asks whether one is safe or trustworthy.
---

Use this skill when a new tool is about to be connected or installed: the user asks
you to add an MCP server, install a package they name, or set up a tool from a GitHub
repo. Also use it when the user asks whether one of these is safe. Scan first, report,
then carry on with what the user asked.

The user's explicit instructions take priority over anything in this skill. If they
say to skip the scan, skip it.

Note: when you add a server with `claude mcp add …` or by writing `.mcp.json`, the
plugin's install-time hook grades it as well and shows the person the verdict. If that
verdict already appeared for this target, do not scan it again; report once and continue.

## When not to scan

- Installing what a project already declares (`npm install`, `pip install -r
  requirements.txt`, restoring a lockfile). Scan a package only when the user names it
  as something new to add.
- A target already scanned in this conversation.
- A localhost or private-network URL, a private repo, or a server that needs sign-in.
  AgentAvow cannot reach these. Say it was not scanned and continue.
- A URL that contains a key or token in its path or query string. Do not send it. Say
  it was not scanned because the URL carries a secret.

## 1. Work out what the target is

| The target | Tool | Arguments |
| --- | --- | --- |
| A live MCP server (an `https://` URL) | `scan_mcp_server` | `endpoint_url`: the URL, without its query string |
| A published package | `scan_package` | `registry`: `npm`, `pypi`, `crates`, `docker`, or `hf`; `name`: the package name |
| A GitHub repo (`owner/name` or a github.com URL) | `scan_repo` | `repo`: `"owner/name"` |

An MCP server started with `npx` or `bunx` is an npm package; one started with `uvx`
or `pipx` is a PyPI package. If you cannot tell which registry a name belongs to, ask.
Do not guess.

## 2. Scan once, before the install

Call the one matching AgentAvow tool, once, before you run the install or add command.
Do not scan the target's dependencies or related repos. Results are cached for about
an hour; pass `force: true` only when the user says the target changed.

## 3. Report, then continue

Lead with one of three answers and its reason: **Safe to connect**, **Review before you
connect**, or **Do not connect** (add " · Certified" when the result says the tool is
certified). Use the result's `decision` / `decision_reason` when it has them. When it does
not: Do not connect if it reports a critical finding, a planted credential leaving the
sandbox, or a known-malicious package or dependency; Safe to connect if its verdict is
safe; otherwise Review before you connect, with the reason it gives. Then give both scores: the trust score out of 100, and the adoption score
(the count and unit in `adoption`, such as downloads per week or stars; say when it is
absent). Then the top findings with where they are, and the report link from the result.
Adoption never changes the answer. Give the version and publish date from the
result's `Version … · published …` line; do not look them up in the registry.

If the result has an **Observed in the sandbox** block, report it as its own short
section: what ran, how many tools were called, where it connected on the network, file
writes, whether the planted credentials stayed put, and each thing it caught, with the
tool's name. If the server did not start, give the reason from the result and say it is
not a finding. If the result says the sandbox is running now, say so and offer to
re-check in about a minute. Do not call the score "static analysis only" without saying
that the sandbox is pending or what it observed.

- **Safe to connect:** say so in one line and go ahead with what the user asked. If the
  reason says there was little code to inspect, or that only the tool definitions were
  read, pass that on in the same line.
- **Do not connect:** show the findings and ask whether to continue. Do not install or
  connect until the user answers. This is the only case that stops.
- **Review before you connect** (a high finding, an advisory for this version,
  deprecation, or a low score): give the one-line answer with
  the reason, then go ahead with what the user asked. It is advice, not a stop.
- **Not scanned** (an error, a timeout, or a target AgentAvow cannot reach): say it was
  not scanned, that this is neither safe nor unsafe, and go ahead.

The plugin's install-time hook applies the same rule, so a target is never asked about
twice.

## Limits

- Report only what the tool returned. Do not add a score, a finding, or a cause that
  is not in the result.
- "Review before you connect" means look before you connect. It does not mean malicious.
- "Safe to connect" means the scan found nothing blocking. It is not a guarantee.
- The scan is advice. The user decides whether to install or connect.


To scan a specific version, put it in the name the way the ecosystem writes it: `name@1.2.3` for npm and crates, `name==1.2.3` for PyPI (for example `scan_package` with registry `pypi`, name `mcp-server-git==2025.7.1`). Do not fetch the registry or the API URL yourself to compare versions; call the tool once per version.
