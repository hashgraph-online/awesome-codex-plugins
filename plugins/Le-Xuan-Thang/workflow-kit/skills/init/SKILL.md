---
name: init
description: Use to initialize workflow-kit in any project with a guided step-by-step wizard. Defines Vision, Mission, Core, audits the system, configures LLMs, and sets lifecycle state to 'define'. Also triggers when the user says "set up workflow-kit", "define the product", "start a new project", or "configure my dev loop".
argument-hint: "[--rebenchmark] [--reset]"
allowed-tools: Read, Write, Bash
---

# Workflow Init — Product Definition Wizard

Guide the user through a complete workflow-kit setup: define Vision/Mission/Core, audit the environment, configure LLMs, write reviewer profiles, and set lifecycle state to `define`.

<HARD-GATE>
One question per message. Verify each step before advancing. Never dump a form.
</HARD-GATE>

## Phase 0: Handle flags

- `--reset` → delete `workflow/` and `workflow.yaml`, start fresh
- `--rebenchmark` → skip to **Phase 5: Benchmark**

## Phase 1: Check existing state

```bash
ls workflow/state.yaml 2>/dev/null && \
  python3 -c "import yaml; s=yaml.safe_load(open('workflow/state.yaml')); print('phase:', s.get('phase'), '| type:', s.get('product_type'))" \
  || echo "no-state"
```

If already initialized: "workflow-kit is in phase X. Reinitialize from scratch, or update config only?"

## Phase 2: Environment scan

Run silently, show one summary:

```bash
python3 --version 2>/dev/null || echo "python-missing"
python3 -c "import workflow_kit; print('runtime-ok')" 2>/dev/null || echo "runtime-missing"
ollama --version 2>/dev/null && echo "ollama-ok" || echo "ollama-missing"
curl -s http://localhost:11434/api/tags 2>/dev/null | \
  python3 -c "import sys,json; [print('model:', m['name']) for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null || echo "ollama-not-running"
free -g 2>/dev/null | awk '/^Mem:/{print "ram:"$2"GB"}' || \
  sysctl -n hw.memsize 2>/dev/null | awk '{printf "ram:%dGB\n",$1/1073741824}' || echo "ram:unknown"
[ -n "$OPENROUTER_API_KEY" ] && echo "openrouter-set" || \
  grep -s OPENROUTER_API_KEY .env 2>/dev/null && echo "openrouter-in-env" || echo "openrouter-missing"
git --version 2>/dev/null | head -1
```

Show summary:
```
Environment:
  Python     ✓ 3.x / ✗ missing
  Runtime    ✓ installed / ✗ will install
  Ollama     ✓ running (models: ...) / ✗ not installed
  RAM        X GB
  OpenRouter ✓ key set / ✗ missing
  Git        ✓
```

## Phase 3: Define — Vision

Ask:
> "Let's define your product. **Vision** first — what is this product's long-term direction? What does it become in 3–5 years?"

Wait. Write to `workflow/product.md` under `## Vision`.

## Phase 4: Define — Mission

Ask:
> "**Mission** — who does this product serve, and what urgent problem does it solve for them?"

Write to `workflow/product.md` under `## Mission`.

## Phase 5: Define — Core

Explain: "Core covers all systems available to build and run this product."

Run system scan:
```bash
uname -sm
free -g 2>/dev/null | awk '/^Mem:/{print "RAM:"$2"GB"}' || \
  sysctl -n hw.memsize 2>/dev/null | awk '{printf "RAM:%dGB\n",$1/1073741824}'
python3 --version; node --version 2>/dev/null; docker --version 2>/dev/null; git --version
[ -n "$OPENROUTER_API_KEY" ] && echo "OpenRouter: configured"
[ -n "$OPENAI_API_KEY" ] && echo "OpenAI: configured"
```

Ask:
> "A few more things I can't detect automatically:
> - Timeline and team size?
> - Main competitors or alternatives in this space?
> - Hard constraints (budget, tech stack, regulatory)?
> - Key documentation, papers, or standards to reference?"

Write complete `workflow/product.md`:

```markdown
# Product

## Vision
<user answer>

## Mission
### Who We Serve
<user answer>
### Problem We Solve
<user answer>

## Core
### Computing Environment
<from system scan>
### Software Environment
<from system scan>
### Cloud & APIs
<detected + user-specified>
### Documentation & Resources
<user answer>
### Constraints
<user answer: timeline, budget, team>
### Competitive Landscape
<user answer>
```

## Phase 6: Detect product type

```python
from workflow_kit.runtime.synthesizer import detect_product_type
import re, pathlib
text = pathlib.Path("workflow/product.md").read_text()
vision = re.search(r"## Vision\n(.*?)##", text, re.DOTALL)
print(detect_product_type(vision.group(1) if vision else text))
```

Confirm with user: "I detected this as a **<type>** project. Correct?"

## Phase 7: LLM setup

Ask:
> "How do you want to run the **worker LLM** (the model that builds your product)?
> A) Local (Ollama) — private, free, needs RAM/GPU
> B) Cloud (OpenRouter/OpenAI/Anthropic) — no GPU, has cost
> C) Hybrid — local worker + free DeepSeek orchestrator (recommended)"

**Path A — Local:**
- If Ollama missing → detect OS → show install command → verify → `ollama pull <model>`
- RAM-based model recommendation: ≥48GB→llama3.1:70b, ≥24GB→qwen2.5-coder:32b, ≥16GB→deepseek-coder-v2:16b, ≥8GB→llama3.1:8b
- Verify: `curl -s http://localhost:11434/v1/chat/completions -d '{"model":"<m>","messages":[{"role":"user","content":"ok"}],"max_tokens":3}'`

**Path B — Cloud:**
- Ask provider (OpenRouter/OpenAI/Anthropic) → show API key URL → verify key → choose model

**Path C — Hybrid:**
- Run Path A for worker
- For orchestrator: get OpenRouter key → verify DeepSeek free tier

## Phase 7b: Reviewer LLM setup

Ask:
> "Do you want to configure a **reviewer LLM** — a separate model that validates each worker output before marking tasks complete? This eliminates sycophancy bias when the same model reviews its own work.
> A) Yes — use a cloud API (Claude/OpenAI/OpenRouter) as reviewer, local model as worker (recommended)
> B) Yes — use the same endpoint as worker (simpler, still adds review step)
> C) No — skip reviewer (worker output accepted after syntax check only)"

**Path A or B:** Add `reviewers:` section to `workflow.yaml`:

```yaml
reviewers:
  - endpoint: "<chosen endpoint>"
    api_key: "<key or ${VAR}>"
    model: "<model name>"
```

**Path C:** Skip — no `reviewers:` key in workflow.yaml. Task auto-passes after syntax check.

Per-task override: any task JSON in `workflow/tasks/pending/` can include a `"reviewer": {"endpoint":…, "api_key":…, "model":…}` field to use a different reviewer for that specific task.

## Phase 8: Write workflow.yaml

```yaml
project:
  name: "<from product.md or dir name>"
  description: "<one-line mission>"
  root: "."

orchestrator:
  endpoint: "<value>"
  api_key: "<${VAR} or literal>"
  model: "deepseek/deepseek-chat:free"

worker:
  endpoint: "<value>"
  api_key: "<value>"
  model: "<value>"

reviewers:
  default_endpoint: "<same as worker>"
  default_api_key: "<same as worker>"
  default_model: "<same as worker>"

settings:
  work_hours: "9-21"
  auto_commit: true
  verify_syntax: true
  max_retries: 2
  dashboard_port: 7860
```

## Phase 9: Ensure runtime

```bash
python3 -c "import workflow_kit" 2>/dev/null || (
  pip install --quiet pyyaml python-dotenv &&
  pip install --quiet git+https://github.com/Le-Xuan-Thang/workflow-kit.git
)
```

## Phase 10: Create workflow/ directory structure

```bash
mkdir -p workflow/tasks/pending workflow/tasks/active workflow/tasks/review workflow/tasks/completed
mkdir -p workflow/reviewers workflow/output workflow/memory workflow/maintenance/jobs
```

## Phase 11: Write reviewer profiles

Based on product_type, write relevant profiles to `workflow/reviewers/<domain>.md` using defaults from `workflow_kit.runtime.reviewer.DEFAULT_PROFILES`:

```python
from workflow_kit.runtime.reviewer import DEFAULT_PROFILES
from pathlib import Path

TYPE_REVIEWERS = {
    "webapp":   ["code-reviewer", "designer", "devops"],
    "library":  ["code-reviewer", "editor"],
    "paper":    ["researcher", "editor"],
    "article":  ["editor"],
    "api":      ["code-reviewer", "devops"],
    "dataset":  ["data-scientist", "researcher"],
}
product_type = "<detected>"
for domain in TYPE_REVIEWERS.get(product_type, ["code-reviewer"]):
    Path(f"workflow/reviewers/{domain}.md").write_text(DEFAULT_PROFILES[domain])
    print(f"  wrote workflow/reviewers/{domain}.md")
```

## Phase 12: Initialize lifecycle state

```python
from workflow_kit.runtime.state import WorkflowState, save_state
from pathlib import Path
state = WorkflowState(phase="define", product_type="<detected>")
save_state(state, Path("."))
print("State: phase=define")
```

## Phase 13: Benchmark

```bash
python -m workflow_kit benchmark
```

## Phase 14: Update .gitignore

Append if missing:
```
workflow/
workflow.yaml
.env
```

## Phase 15: Final report

```
╔══════════════════════════════════════════════════════════╗
║         workflow-kit initialized ✓                       ║
╚══════════════════════════════════════════════════════════╝

  Product:      <name>
  Type:         <product_type>
  Phase:        define
  Worker:       <model>
  Orchestrator: <model>
  Reviewers:    <domain list>

  Files:
    ✓ workflow/product.md
    ✓ workflow/state.yaml       (phase: define)
    ✓ workflow/reviewers/       (<N> profiles)
    ✓ workflow.yaml

  Next:
    Edit workflow/product.md if needed, then:
    /workflow-kit:plan  — generate your workplan
```
