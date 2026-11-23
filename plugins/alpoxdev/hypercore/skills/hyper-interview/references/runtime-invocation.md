# Runtime Invocation Metadata (`hyper-interview`)

`hyper-interview` is an opt-in requirements interview skill. Because agent hosts expose manual-only skill switches in different metadata surfaces, the skill keeps `routing_rule` inside `SKILL.md` as the load-bearing activation rule and ships optional host hints alongside it:

| Host / Runtime | Optional metadata surface | Behavior |
|---|---|---|
| Codex | `agents/openai.yaml` (`policy.allow_implicit_invocation: false`) | Prevents implicit model discovery activation while allowing explicit user invocation (`[doc]`). |
| Claude Code / `omp` | `SKILL.md` frontmatter `disable-model-invocation: true` | Marks the skill manual-only where supported so vague build prompts do not auto-trigger an interview (`[doc]`). |
| Antigravity (`agy`) & other hosts | Ignored as unknown optional metadata | Falls back cleanly to `<routing_rule>` in `SKILL.md`, which requires explicit user invocation by name before starting. |

Never rely on frontmatter switches alone: if a host ignores `disable-model-invocation` or `agents/openai.yaml`, `<routing_rule>` still forbids starting an interview without explicit user opt-in in the current turn.

## Sources

> Checked 2026-11-21.

| Claim | Source |
|---|---|
| `agents/openai.yaml` `allow_implicit_invocation` policy | <https://learn.chatgpt.com/docs/build-skills> |
| `disable-model-invocation` frontmatter flag | <https://code.claude.com/docs/en/skills.md>, <https://raw.githubusercontent.com/can1357/oh-my-pi/HEAD/docs/skills.md> |
| Runtime-only frontmatter fields must stay non-load-bearing (`SK-P-3`) | `instructions/skill/SKILL_AUTHORING.md` |
