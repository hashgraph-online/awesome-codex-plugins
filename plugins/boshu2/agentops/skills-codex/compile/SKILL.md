---
name: compile
description: Compile .agents knowledge wiki.
---
# Compile — Knowledge Compiler

> **Loop position:** move 7 (capture + ratchet) of the [operating loop](../../docs/architecture/operating-loop.md) — compiles promoted `.agents/` learnings into the interlinked wiki (the compound sub-step).

Reads raw `.agents/` artifacts and compiles them into a structured, interlinked
markdown wiki. Inspired by [Karpathy's LLM Knowledge Bases](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## What This Skill Does

The knowledge flywheel captures signal reactively (via `$post-mortem`,
`$forge`). `$compile` closes the loop by:

1. **Mining** unextracted signal from git and `.agents/` (existing)
2. **Growing** learnings via validation, synthesis, and gap detection (existing)
3. **Compiling** raw artifacts into interlinked wiki articles (NEW — the core value)
4. **Linting** the compiled wiki for contradictions, orphans, and gaps (NEW)
5. **Defragging** stale and duplicate artifacts (existing)

**No vector DB.** At personal scale (~100-400 articles), the compiled wiki fits
in context windows. The wiki IS the retrieval layer.

**Output:** `.agents/compiled/` — encyclopedia-style markdown with `[[backlinks]]`,
`index.md` catalog, and `log.md` chronological record.

## Pluggable Compute Backend

Set `AGENTOPS_COMPILE_RUNTIME` to choose the LLM backend:

| Value | Backend | Notes |
|-------|---------|-------|
| `codex-cli` | Local `codex` binary | Zero-config. Inherits your Codex CLI auth — no API key needed. Auto-selected if `codex` is on PATH and nothing else is set. |
| `ollama` | Ollama API | Default model: `gemma3:27b`. Set `OLLAMA_HOST` for remote (e.g., `ssh -L 11435:localhost:11435 bushido-windows`). |
| `claude` | Claude API (HTTP) | Uses `ANTHROPIC_API_KEY`. Model: `claude-sonnet-4-20250514`. |
| `openai` | OpenAI-compatible | Uses `OPENAI_API_KEY` + `OPENAI_BASE_URL`. |
| (unset) | Codex session | Compilation happens inline via the current session's LLM. |

When `AGENTOPS_COMPILE_RUNTIME` is unset, `ao compile` first tries to
auto-detect a local `codex` binary (codex-cli runtime). If that is also
absent, headless compile fails fast with an explicit error naming the env var
to set. Interactive `$compile` invocations still run compilation prompts
inline — the agent reading this SKILL.md IS the compiler.

### Runtime preference (override auto-detect)

To force a non-auto-detected runtime permanently (e.g. you have `claude`
installed but prefer Ollama for privacy), set it in
`~/.agentops/config.yaml`:

```yaml
compile:
  preferred_runtime: ollama
```

Precedence (high → low): `--runtime` flag, `AGENTOPS_COMPILE_RUNTIME`
env, `compile.preferred_runtime` config, `codex`-binary auto-detect,
empty (error).

### Large-corpus batching

`ao compile` passes `--batch-size` to the headless compiler (default `25`
changed files per LLM prompt). A fresh run against a 2000+ file corpus will
split into batches automatically instead of sending one giant prompt.

Flags:

- `--batch-size N` — files per batch (default 25)
- `--max-batches N` — cap batches per invocation; remaining files are picked
  up on the next run (default 0 = unlimited)

## Execution Steps

Phase-by-phase detail lives in [references/phases.md](references/phases.md).
Summary of modes:

- `$compile` — Full cycle: Mine → Grow → Compile → Lint → Defrag
- `$compile --compile-only` — Skip mine/grow, just compile + lint
- `$compile --lint-only` — Only lint the existing compiled wiki
- `$compile --defrag-only` — Only run defrag/cleanup
- `$compile --mine-only` — Only run mine + grow (legacy behavior)

The steps are:

1. **Mine** — extract signal from git + `.agents/research/` + complexity hotspots
2. **Grow** — LLM-driven validation, synthesis, gap detection; adjust learning confidence
3. **Compile** — inventory → topic extraction → wiki articles with `[[backlinks]]`
4. **Lint** — contradictions, orphans, missing cross-refs, stale claims
5. **Defrag** — prune stale, dedup near-duplicates, sweep oscillating goals, normalization scan
6. **Report** — write `.agents/compile/YYYY-MM-DD-report.md`

See [references/phases.md](references/phases.md) for the full per-phase
procedure, confidence-scoring table, auto-promotion rules, template
shapes for article / index / log / lint-report / compile-report, and
the normalization defect scan.

## Scheduling / Auto-Trigger

Lightweight defrag (prune + dedup, no mining or compilation) runs automatically at
session end via the `compile-session-defrag.sh` hook. This keeps the knowledge store
clean without requiring manual `$compile` invocations. The hook:

- Fires on every `SessionEnd` event after `session-end-maintenance.sh`
- Skips silently if the `ao` CLI is not available
- Runs only `ao defrag --prune --dedup` (no compilation or mining)
- Has a 20-second timeout to avoid blocking session teardown

For full compilation, invoke `$compile` manually or schedule the headless compiler
script with your host OS:

```bash
# Example: external cron entry for nightly compilation on bushido
0 3 * * * cd /path/to/repo && AGENTOPS_COMPILE_RUNTIME=ollama bash skills/compile/scripts/compile.sh --force
```

AgentOps exposes this flow through `ao compile`. If you want unattended
compilation, use your host scheduler (`launchd`, `cron`, `systemd`, CI, etc.)
to invoke `ao compile --force --runtime ollama` or call the lower-level
`bash skills/compile/scripts/compile.sh` directly.
If you want the broader out-of-session compounding loop, run it on the
out-of-session substrate (NTM + MCP + managed-agents) instead of inventing a
parallel Dream wrapper inside `$compile`.

## Interactive Modes

These modes describe the interactive `$compile` skill behavior:

| Mode | Description |
|------|-------------|
| `--compile-only` | Skip mine/grow, just compile + lint |
| `--lint-only` | Only lint the existing compiled wiki |
| `--defrag-only` | Only run defrag/cleanup |
| `--mine-only` | Only run mine + grow (legacy behavior) |
| `--full` | Full cycle: mine → grow → compile → lint → defrag |
| `--since 26h` | Time window for the mine phase |
| `--incremental` | Skip unchanged source files (hash-based) |
| `--force` | Recompile all articles regardless of hashes |

## Headless Script Flags

For unattended runs, `bash skills/compile/scripts/compile.sh` supports:

| Flag | Default | Description |
|------|---------|-------------|
| `--sources <dir>` | `.agents` | Source root for learnings, patterns, research, retros, forge, and knowledge |
| `--output <dir>` | `.agents/compiled` | Target directory for compiled wiki output |
| `--incremental` | on | Skip unchanged source files (hash-based) |
| `--force` | off | Recompile all articles regardless of hashes |
| `--lint-only` | off | Only run the lint pass on the existing compiled wiki |
| `--full` | on | Accepted for parity; default behavior already runs the full headless compile path |

## Examples

**User says:** `$compile` — Full Mine → Grow → Compile → Lint → Defrag cycle.

**User says:** `$compile --compile-only` — Just compile raw artifacts into wiki.

**User says:** `$compile --lint-only` — Scan existing wiki for health issues.

**User says:** `$compile --since 7d` — Mines with a wider window (7 days).

**Scheduled externally:** Nightly compilation on bushido GPU via Ollama.

**Pre-evolve warmup:** Run `$compile` before `$evolve` for a fresh, validated knowledge base.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ao mine` not found | ao CLI not in PATH | Use manual fallback in Step 1 |
| No orphaned research | All research already referenced | Skip 2b, proceed to synthesis |
| Empty mine output | No recent activity | Widen `--since` window |
| Oscillation sweep empty | No oscillating goals | Healthy state — no action needed |
| Ollama connection refused | Tunnel not running or wrong host | Run `ssh -L 11435:localhost:11435 bushido-windows` or check `OLLAMA_HOST` |
| Compilation too slow | Large corpus on small model | Use `--incremental` or switch to larger model |
| Hash file missing | First compilation | Normal — full compile runs, hashes saved after |

## Reference Documents

- [references/compile.feature](references/compile.feature) — Executable spec: Mine→Grow→Lint→Defrag rebuild, lint-not-autofix, incremental batching, evolve warmup (soc-qk4b)

- [references/phases.md](references/phases.md) — full per-phase procedure (mine → grow → compile → lint → defrag → report)
- [references/confidence-scoring.md](references/confidence-scoring.md)
- [references/knowledge-synthesis-patterns.md](references/knowledge-synthesis-patterns.md)
- [references/flywheel-diagnostics.md](references/flywheel-diagnostics.md)
