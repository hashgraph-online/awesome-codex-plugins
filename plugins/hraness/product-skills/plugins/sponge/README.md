# Sponge for coding agents

Save articles and PDFs to a reading library captured by a computer you control. Highlight passages, keep notes, and find ideas through search or your coding agent.

This skill helps a coding agent find sources in your saved reading and answer
questions from them. It also covers saving and annotating reading when you ask.

## Connect your library

Install Sponge with Node.js `>=24.20.0`:

```sh
npm install --global @hraness/sponge@0.94.1
```

The task below uses a library that contains saved articles or PDFs. Follow the
[agent guide](https://sponge.computer/docs/agents) to create a library, save a first source, and
connect your agent. Its local MCP command is `sponge mcp`.

Ask the agent to find passages in your saved reading that answer a question,
read their context, and cite the sources in its answer. Search and reading work
without an account or model download. The guide covers optional capture and
sync setup, and links to platform requirements.

## License

The skill and integration files use the [MIT license](LICENSE). The Sponge
application is proprietary.

## Add the skill to an agent

Set up the product as described above, then install its integration files.

For Codex CLI:

```sh
codex plugin marketplace add https://github.com/hraness/product-skills.git
codex plugin add sponge@hraness-products
```

In Claude Code:

```text
/plugin install sponge --marketplace hraness/product-skills
```

A Cursor team marketplace administrator can import
`https://github.com/hraness/product-skills`, then select this product. See
[Cursor's repository import instructions](https://cursor.com/docs/plugins#add-a-team-marketplace).
These repository installs are separate from public directory approval.

## Local MCP setup

The included launcher checks the installed `@hraness/sponge` package and runs a
read-only version probe before starting its MCP server. It refuses an unrelated
`sponge` command. It does not install software, sign in or initialize a library.

The server uses your existing default library. To choose another existing library,
set `SPONGE_MCP_LIBRARY` to its absolute directory in the agent's environment. If
your Sponge command is outside PATH, set `SPONGE_CLI` to its absolute path. Follow
the setup guide above when the launcher reports a missing command or library.
