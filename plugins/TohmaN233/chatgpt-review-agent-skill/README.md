# ChatGPT Agent for Codex

[English](README.md) | [简体中文](README.zh-CN.md)

> Four focused roles. Three clear routes. Keep ChatGPT connected to the work in Codex.

Use ChatGPT as a **reviewer, advisor, editor, or implementer** in your Codex workflow. Send a bounded ZIP packet when that is enough, connect a local workspace with MCP when you want direct access, or work against an authorized GitHub ref.

## Work with the right role and route

- **Configure MCP with the setup Skill.** It prepares the Bridge runtime and platform prerequisites, then configures one Bridge and Connector for the selected workspace. Choose a Cloudflare Named Tunnel when you have a Cloudflare-managed domain; without one, use a Quick Tunnel that updates the same workspace Connector when its address changes.
- **Choose a role for the task.** Get review and verification, reasoning and planning, prose editing, or software implementation from focused role instructions.
- **Choose a route for the source.** Use ZIP for local files without MCP setup, MCP for direct access to one configured workspace, or the authorized GitHub route for a remote repository or PR. ZIP and MCP remain independent choices; neither silently switches to the other.

## Install

Add the Codex marketplace and install the plugin:

```bash
codex plugin marketplace add TohmaN233/chatgpt-review-agent-skill
codex plugin add chatgpt-agent@chatgpt-agent
```

In the Codex app, open **Plugins → Add Marketplace**, enter `TohmaN233/chatgpt-review-agent-skill`, then install **ChatGPT Agent**. Start a new chat after installation.

Plugin installation adds its packaged Skills and resources. It does not download or start the MCP Bridge. Start with `$chatgpt-agent-setup`; ZIP is the default, and MCP is configured only when you explicitly choose it.

To install the Skills separately with the Skills CLI, run:

```bash
npx skills add TohmaN233/chatgpt-review-agent-skill --skill chatgpt-agent --skill chatgpt-agent-setup
```

From a local checkout, `setup.cmd` on Windows and `bash setup.sh` on macOS/Linux install only the Skills. The Python helpers use only the Python standard library; they require no `pip` packages or Python lockfile.

## Choose a role

| Role | Use it to… |
| --- | --- |
| `reviewer` | Find actionable issues in code, research, or writing; verify claims and acceptance criteria against evidence. |
| `advisor` | Answer a reasoning question, compare options, or build a bounded plan. |
| `editor` | Revise prose and documents while preserving the author's intent and voice. |
| `implementer` | Change software behavior or source code within the selected route's write permissions. |

Examples:

```text
$chatgpt-agent Review these changes for correctness and regressions.
$chatgpt-agent Compare the migration options and recommend a plan.
$chatgpt-agent Edit docs/guide.md for a first-time user.
$chatgpt-agent Implement the requested change and report what you verified.
```

## Choose a route

| Route | Best for | Access and output |
| --- | --- | --- |
| **ZIP** (default) | A local task that can be answered from selected files | Codex builds a bounded packet and sends it to ChatGPT. No MCP or Connector setup is needed. ChatGPT can return an answer or patch; Codex applies local changes. Works with ChatGPT Pro models when included in your subscription. |
| **MCP** (opt in) | Direct ChatGPT access to one local workspace | A workspace Connector reads local files. Sessions start read-only; requested report or source writes need the appropriate task-scoped grant. ZIP remains available for other tasks. |
| **GitHub (beta)** | A remote repository, branch, or PR | Uses the authorized GitHub host integration and a pinned source revision. Review is read-only; implementation targets an authorized task branch. |

For MCP, the setup Skill prepares the Bridge package and missing prerequisites. If you have a Cloudflare-managed domain, choose a Named Tunnel for a stable address. If you do not, choose a Quick Tunnel; when its address changes after a restart, setup updates that workspace's existing Connector. A user-managed HTTPS endpoint can also be reused. ChatGPT or Cloudflare sign-in may require your participation.

## How the roles and routes fit together

Choose the role by the result you want and the route by where the evidence lives. The reviewer can review a ZIP packet, the configured local workspace, or a GitHub PR. The advisor can reason over a packet or plan from local/GitHub evidence. The editor and implementer can return bounded patches in ZIP mode or make authorized changes through MCP or a GitHub task branch.

## More

- [ZIP packet workflow](docs/workflows/PACKET.md)
- [MCP local workspace tasks](docs/workflows/LOCAL.md)
- [GitHub routes](docs/workflows/GITHUB.md)
- [MCP setup](docs/setup/ONE_COMMAND.md)
- [Route model](docs/ROUTE_MODEL.md)

MIT License · Maintained by [@TohmaN233](https://github.com/TohmaN233).
