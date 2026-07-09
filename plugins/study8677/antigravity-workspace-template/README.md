<div align="center">

<img src="docs/assets/logo.svg" alt="RepoBrain" width="140"/>

# RepoBrain

### Give your repo a brain 🧠 — ChatGPT for your codebase, works in Claude Code, Cursor, Codex, Windsurf & 4 more.

<sub>Formerly known as <b>Antigravity Workspace Template</b> — same project, new name.</sub>

[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/study8677/repobrain/test.yml?style=flat-square&label=CI)](https://github.com/study8677/repobrain/actions)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Docs-3B82F6?style=flat-square&logo=gitbook&logoColor=white)](https://deepwiki.com/study8677/repobrain)
[![NLPM](https://img.shields.io/badge/NLPM-audited-7C3AED?style=flat-square)](https://github.com/xiaolai/nlpm-for-claude)
[![Stars](https://img.shields.io/github/stars/study8677/repobrain?style=flat-square&color=F59E0B)](https://github.com/study8677/repobrain/stargazers)

<br/>

<img src="https://img.shields.io/badge/Claude_Code-✓-D97757?style=flat-square" alt="Claude Code"/>
<img src="https://img.shields.io/badge/Codex_CLI-✓-412991?style=flat-square" alt="Codex"/>
<img src="https://img.shields.io/badge/Cursor-✓-000000?style=flat-square" alt="Cursor"/>
<img src="https://img.shields.io/badge/Windsurf-✓-06B6D4?style=flat-square" alt="Windsurf"/>
<img src="https://img.shields.io/badge/Gemini_CLI-✓-4285F4?style=flat-square" alt="Gemini CLI"/>
<img src="https://img.shields.io/badge/VS_Code_+_Copilot-✓-007ACC?style=flat-square" alt="VS Code"/>
<img src="https://img.shields.io/badge/Cline-✓-FF6B6B?style=flat-square" alt="Cline"/>
<img src="https://img.shields.io/badge/Aider-✓-8B5CF6?style=flat-square" alt="Aider"/>

<sub>**English** · [中文](README_CN.md) · [Español](README_ES.md)</sub>

<br/><br/>

<img src="docs/assets/demo.gif" alt="rb-ask demo — ask your codebase, get grounded answers with file paths and line numbers" width="800"/>

</div>

<br/>

<div align="center">

<p><strong>🚀 实测推荐:</strong> <a href="https://teamorouter.com/?i=e188641773">TeamoRouter</a> —— 非广告，我自己在 Codex、Claude Code 等 AI 编程工具里高强度使用：一个 API Key 接入 Claude、GPT-5.5 等，模型价格方便调整，价格优惠，并没有掺水的情况。接入指南见 <a href="https://github.com/xixiaoyao/openrouter-api-key">openrouter-api-key</a>。</p>

</div>

<br/>

<div align="center">

<a href="https://doloffer.com">
  <img src="docs/assets/doloffer-banner.png" alt="DolOffer - GPT and Claude membership recharge, official subscriptions with after-sales support" width="800"/>
</a>

<sub><b>Sponsored placement:</b> <a href="https://doloffer.com">DolOffer</a> (<a href="https://github.com/Doloffer-g/guide">GitHub project</a>) offers discounted GPT and Claude membership recharge, official subscriptions, and after-sales support. Use code <code>AI8888</code> for 10% off.</sub><br/>
<sub><b>Disclaimer:</b> This is a paid sponsor placement. DolOffer services, pricing, availability, and support are provided by DolOffer; please review their terms before purchase.</sub>

</div>

<br/>

<div align="center">
<img src="docs/assets/before_after.svg" alt="Before vs After RepoBrain" width="800"/>
</div>

<br/>

```bash
# 1 — Install (Claude Code plugin marketplace)
/plugin marketplace add study8677/repobrain
/plugin install repobrain@repobrain

# 2 — Pick LLM provider, build the knowledge base
/repobrain:rb-setup
/repobrain:rb-refresh

# 3 — Ask anything, grounded in real code with file paths + line numbers
/repobrain:rb-ask "How does auth work?"
```

> Note: the plugin/package ID is still `repobrain`; it will migrate in a future release.

> **99% factual · 2.1× faster than Codex CLI · works in any AI IDE.**
> [Head-to-head benchmark ↓](#head-to-head-eval-repobrain-vs-codex-cli-vs-claude-code-2026-05-09)
> Codex CLI users — drop the `repobrain:` prefix; the same four slash commands ship there too.

---

## Why RepoBrain?

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

---

## Head-to-Head Eval: RepoBrain vs Codex CLI vs Claude Code (2026-05-09)

Asymmetric benchmark on three real-world Python codebases — `fastapi/fastapi`,
`psf/requests`, `fastapi/sqlmodel` — asking each tool **the same 36 questions**
across three difficulty bands. All three tools used `gpt-5.5` with high
reasoning effort; Codex and Claude had full read access to the workspace.
Codex was the grader (4-axis 0–3 rubric, scores verified against actual source).

| Question type | RepoBrain | Codex CLI | Claude Code |
|:---|:---:|:---:|:---:|
| 15 factual lookups | **179/180 (99%)** | 179/180 (99%) | 178/180 (99%) |
| 12 synthesis (project / arch tour) | 116/144 (81%) | **144/144 (100%)** | 136/144 (94%) |
| 9 audit / security | **105/108 (97%)** | 104/108 (96%) | 98/108 (91%) |

**Combined factual + audit (24 cells): RepoBrain 284/288, Codex 283/288,
Claude 276/288.** RepoBrain edges out both — at lower latency than Codex on
every single question.

**Latency** (mean wall-clock per question, same proxy):

| Question type | RepoBrain | Codex | Claude |
|:---|:---:|:---:|:---:|
| Factual | **56s** | 119s | 42s |
| Audit | 160s | 177s | **100s** |

RepoBrain is **2.1× faster than Codex on factual** and on par with Codex on
audit, while matching or beating it on correctness. Claude is fastest on
audit but loses 7 percentage points of correctness.

<details>
<summary><b>What changed in this repo to get there</b> — engine fixes that drove the numbers</summary>

Two engine fixes landed during the benchmark, both committed in this branch:

1. `_ask_with_agent_md` now surfaces project-level docs (`conventions.md`,
   `module_registry.md`, `map.md`, `structure.md`) into its answer prompts.
   Removes the "module knowledge does not include project-wide conventions"
   refusal pattern.
2. The structured-facts answer agents now have `search_code`, `read_file`,
   `list_directory`, `read_file_metadata`, `search_by_type` bound at runtime,
   so the LLM can grep and read actual source instead of paraphrasing the KG.

Full report (data, methodology, per-cell tables, caveats):
[`artifacts/benchmark-2026-05-09/REPORT.md`](artifacts/benchmark-2026-05-09/REPORT.md).

</details>

---

## Quick Start

**Plugin install for Claude Code / Codex CLI** (recommended — the engine CLI auto-installs on first session via SessionStart hook):

```bash
# Claude Code
/plugin marketplace add study8677/repobrain
/plugin install repobrain@repobrain
/repobrain:rb-setup            # interactive: pick LLM provider, paste API key, writes .env
/repobrain:rb-refresh          # first refresh auto-creates .repobrain/
/repobrain:rb-ask "How does this project work?"

# Codex CLI (manual engine install — Codex hooks are not yet supported)
pipx install "git+https://github.com/study8677/repobrain.git#subdirectory=engine"
codex plugin marketplace add study8677/repobrain
/rb-setup
/rb-refresh
/rb-ask "How does this project work?"
```

Codex auto-discovers slash commands from the plugin's `commands/` directory, so the same four commands work without the `repobrain:` namespace prefix. The raw CLI calls (`rb-refresh --workspace .`, `rb-ask "..." --workspace .`) also still work. If your Codex build supports MCP, register `rb-mcp --workspace <project>` separately.

<details>
<summary><b>Option B — Manual install: engine + CLI via pip</b></summary>

```bash
# 1. Install engine + CLI
pip install "git+https://github.com/study8677/repobrain.git#subdirectory=cli"
pip install "git+https://github.com/study8677/repobrain.git#subdirectory=engine"

# 2. Configure .env with any OpenAI-compatible API key
cd my-project
cat > .env <<EOF
OPENAI_BASE_URL=https://your-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-model
RB_ASK_TIMEOUT_SECONDS=120
EOF

# 3. Build knowledge base (ModuleAgents self-learn each module)
rb-refresh --workspace .

# 4. Ask anything
rb-ask "How does auth work in this project?"

# 5. (Optional) Register as MCP server for Claude Code
claude mcp add repobrain rb-mcp -- --workspace $(pwd)
```

</details>

<details>
<summary><b>Option C — Context files only (any IDE, no LLM needed)</b></summary>

```bash
pip install git+https://github.com/study8677/repobrain.git#subdirectory=cli
rb init my-project && cd my-project
# IDE entry files bootstrap into AGENTS.md; dynamic knowledge is in .repobrain/
```

</details>

See [INSTALL.md](INSTALL.md) for full details and troubleshooting.

---

## Slash Commands

Same four slash commands ship to both **Claude Code** and **Codex CLI**. Claude namespaces them as `/repobrain:<name>`; Codex auto-discovers `commands/` and surfaces the bare `/<name>` form. No retraining — same flow on both hosts.

| Claude Code | Codex CLI | Purpose |
|---|---|---|
| `/repobrain:rb-setup` | `/rb-setup` | First-time setup — pick LLM provider, write `.env` |
| `/repobrain:rb-refresh [quick]` | `/rb-refresh [quick]` | Build / incrementally refresh the project knowledge base |
| `/repobrain:rb-ask <question>` | `/rb-ask <question>` | Routed Q&A on the current codebase |
| `/repobrain:rb-init <name>` | `/rb-init <name>` | Scaffold a new multi-agent repo from this template |

A typical first session is **rb-setup → rb-refresh → rb-ask**.

<details>
<summary><b>What each slash command actually does</b></summary>

### `rb-setup` — first-time configuration

Run this **once per project**, right after installing the plugin. Interactive picker for the LLM provider (OpenAI / DeepSeek / Groq / 阿里灵积 / NVIDIA NIM / Ollama local / any OpenAI-compatible endpoint), then writes `.env` to the project root with `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `RB_ASK_TIMEOUT_SECONDS`. It can also write an explicit local Codex host-runner config for experimental no-API-key `rb-ask`. Also ensures `.env` is in `.gitignore`. Skip it if you already have a working `.env`.

### `rb-refresh` — build / refresh the knowledge base

Deploys the multi-agent cluster to read your code: each module gets its own Agent that produces a knowledge doc under `.repobrain/agents/*.md`, plus a `map.md` routing index. Run after install, after significant code changes, or when `rb-ask` returns stale answers. The first refresh auto-creates `.repobrain/` — no separate init step needed. Pass `quick` for an incremental update, `failed-only` to rerun only previously failed modules.

Time: a few minutes for small repos, longer for large ones. Requires `rb-setup` to have completed. Full LLM refresh requires an API-key/OpenAI-compatible provider; local host-runner mode can use `RB_REFRESH_SCAN_ONLY=1 rb-refresh --workspace .` for scan artifacts.

### `rb-ask` — routed Q&A on the codebase

The **main reason this plugin exists**. Routes your question to the right ModuleAgent (and GitAgent when applicable), then returns an answer grounded in actual source with file paths and line numbers. Use it **before** manually grepping or reading files — it's faster and more accurate. Good question shapes: "where is X defined/handled?", "why was Y done this way?", "how does the auth flow work?", "what depends on module Z?".

Requires a knowledge base — if you see "no index" or empty answers, run `rb-refresh` first.

### `rb-init` — scaffold a new multi-agent repo

Creates a **new** project from the RepoBrain template. Two modes: `quick` (fast scaffold, clean copy) and `full` (adds runtime profile, `.env`, mission file, sandbox config, optional `git init`). This is for **starting a new repo** — you do **not** need it before `rb-refresh` on an existing project.

> The plugin also bundles the `agent-repo-init` skill (the same backend that `rb-init` invokes — Codex / Claude can also match it by description) and the optional `rb-mcp` MCP server (`ask_project` + `refresh_project`) for tool-style integration.

</details>

---

## Support Matrix

| Layer | Channels | Contract |
|:------|:---------|:---------|
| Native plugins | Claude Code, Codex CLI | Bundled slash commands for `rb-setup`, `rb-refresh`, `rb-ask`, and `rb-init`. |
| Compatible IDEs | Cursor, Windsurf, Gemini CLI, VS Code + Copilot, Cline, Aider | Use shared context files, the `rb`/`rb-*` CLI entrypoints, or an MCP client. |
| Advanced tool integration | `rb-mcp` | Exposes `ask_project` and `refresh_project` for hosts that can call MCP tools. |
| Workspace bootstrapping | `rb-init`, `rb init` | Starts a new repo or injects portable agent context into an existing one. |

The native plugins are the first-class install path today. Other environments are supported through the same repository knowledge artifacts rather than separate host-specific plugin packages.

---

## Architecture (TL;DR)

```
  rb init             Inject context files into any project (--force to overwrite)
       │
       ▼
  .repobrain/       Shared knowledge base — every IDE reads from here
       │
       ├──► rb-refresh     Dynamic multi-agent self-learning → module knowledge docs + structure map
       ├──► rb-ask         Router → ModuleAgent Q&A with live code evidence
       └──► rb-mcp         Optional MCP server → IDE tool integration
```

**Dynamic Multi-Agent Cluster** — During `rb-refresh`, files are grouped by import graph, directory co-location, and filename prefix. Each sub-agent gets ~30K tokens of focused, related code pre-loaded (no tool calls needed) and writes a **comprehensive Markdown knowledge doc** to `agents/*.md`. Large modules → multiple agent docs in parallel (no merging, no information loss). A **Map Agent** indexes everything into `map.md`. During `rb-ask`, the Router reads `map.md` to pick modules, then feeds their agent docs to answer agents. **Fully language-agnostic** — pure directory-structure module detection, LLM-driven code analysis.

**GitAgent** — Dedicated agent for analyzing git history — who changed what and why.

**NLPM Audit Feedback** — Improved by [NLPM](https://github.com/xiaolai/nlpm-for-claude), a natural-language programming linter by [xiaolai](https://github.com/xiaolai).

<details>
<summary><b>Detailed pipeline & internals</b></summary>

### `rb-refresh` — Multi-agent self-learning (8-step pipeline)

```bash
rb-refresh --workspace my-project
```

1. Scan codebase (languages, frameworks, structure)
2. Multi-agent pipeline generates `conventions.md`
3. Generate `structure.md` — language-agnostic file tree with line counts
4. Build knowledge graph (`knowledge_graph.json` + mermaid)
5. Write document/data/media indexes
6. **LLM full-context analysis** — group files by import graph + directory + prefix, pre-load into context (~30K tokens per sub-agent), filter out build artifacts. Each sub-agent reads the full source code and outputs a **comprehensive Markdown knowledge document** (`agents/*.md`). Large modules get multiple agent docs (one per group, no merging). Global API concurrency control prevents rate-limiting. **Fully language-agnostic** — works with any programming language.
7. **RefreshGitAgent** analyzes git history, generates `_git_insights.md`
8. **Map Agent** reads all agent docs → generates `map.md` (module routing index with descriptions and key topics)

### `rb-ask` — Router-based Q&A

```bash
rb-ask "How does auth work in this project?"
```

Router reads `map.md` → selects modules → reads `agents/*.md` → LLM answers with code references. Multiple agent docs are read in parallel, then a Synthesizer combines answers.

Falls back to the legacy Router → ModuleAgent/GitAgent swarm when agent docs are not yet generated.

### Key design choices

- **LLM as analyzer**: No AST parsing or regex — source code is fed directly to LLMs. Works with any programming language out of the box.
- **Smart grouping**: Files grouped by import relationships, directory co-location, filename prefixes. Build artifacts filtered. Hard character limit (800K) prevents context overflow.
- **No information loss**: Large modules produce multiple `agent.md` files — no merging or compression. Parallel reads + Synthesizer recombines at answer time.
- **Global API concurrency control**: `RB_API_CONCURRENCY` limits total simultaneous LLM calls.
- **Language-agnostic module detection**: Pure directory structure — no `__init__.py` or any language-specific marker required.

</details>

---

## IDE Compatibility

Architecture is encoded in **files** — any agent that reads project files benefits:

| IDE | Config File |
|:----|:------------|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| Windsurf | `.windsurfrules` |
| VS Code + Copilot | `.github/copilot-instructions.md` |
| Gemini CLI / Codex | `AGENTS.md` |
| Cline | `.clinerules` |
| Google Antigravity | `.repobrain/rules.md` |

All are generated by `rb init`: `AGENTS.md` is the single behavioral rulebook, IDE-specific files are thin bootstraps, and `.repobrain/` stores shared dynamic project context.

---

## Advanced Features

<details>
<summary><b>MCP Server — Give Claude Code a ChatGPT for your codebase</b></summary>

Instead of reading hundreds of documentation files, Claude Code can call `ask_project` as a live tool — backed by a dynamic multi-agent cluster: Router routes questions to the right ModuleAgent, returning grounded answers with file paths and line numbers.

**Setup:**

```bash
# Install engine
pip install "git+https://github.com/study8677/repobrain.git#subdirectory=engine"

# Refresh knowledge base first (ModuleAgents self-learn each module)
rb-refresh --workspace /path/to/project

# Register as MCP server in Claude Code
claude mcp add repobrain rb-mcp -- --workspace /path/to/project
```

**Tools exposed to Claude Code:**

| Tool | What it does |
|:-----|:-------------|
| `ask_project(question)` | Router → ModuleAgent/GitAgent answers codebase questions. Returns file paths + line numbers. |
| `refresh_project(quick?)` | Rebuild knowledge base after significant changes. ModuleAgents re-learn the code. |

</details>

<details>
<summary><b>MCP Integration (Consumer) — Let agents call external tools</b></summary>

`MCPClientManager` lets your agents connect to external MCP servers (GitHub, databases, etc.), auto-discovering and registering tools.

```json
// mcp_servers.json
{
  "servers": [
    {
      "name": "github",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "enabled": true
    }
  ]
}
```

Set `MCP_ENABLED=true` in `.env` to make configured servers available, and set `RB_ALLOW_MCP=true` only when you want `rb-ask` to auto-connect those external servers. Stdio MCP servers inherit process environment plus configured `env` values, so treat enabled servers as local-permission code.

</details>

<details>
<summary><b>Sandbox — Configurable code execution environment</b></summary>

| Variable | Default | Options |
|:---------|:--------|:--------|
| `SANDBOX_TYPE` | `local` | `local` · `microsandbox` |
| `SANDBOX_TIMEOUT_SEC` | `30` | seconds |
| `RB_RETRIEVAL_MODE` | `compact` | `off` · `compact` · `full` |

The default sandbox is for trusted local workspaces, not untrusted code isolation. Retrieval graph files redact common secrets before writing to disk, but `full` mode can still preserve source snippets. See [Sandbox docs](docs/en/SANDBOX.md).

</details>

<details>
<summary><b>CLI Commands Reference</b></summary>

| Command | What it does | LLM needed? |
|:--------|:-------------|:-----------:|
| `rb init <dir>` | Inject cognitive architecture templates | No |
| `rb init <dir> --force` | Re-inject, overwriting existing files | No |
| `rb refresh --workspace <dir>` | CLI convenience wrapper around the knowledge-hub refresh pipeline | Yes |
| `rb ask "question" --workspace <dir>` | CLI convenience wrapper around the routed project Q&A flow | Yes, or local Codex host runner |
| `rb-refresh` | Multi-agent self-learning of codebase, generates module knowledge docs + `conventions.md` + `structure.md` | Yes |
| `rb-ask "question"` | Router → ModuleAgent/GitAgent routed Q&A | Yes, or local Codex host runner |
| `rb-mcp --workspace <dir>` | **Start MCP server** — exposes `ask_project` + `refresh_project` to Claude Code | Yes |
| `rb report "message"` | Log a finding to `.repobrain/memory/` | No |
| `rb log-decision "what" "why"` | Log an architectural decision | No |

`rb ask` / `rb refresh` are available when both `cli/` and `engine/` are installed. `rb-ask` / `rb-refresh` are the engine-only entrypoints.

</details>

<details>
<summary><b>Two Packages, One Workflow — repo layout</b></summary>

```
repobrain/
├── cli/                     # rb CLI — lightweight, pip-installable
│   └── templates/           # .cursorrules, CLAUDE.md, .repobrain/, ...
└── engine/                  # Multi-agent engine + Knowledge Hub
    └── repobrain_engine/
        ├── _cli_entry.py    # rb-ask / rb-refresh / rb-mcp + python -m dispatch
        ├── config.py        # Pydantic configuration
        ├── hub/             # ★ Core: multi-agent cluster
        │   ├── agents.py    #   Router + ModuleAgent + GitAgent
        │   ├── contracts.py #   Pydantic models: claims, evidence, refresh status
        │   ├── ask_pipeline.py    # agent.md + graph-enriched ask
        │   ├── refresh_pipeline.py # LLM-driven refresh → agents/*.md + map.md
        │   ├── ask_tools.py
        │   ├── scanner.py   #   multi-language project scanning
        │   ├── module_grouping.py # smart functional file grouping
        │   ├── structure.py
        │   ├── knowledge_graph.py
        │   ├── retrieval_graph.py
        │   └── mcp_server.py
        ├── mcp_client.py    # MCP consumer (connects external tools)
        ├── memory.py        # Persistent interaction memory
        ├── tools/           # MCP query tools + extensions
        ├── skills/          # Skill loader
        └── sandbox/         # Code execution (local / microsandbox)
```

**CLI** (`pip install .../cli`) — Zero LLM deps. Injects templates, logs reports & decisions offline.

**Engine** (`pip install .../engine`) — Repository knowledge runtime. Powers `rb-ask`, `rb-refresh`, `rb-mcp`. Uses the OpenAI-compatible endpoint written by `rb-setup` (OpenAI, DeepSeek, Groq, DashScope, NVIDIA NIM, Ollama, or custom). Experimental local mode can set `RB_HOST_RUNNER=codex` so `rb-ask` runs through the user's local `codex login` instead of an API key; this is for personal/local use and is not a hosted product backend.

**Skill packaging:**
- `engine/repobrain_engine/skills/graph-retrieval/` — graph-oriented retrieval tools for structure and call-path reasoning.
- `engine/repobrain_engine/skills/knowledge-layer/` — project knowledge-layer tools for semantic context consolidation.

For local work on this repository itself:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ./cli -e './engine[dev]'
pytest engine/tests cli/tests
```

</details>

---

## Documentation

| | |
|:--|:--|
| 🇬🇧 English | **[`docs/en/`](docs/en/)** |
| 🇨🇳 中文 | **[`docs/zh/`](docs/zh/)** |
| 🇪🇸 Español | **[`docs/es/`](docs/es/)** |

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
