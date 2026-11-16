# Yaptake for coding agents

Edit video for every feed (9:16, 4:5, 1:1 or 16:9) in a native Mac app with a transcript, captions and timeline. Local tools let coding agents work on the same project.

This package teaches a coding agent to edit a saved Yaptake project through
the local `yaptake` command. The CLI works on local projects; your agent's
own model and data settings determine what it sends to its model.

## Set up Yaptake

[Download Yaptake](https://yaptake.com) for Apple Silicon and macOS
26.0 or newer. This package supports version 0.1.0
(build 231). In the app, choose **Help → Use with Coding Agents…** to
set up your agent and the command line.

Install this package through your agent's skill or plugin installer. The
[setup guide](https://yaptake.com/docs/agents) explains the supported connections.

## Make an edit

Open a saved project in Yaptake, give your agent its project folder, and ask:

> Remove filler words and shorten long pauses. Validate the edit before
> applying it, then preview the changed passage so I can review the cut.

The agent reads the transcript, checks its proposed edit and applies it as
one undo step. You can review the result in Yaptake. Export when you are
ready; the app's export allowance applies.

For commands and the editable transcript format, see the [CLI
reference](https://yaptake.com/docs/cli) and [editing
reference](https://yaptake.com/docs/agent-requests).

## License

The skill and integration files in this package use the MIT license.
The Yaptake application has its [own license and terms](https://yaptake.com/terms).

## Add the skill to an agent

Set up the product as described above, then install its integration files.

For Codex CLI:

```sh
codex plugin marketplace add https://github.com/hraness/product-skills.git
codex plugin add yaptake@hraness-products
```

In Claude Code:

```text
/plugin install yaptake --marketplace hraness/product-skills
```

A Cursor team marketplace administrator can import
`https://github.com/hraness/product-skills`, then select this product. See
[Cursor's repository import instructions](https://cursor.com/docs/plugins#add-a-team-marketplace).
These repository installs are separate from public directory approval.
