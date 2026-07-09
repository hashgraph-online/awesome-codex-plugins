# BABOK Analyst - AI-Powered Business Analysis Agent

[![Release](https://img.shields.io/github/v/release/GSkuza/BABOK_ANALYST)](https://github.com/GSkuza/BABOK_ANALYST/releases)
[![Lint Stage Prompts](https://github.com/GSkuza/BABOK_ANALYST/actions/workflows/lint-prompts.yml/badge.svg)](https://github.com/GSkuza/BABOK_ANALYST/actions/workflows/lint-prompts.yml)

An AI agent for professional business analysis compliant with **BABOK v3** (International Institute of Business Analysis) standard. Guides the analyst through a structured **9-stage** flow - from Stage 0 project charter to Stage 8 business case and ROI.

**Current version:** 2.2.8 | **Plugin install:** Claude Code, Codex, Copilot CLI

## What is BABOK Analyst?

BABOK Analyst is a set of system prompts for AI models (Claude, ChatGPT, other LLMs) that transforms them into business analysis experts. The agent:

- Conducts a structured analysis process in **9 stages** (Stage 0 charter gate + Stages 1-8)
- Uses **Short Rationale + Evidence** methodology (concise conclusions with cited evidence)
- Requires **human approval** at each stage (human-in-the-loop)
- Generates complete **project documentation** in Markdown format
- Manages **project lifecycle** with unique Project IDs, save/load, and persistent journal logs
- Specializes in IT projects for **mid-market** companies (€10-100M revenue, 50-500 employees)

## Repository Structure

```
BABOK_ANALYST/
|
|-- BABOK_AGENT/                          # Agent files
|   |-- BABOK_Agent_System_Prompt.md      # Main system prompt (modular, references stage files)
|   |-- BABOK_Agent_Quick_Start_Guide.md  # Quick start guide
|   |-- BABOK_Project_Structure_Template.md # Generic project folder structure template
|   |-- stages/                           # Individual stage instruction files
|   |   |-- BABOK_agent_stage_0.md        # Stage 0: Project Charter
|   |   |-- BABOK_agent_stage_1.md        # Stage 1: Project Initialization
|   |   |-- BABOK_agent_stage_2.md        # Stage 2: Current State Analysis
|   |   |-- BABOK_agent_stage_3.md        # Stage 3: Problem Domain Analysis
|   |   |-- BABOK_agent_stage_4.md        # Stage 4: Solution Requirements
|   |   |-- BABOK_agent_stage_5.md        # Stage 5: Future State Design
|   |   |-- BABOK_agent_stage_6.md        # Stage 6: Gap Analysis & Roadmap
|   |   |-- BABOK_agent_stage_7.md        # Stage 7: Risk Assessment
|   |   |-- BABOK_agent_stage_8.md        # Stage 8: Business Case & ROI
|   |-- agents/                           # Multi-agent orchestration layer (NEW v2.1.0)
|   |   |-- orchestrator_config.json      # Pipeline: model routing, handoff, retry rules
|   |   |-- stage1_config.json … stage8_config.json  # Per-stage model & prompt config
|   |   |-- quality_audit_agent.md        # Automated post-stage quality review agent
|   |   |-- quality_scoring_rubric.json   # Scoring rubric (completeness/SMART/consistency)
|   |   |-- context_schema_v2.json        # Extended context schema v2
|   |-- LLM_BABOK_AGENT/                  # Standalone prompt for LLM chat
|   |   |-- BABOK_Agent_LLM_Prompt.md     # Self-contained prompt (all stages inline)
|
|-- cli/                                  # Node.js CLI tool
|   |-- bin/babok.js                      # CLI entry point
|   |-- src/commands/                     # Command implementations
|   |   |-- ingest.js                     # babok ingest <file> (NEW v2.1.0)
|   |-- src/quality/                      # Quality scoring engine (NEW v2.1.0)
|   |   |-- scorer.js                     # scoreStage() / scoreAll()
|   |   |-- checks/completeness.js        # Section completeness checker
|   |   |-- checks/smart.js               # SMART criteria heuristics
|   |   |-- checks/consistency.js         # Cross-stage consistency checks
|   |-- src/validation/                   # Validation engine (NEW v2.1.0)
|   |   |-- cross-stage-validator.js      # validateProject() — 6 built-in rules
|   |-- src/reasoning/                    # AI reasoning engine (NEW v2.1.0)
|   |   |-- process-mapper.js             # generateProcessDiagram() — Mermaid output
|   |   |-- prompts/                      # LLM prompt templates
|   |-- src/lib/document-parser.js        # PDF/DOCX/XLSX/CSV/TXT/MD parser (NEW v2.1.0)
|   |-- src/lock.js                       # File-locking for team collaboration
|   |-- src/llm.js                        # Multi-provider LLM integration & keystore
|   |-- src/journal.js                    # Project journal management
|   |-- src/project.js                    # Project ID generation
|   |-- src/display.js                    # Terminal output formatting
|   |-- package.json                      # npm package configuration
|   |-- README.md                         # CLI Quick Start Guide
|
|-- babok-mcp/                            # MCP Server (v2.2.x)
|   |-- bin/babok-mcp.js                  # Entry point (npx babok-mcp)
|   |-- src/server.js                     # MCP server — 19 tools + 9 resources
|   |-- src/lib/project.js                # Project ID & path resolution
|   |-- src/lib/journal.js                # Journal CRUD + stage transitions
|   |-- src/test/smoke.js                 # 10-assertion smoke test suite
|   |-- setup.bat                         # One-click MCP installer (Windows)
|   |-- package.json                      # npm package (babok-mcp)
|   |-- README.md                         # Setup guide for Claude/Cursor/VS Code
|   |-- babok-mcp-user-manual.md          # Full user manual (EN)
|
|-- web/                                  # Web UI — Next.js 15 App Router
|   |-- app/                              # App Router pages & API routes
|   |   |-- page.tsx                      # Dashboard — server-rendered project overview
|   |   |-- projects/                     # Project detail, stage review, export page
|   |   |-- api/                          # REST API routes (projects, stages, export)
|   |-- components/                       # Reusable React components + UI primitives
|   |-- lib/project-store.ts              # Shared server-side project/stage readers
|   |-- lib/babok-client.ts               # Typed API client helpers
|   |-- next.config.js
|   |-- package.json
|
|-- docs/                                 # Architecture & reference docs (NEW v2.1.0)
|   |-- L2_L3_ARCHITECTURE.md             # L2/L3 agent layer design with sequence diagrams
|   |-- MCP_TOOLS_SPECIFICATION.md        # Full MCP tools API reference
|   |-- MIGRATION_GUIDE_L1_to_L2.md       # CLI → MCP migration guide
|   |-- workflows.md                      # End-to-end workflow diagrams
|   |-- agent-portability.md              # Plugin marketplace adapter matrix (NEW v2.1.0)
|
|-- templates/                            # BABOK deliverable templates (NEW v2.1.0)
|   |-- BRD_Template.md                   # Business Requirements Document
|   |-- Risk_Register_Template.md         # Risk Register with probability/impact matrix
|   |-- Stakeholder_Analysis_Template.md  # Stakeholder Analysis + RACI matrix
|   |-- User_Story_Template.md            # User Story with Given/When/Then criteria
|   |-- project_context.example.json      # Reference context file for babok run
|
|-- knowledge/                            # BABOK knowledge base (NEW v2.1.0)
|   |-- benchmarks/                       # Industry benchmark data
|   |-- industries/                       # Industry-specific reference data
|   |-- regulations/                      # Regulatory requirements by jurisdiction
|   |-- anti_patterns/                    # Known BA anti-patterns
|   |-- technology/                       # Technology reference data
|   |-- schema/
|   |-- README.md
|
|-- tests/                                # Automated test suite (NEW v2.1.0)
|   |-- unit/                             # Unit tests (project, journal, scoring, validation)
|   |-- integration/                      # Integration tests (CLI workflow)
|   |-- plugin-manifest.test.cjs          # Plugin marketplace smoke tests (NEW v2.1.0)
|   |-- hooks.test.cjs                    # Lifecycle hook tests (NEW v2.1.0)
|   |-- uninstall.test.cjs                # Uninstall script tests (NEW v2.1.0)
|   |-- fixtures/                         # Sample deliverable files for testing
|   |-- helpers/                          # mock-llm.js, temp-project.js
|
|-- evaluation/                           # Gold standard evaluation suite (NEW v2.1.0)
|
|-- .claude-plugin/                       # Claude Code marketplace manifests (NEW v2.1.0)
|-- .codex-plugin/                        # Codex plugin manifest
|-- .github/plugin/                       # Copilot CLI plugin manifest
|-- .mcp.json                             # Portable MCP wiring (${CLAUDE_PLUGIN_ROOT})
|-- hooks/                                # Lifecycle hooks (Claude/Codex/Copilot)
|-- skills/                               # Bundled agent skills
|-- commands/                             # Slash commands: *.md (Claude), *.toml (Copilot/Codex)
|-- agents/                               # Subagent definitions (orchestrator + stages 0–8)
|-- AGENTS.md                             # Always-on rules for generic agents
|-- scripts/                              # check-versions.cjs, uninstall.cjs
|
|-- setup.bat                             # One-click installer (Windows)
|-- setup.sh                              # One-click installer (Linux/macOS)
|-- generate_manual.py                    # DOCX/PDF manual generator (NEW v2.1.0)
|-- babok-mcp-podrecznik uzytkownika.md   # Full MCP user manual (PL)
|-- babok-mcp-user-manual.md              # Full MCP user manual (EN)
|-- BABOK_AGENT_SYSTEM_PROMPT.md          # Consolidated root-level system prompt (NEW v2.1.0)
|
|-- .github/
|   |-- copilot-instructions.md           # Configuration for GitHub Copilot / VS Code (1,600 lines)
|   |-- prompts/                          # Stage-specific Copilot Chat prompt files (NEW v2.1.0)
|   |-- workflows/
|   |   |-- lint-prompts.yml              # CI: validates stage files on every push
|
|-- .gitignore                            # Excludes local analysis files
|-- README.md                             # This file
```

## Stages

| Stage | Name | What You Get |
|------|-------|----------------|
| **Stage 0** ⭐ | Project Charter | Business trigger, sponsor sign-off, scope boundary, Go/No-Go gate |
| **Stage 1** | Project Initialization & Stakeholder Mapping | Project scope, stakeholder register, success criteria |
| **Stage 2** | Current State Analysis (AS-IS) | Process maps, cost baseline, system analysis |
| **Stage 3** | Problem Domain Analysis | Problem categorization, root cause analysis, prioritization |
| **Stage 4** | Solution Requirements Definition | Functional/non-functional requirements, user stories, MoSCoW |
| **Stage 5** | Future State Design (TO-BE) | Target architecture, TO-BE processes |
| **Stage 6** | Gap Analysis & Implementation Roadmap | Gap analysis, implementation roadmap |
| **Stage 7** | Risk Assessment & Mitigation Strategy | Risk register, mitigation plans |
| **Stage 8** | Business Case & ROI Model | Financial model, ROI, NPV, payback period |

---

## Web UI Highlights

The bundled Next.js UI provides a lightweight review layer over the shared project files in `projects/<project_id>/`.

- **Dashboard**: server-rendered project cards with progress bars and approval counts
- **Project view**: stage list, overall progress, and ZIP export
- **Stage view**: rendered deliverables, Mermaid diagrams, quality score badge, and approve/reject controls
- **Export endpoint**: project ZIP download via `web/app/api/projects/[id]/export/route.ts`, with Windows-compatible archive creation

Run locally:

```bash
cd web
npm install
npm run build
npm run start
```

Open `http://localhost:3000`.

---

## Modular Architecture (v2.0)

The agent system uses a **modular architecture** where each analysis stage has its own detailed instruction file:

```
BABOK_AGENT/
|-- BABOK_Agent_System_Prompt.md          # Core prompt (references stage files)
|-- stages/
|   |-- BABOK_agent_stage_0.md            # Stage 0: Project Charter gate
|   |-- BABOK_agent_stage_1.md            # Detailed Stage 1 instructions
|   |-- BABOK_agent_stage_2.md            # Detailed Stage 2 instructions
|   |-- ...                               # Stages 3-7
|   |-- BABOK_agent_stage_8.md            # Detailed Stage 8 instructions
|-- LLM_BABOK_AGENT/
|   |-- BABOK_Agent_LLM_Prompt.md         # All-in-one prompt for LLM chat windows
```

**Two usage variants:**

| Variant | File | Use When |
|---------|------|----------|
| **Modular** | `BABOK_Agent_System_Prompt.md` + `stages/*.md` | VS Code, Claude Code, IDE-based workflows (agent can load stage files as needed) |
| **Standalone** | `LLM_BABOK_AGENT/BABOK_Agent_LLM_Prompt.md` | Direct paste into LLM chat (Claude.ai, ChatGPT, etc.) — all stages inline, self-contained |

Each stage file contains: step-by-step process, questions for human, deliverable template, quality checklist, and CLI command references.

---

## How to Get Started

### Plugin Marketplace Install (recommended) — v2.2+

Install the full BABOK Analyst stack (skills, agents, hooks, MCP, slash commands) in Claude Code, Codex, or Copilot CLI.

**Claude Code (3 steps):**

```
/plugin marketplace add GSkuza/BABOK_ANALYST
/plugin install babok_analyst@babok_analyst
/reload-plugins
```

Then open `/hooks` and authorize lifecycle hooks. Start a **new session**.

**Update to latest release:**

```
/plugin marketplace update babok_analyst
/plugin install babok_analyst@babok_analyst
/reload-plugins
```

**Codex** (run in **PowerShell / cmd**, not inside the Codex chat — the in-app sandbox cannot write to `~/.codex`):

```
codex plugin marketplace add GSkuza/BABOK_ANALYST
codex plugin add babok_analyst@babok_analyst
```

Then open `/plugins` to confirm **babok_analyst@babok_analyst** is listed, and authorize hooks in `/hooks`.

**Update:**

```
codex plugin marketplace upgrade babok_analyst
codex plugin add babok_analyst@babok_analyst
```

**GitHub Copilot CLI:**

```
copilot plugin marketplace add GSkuza/BABOK_ANALYST
copilot plugin install babok_analyst@babok_analyst
```

#### What the plugin includes

| Component | Location | Purpose |
|-----------|----------|---------|
| Marketplace manifest | `.claude-plugin/` (Claude), `.agents/plugins/` (Codex) | Plugin registry per host |
| MCP wiring | `.mcp.json` | 19 tools + 9 stage resources (`${CLAUDE_PLUGIN_ROOT}`) |
| Lifecycle hooks | `hooks/` | Session activation + `babok-mcp` dependency install |
| Skills | `skills/babok-analyst/` | Auto-activated BABOK operating rules |
| Agents | `agents/` | Orchestrator + per-stage subagents (12) |
| Commands | `commands/babok-*.md` | `/babok-new`, `/babok-new PL`, `/babok-new ENG`, `/babok-new-pl`, `/babok-new-eng`, `/babok-status`, `/babok-help` |
| Always-on rules | `AGENTS.md` | Generic agents / Gemini CLI fallback |

Projects are stored in **`projects/<project_id>/`** under your workspace (not `BABOK_Analysis/`).

**Uninstall external state:** `node scripts/uninstall.cjs`

See [`docs/agent-portability.md`](docs/agent-portability.md) for the full adapter matrix.

#### Troubleshooting

| Error | Fix |
|-------|-----|
| `marketplace "babok_analyst" not found` | Run `/plugin marketplace add GSkuza/BABOK_ANALYST` **before** install |
| `agents: Invalid input` | Update to **v2.2.0+** (`/plugin marketplace update babok_analyst`) — fixed manifest |
| MCP tools missing | `/reload-plugins`, ensure Node.js ≥18; hook runs `npm install` in `babok-mcp/` |
| Codex: MCP `babok` handshake failed | Update to **v2.2.4+** — uses `hooks/babok-mcp-launcher.cjs` with `cwd: "."` (Codex does not expand `${CLAUDE_PLUGIN_ROOT}`) |
| Stale plugin cache | `/plugin marketplace update babok_analyst` then reinstall |
| Codex: empty plugin list / sandbox write error | Run `codex plugin marketplace add` in a **normal terminal** (v2.2.4+); update marketplace if on older tag |

**Local checkout (no GitHub fetch):**

```
/plugin marketplace add C:/AI_WORKSPACE/CURSOR_PROJECTS/CURSOR_PROJECTS_BIZ/BABOK_ANALYST/BABOK_ANALYST
/plugin install babok_analyst@babok_analyst
/reload-plugins
```

---

### Quick Start (non-technical users)

**Windows:**
```bat
setup.bat
```

**Linux / macOS:**
```bash
chmod +x setup.sh && ./setup.sh
```

The setup script automatically:
- checks for Node.js (with download link if missing)
- runs `npm install`
- optionally adds `babok` to PATH
- launches the **interactive setup wizard** (`babok setup`) for API key entry and language selection — no JSON editing required

---

### Method 1: Claude.ai (Projects)

1. **Clone or download the repository** (see section below)
2. Go to [claude.ai](https://claude.ai) and create a new **Project**
3. In project settings, click **"Project Instructions"** (Custom Instructions)
4. Copy the **entire** content of `BABOK_AGENT/LLM_BABOK_AGENT/BABOK_Agent_LLM_Prompt.md` file and paste it into the Project Instructions field
5. Start a new conversation in the project and type:
   ```
   BEGIN NEW PROJECT
   ```

### Method 2: VS Code with Claude Code (CLI)

1. Clone the repository:
   ```bash
   git clone https://github.com/GSkuza/BABOK_ANALYST.git
   cd BABOK_ANALYST
   ```
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (requires Node.js 18+):
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
3. Launch Claude Code in the project directory:
   ```bash
   claude
   ```
4. Claude will automatically load the configuration from `.github/copilot-instructions.md`
5. Type:
   ```
   BEGIN NEW PROJECT
   ```

### Method 3: VS Code with GitHub Copilot Chat

1. Clone the repository and open in VS Code:
   ```bash
   git clone https://github.com/GSkuza/BABOK_ANALYST.git
   code BABOK_ANALYST
   ```
2. Make sure you have the **GitHub Copilot Chat** extension installed
3. Copilot will automatically load instructions from `.github/copilot-instructions.md`
4. Open Copilot Chat (Ctrl+Shift+I) and type:
   ```
   BEGIN NEW PROJECT
   ```

### Method 4: ChatGPT or other LLM

1. Download the content of `BABOK_AGENT/LLM_BABOK_AGENT/BABOK_Agent_LLM_Prompt.md` file
2. In ChatGPT: Settings -> "Custom Instructions" or "System Prompt"
3. Paste the file content as system instructions
4. Start a new conversation and type:
   ```
   BEGIN NEW PROJECT
   ```

### Method 5: API (Anthropic, OpenAI, others)

Use the content of `BABOK_Agent_LLM_Prompt.md` as the `system` parameter in the API call:

```python
import anthropic

client = anthropic.Anthropic()

with open("BABOK_AGENT/LLM_BABOK_AGENT/BABOK_Agent_LLM_Prompt.md") as f:
    system_prompt = f.read()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8192,
    system=system_prompt,
    messages=[{"role": "user", "content": "BEGIN NEW PROJECT"}]
)
```

---

## BABOK CLI Tool

The repository includes a **cross-platform CLI tool** for managing project lifecycle directly from the terminal. The CLI handles project creation, state tracking via journal files, stage management, and **interactive AI chat** with multiple LLM providers — independently of any specific AI platform.

### Installation

Requires **Node.js 18+**.

**Option A — one-click installer (recommended for non-technical users):**
```bat
# Windows
setup.bat

# Linux / macOS
chmod +x setup.sh && ./setup.sh
```

**Option B — manual:**
```bash
git clone https://github.com/GSkuza/BABOK_ANALYST.git
cd BABOK_ANALYST/cli
npm install
npm link        # Makes 'babok' command available globally
```

After manual install, run the setup wizard for first-time configuration:
```bash
babok setup
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `babok setup` | **First-time setup wizard** — API keys, language, optional first project |
| `babok new [--name "Name"]` | Create a new project with unique ID and timestamp |
| `babok list` | List all projects with current status |
| `babok status [id]` | Show detailed project status (all stages) |
| `babok load <id>` | Load project context (generates text to paste into AI chat) |
| `babok save <id>` | Save current project state snapshot |
| `babok rename <id> [new-name]` | Rename a project |
| `babok delete <id>` | Permanently delete a project with confirmation |
| `babok approve <id> <stage>` | Mark a stage as approved, advance to next (stages 0–8) |
| `babok reject <id> <stage> -r "reason"` | Reject a stage with reason |
| `babok diff <id> [--stage N]` | Show stage history and deliverable preview |
| `babok diff <id1> <id2> [--stage N]` | Line diff between two projects' deliverables |
| `babok export <id>` | Export project deliverables to output directory |
| `babok chat <id>` | **Interactive AI chat** for current stage |
| `babok run [--context file.json]` | **Automated 8-stage pipeline** (interactive or `--auto`) |
| `babok run --diagram` | Run pipeline with auto-generated Mermaid process diagrams (NEW v2.1.0) |
| `babok ingest <file>` | **Ingest a document** (PDF/DOCX/XLSX/CSV/TXT/MD) into the project (NEW v2.1.0) |
| `babok score <id> <stage\|all>` | **Quality score** for a stage or all stages (NEW v2.1.0) |
| `babok validate <id>` | **Cross-stage consistency validation** — 6 built-in rules (NEW v2.1.0) |
| `babok make docx <id>` | Generate DOCX document(s) from stage files |
| `babok make pdf <id>` | Generate PDF document(s) from stage files |
| `babok make all <id>` | Generate DOCX + PDF in one run |
| `babok llm list` | List all available AI models |
| `babok llm change` | Interactively switch AI provider/model |
| `babok lang [EN\|PL]` | Set or show interface language |

### Stage diff

Inspect and compare deliverables directly from the terminal:

```bash
# Show stage history + deliverable preview for a single project
babok diff K7M3
babok diff K7M3 --stage 3

# Line-by-line diff between two project versions (e.g. rejected vs reworked)
babok diff K7M3 R9TN
babok diff K7M3 R9TN --stage 4 --context 5
```

The two-project diff uses LCS to produce colored `+` / `-` output — no external tools needed.

---

### Document export (DOCX/PDF)

In addition to raw Markdown exports, the CLI can generate **CEO-ready DOCX and PDF** documents directly from stage files:

```bash
# DOCX only
babok make docx <project_id>
babok make docx <project_id> --stage 1      # only Stage 1

# PDF only
babok make pdf <project_id>

# DOCX + PDF in one run
babok make all <project_id>
```

- Works on `STAGE_XX_*.md` files generated by the agent
- Applies professional corporate styling (tables, headings, headers/footers)
- Default output directory: `<project_dir>/exports` (configurable via `--output`)

### Quick Example

```bash
# First-time setup
babok setup

# Create a new project
babok new --name "ERP Integration"
# Output: Project ID: BABOK-20260208-K7M3

# Check all projects
babok list

# Approve Stage 1 after completing it in AI chat
babok approve K7M3 1

# View detailed status
babok status K7M3

# Load context for AI chat (copy & paste the output)
babok load K7M3

# Start interactive AI chat for current stage
babok chat K7M3

# Rename a project
babok rename K7M3 "ERP Integration v2"

# Delete a project (prompts confirmation)
babok delete K7M3

# Export deliverables when done
babok export K7M3
```

Partial IDs work — `babok status K7M3` matches `BABOK-20260208-K7M3`.

For the full CLI guide, see: [`cli/README.md`](cli/README.md)

---

## Document Ingestion (`babok ingest`) — NEW in v2.1.0

The `babok ingest` command allows you to feed existing documents into a project so the AI agent can use them as context during analysis. Supported formats: **PDF, DOCX, XLSX, CSV, TXT, MD**.

```bash
# Ingest a supplier contract into a project
babok ingest path/to/contract.pdf --project K7M3

# Ingest an Excel data export
babok ingest data_export.xlsx --project K7M3
```

- Documents are parsed and classified by the LLM automatically
- Ingested files are listed in `babok status` output
- Source: `cli/src/commands/ingest.js` + `cli/src/lib/document-parser.js`

---

## Quality Scoring & Cross-Stage Validation — NEW in v2.1.0

### `babok score` — Stage Quality Scorer

Scores a deliverable (or all stages) against a rubric with three dimensions:

| Dimension | Weight | What It Checks |
|-----------|--------|----------------|
| **Completeness** | 40% | All required sections present |
| **SMART quality** | 30% | Numeric targets, dates, currencies, ROI present |
| **Consistency** | 30% | Cross-references match within the stage |

```bash
babok score K7M3 1          # Score Stage 1 only
babok score K7M3 all        # Score all completed stages
```

Output: color-coded score card in the terminal (chalk).

### `babok validate` — Cross-Stage Consistency Validator

Validates that all approved stages are internally consistent. Six built-in rules:

| Rule | What It Checks |
|------|----------------|
| FR Traceability | All FR IDs in Stage 4 appear in the RTM |
| Budget Ceiling | Stage 8 cost ≤ budget ceiling set in Stage 1 |
| Integration Coverage | Every system in Stage 2 addressed in Stage 5 TO-BE |
| KPI Coverage | Every KPI from Stage 1 measured in Stage 2 baseline |
| Critical Risk Owner | Every HIGH risk in Stage 7 has an assigned owner |
| Roadmap Date | Stage 6 go-live date does not precede Stage 1 hard deadline |

```bash
babok validate K7M3         # Validates all approved stages; exits with code 1 on errors
```

---

## Web UI (`web/`) — NEW in v2.1.0

The repository now ships a **Next.js 15 App Router** web interface for teams who prefer a browser-based workflow.

### Features

- **Dashboard** — lists all projects with stage progress bars
- **New project form** — name + language selection
- **Project detail view** — stage pipeline with status indicators
- **Stage view** — renders deliverable Markdown + Approve / Reject buttons
- **Export page** — one-click ZIP download of all stage deliverables
- **Mermaid diagram viewer** — inline rendering of auto-generated process maps

### Running the Web UI

```bash
cd web
npm install
npm run dev        # http://localhost:3000
```

### API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/projects` | GET / POST | List or create projects |
| `/api/projects/[id]` | GET | Get project detail + stage list |
| `/api/projects/[id]/stages/[n]` | GET / POST | Read or save a stage deliverable |
| `/api/projects/[id]/export` | GET | Download all deliverables as ZIP |

---

## Team Collaboration & File Locking

When multiple analysts work on the **same project directory** (e.g. on a shared network drive), concurrent edits to the same stage can overwrite each other. v2.0.1 introduces **automatic file locking**:

- When `babok chat` or `babok run` starts working on a stage, a lock file is created:
  `<project_dir>/.stage_N.lock`
- The lock file records: `locked_by`, `hostname`, `pid`, `locked_at`
- If another user tries to open the same stage, they get a clear error:
  ```
  ⛔ Stage 3 is currently locked by another user:
     anna@WORKSTATION-02 (PID 14872), locked 12 min ago
  ```
- Locks older than **2 hours** are automatically treated as stale and removed
- Lock files are excluded from git (`.gitignore`)

> **Recommendation:** Store the `projects/` directory on a shared network drive or sync folder for team use. Each analyst works on separate stages to avoid contention.

---

## MCP Server — `babok-mcp` (v2.2.x)

> **The biggest differentiator.** Claude and other MCP-compatible AI assistants can now manage your BABOK project lifecycle _without leaving the chat interface_.

The `babok-mcp` package is a [Model Context Protocol](https://modelcontextprotocol.io) server that exposes **19 tools** and 9 resources to any compatible AI client.

### Setup (Plugin install — recommended)

If you installed via the plugin marketplace (see above), MCP is wired automatically
via `.mcp.json` with `${CLAUDE_PLUGIN_ROOT}` paths. Run `/reload-plugins` after install.

### Setup (Claude Desktop / manual Claude Code)

**Windows (one-click):**
```bat
cd BABOK_ANALYST/babok-mcp
setup.bat
```

**Manual:**
```bash
cd BABOK_ANALYST/babok-mcp
npm install
```

Add to `claude_desktop_config.json` (or `.claude/mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "babok": {
      "command": "node",
      "args": ["D:/BABOK_ANALYST/babok-mcp/bin/babok-mcp.js"],
      "env": {
        "BABOK_PROJECTS_DIR": "D:/BABOK_ANALYST/projects",
        "BABOK_AGENT_DIR": "D:/BABOK_ANALYST/BABOK_AGENT/stages"
      }
    }
  }
}
```

Restart Claude Desktop — a 🔧 tool icon confirms the server is connected.

### Available Tools

| Tool | What it does |
|------|-------------|
| `babok_new_project` | Create a new project, get ID |
| `babok_list_projects` | List all projects with stage + status |
| `babok_get_stage` | Full stage context: prompt + journal + existing deliverable |
| `babok_get_stage_template` | Load stage template skeleton (with optional modules) |
| `babok_approve_stage` | Approve stage, advance to next |
| `babok_submit_for_review` | Submit deliverable snapshot for human review (Two-Key key 1) |
| `babok_open_revision` | Re-open an approved stage for edits |
| `babok_get_deliverable` | Read a completed stage MD file |
| `babok_save_deliverable` | Persist AI-generated content to project dir |
| `babok_search` | Full-text search across all project files |
| `babok_export` | Copy all deliverables to an export directory |
| `babok_rename_project` | Rename a project |
| `babok_delete_project` | Delete a project with explicit confirmation |
| `babok_get_stage_artifact` | Read stage artefact file |
| `babok_quality_check` | Score deliverable quality |
| `babok_sync_stage_artifact` | Sync artefact to project |
| `babok_create_jira_epic` | Create Jira epic from roadmap |
| `babok_create_github_issues` | Create GitHub issues from roadmap |
| `babok_read_external_context` | Read external context files |

### Example flow in Claude

```
You:    "Start a new BABOK project for SAP integration at Acme Corp"

Claude: [babok_new_project → BABOK-20260316-K7M3]
        [babok_get_stage stage_n=0 → loads Stage 0 Charter prompt]
        → asks 3 questions about business trigger, sponsor, scope

You:    [answers]

Claude: [babok_save_deliverable stage_n=0 content="..."]
        [babok_approve_stage stage_n=0]
        → "Stage 0 approved. Moving to Stage 1: Stakeholder Mapping."
```

For the full MCP guide, see: [`babok-mcp/README.md`](babok-mcp/README.md)

---

## AI Chat in Terminal (`babok chat`)

The `babok chat` command starts an interactive AI conversation in the terminal, contextually aware of your project stage. It supports **5 LLM providers** — choose the one you prefer.

### Supported Providers

| Provider | Models | Get API Key |
|----------|--------|-------------|
| **Google Gemini** | `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-flash` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **OpenAI** | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4o`, `gpt-4o-mini`, `o3-mini` | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Anthropic Claude** | `claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku`, `claude-3-opus` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| **Hugging Face** | `Qwen2.5-72B`, `Llama-3.3-70B`, `DeepSeek-R1`, `Bielik-11B` | [huggingface.co](https://huggingface.co/settings/tokens) |
| **Google Vertex AI** | `gemini-2.5-pro-exp`, `gemini-2.0-flash` | [cloud.google.com](https://cloud.google.com/vertex-ai) |

### Usage

```bash
# Interactive provider selection (first run)
babok chat K7M3

# Specify provider and stage
babok chat K7M3 --provider openai --stage 3

# Specify custom model
babok chat K7M3 --provider anthropic --model claude-3-7-sonnet-20250219

# Use Hugging Face
babok chat K7M3 -p huggingface -m "Qwen/Qwen2.5-72B-Instruct"
```

### Chat Commands (inside session)

| Command | Description |
|---------|-------------|
| `/exit`, `/quit` | End chat session (auto-saves, releases stage lock) |
| `/save` | Save conversation to project |
| `/clear` | Clear conversation history |
| `/stage N` | Switch to stage N (1-8) |
| `/status` | Show project status |
| `/provider` | Show current provider & model |
| `/llm` | Change AI provider/model mid-session |
| `/key` | API key management info |
| `/key clear [provider]` | Remove stored key(s) |
| `/help` | Show all commands |

### Features

- **Streaming responses** — real-time output from LLM
- **Stage context** — system prompt includes project info, stage instructions, decisions, and history
- **Auto-save** — conversation saved every 5 messages and on exit
- **Conversation history** — resume where you left off per stage
- **Switch stages** — `/stage N` to jump between stages mid-session
- **File locking** — stage locked on start, released on exit (prevents team conflicts)

---

## API Key Security

All API keys are secured and **never committed to the repository**.

### Key Storage Hierarchy

| Priority | Source | Security Level |
|----------|--------|----------------|
| 1 | Environment variable (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_API_KEY`) | Session-only, in memory |
| 2 | `.env` file | Gitignored, plaintext local file |
| 3 | `.babok_keystore` | Gitignored, **encrypted** with machine-specific key |
| 4 | `babok setup` wizard | Prompted interactively, saved to keystore |

### How It Works

1. **First run**: run `babok setup` (or `setup.bat` / `setup.sh`) — wizard guides you through provider selection and key entry
2. **Key encryption**: The key is XOR-encrypted using a SHA-256 hash derived from `hostname + username + working directory` — the encrypted file is **useless on another machine or repo clone**
3. **Gitignored**: `.babok_keystore`, `.env`, and `.env.*` are all in `.gitignore`
4. **No keys in config**: `agent_config.json` (tracked by git) contains **zero API keys**
5. **Per-provider storage**: Each provider's key is stored independently — you can have keys for all 5 providers

### Setting Up API Keys

**Option A: Setup wizard (recommended)**
```bash
babok setup
# → Select language → select provider → paste key → test connection
```

**Option B: Environment variables**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:GEMINI_API_KEY = "AI..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:HF_API_KEY = "hf_..."

# Linux/macOS
export OPENAI_API_KEY="sk-..."
```

**Option C: `.env` file** (gitignored)
```env
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
HF_API_KEY=hf_...
```

### Removing Stored Keys

```bash
# Inside chat session:
/key clear              # Remove all stored keys
/key clear openai       # Remove only OpenAI key

# Or delete the keystore file directly:
# Windows: del .babok_keystore
# Linux:   rm .babok_keystore
```

---

## Cloning the Repository

### Requirements

- **Git** installed on your computer ([installation guide](https://git-scm.com/downloads))
- Optional: **VS Code** or other code editor

### Cloning via HTTPS

```bash
git clone https://github.com/GSkuza/BABOK_ANALYST.git
```

### Cloning via SSH

```bash
git clone git@github.com:GSkuza/BABOK_ANALYST.git
```

### Cloning via GitHub CLI

```bash
gh repo clone GSkuza/BABOK_ANALYST
```

### Download ZIP (without Git)

1. Go to https://github.com/GSkuza/BABOK_ANALYST
2. Click the green **"Code"** button
3. Select **"Download ZIP"**
4. Extract the archive to your chosen location

---

## How to Work with the Agent

### Communication Format

The agent asks questions in a structured format:

```
RATIONALE: [Concise conclusion with key assumptions]
EVIDENCE: [Data source: Stage N, stakeholder input, industry standard]

QUESTIONS FOR HUMAN:
1. [Question 1]
2. [Question 2]
...

WAIT FOR HUMAN INPUT.
```

### Sequential questions

The agent uses a **sequential questioning protocol** inside each stage:

- Questions are asked **one-by-one** with a progress indicator (e.g. `STAGE 1 - QUESTION 1/5`, then `QUESTION 2/5`, etc.)
- After each answer the agent shows a short confirmation, e.g. `✅ Answer recorded: [summary]`
- Before generating the stage deliverable, the agent presents a **summary of all your answers** for that step/stage

You can control the flow using high-level commands:

- `Next question` – skip current question and move to the next
- `Previous question` – go back to the previous question (within the same step)
- `Skip questions` – show all remaining questions at once (batch mode)

### How to Respond

Respond specifically, using question numbering:

```
1. YES - all documents in scope: invoices, delivery notes, orders
2. ERP: SAP Business One v10.0
3. Accounting: Comarch ERP Optima v2024.1
4. We don't currently have a DMS
5. KSeF deadline: July 1, 2026
```

If you don't know something:

```
I DON'T KNOW - I need to check with [person/department]
```

### Control Commands

| Command | Action |
|---------|--------|
| `BEGIN NEW PROJECT` | Start a new project with unique ID and timestamp |
| `SAVE PROJECT` | Save project state (available after completing a stage) |
| `LOAD PROJECT [project_id]` | Resume a saved project at the last active stage |
| `Approve [N]` | Approve stage N and proceed to next |
| `Reject [N] [reason]` | Reject stage N with reason |
| `Status` | Display progress of all stages for current project |
| `Pause` | Pause current session (auto-saves to journal) |
| `Export all` | Export all completed stage deliverables |
| `Deep analysis [topic]` | Activate deep reasoning for critical decisions |
| `Help` | Show all available commands |

---

## Output Files

Each project gets its own directory identified by a unique **Project ID** (e.g., `BABOK-20260208-M3R1`). The agent generates Markdown documents for each stage plus a persistent journal log.

**Canonical storage (MCP, CLI, plugin):** `projects/<project_id>/`

**Legacy CLI export default:** `BABOK_Analysis/` — only when using `babok run -o BABOK_Analysis`

```
projects/
└── BABOK-20260208-M3R1/                    # Project directory (unique per project)
    ├── PROJECT_JOURNAL_BABOK-20260208-M3R1.json  # State tracking journal
    ├── STAGE_00_Project_Charter.md
    ├── STAGE_01_Project_Initialization.md
    ├── STAGE_02_Current_State_Analysis.md
    ├── STAGE_03_Problem_Domain_Analysis.md
    ├── STAGE_04_Solution_Requirements.md
    ├── STAGE_05_Future_State_Design.md
    ├── STAGE_06_Gap_Analysis_Roadmap.md
    ├── STAGE_07_Risk_Assessment.md
    └── STAGE_08_Business_Case_ROI.md
```

The **Project Journal** (`PROJECT_JOURNAL_*.json`) tracks all stage transitions, approvals, decisions, and assumptions — enabling exact state restoration with `LOAD PROJECT`.

---

## Estimated Timeline

| Stage | Work with Agent | Internal Consultations | Total |
|------|----------------|----------------------|-------|
| Stage 1 | 30-45 min | 1-2 days | 1-2 days |
| Stage 2 | 1-2 hours | 3-5 days | ~1 week |
| Stage 3 | 45-60 min | 1-2 days | 2-3 days |
| Stage 4 | 2-3 hours | 3-5 days | ~1 week |
| Stage 5 | 1-2 hours | 2-3 days | 3-4 days |
| Stage 6 | 1 hour | 1 day | 1-2 days |
| Stage 7 | 45 min | 1 day | 1-2 days |
| Stage 8 | 1-2 hours | 2-3 days | 3-5 days |
| **TOTAL** | **8-12 hours** | **2-3 weeks** | **3-4 weeks** |

Most of the time is not spent working with the agent, but gathering data from stakeholders and internal consultations.

---

## Best Practices

**Do:**
- Read RATIONALE + EVIDENCE sections - you'll understand the agent's logic
- Be specific - "average 50 invoices/month" instead of "a lot"
- Approve sections progressively - you don't have to wait for the entire stage
- Correct immediately if the agent makes an error

**Don't:**
- Don't guess - say "I DON'T KNOW" if you don't know the answer
- Don't skip questions - each one has a justification
- Don't approve documents without reading them
- Don't mix stages - complete one before moving to the next

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent doesn't understand response | Rephrase more specifically, provide example |
| Agent asks about something you don't know | Respond "I DON'T KNOW" or mark as OPEN QUESTION |
| Error in earlier response | `CORRECTION in [Section X.Y]: [error description and fix]` |
| Document too technical | "Simplify section [X] for non-technical audience" |
| Change requirement priority | "Change requirement FR-015 from MUST to SHOULD. Reasoning: [...]" |
| Stage locked by another user | Wait for them to finish, or remove stale lock file after 2 h |
| `babok` command not found | Run `setup.bat` (Windows) or `npm link` in `cli/` |

---

## Security and Privacy

**Agent DOES NOT store:** passwords, API keys, bank account numbers, personal data (except roles).

**Agent MAY store:** organizational structure, business processes, aggregated metrics, system names.

The agent is designed in compliance with GDPR, BABOK Code of Conduct, and ISO 27001 principles.

---

## Test Suite

The repository currently runs **106 automated tests** (native `node:test` runner, ESM) covering CLI workflow, templates, Two-Key gate, plugin manifests, hooks, and uninstall flow:

| File | Tests | What It Covers |
|------|-------|----------------|
| `tests/unit/project.test.js` | 15 | Project ID generation, path resolution |
| `tests/unit/journal.test.js` | 16 | Journal CRUD, stage transitions |
| `tests/unit/two-key-gate.test.js` | 7 | Two-Key attestation guard and SHA checks |
| `tests/unit/scoring.test.js` | 14 | Quality scorer rubric logic |
| `tests/unit/validation.test.js` | 18 | Cross-stage validation rules |
| `tests/unit/templates.test.js` | 13 | Stage template manifest and rubric alignment |
| `tests/integration/cli-workflow.test.js` | 10 | End-to-end CLI workflow steps |
| `tests/plugin-manifest.test.cjs` | 12 | Marketplace/plugin manifest integrity |
| `tests/hooks.test.cjs` | 1 | Lifecycle hook wiring checks |
| `tests/uninstall.test.cjs` | 1 | External state uninstall behavior |

Run the tests:

```bash
npm test
```

---

## Additional Resources

- [IIBA BABOK Guide v3](https://www.iiba.org/babok-guide/)
- [IIBA Agile Extension](https://www.iiba.org/agile-extension/)
- [BABOK Glossary](https://www.iiba.org/babok-guide/glossary/)
- [`docs/`](docs/) — L2/L3 architecture, MCP tools specification, migration guide, workflow diagrams
- [`templates/`](templates/) — Ready-to-use BRD, Risk Register, Stakeholder Analysis, User Story templates
- [`knowledge/`](knowledge/) — 16 JSON benchmark, industry, regulatory, and anti-pattern reference files
- [`CHANGELOG.md`](CHANGELOG.md) — full version history
- [`RELEASE_NOTES.md`](RELEASE_NOTES.md) — detailed release notes per version

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

BABOK® is a registered trademark of the International Institute of Business Analysis (IIBA®).
This project is not officially endorsed by IIBA.

---

## Contributing

Contributions are welcome! Please feel free to submit:
- Bug reports and feature requests via GitHub Issues
- Pull requests for documentation improvements
- Sample analysis templates (anonymized)
- Translations to other languages

---

## Author

**Grzegorz Skuza**
- GitHub: [@GSkuza](https://github.com/GSkuza)
- Repository: [BABOK_ANALYST](https://github.com/GSkuza/BABOK_ANALYST)

---

**Version:** 2.2.8  
**Release Date:** July 2, 2026  
**Last Updated:** 2026-07-02
