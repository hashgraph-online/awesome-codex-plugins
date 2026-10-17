# workflow-kit

[![CI](https://github.com/Le-Xuan-Thang/workflow-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/Le-Xuan-Thang/workflow-kit/actions/workflows/ci.yml)

A **full product lifecycle plugin** for Claude Code, Codex CLI, OpenCode, and Gemini CLI.

Define your product's Vision, Mission, and Core → generate a structured workplan → execute with mandatory domain-expert reviewer agents → synthesize deliverables → maintain.

The product can be anything: a webapp, a research paper, a library, an API, an article, a dataset. The workflow adapts automatically.

---

## Philosophy

**Everything needs a reviewer.** No task is complete until a domain-expert reviewer agent has validated the output. The worker builds; the reviewer validates. These are separate agent processes — the reviewer is mandatory infrastructure, not optional.

**The product defines the workflow.** A webapp needs a code-reviewer and a devops reviewer. A research paper needs a researcher reviewer. An article needs an editor. workflow-kit detects your product type from your Vision and creates the right reviewer profiles automatically.

**User is always the admin.** Agents execute; you decide. You approve transitions between phases. Feedback at synthesis creates sub-tasks that loop back through execution — you never lose control of direction.

---

## Lifecycle

```
┌─────────┐    ┌──────┐    ┌─────────┐    ┌───────────┐    ┌──────────┐
│  DEFINE  │───▶│ PLAN │───▶│ EXECUTE │───▶│ SYNTHESIZE│───▶│ MAINTAIN │
└─────────┘    └──────┘    └─────────┘    └───────────┘    └──────────┘
  Vision +            Objectives     Agent+Reviewer     Package +       Scheduled
  Mission +           + Tasks        pairs per task     User review     jobs
  Core +                                  ▲                  │
  System audit                            └──────────────────┘
                                          feedback loop
```

State tracked in `workflow/state.yaml`. Each phase requires user approval to advance.

---

## New in v0.3: Tier 1 Features

### Cross-provider reviewer

Use a different LLM provider for reviews than for worker tasks — eliminates sycophancy bias when a model reviews its own output.

```yaml
# workflow.yaml
reviewers:
  - endpoint: "https://api.anthropic.com/v1/messages"
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-haiku-4-5-20251001"
```

Per-task override: add a `"reviewer"` field to any task JSON in `workflow/tasks/pending/<id>.json` to use a different reviewer for that specific task:

```json
{
  "task_id": "feat-007",
  "reviewer": {
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4o"
  }
}
```

### Checkpoint & Resume

If the dispatcher crashes mid-task (power loss, OOM, Ctrl+C), workflow-kit recovers automatically on next startup. File snapshots are written before each task begins and deleted when the task completes.

```bash
# Auto-detected on every startup. If dispatcher crashed mid-task:
python -m workflow_kit start              # automatically recovers + retries interrupted task
python -m workflow_kit start --resume     # same, explicit flag for clarity
```

### Parallel execution

Run multiple tasks concurrently. Tasks that share files are never run in parallel — conflict detection is automatic.

```yaml
# workflow.yaml
settings:
  max_parallel_tasks: 3  # run up to 3 tasks concurrently (default: 1)
```

### AgentOps metrics

Every completed task records timing, retry count, and reviewer pass/fail to `.workflow/metrics.jsonl`. View the dashboard via:

```
/workflow-kit:status   →  shows metrics dashboard
```

Or from CLI:

```bash
python -m workflow_kit status
```

---

## Skills

| Skill | Phase | What it does |
|---|---|---|
| `/workflow-kit:init` | define | Guided wizard: Vision/Mission/Core + system audit + LLM setup + reviewer profiles |
| `/workflow-kit:plan` | plan | Orchestrator generates objectives + tasks from `workflow/product.md` |
| `/workflow-kit:execute` | execute | Dispatcher runs tasks; spawns reviewer agent after each |
| `/workflow-kit:synthesize` | synthesize | Packages output by product type; presents to user; handles feedback loop |
| `/workflow-kit:maintain` | maintain | Creates and runs scheduled maintenance jobs |
| `/workflow-kit:status` | any | Inline phase + dispatcher + task counts + reviewer results |
| `/workflow-kit:monitor` | any | Live TUI or web dashboard |

---

## Installation

### Claude Code

```bash
# Step 1: add the marketplace (one time only)
claude plugin marketplace add Le-Xuan-Thang/workflow-kit

# Step 2: install the plugin
claude plugin install workflow-kit
```

Restart Claude Code. Skills available as `/workflow-kit:init`, `/workflow-kit:plan`, etc.

### Codex CLI

```bash
# Step 1: add the marketplace
codex plugin marketplace add Le-Xuan-Thang/workflow-kit

# Step 2: install the plugin
codex plugin add workflow-kit@Le-Xuan-Thang
```

Skills callable as `$workflow-kit:init`, `$workflow-kit:execute`, etc.

### OpenCode

```bash
opencode plugin github:Le-Xuan-Thang/workflow-kit
```

Skills are copied to `~/.config/opencode/skills/` automatically.

### Gemini CLI

Add to `~/.gemini/config.yaml`:

```yaml
plugins:
  - source: github:Le-Xuan-Thang/workflow-kit
    name: workflow-kit
```

### Standalone CLI (no AI tool needed)

```bash
git clone https://github.com/Le-Xuan-Thang/workflow-kit.git
cd workflow-kit
pip install pyyaml python-dotenv
python -m workflow_kit --help
```

---

## Quick Start

### 1. Install runtime dependencies

```bash
pip install pyyaml python-dotenv
```

### 2. Run the init wizard

```
/workflow-kit:init
```

The wizard will:
1. Scan your environment (Python, Ollama, RAM, API keys, Git)
2. Ask for your product's **Vision** — long-term direction (3–5 years)
3. Ask for your **Mission** — who you serve, what problem you solve
4. Ask for **Core** context — timeline, team, constraints, competitive landscape
5. Detect product type from your Vision (webapp / paper / library / article / api / dataset)
6. Guide you through LLM setup (local Ollama or cloud API)
7. Write `workflow/product.md`, `workflow.yaml`, and reviewer profiles
8. Benchmark the worker model (2–5 min)

### 3. Generate a workplan

```
/workflow-kit:plan
```

DeepSeek reads your `workflow/product.md` and worker capability profile, then creates objectives aligned to your Vision and tasks matched to what your worker can actually do.

Review `workflow/workplan.md`, then:

### 4. Execute

```
/workflow-kit:execute
```

The dispatcher runs the loop:
```
pick task → worker builds → reviewer validates
  PASS → mark done → plan next task
  FAIL → retry with feedback (up to max_retries) → escalate to user
```

Check progress anytime:
```
/workflow-kit:status
```

### 5. Synthesize and review

When all tasks are done:

```
/workflow-kit:synthesize
```

Packages deliverables appropriate to your product type and presents them for your review. You can:
- **Approve** → move to maintenance
- **Give feedback** → creates sub-tasks, loops back to execute
- **Reject specific items** → targeted rework

### 6. Maintain (optional)

```
/workflow-kit:maintain
```

Sets up scheduled maintenance jobs (dependency audits, health checks, citation freshness, etc.) matched to your product type.

---

## Product Types

workflow-kit detects your product type from the Vision and adapts accordingly:

| Type | Reviewer profiles | Deliverables | Maintenance jobs |
|---|---|---|---|
| `webapp` | code-reviewer, designer, devops | Code repo, Deployed URL, User guide | Dependency audit, Uptime check |
| `library` | code-reviewer, editor | Package, API docs, CHANGELOG | Compat check, CVE scan |
| `paper` | researcher, editor | Document (PDF/MD), Bibliography | Citation freshness, Related-work scan |
| `article` | editor | Formatted text, Assets | Revision reminders |
| `api` | code-reviewer, devops | OpenAPI spec, Endpoint, Postman | Health check, Schema drift |
| `dataset` | data-scientist, researcher | Data files, Data card, Methodology | Quality audit, License check |

---

## Reviewer Agent System

Every task has two agents: a **worker** (builds) and a **reviewer** (validates). The reviewer is a separate agent process with a domain-specific system prompt.

**Domain detection** is automatic from task type and description:

| Task content | Reviewer domain |
|---|---|
| Code, feature, bugfix, refactor | `code-reviewer` |
| Writing, article, docs, README | `editor` |
| Research, literature, analysis | `researcher` |
| UI, architecture, schema | `designer` |
| Data, ML pipeline, analysis | `data-scientist` |
| Deploy, infra, CI/CD | `devops` |

**Review cycle:**
```
Worker completes task
    │
    ▼
Reviewer spawned with task spec + output + domain expertise
    │
    ├── PASS → task marked done, orchestrator plans next
    └── FAIL → feedback appended, task retried (max_retries)
                    │
              After max retries: escalate to user
              A) Skip  B) Retry with guidance  C) Redesign
```

Reviewer profiles live in `workflow/reviewers/<domain>.md` — created by `init`, customizable.

---

## File Structure

Created by `/workflow-kit:init`, kept out of git:

```
workflow/
├── state.yaml              ← current phase, product_type, task counts
├── product.md              ← Vision / Mission / Core
├── system.md               ← hardware, software, cloud, constraints, competitive
├── workplan.md             ← objectives + tasks (human-readable)
├── tasks/
│   ├── pending/            ← tasks waiting to run
│   ├── active/             ← task currently executing
│   ├── review/             ← awaiting reviewer agent
│   └── completed/          ← done (pass/fail + reviewer notes)
├── reviewers/
│   └── <domain>.md         ← reviewer agent profiles (editable)
├── output/
│   ├── report.md           ← synthesis report
│   └── [deliverables]      ← product files
├── memory/
│   ├── decisions.md        ← append-only decisions log
│   └── progress.md         ← progress snapshots
└── maintenance/
    └── jobs/               ← scheduled maintenance task JSONs
```

---

## Configuration — `workflow.yaml`

Created by `/workflow-kit:init`. Edit as needed.

### Minimal

```yaml
project:
  name: "my-project"
  description: "One-line mission"
  root: "."

orchestrator:
  endpoint: "https://openrouter.ai/api/v1/chat/completions"
  api_key: "${OPENROUTER_API_KEY}"
  model: "deepseek/deepseek-chat:free"

worker:
  endpoint: "http://localhost:11434/v1/chat/completions"
  api_key: "ollama"
  model: "llama3.1:70b"

# Optional: cross-provider reviewer (recommended — eliminates sycophancy bias)
reviewers:
  - endpoint: "https://api.anthropic.com/v1/messages"
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-haiku-4-5-20251001"

settings:
  work_hours: "9-21"
  auto_commit: true
  verify_syntax: true
  max_retries: 2
  dashboard_port: 7860
```

### Multi-model fallback chain

```yaml
workers:
  - endpoint: "http://localhost:11434/v1/chat/completions"
    api_key: "ollama"
    model: "llama3.1:70b"
  - endpoint: "http://localhost:11434/v1/chat/completions"
    api_key: "ollama"
    model: "qwen2.5-coder:32b"   # fallback if 70b unavailable

orchestrators:
  - endpoint: "https://openrouter.ai/api/v1/chat/completions"
    api_key: "${OPENROUTER_API_KEY}"
    model: "deepseek/deepseek-chat:free"
  - endpoint: "https://openrouter.ai/api/v1/chat/completions"
    api_key: "${OPENROUTER_API_KEY}"
    model: "deepseek/deepseek-chat"   # paid fallback
```

### Settings reference

| Key | Default | Description |
|---|---|---|
| `work_hours` | `"9-21"` | Dispatch tasks during these hours only. `"0-24"` = always. |
| `auto_commit` | `true` | Git commit after each successful task |
| `verify_syntax` | `true` | Syntax check before accepting worker output |
| `max_retries` | `2` | Reviewer FAIL retries before escalating to user |
| `dashboard_port` | `7860` | Web dashboard port |
| `max_parallel_tasks` | `1` | Number of tasks to run concurrently. Tasks sharing `files_to_modify` are never run in parallel. |
| `reviewer` | — | Per-task field in task JSON to override the global reviewer config. |

---

## CLI Reference

All skills are also callable directly from the terminal (no AI tool needed):

```bash
python -m workflow_kit benchmark          # profile worker model
python -m workflow_kit workplan           # generate tasks from workflow/product.md
python -m workflow_kit execute            # start dispatcher loop
python -m workflow_kit synthesize         # package deliverables
python -m workflow_kit maintain           # list maintenance jobs
python -m workflow_kit status             # print lifecycle status
python -m workflow_kit stop               # stop dispatcher
python -m workflow_kit stop --report      # stop + generate morning report
python -m workflow_kit schedule \         # overnight cron
  --start 21:00 --stop 09:00 --recurring
```

---

## Overnight Scheduling

Let the dispatcher run while you sleep:

```bash
# Run tonight 21:00–09:00, generate report at stop
python -m workflow_kit schedule --start 21:00 --stop 09:00

# Recurring every night
python -m workflow_kit schedule --start 21:00 --stop 09:00 --recurring

# Stop with morning report
python -m workflow_kit stop --report
# Saves to workflow/output/reports/YYYY-MM-DD.md
```

---

## Platform Compatibility

| Feature | Claude Code | Codex CLI | Codex App | OpenCode | Gemini CLI | Terminal |
|---|---|---|---|---|---|---|
| All 7 skills | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| `python -m workflow_kit` CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Background dispatcher | ✅ | ✅ | ⚠️ web dashboard | ✅ | ✅ | ✅ |
| TUI monitor | ✅ | ✅ | ❌ sandboxed | ✅ | ✅ | ✅ |
| Web dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Git auto-commit | ✅ | ✅ | ⚠️ use App UI | ✅ | ✅ | ✅ |
| Overnight schedule | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |

**Codex App note:** The sandbox blocks `git push` and terminal control. The dispatcher still runs and commits — use the App's "Create branch" button to push when done. Use `/workflow-kit:monitor --web` instead of TUI.

---

## Troubleshooting

### `workflow/product.md not found`
Run `/workflow-kit:init` first. Make sure you're running from the project root.

### `worker_capability.json not found`
Run `/workflow-kit:init` (or `python -m workflow_kit benchmark`) to benchmark the worker.

### Phase mismatch warning
Skills check `workflow/state.yaml` before acting. If you see "phase is X, expected Y", run the correct skill for your current phase or use `--reset` to start over.

### Reviewer keeps failing tasks
Check `workflow/tasks/completed/` for failed task JSONs — they contain the reviewer's exact feedback. Options:
- Edit `workflow/reviewers/<domain>.md` to adjust the review criteria
- Lower `max_retries` in `workflow.yaml` to escalate sooner
- After escalation, choose "Retry with your guidance" and describe the fix

### Ollama not running
```bash
ollama serve
ollama pull llama3.1:70b  # or your chosen model
```

### `OPENROUTER_API_KEY` not set
```bash
export OPENROUTER_API_KEY=sk-or-...
# or add to .env in your project root
```

### `pyyaml` or `python-dotenv` not found
```bash
pip install pyyaml python-dotenv
```

---

## License

MIT — see [LICENSE](LICENSE).
