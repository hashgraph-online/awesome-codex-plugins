---
name: live-editor
description: Control and verify a running Unity Editor with the low-token hera-agent-unity CLI.
---

# Hera Unity live editor

Use `hera-agent-unity` whenever work depends on the real Unity Editor state. Prefer dedicated commands over arbitrary C# execution.

## Bootstrap

Run these commands in order when first connecting:

```bash
hera-agent-unity doctor --json
hera-agent-unity status
hera-agent-unity list --compact
```

Report the project, port, Unity version, state, and tool count. If Unity is unreachable, ask the user to open the project with the connector installed.

## Working loop

1. Read only the state needed for the task.
2. Apply the scene, Inspector, asset, or code change.
3. Compile or re-read the changed state.
4. Check recent console errors.
5. Run focused tests or Play Mode checks when behavior changed.

Useful commands:

```bash
hera-agent-unity scene info
hera-agent-unity console --type error --lines 20
hera-agent-unity editor refresh --compile
hera-agent-unity editor play --wait
hera-agent-unity test --mode PlayMode
hera-agent-unity screenshot --view game
```

## Efficiency and safety

- Use `list --compact`, bounded console reads, and shallow `exec --depth 1` responses.
- Prefer `scene`, `console`, `editor`, `test`, `describe_type`, and other dedicated commands over `exec`.
- Batch related side effects into one `exec`; return `null` or omit the return.
- Never return a `UnityEngine.Object` directly. Return only the fields needed.
- Branch on structured error `code`, not message text.
- Throw or use `--strict` when a logical failure must produce a non-zero exit.
- Treat `input` commands as Unity EventSystem QA, not proof of a physical OS click.

The complete command and agent guide is at <https://github.com/NotNull92/hera-agent-unity/blob/main/AGENTS.md>.
