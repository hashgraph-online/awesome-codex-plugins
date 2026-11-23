# OH for coding agents

Supervise Claude Code and Codex sessions in a native Mac app, share one Vercel Board, and pair machines over Cloudflare Tunnel.

This package teaches a coding agent to inspect, spawn, and steer supervised
Claude Code and Codex sessions through the local `oh-router` command,
coordinate tasks on a shared Vercel Board, and generate multi-machine pairing
recipes.

## Set up OH

[Download OH](https://oh.computer) for Apple Silicon and macOS
15.0 or newer, or install with `brew install --cask hraness/tap/oh`.
This package supports version 0.2.0 (build 6). In the app, choose
**Help → Use with Coding Agents…** to link `~/.local/bin/oh-router` and install
the skill.

Read the [setup guide](https://oh.computer/docs/agents) and
[CLI reference](https://oh.computer/docs/cli) for all commands and
routing options.

## License

The skill and integration files in this package use the MIT license.
The OH application has its [own terms](https://oh.computer/terms).

## Add the skill to an agent

Set up the product as described above, then install its integration files.

For Codex CLI:

```sh
codex plugin marketplace add https://github.com/hraness/product-skills.git
codex plugin add oh@hraness-products
```

In Claude Code:

```text
/plugin install oh --marketplace hraness/product-skills
```

A Cursor team marketplace administrator can import
`https://github.com/hraness/product-skills`, then select this product. See
[Cursor's repository import instructions](https://cursor.com/docs/plugins#add-a-team-marketplace).
These repository installs are separate from public directory approval.
