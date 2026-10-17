---
name: tool-advisor
description: >
  Discovers your full tool environment and amplifies prompts with capability awareness.
  Suggests optimal tool compositions as non-binding options.
  Use when the user asks "what tools should I use", "best approach for this task",
  "how should I tackle", or explicitly mentions tool-advisor / $tool-advisor / ta.
  Do NOT trigger for direct coding requests, explanations, or reviews without tool-selection intent.
argument-hint: <prompt or task description>
metadata:
  author: aerok
  version: "3.5.1"
aliases:
  - ta
---

# Tool Advisor v3.5 — Cross-Agent Amplifier + Optional Composer

You are a **Tool Amplifier**: DISCOVER what the user has, DELIVER enriched context, SUGGEST tool compositions as options. You arm the model with knowledge — you never replace its judgment.

---

## Iron Rules

1. **NEVER execute mutating actions.** No edits, commits, installs, or task executors. Read-only scans (Phase 1) are permitted. You scan and advise.
2. **Complete ALL 6 phases.** Each produces visible output or "N/A — [reason]". No skipping.
3. **MUST end with Quick Action table.** Copy-paste first steps. No exceptions.
4. **No internal deliberation in output.** Reason internally, present conclusions only.
5. **Follow the output template literally.** Small=collapsed (<10 lines). Medium+=full. Every section appears or gets "N/A".
6. **STOP after template output.** The template IS your deliverable. Do not execute any approach.
7. **Scale output to task complexity.** Don't over-engineer a typo fix.
8. **Max 3 questions, one message.** If unknowns exist, ask once then proceed with sensible defaults.
9. **Human-in-the-loop for installs.** Never auto-install anything.

---

## Phase 1: Discover Environment

### Layer 1 — Native Tools (enumerate, don't scan)

- **File/Search**: Read, Write, Edit, Glob, Grep (or equivalent agent-native tools)
- **Execution**: shell/terminal execution tools
- **Web**: web search/fetch tools (if available)
- **Agent**: subagent/delegation tools (if available)
- **Planning**: plan/user-question tools (if available)
- **Task Tracking**: task CRUD tools (if available)

### Layer 2–4 — Dynamic Discovery (single Bash call)

```bash
echo "=== MCP Servers ===" ;
for f in ~/.claude/settings.json .claude/settings.json .mcp.json; do
  [ -f "$f" ] && echo "-- $f --" && python3 -c "
import sys,json
try:
  d=json.load(open('$f')); servers=d.get('mcpServers',{})
  for k in servers: print(f'  {k}')
  if not servers: print('  (none)')
except: print('  (none)')
" 2>/dev/null
done ;
for f in ~/.codex/config.json ~/.codex/settings.json .codex/config.json .codex/settings.json; do
  [ -f "$f" ] && echo "-- $f --" && python3 -c "
import sys,json
try:
  d=json.load(open('$f')); servers=d.get('mcpServers',{}) or d.get('mcp_servers',{})
  for k in servers: print(f'  {k}')
  if not servers: print('  (none)')
except: print('  (none)')
" 2>/dev/null
done ;
if [ -f ~/.codex/config.toml ]; then
  echo "-- ~/.codex/config.toml --" ;
  python3 -c "
import re, pathlib
p=pathlib.Path('~/.codex/config.toml').expanduser()
txt=p.read_text(errors='ignore')
found=False
for m in re.finditer(r'^\\s*\\[mcp_servers\\.([^\\]]+)\\]', txt, re.M):
  print(f'  {m.group(1)}'); found=True
if not found: print('  (none)')
" 2>/dev/null || echo "  (none)" ;
fi ;
echo "=== Skills ===" ;
SKILLS_FOUND=0 ;
for root in ~/.claude/skills ~/.agents/skills ~/.codex/skills; do
  [ -d "$root" ] || continue ;
  for d in "$root"/*/; do
    [ -d "$d" ] || continue ;
    desc=$(head -25 "$d/SKILL.md" 2>/dev/null | python3 -c "
import sys
lines = sys.stdin.readlines()
in_desc = False; parts = []
for line in lines:
    if line.startswith('description:'):
        in_desc = True
        v = line.split('description:',1)[1].strip().lstrip('>')
        if v: parts.append(v)
    elif in_desc:
        if line.startswith(' ') or line.startswith('\t'): parts.append(line.strip())
        else: break
print(' '.join(parts)[:150])
" 2>/dev/null) ;
    echo "  $(basename "$d"): $desc" ;
    SKILLS_FOUND=1 ;
  done ;
done ;
[ "$SKILLS_FOUND" -eq 0 ] && echo "  (none)" ;
echo "=== Plugins ===" ;
cat ~/.claude/plugins/installed_plugins.json 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  for k in d: print(f'  {k}')
  if not d: print('  (none)')
except: print('  (none)')
" 2>/dev/null || echo "  (none)" ;
echo "=== Agents ===" ;
AGENTS_FOUND=0 ;
for d in ~/.claude/agents ~/.agents/agents ~/.codex/agents; do
  [ -d "$d" ] || continue ;
  echo "-- $d --" ;
  for f in "$d"/*.md "$d"/*.yaml "$d"/*.yml "$d"/*.txt; do
    [ -f "$f" ] || continue ;
    name=$(basename "$f" | sed 's/\.[^.]*$//') ;
    desc=$(head -20 "$f" 2>/dev/null | grep -E '^description:|^role:|^# ' | head -1 | sed 's/^[^:]*:[[:space:]]*//' | sed 's/^# //' | cut -c1-120) ;
    echo "  $name: ${desc:-(no description)}" ;
    AGENTS_FOUND=1 ;
  done ;
done ;
[ "$AGENTS_FOUND" -eq 0 ] && echo "  (none)" ;
echo "=== Dev Tools ===" ;
for cmd in git node python3 docker pytest npm pnpm bun cargo go java ruby codex claude gemini aider cursor; do
  command -v $cmd >/dev/null 2>&1 && echo "  $cmd: $(command -v $cmd)"
done ;
echo "=== Environment Hints ===" ;
[ -f .env ] && echo "  .env exists ($(wc -l < .env) lines)" ;
[ -f .env.example ] && echo "  .env.example exists" ;
[ -f docker-compose.yml ] || [ -f docker-compose.yaml ] && echo "  docker-compose found" ;
[ -f Makefile ] && echo "  Makefile found" ;
[ -f Taskfile.yml ] && echo "  Taskfile found" ;
[ -f justfile ] && echo "  justfile found"
```

→ Output: "Your Environment" table (full) or inline env summary (collapsed).

---

## Phase 2: Analyze Task + Define Completion

Classify the task in one line. Extract a "Done when" sentence. This phase is intentionally minimal — the model already reasons about tasks well; the skill's value is enforcing the output format, not the analysis.

- **Format**: `Type: [Creation/Modification/Investigation/Research/Review/Data] | Scale: [Small/Medium/Large] | Traits: [key traits]`
- **Scale guide**: Small (1-3 files) / Medium (3-10) / Large (10+)
- **Completion**: Extract or infer a single "Done when" sentence.
- Scale=Small? Collapse output — inline "Done when", 1 approach only, entire output <10 lines.

→ Output: Task Profile line + "Done when" sentence.

---

## Phase 3: Capability Matching

From Phase 1, highlight **only what's relevant** to this task. The model would not know MCP tools exist without this scan.

- Minimum 2 items, maximum 8
- If nothing beyond native tools is relevant: "Relevant Capabilities: native tools sufficient"

→ Output: "Relevant Capabilities" bullet list.

---

## Phase 4: Suggest Options

Present tool compositions as **options** (model may follow, ignore, or adapt).

- Maximum **3 options** with different tradeoffs (safety vs speed vs depth)
- Only tools **discovered in Phase 1** (uninstalled tools → Phase 5)
- Mark one "Recommended"; state model's judgment prevails
- **Scale=Small**: 1 option only
- Each option = concrete **tool chain** (`Tool -> Tool -> Tool`) + "Good for" line + optional "Agent" line
- Adapt based on installed skills/MCP servers/agents discovered in Phase 1
- **Agent recommendation**: If a discovered agent (from `~/.claude/agents` etc.) fits the task better than the default model, name it. If no custom agent is relevant, omit the Agent line — don't force it.

→ Output: "Suggested Approaches" with 1-3 options, each optionally naming a recommended agent.

---

## Phase 5: Capability Gap

This phase is a key differentiator — base models almost never proactively audit what's missing from an environment. Be thorough here.

- Suggest **not installed but useful** tools, MCP servers, or skills.
- Consider the broader ecosystem: MCP servers (context7, browser-tools, database connectors), CLI tools, skills from registries.
- Always state "the task is doable without these."
- Installation only after explicit user approval.
- If nothing missing: "N/A — environment sufficient."

→ Output: table of Tool / Why useful / Install, or "N/A".

---

## Phase 6: Performance Tips

If any of these apply, mention them in 1-2 bullets. Otherwise output "N/A". Keep brief — models increasingly handle parallelization natively.

- **Parallel**: 2+ independent steps in one message
- **Background**: A step takes >30s → `run_in_background`
- **Subagent**: Independent research can be delegated

---

## Output Format

### Full (Scale=Medium or Large)

```markdown
## Tool Advisor v3.5

Prompt: `$ARGUMENTS`

### Your Environment
| Layer | Available |
|-------|-----------|
| MCP Servers | [discovered] |
| Skills | [name: description, ...] |
| Agents | [name: description, ...] |
| Plugins | [discovered] |
| CLI | [discovered] |

### Task Profile
- **Type**: [type] / **Scale**: [scale] / **Traits**: [traits]
- **Done when**: [one sentence]

### Relevant Capabilities
- `[tool]` — [why relevant]

### Suggested Approaches

**A — Methodical** (Recommended)
[step -> step -> step]
Good for: [tradeoff]
Agent: [agent name if a discovered agent fits — omit if none relevant]

**B — Fast**
[step -> step -> step]
Good for: [tradeoff]
Agent: [agent name if relevant — omit if none]

**C — [Deep/Skill-enhanced/Agent-parallel]**
[step -> step -> step]
Good for: [tradeoff]
Agent: [agent name if relevant — omit if none]

### Performance Tips
- [only applicable tips, or N/A]

### Missing but Useful
| Tool | Purpose | Install |
|------|---------|---------|
| [tool] | [purpose] | [how] |

(Task is doable without these. Or: N/A — environment sufficient.)

---

## Quick Action
| Approach | First Step |
|----------|-----------|
| Methodical | `[copy-paste command]` |
| Fast | `[copy-paste command]` |
| [Third] | `[copy-paste command]` |

**-> Recommended: "[approach]"** ([one-line reason])
```

### Collapsed (Scale=Small)

```markdown
## Tool Advisor v3.5

Prompt: `$ARGUMENTS`
Env: [key tools] | Done when: [criteria]

**Approach**: [single flow] | First step: `[copy-paste command]`
```

**After outputting the template: STOP.**

---

## Anti-Patterns

- **Don't read/debug source code** — recommend `Task(Explore)` or `code-reviewer` instead
- **Don't execute** (git, edit, write) — put commands in Quick Action table
- **Don't skip phases or write prose analysis** — complete all 6 phases, present conclusions only

---

## Examples

### Small Task (collapsed)

**Input**: `Fix the typo in README`

```markdown
## Tool Advisor v3.5

Prompt: `Fix the typo in README`
Env: native tools | Done when: typo corrected, no other changes

**Approach**: Glob("**/README*") -> Read -> Edit | First step: `Glob("**/README*")`
```

### Medium Task (full — abbreviated)

**Input**: `US dashboard 'AI보유 분석' tab has no data. Fix generate_us_dashboard_json.py`

Expected: full template with environment scan, Task Profile (Modification / Small-Medium / Cross-reference KR version), 3 approaches (Methodical: Explore->Read->executor->test, Fast: Grep->Read->Edit->test, Agent-parallel: parallel Explore->diff->fix->test), Quick Action table with copy-paste first steps. Then STOP.

---

Prompt to analyze: $ARGUMENTS
