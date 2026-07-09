# Backend: Codex Sub-Agents

Concrete tool calls for spawning agents using Codex CLI (`codex exec`). Used for `--mixed` mode cross-vendor consensus and as the primary backend when running inside a Codex session with `spawn_agent`.

---

## Variant A: Codex CLI (from any runtime)

Used when `codex` CLI is available on PATH. Agents run as background shell processes.

**When detected:** `which codex` succeeds.

### Spawn: Background Shell Processes

```bash
# With structured output (preferred for council judges)
Bash(
  command='codex exec -s read-only -m gpt-5.3-codex -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-1.json "JUDGE PROMPT HERE"',
  run_in_background=true
)

# Without structured output (fallback)
Bash(
  command='codex exec --full-auto -m gpt-5.3-codex -C "$(pwd)" -o .agents/council/codex-1.md "JUDGE PROMPT HERE"',
  run_in_background=true
)
```

**Flag order:** `-s`/`--full-auto` → `-m` → `-C` → `--output-schema` → `-o` → prompt

**Valid flags:** `--full-auto`, `-s`, `-m`, `-C`, `--output-schema`, `-o`, `--add-dir`
**Invalid flags:** `-q` (doesn't exist), `--quiet` (doesn't exist), `-p` as a prompt flag (in Codex CLI it means profile)

### Wait: Poll Background Shell

```
TaskOutput(task_id="<shell-id>", block=true, timeout=120000)
```

Then read the output file:

```
Read(".agents/council/codex-1.json")
```

### Limitations

- No messaging — Codex CLI processes are fire-and-forget
- No debate R2 with Codex judges — they produce one verdict only
- `--output-schema` requires `additionalProperties: false` at all levels
- `--output-schema` requires ALL properties in `required` array
- `-s read-only` + `-o` works — `-o` is CLI-level post-processing, not sandbox I/O

---

## Variant B: Codex Sub-Agents (inside Codex runtime)

Used when running inside a Codex session where `spawn_agent` is available.

**When detected:** `spawn_agent` tool is in your tool list.

### Spawn

```
spawn_agent(message="You are judge-1.\n\nPerspective: Correctness & Completeness\n\n<PACKET>...</PACKET>\n\nWrite verdict to .agents/council/2026-02-17-auth-judge-1.md")
# Returns: agent_id

spawn_agent(message="You are worker-3.\n\nTask: Add password hashing\n...\n\nWrite result to .agents/swarm/results/3.json")
# Returns: agent_id
```

### Wait

```
wait(ids=["agent-id-1", "agent-id-2"])
```

**Timeout:** `wait()` blocks until completion. Set a timeout at the orchestration level (default: `COUNCIL_TIMEOUT=120s`). If an agent doesn't complete within the timeout, `close_agent` it and proceed with N-1 verdicts/workers.

### Message (retry/follow-up)

```
send_input(id="agent-id-1", message="Validation failed: fix tests and retry")
```

### Cleanup

```
close_agent(id="agent-id-1")
```

---

## Mixed Mode (Council)

For `--mixed` council, spawn runtime-native judges AND Codex CLI judges in parallel:

```
# Claude native team judges (via TeamCreate — see backend-claude-teams.md)
Task(subagent_type="general-purpose", team_name="council-20260217-auth", name="judge-1", prompt="...", description="Judge 1")
Task(subagent_type="general-purpose", team_name="council-20260217-auth", name="judge-2", prompt="...", description="Judge 2")

# Codex CLI judges (parallel background shells)
Bash(command='codex exec -s read-only -m gpt-5.3-codex -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-1.json "PACKET"', run_in_background=true)
Bash(command='codex exec -s read-only -m gpt-5.3-codex -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-2.json "PACKET"', run_in_background=true)
```

All four spawn in the **same message** — maximum parallelism.

**Mixed mode quorum:** At least 1 judge from each vendor should respond for cross-vendor consensus. If all judges from one vendor fail, proceed as single-vendor council and note the degradation in the report.

---

## Key Rules

1. **Pre-flight check:** `which codex` before attempting Codex CLI spawning
2. **Model availability:** `gpt-5.3-codex` requires API account — fall back to `gpt-4o` if unavailable
3. **Flag order matters** — agents copy examples exactly
4. **`codex review` is a different command** with different flags — do not conflate with `codex exec`
5. **No debate with Codex judges** — they produce one verdict, Codex CLI has no messaging
