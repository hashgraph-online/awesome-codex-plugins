<div align="center">

<img src="docs/assets/logo.svg" alt="RepoBrain" width="140"/>

# RepoBrain

Cross-IDE repository knowledge engine for grounded codebase Q&A.

<sub>Formerly known as <b>Antigravity Workspace Template</b> — same project, new name.</sub>

**English** · [中文](README_CN.md) · [Español](README_ES.md)

[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/study8677/repobrain/test.yml?style=flat-square&label=CI)](https://github.com/study8677/repobrain/actions)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Docs-3B82F6?style=flat-square&logo=gitbook&logoColor=white)](https://deepwiki.com/study8677/repobrain)
[![NLPM](https://img.shields.io/badge/NLPM-audited-7C3AED?style=flat-square)](https://github.com/xiaolai/nlpm-for-claude)
[![Stars](https://img.shields.io/github/stars/study8677/repobrain?style=flat-square&color=F59E0B)](https://github.com/study8677/repobrain/stargazers)

<img src="docs/assets/demo.gif" alt="rb-ask demo — ask your codebase, get grounded answers with file paths and line numbers" width="800"/>

</div>

<div align="center">

<p><strong>🚀 实测推荐:</strong> <a href="https://teamorouter.com/?i=e188641773">TeamoRouter</a> —— 非广告，我自己在 Codex、Claude Code 等 AI 编程工具里高强度使用：一个 API Key 接入 Claude、GPT-5.5 等，模型价格方便调整，价格优惠，并没有掺水的情况。接入指南见 <a href="https://github.com/xixiaoyao/openrouter-api-key">openrouter-api-key</a>。</p>

</div>

RepoBrain helps you understand an unfamiliar repository, trace an implementation,
and ask questions with source-file references. It keeps project knowledge in
`.repobrain/`, shared across supported IDEs and agents.

## Project Philosophy

**Cross-IDE repository knowledge engine for grounded codebase Q&A.** Same `.repobrain/` knowledge layer reads in every IDE; one engine, every host.

> An AI Agent's capability ceiling = **the quality of context it can read.**

`rb-refresh` deploys a multi-agent cluster that autonomously reads your code — each module gets its own Agent that generates a knowledge doc. `rb-ask` routes questions to the right Agent, grounded in real code with file paths and line numbers.

**Instead of handing Claude Code / Codex a repo-wide `grep` and making it hunt on its own, give it a ChatGPT for your repository.**

```
Traditional approach:              RepoBrain approach:
  CLAUDE.md = 5000 lines of docs     Claude Code calls ask_project("how does auth work?")
  Agent reads it all, forgets most   Router → ModuleAgent reads actual source, returns exact answer
  Hallucination rate stays high      Grounded in real code, file paths, and git history
```

<details>
<summary><b>Four concrete failure modes RepoBrain fixes</b> — click to expand</summary>

| Problem | Without RepoBrain | With RepoBrain |
|:--------|:-------------------|:-----------------|
| Agent forgets coding style | Repeats the same corrections | Reads `.repobrain/conventions.md` — gets it right the first time |
| Onboarding a new codebase | Agent guesses at architecture | `rb-refresh` → ModuleAgents self-learn each module |
| Switching between IDEs | Different rules everywhere | One `.repobrain/` folder — every IDE reads it |
| Asking "how does X work?" | Agent reads random files | `ask_project` MCP → Router routes to the responsible ModuleAgent |

Architecture is **files + a live Q&A engine**, not plugins. Portable across any IDE, any LLM, zero vendor lock-in.

</details>

Read the full [project philosophy](docs/en/PHILOSOPHY.md).

## Quick Start

Ask an AI assistant that can run commands in your project to install RepoBrain:

> Read [AI_INSTALL.md](https://github.com/study8677/repobrain/blob/main/AI_INSTALL.md) and follow it to install RepoBrain in this project.

The guide installs the tools, configures a model backend, then builds the knowledge
base and checks an answer. A logged-in headless CLI such as Trae can serve as the
backend without an API key; an OpenAI-compatible API is also supported. Requirements:
Python 3.10+, Git with at least one commit, and a clean worktree before refresh.

For platform-specific installation or manual configuration, see
[the installation guide](INSTALL.md) and [the quick-start guide](docs/en/QUICK_START.md).
Installing RepoBrain into an existing project does not require `rb init` or `rb-init`.

## Everyday Use

Run these commands in your project directory after installation and configuration:

```bash
rb-refresh
rb-ask "How does authentication work in this project?"
```

`rb-refresh` automatically builds the first knowledge base, updates affected groups
after committed changes, or continues a matching interrupted task. If knowledge is
already current, it skips without calling a model. After a failure, run the same
command again to continue.

Use this only when you want to regenerate all knowledge:

```bash
rb-refresh --full
```

`rb-ask` reads the existing knowledge base and answers with source evidence. It
reminds you when committed code is newer; it does not refresh during a question.

Examples of useful questions:

- Where is this API implemented, and what calls it?
- How does data move from the UI to the backend?
- Which modules are affected by changing this function?

## How It Works

```text
Source code → rb-refresh → .repobrain/ knowledge → rb-ask → answer with code references
```

RepoBrain groups related code, generates module knowledge, and routes each question
to relevant context. Knowledge lives in your project, so supported IDEs share the
same base. Updates are staged separately and become active only when complete;
a failed update preserves the existing usable generation.

The first build can take several minutes or longer on large repositories and
uses your configured model. Commit or stash local changes before refreshing.
IDE rules and new-project scaffolding are optional; see [the usage reference](docs/en/USAGE.md).

## Support Matrix

| Use | Environments | How to connect |
|:----|:-------------|:---------------|
| Native plugins | Claude Code, Codex CLI | Setup, refresh, and ask via slash commands. |
| Compatible IDEs | Cursor, Windsurf, Gemini CLI, VS Code + Copilot, Cline, Aider, DeepSeek Harness | Shared context files, CLI, or an MCP client. |
| Other agents and scripts | Any host that can run commands or call MCP tools | CLI/JSON output or optional `rb-mcp`. |

Platform-specific commands, JSON output, and MCP registration are documented in
[the usage reference](docs/en/USAGE.md) and [INSTALL.md](INSTALL.md).

## Evaluation

A locked comparison on Flask, ripgrep, Vite, and Prometheus used the same source
access and model route for RepoBrain and CodeGraph + Trae. The
[full report](benchmarks/codegraph-comparison/results/latest-v2-full-report.md)
includes accuracy, query time, tokens, and cold-build cost. Results apply to that
experiment; AI knowledge generation and static graph indexing are different workloads.

## Documentation

- [Installation and troubleshooting](INSTALL.md)
- [Commands, JSON, and optional integrations](docs/en/USAGE.md)
- [Knowledge generation and Q&A architecture](docs/en/SWARM_PROTOCOL.md)
- [External MCP tools](docs/en/MCP_INTEGRATION.md) · [Sandbox configuration](docs/en/SANDBOX.md)
- [Release changes](CHANGELOG.md)
- Full documentation: [English](docs/en/README.md) · [中文](docs/zh/README.md) · [Español](docs/es/README.md)

**NLPM Audit Feedback** — Improved by [NLPM](https://github.com/xiaolai/nlpm-for-claude), a natural-language programming linter by [xiaolai](https://github.com/xiaolai).

---

## Contributing

Ideas are contributions too! Open an [issue](https://github.com/study8677/repobrain/issues) to report bugs, suggest features, or propose architecture.

## Contributors

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Lling0000">
        <img src="https://github.com/Lling0000.png" width="80" /><br/>
        <b>⭐ Lling0000</b>
      </a><br/>
      <sub><b>Major Contributor</b> · Creative suggestions · Project administrator · Project ideation & feedback</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/h13181278389">
        <img src="https://github.com/h13181278389.png" width="80" /><br/>
        <b>h13181278389</b>
      </a><br/>
      <sub><b>Core Contributor</b> · Thank you for your support, feedback, and contributions to RepoBrain</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/flyw1015">
        <img src="https://github.com/flyw1015.png" width="80" /><br/>
        <b>flyw1015</b>
      </a><br/>
      <sub><b>Core Contributor</b> · Thank you for your support, feedback, and contributions to RepoBrain</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/devalexanderdaza">
        <img src="https://github.com/devalexanderdaza.png" width="80" /><br/>
        <b>Alexander Daza</b>
      </a><br/>
      <sub>Sandbox MVP · OpenSpec workflows · Technical analysis docs · PHILOSOPHY</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/chenyi">
        <img src="https://github.com/chenyi.png" width="80" /><br/>
        <b>Chen Yi</b>
      </a><br/>
      <sub>First CLI prototype · 753-line refactor · DummyClient extraction · Quick-start docs</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/Subham-KRLX">
        <img src="https://github.com/Subham-KRLX.png" width="80" /><br/>
        <b>Subham Sangwan</b>
      </a><br/>
      <sub>Dynamic tool & context loading (#4) · Multi-agent swarm protocol (#3)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/shuofengzhang">
        <img src="https://github.com/shuofengzhang.png" width="80" /><br/>
        <b>shuofengzhang</b>
      </a><br/>
      <sub>Memory context window fix · MCP shutdown graceful handling (#28)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/goodmorning10">
        <img src="https://github.com/goodmorning10.png" width="80" /><br/>
        <b>goodmorning10</b>
      </a><br/>
      <sub>Enhanced <code>rb ask</code> context loading — added CONTEXT.md, AGENTS.md, and memory/*.md as context sources (#29)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/abhigyanpatwari">
        <img src="https://github.com/abhigyanpatwari.png" width="80" /><br/>
        <b>Abhigyan Patwari</b>
      </a><br/>
      <sub>Code knowledge graph integration for <code>rb ask</code> — symbol search, call graphs, and impact analysis</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/BBear0115">
        <img src="https://github.com/BBear0115.png" width="80" /><br/>
        <b>BBear0115</b>
      </a><br/>
      <sub>Skill packaging & KG retrieval enhancements · Multi-language README sync (#30)</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/SunkenCost">
        <img src="https://github.com/SunkenCost.png" width="80" /><br/>
        <b>SunkenCost</b>
      </a><br/>
      <sub><code>rb clean</code> command · <code>__main__</code> entry-point guard (#37)</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/aravindhbalaji04">
        <img src="https://github.com/aravindhbalaji04.png" width="80" /><br/>
        <b>Aravindh Balaji</b>
      </a><br/>
      <sub>Unified instruction surface around <code>AGENTS.md</code> (#41)</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/xiaolai">
        <img src="https://github.com/xiaolai.png" width="80" /><br/>
        <b>xiaolai</b>
      </a><br/>
      <sub><a href="https://github.com/xiaolai/nlpm-for-claude">NLPM</a> audit feedback · Skill frontmatter fixes · Dependency hygiene review (#51, #52, #53)</sub>
    </td>
  </tr>
</table>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=study8677/repobrain&type=Date)](https://star-history.com/#study8677/repobrain&Date)

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**[📚 Full Documentation →](docs/en/)**

*Built for the AI-native development era*

Friendly Link: [LINUX DO](https://linux.do/)

</div>
