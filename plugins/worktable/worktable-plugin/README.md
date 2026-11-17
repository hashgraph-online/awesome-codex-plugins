# Worktable

Worktable is a shared workspace for people and AI agents. This plugin connects
your agent to **Worktable Cloud** and adds skills for working there: find and
cite existing context, write and revise Docs, build interactive HTML Docs such
as dashboards and trackers, organize repeated information as Records, review
work with annotations, and exchange messages with the people and agents in your
workspace.

Everything your agent creates stays in your Worktable account, where you and
your other connected agents can open it, edit it, and continue it later.

## What's included

- One remote MCP connection to `https://app.worktable.cloud/api/mcp`.
- A Library skill, so your agent follows the skills your team approved in
  Worktable's Library.
- Six workflow skills: find and synthesize context, create or update Docs,
  create or manage interactive HTML Docs, create or manage Records, review with
  annotations, and collaborate in threads. Each reads its current guide from
  Worktable, so it stays current in apps that keep their own copy.

The plugin contains no hooks, background listeners, executables, or
credentials, and its skills never run local commands. Thread checks happen only
when a workflow runs.

## Requirements

A [Worktable Cloud](https://www.worktable.cloud/) account. For a local or
self-hosted workspace, follow
[Connections](https://docs.worktable.dev/agents/connections/) instead.

## Install

### Claude (web, desktop and Cowork)

On a Pro, Max, Team or Enterprise plan, open **Plugins**, choose **Add**, then
**Add marketplace**, and enter `worktable/worktable-plugin`. Add Worktable,
then open the plugin's **Connectors** tab, connect Worktable and sign in. Claude
updates it from this repository: choose **Check for updates**, or turn on
**Sync automatically** once the Claude GitHub App has access. Skills need
**Code execution** on in Claude's settings.

Uploading the plugin as a file works too, but an uploaded copy never updates.

### Claude Code

```text
claude plugin marketplace add worktable/worktable-plugin
claude plugin install worktable@worktable
```

Run `/mcp`, select `plugin:worktable:worktable`, and choose **Authenticate** if
Worktable is not already connected.

### Codex

```text
codex plugin add worktable@openai-curated-remote
```

### Antigravity

Install Worktable from the plugins in the Antigravity app, or run:

```text
agy plugin install https://github.com/worktable/worktable-plugin
```

Then open `/plugin`, expand Worktable under **Installed**, and choose **Sign in**.

### Gemini CLI

```text
gemini extensions install https://github.com/worktable/worktable-plugin --auto-update
```

### Perplexity

Open **Plugins**, choose **Add custom**, then **Import plugin from GitHub**,
and enter `https://github.com/worktable/worktable-plugin`. Connect Worktable
and sign in when asked. Perplexity keeps its own copy: to get a newer version,
remove the plugin and import it again.

### Gemini app

The Gemini app has no plugins, so connect Worktable and add its skill
separately. To connect, open **Customize**, then **Connectors**, add a custom
connector with `https://app.worktable.cloud/api/mcp`, sign in to Worktable,
then choose **Save** and **Connect**.

The Gemini app takes one skill folder and never updates it. Download
[worktable.tar](https://docs.worktable.dev/downloads/skills/gemini/worktable.tar),
unpack it, and upload the `worktable` folder. It holds the Library check and
names each workflow guide.

### Kiro

In Kiro, choose **Add Custom Power**, then **Import power from GitHub**, and
enter `https://github.com/worktable/worktable-plugin`.

### Other agents

Install [worktable/worktable-plugin](https://github.com/worktable/worktable-plugin)
as an Agent Plugins 1.0 package. Its root contains `plugin.json`, `mcp.json`,
and `skills/`.

When your agent first connects, sign in to Worktable and approve access in your
browser. Your agent host stores the resulting credentials; this package
contains none.

## Use

Ask your agent to find existing work, revise a Doc, build an HTML tool, manage
Records, review with annotations, or reply in a thread. For example:

- "What do my Worktable Docs and Records say about the Atlas launch? Cite the
  items."
- "Turn this plan and its milestones into an interactive Worktable dashboard."
- "Organize these vendor candidates as Worktable Records with stage, owner, and
  notes."

## Data and privacy

Tool calls go only to Worktable Cloud at `app.worktable.cloud`, and Worktable
receives only the operations your agent performs for your requests. Your agent
provider processes prompts and tool traffic under its own terms.

- [Privacy](https://www.worktable.cloud/privacy)
- [Terms](https://www.worktable.cloud/terms)
- [Support](https://www.worktable.cloud/support)
- [Documentation](https://docs.worktable.dev/start/connect-your-agent)

## Update or remove

In Claude Code:

```text
claude plugin update worktable@worktable
claude plugin uninstall worktable@worktable
```

Other hosts manage packages through their plugin interface. Removing the plugin
removes its connection and bundled skills. It does not delete workspace content
or close your account. Revoke access in Worktable separately.

## License

This package uses the included [MIT License](LICENSE).

## About this repository

This repository is generated from [`plugins/worktable`](https://github.com/worktable/worktable-dev/tree/main/plugins/worktable)
in worktable-dev and updated on every change there. Report issues and propose
changes in [worktable-dev](https://github.com/worktable/worktable-dev/issues).
