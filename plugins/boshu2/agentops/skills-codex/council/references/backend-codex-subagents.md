# Backend: Codex Session Agents and CLI Judges

Concrete agent calls for council judges when running inside a Codex session, plus Codex CLI judge commands for strict `--mixed` mode.

---

## Spawn

Spawn one judge per perspective.

```text
spawn_agent(message="You are judge-1.

Perspective: correctness
Task: validate the target
Target files: ...

Write your analysis to .agents/council/judge-1.md.")

spawn_agent(message="You are judge-2.

Perspective: completeness
Task: validate the target
Target files: ...

Write your analysis to .agents/council/judge-2.md.")
```

## Wait

Wait for the agent ids returned by `spawn_agent`.

```text
wait_agent(targets=["agent-id-1", "agent-id-2"])
```

If one judge needs a correction, use `send_input` with a short follow-up prompt.

## Cleanup

Use `close_agent` for any judge you no longer need.

```text
close_agent(target="agent-id-1")
```

## Mixed Mode: Codex CLI Judges

For `$council --mixed`, run 3 runtime-native judges with `spawn_agent(...)` and 3 Codex CLI judges with `codex exec`.

Pre-flight is strict:

1. `command -v codex` must succeed.
2. `codex --version` must succeed.
3. If `COUNCIL_CODEX_MODEL` is set, a dry `codex exec` smoke call with that model must succeed.

If any pre-flight fails, stop before spawning any judges. Do not silently run a runtime-native-only council.

```bash
mkdir -p .agents/council
codex exec -s read-only -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-1.json "$PACKET"
codex exec -s read-only -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-2.json "$PACKET"
codex exec -s read-only -C "$(pwd)" --output-schema skills/council/schemas/verdict.json -o .agents/council/codex-3.json "$PACKET"
```

Only add `-m "$COUNCIL_CODEX_MODEL"` when the override is explicitly set. If `--output-schema` is unsupported, use `.md` output as an output-format fallback; Codex itself is still required.

## Key Rules

1. One judge, one perspective.
2. Keep the durable analysis in the output file.
3. Use `send_input` only for short steering messages.
4. In `--mixed`, require at least one responded judge from each vendor for cross-vendor consensus.
